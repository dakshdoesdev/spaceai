<!-- refreshed: 2026-05-09 -->
# Architecture

**Analysis Date:** 2026-05-09

## Hackathon framing (read first)

KilnWatch is **the AI workload that would run on a satellite**, not a satellite. It is built for the Liquid AI x DPhi Space *AI in Space* hackathon. Two layers — `satellite_edge_node/` (the would-be onboard pipeline) and `kilnwatch/ground_station.py` + `app.py` (the operator dashboard) — communicate **only** through the `transmission_queue/` folder. That folder is the simulated radio link. Everything in this document describes that simulation; nothing in this repo runs in orbit.

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                    Tile sources (local disk)                │
├──────────────────┬──────────────────┬───────────────────────┤
│  Demo tiles      │  Final demo set  │  SimSat fetches       │
│ `data/raw_tiles` │ `data/final_     │ `data/raw/`,          │
│ (placeholders)   │  demo_tiles/`    │ `data/metadata/`      │
│                  │ (real Roboflow   │ via                   │
│                  │  brick-kiln imgs)│ `kilnwatch/ingestion/`│
└────────┬─────────┴────────┬─────────┴──────────┬────────────┘
         │                  │                     │
         └──────────────────┴────────┬────────────┘
                                     ▼
┌─────────────────────────────────────────────────────────────┐
│      SATELLITE EDGE LAYER (the simulated onboard AI)        │
│                                                             │
│  discover_tiles()                                           │
│    `satellite_edge_node/orbital_pass.py`                    │
│         │                                                    │
│         ▼                                                    │
│  detector (strict YOLO, baseline, or fallback)              │
│    `satellite_edge_node/detectors.py`                       │
│    `satellite_edge_node/yolo_detector.py`                   │
│    `satellite_edge_node/baseline_detector.py`               │
│         │   → DetectionResult (frozen dataclass)            │
│         ▼                                                    │
│  reasoner (optional Liquid LFM2.5-VL-450M)                  │
│    `satellite_edge_node/liquid_vlm_reasoner.py`             │
│         │   → VlmReasoning (frozen dataclass) | None        │
│         ▼                                                    │
│  payload + crop + telemetry builder                         │
│    `satellite_edge_node/payloads.py`                        │
│         │                                                    │
└─────────┼────────────────────────────────────────────────────┘
          │   (writes through the simulated radio link)
          ▼
┌─────────────────────────────────────────────────────────────┐
│      `transmission_queue/`  ← THE QUEUE BOUNDARY            │
│      `transmission_queue/<tile_id>.json`     payloads        │
│      `transmission_queue/crops/<tile_id>_crop.png`           │
│      `transmission_queue/telemetry.jsonl`    every tile      │
│      `telemetry_logs/sample_mission.jsonl`   sample replay   │
└─────────┬────────────────────────────────────────────────────┘
          │   (read only — never anything upstream)
          ▼
┌─────────────────────────────────────────────────────────────┐
│             GROUND STATION LAYER                            │
│  domain helpers   `kilnwatch/ground_station.py`             │
│  Streamlit UI     `app.py`                                  │
│  simple replay UI `ground_station_ui/app.py`                │
│                   `ground_station_ui/queue_reader.py`       │
└─────────────────────────────────────────────────────────────┘
```

## The queue boundary is the central invariant

Everything else in this architecture flows from one rule:

> The ground-station layer reads `transmission_queue/`, `telemetry_logs/`, and (legacy) `telemetry/` — and **nothing else upstream**. It does not import anything from `satellite_edge_node/`. It does not open `data/raw_tiles/`, `data/final_demo_tiles/`, or `datasets/roboflow/`. It does not even let `.tile` placeholder paths leak into UI code.

This rule is enforced **in code** by `tests/test_ground_station_boundary.py`. That test scans every ground-station surface file (`app.py`, `kilnwatch/ground_station.py`, every `ground_station_ui/*.py`) and asserts that none of these strings appear:

| Forbidden string | Why |
|------------------|-----|
| `satellite_edge_node` | UI must not import the onboard pipeline |
| `data/raw_tiles` | UI must not read raw onboard inputs |
| `data/final_demo_tiles` | UI must not read raw onboard inputs |
| `datasets/roboflow` | UI must not read raw onboard inputs |
| `raw_tiles` | UI must not refer to raw onboard inputs |
| `'.tile` / `".tile` | UI must not use placeholder fixtures as previews |

The single legitimate exception is `kilnwatch/ground_station.py`'s `FORBIDDEN_CROP_SOURCE_FRAGMENTS` constant — the boundary scanner partitions that constant block out before checking. That constant is what gives the runtime side of the boundary teeth: `_safe_crop_path()` (`kilnwatch/ground_station.py:412`) refuses to render any crop reference whose path string contains a forbidden fragment, ends in `.tile`, or escapes the queue root.

If you are adding a new ground-station feature and you find yourself wanting to import a satellite module or peek at a raw tile path: stop. Add the field to the payload (`satellite_edge_node/payloads.py`) or to telemetry (`satellite_edge_node/orbital_pass.py`) and let the queue carry it. That is the architecture.

## The two gates (this is the easy thing to get backwards)

The pipeline has two decision points that decide bytes-on-the-wire. They are not interchangeable.

### Gate 1 — `triage_label(detection, vlm_reasoning, *, min_confidence)` → `should_transmit_triage(decision)` — **4-tier transmit gate**

**Lives in:** `satellite_edge_node/payloads.py` (`triage_label`, `transmission_action_for`, `should_transmit_triage`, `crop_required_for`, `full_tile_required_for`).
**Decides:** what — if anything — leaves the satellite for this tile, *and* what shape it takes.

Mapping is one-to-one:

| `TriageDecision`     | `transmission_action_for(decision)`  | What is written to the queue |
|----------------------|--------------------------------------|------------------------------|
| `IGNORE`             | `DROP_RAW_TILE`                      | telemetry only — no payload  |
| `JSON_ALERT_ONLY`    | `TRANSMIT_JSON_ONLY`                 | `<tile_id>.json` (no `crop_ref`, no `full_tile_ref`) |
| `CROP_OR_REVIEW`     | `TRANSMIT_ALERT`                     | `<tile_id>.json` + `crops/<tile_id>_crop.png` |
| `FULL_DOWNLINK`      | `TRANSMIT_FULL_TILE`                 | `<tile_id>.json` + crop + `full_tiles/<tile_id>_full.<ext>` (raw tile copied) |

**Logic:** detector kiln/confidence + risk band chosen by triage (Liquid's `compliance_risk` if reasoning was attached, otherwise the detector's). `compute_triage()` accepts `min_confidence` so the IGNORE band aligns with the detector's gating threshold (the orbital pass passes `confidence_threshold=0.25`, not the triage default of `0.45`, to avoid spurious IGNORE-on-transmitted mismatches).
**Driven by:** `"liquid+yolo"` when `vlm_reasoning is not None`, otherwise `"yolo-only"`. Recorded in `triage["driven_by"]`.

The orbital pass loop (`satellite_edge_node/orbital_pass.py`) computes the decision once per tile, dispatches crop generation only when `crop_required_for(decision)` is true, dispatches full-tile copy only when `full_tile_required_for(decision)` is true, and writes the JSON payload only when `should_transmit_triage(decision) or write_drop_payloads`. `--require-crops` enforces a real crop only on the two tiers that need one.

Every payload (transmitted) and every telemetry record carries:

```jsonc
"triage_decision": "CROP_OR_REVIEW",
"action":          "TRANSMIT_ALERT",
"triage": {
    "decision":        "CROP_OR_REVIEW",
    "reason":          "Kiln detected with medium/high risk; ...",
    "risk_band_used":  "medium",
    "risk_score_used": 0.55,
    "driven_by":       "liquid+yolo"
}
```

The legacy `should_transmit_alert(detection)` boolean (`payloads.py`) is preserved for backward-compatible callers but is no longer the runtime gate; the 4-tier path is.

### Gate 2 — `safe_review_payloads(payloads)` — **ground-side crop-evidence filter**

**Lives in:** `kilnwatch/ground_station.py:148`
**Decides:** which received payloads are eligible to render a crop image in the dashboard.
**Logic:** `_decision(payload) in REVIEW_DECISIONS` where `REVIEW_DECISIONS = {"CROP_OR_REVIEW", "FULL_DOWNLINK"}`.
**Driven by:** the `triage_decision` field that Gate 1 stamped on the payload upstream.

The dashboard never re-decides what to show; it only renders what the satellite already decided to send.

### One-line summary

> **Gate 1** is the 4-tier triage that decides what leaves the satellite (drop / JSON-only / JSON+crop / JSON+crop+full-tile). **Gate 2** uses that label to render crops only for review/full-downlink payloads.

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Orbital pass runner | Discover tiles, run detector → optional Liquid reasoner → payload+crop+telemetry builder, expose CLI | `satellite_edge_node/orbital_pass.py` |
| Detector router | Build `BaselineDetector`, `YoloDetector`, or explicit `FallbackBaselineDetector`; preserve fallback metadata | `satellite_edge_node/detectors.py` |
| Baseline detector (simulated) | Deterministic placeholder using sidecar `.meta.json` or filename hints; `simulated=True`, `detector_is_real=False` | `satellite_edge_node/baseline_detector.py` |
| YOLO detector (real) | Strict local Ultralytics integration, normalizes results into `DetectionResult`; raises `YoloModelUnavailable` instead of degrading | `satellite_edge_node/yolo_detector.py` |
| Liquid VLM reasoner | Optional crop-level reasoning via `LiquidAI/LFM2.5-VL-450M`; system+user prompt split, deterministic decode, JSON-only schema | `satellite_edge_node/liquid_vlm_reasoner.py` |
| Payload + telemetry builder | `should_transmit_alert` (Gate 1), `triage_label` (Gate 2), crop generation, byte accounting, telemetry record | `satellite_edge_node/payloads.py` |
| 4-tier triage core | Generic `compute_triage(prediction, *, min_confidence)` returning `TriageResult`; `TriageDecision` enum | `kilnwatch/triage.py` |
| Ground-station domain | Load queue payloads + telemetry, compute `MissionMetrics`, `ProofStatus`, `MissionProofCounts`, resolve crop evidence (Gate 3) | `kilnwatch/ground_station.py` |
| Primary Streamlit dashboard | Single-page hero metrics, honesty panel, alert cards with Liquid reasoning, downlink chart, diagnostics | `app.py` |
| Simple queue-reader UI | Alternate Streamlit UI bound to a selectable transmission queue path | `ground_station_ui/app.py`, `ground_station_ui/queue_reader.py` |
| SimSat ingestion | Local SimSat HTTP fetch for one Haryana Sentinel-style tile; writes raw + metadata or smoke report | `kilnwatch/ingestion/cli.py`, `kilnwatch/ingestion/simsat_client.py`, `kilnwatch/ingestion/dataset.py`, `kilnwatch/ingestion/regions.py` |
| Dataset validation | Manifest schema + optional image readability checks | `kilnwatch/datasets/manifest.py`, `kilnwatch/datasets/image_validation.py` |
| Dataset adapters | Convert third-party local datasets into KilnWatch JSONL manifest | `kilnwatch/datasets/adapters/` |
| Operational scripts | Thin CLI wrappers — readiness, evaluation, demo tile fetch, manifest validation, APAD batch convert | `scripts/` |
| Tests | Boundary, bandwidth, detector, reasoner, ingestion, manifest, readiness, triage | `tests/` |

## Pattern Overview

**Overall:** File-backed two-layer simulation with a queue boundary that is enforced in code, plus per-record honesty metadata so any downstream surface can prove what was real and what was simulated.

**Key Characteristics:**
- The radio link is a folder: `transmission_queue/`. Every cross-layer fact transits through it.
- All detector implementations normalize to one schema: `satellite_edge_node.baseline_detector.DetectionResult`.
- All reasoner implementations normalize to one schema: `satellite_edge_node.liquid_vlm_reasoner.VlmReasoning`.
- Honesty metadata (`detector_mode`, `detector_is_real`, `simulated`, `fallback_used`, `fallback_reason`, `vlm_reasoning.reasoner_is_real`, `vlm_reasoning.reasoner_mode`, `vlm_reasoning.model_name`) rides on every payload and telemetry row, and the ground station turns it into typed labels (see "Honesty contract" below).
- Failures are explicit, not silent: missing YOLO weights raise `YoloModelUnavailable`; broken Liquid loading raises `LiquidReasonerUnavailable`; missing crop for an alert raises `RequiredCropUnavailable` when `--require-crops` is set.
- Streamlit files are renderers. Business logic lives in `kilnwatch/ground_station.py`.

## Layers

**Tile-source layer (inputs to the simulated satellite):**
- Purpose: Provide local imagery to feed the orbital-pass loop. Three concurrent sources exist.
- Location: `data/raw_tiles/` (placeholder `.tile` + sidecar `.meta.json` for unit tests and demo flow), `data/final_demo_tiles/` (real Roboflow brick-kiln `.jpg` for end-to-end demo), `data/manual_tiles/`, `data/raw/` + `data/metadata/` (SimSat fetches).
- Used by: `satellite_edge_node/orbital_pass.py` via `discover_tiles()`.

**Satellite edge layer (the would-be onboard AI):**
- Purpose: Discover tiles, detect, reason, decide, emit JSON + crop + telemetry. Sequential synchronous loop.
- Location: `satellite_edge_node/`
- Depends on: tile-source layer, optional `ultralytics`, optional `transformers` + `Pillow`.
- Used by: `python -m satellite_edge_node.orbital_pass`, `kilnwatch-orbital-pass`, bandwidth/detector/reasoner tests.

**Queue boundary layer (the simulated radio link):**
- Purpose: The only place the satellite layer writes and the only place the ground layer reads.
- Location: `transmission_queue/`, `telemetry_logs/`, optional legacy `telemetry/`.
- Contains: per-tile `<tile_id>.json` payloads, `telemetry.jsonl`, `crops/<tile_id>_crop.png`. `telemetry_logs/sample_mission.jsonl` is a checked-in sample for empty-queue replay.
- Used by: ground-station layer.

**Ground-station layer (the operator dashboard):**
- Purpose: Read queue artifacts, compute mission metrics, render single-page mission proof.
- Location: `app.py`, `kilnwatch/ground_station.py`, `ground_station_ui/`.
- Depends on: queue boundary layer, `streamlit`, `pandas`, `Pillow`.

**Triage core (shared decision math):**
- Purpose: Pure decision function used both by the satellite-side `triage_label()` (Gate 2) and by anything that wants the same 4-tier model.
- Location: `kilnwatch/triage.py`.

**Ingestion layer (Sentinel-style fetch):**
- Purpose: Pull one Haryana tile from a local SimSat HTTP endpoint, or write a smoke report when SimSat is unreachable.
- Location: `kilnwatch/ingestion/`. Region constant is `HARYANA_INDIA` in `kilnwatch/ingestion/regions.py`.

**Dataset normalization layer:**
- Purpose: Validate manifests, convert third-party datasets (APAD, SentinelKilnDB, KDD24, SustainBench/GEO-Bench).
- Location: `kilnwatch/datasets/`.

**Operational scripts layer:**
- Purpose: Thin CLI wrappers around package functions.
- Location: `scripts/`.

## Data Flow

### Primary orbital pass (the demo path)

1. `simulate_orbital_pass(...)` resets the queue if requested, ensures `transmission_queue/` exists, opens `telemetry.jsonl` for append (`satellite_edge_node/orbital_pass.py:33`).
2. Builds the detector via `build_detector_with_fallback()` — strict YOLO unless `--allow-baseline-fallback` permits an explicit fallback wrapper that records `fallback_used=True` (`satellite_edge_node/detectors.py:43`, `:58`).
3. Builds the reasoner via `build_reasoner(mode)` — one of `disabled` (returns `None`), `liquid-mock`, or `liquid-local` (`satellite_edge_node/liquid_vlm_reasoner.py:187`).
4. For each discovered tile (`discover_tiles()` walks `is_tile_file` matches):
   - Read original byte size, time the call, run `detector.detect_tile(tile_path)` → `DetectionResult` (`satellite_edge_node/orbital_pass.py:65`).
   - Generate a crop only when `should_transmit_alert(detection)` is true and the bbox is valid; PIL crop saved to `transmission_queue/crops/<tile_id>_crop.png`. Errors recorded into `CropArtifact.error` rather than thrown (`satellite_edge_node/payloads.py:64`).
   - If a reasoner exists and `detection.kiln_detected`, call `reasoner.reason(image_path, detection, crop_path)` → `VlmReasoning`. Liquid uses the crop when present; falls back to the full tile otherwise (`satellite_edge_node/liquid_vlm_reasoner.py:107`).
   - If `--require-crops` and Gate 1 says alert but `crop_artifact.path is None`, raise `RequiredCropUnavailable` (`satellite_edge_node/orbital_pass.py:79`). CLI exits with code 4.
   - **Gate 1 fires:** if `should_transmit_alert(detection)` (or `--write-drop-payloads`), build the payload (alert or dropped event), iterate `_finalize_payload_bytes()` to converge byte accounting against itself, write `transmission_queue/<tile_id>.json` (`satellite_edge_node/orbital_pass.py:86`, `:122`).
   - **Gate 2 fires (always):** `telemetry_record(...)` calls `triage_label(...)` and writes a JSONL line containing the 4-tier `triage_decision`, the `triage` dict (`decision`, `reason`, `risk_band_used`, `risk_score_used`, `driven_by`), all detector-honesty fields, byte accounting, the action, and a serialized `DetectionResult` (`satellite_edge_node/payloads.py:176`).
5. CLI prints aggregate stats (tiles processed, original bytes, transmitted bytes, saved bytes, compression ratio, reasoner mode). Reported end-to-end demo numbers: 14 tiles → 5 alerts; 5/5 with real Liquid reasoning; ~9.5 KB downlinked at 116x compression with Liquid on, ~6.6 KB at 168x with Liquid off.

### Ground-station display path

1. `load_ground_station_records()` reads `transmission_queue/*.json` as payloads, `transmission_queue/*.jsonl` + `telemetry_logs/*.jsonl` (or legacy `telemetry/*.jsonl`) as telemetry events. Real records win over `sample_demo_data` records when both exist (`kilnwatch/ground_station.py:61`).
2. `calculate_metrics(events)` computes `MissionMetrics`: tiles processed, raw bytes processed, downlinked bytes, bytes saved, percent saved, compression ratio, ignored / JSON-alert / review-or-full counts (using `_decision()` which prefers the explicit `triage_decision` and falls back to deriving one from `action` + risk + confidence), and average inference latency (`kilnwatch/ground_station.py:82`).
3. `proof_status_summary()` and `mission_proof_counts()` extract honesty fields and counts.
4. `resolve_crop_evidence()` is **Gate 3**: it filters payloads through `safe_review_payloads()`, then validates every crop reference with `_safe_crop_path()` (rejects forbidden fragments, `.tile` paths, paths escaping the queue root) before declaring crop evidence available (`kilnwatch/ground_station.py:182`, `:412`).
5. `app.py` renders the single-page dashboard: honesty chips, hero metrics, imagery provenance disclaimer, per-alert cards (with Liquid reasoning JSON), downlink chart, diagnostics expander. The simple replay UI in `ground_station_ui/app.py` is an alternate small dashboard pointed at any selectable queue directory.

### SimSat ingestion path (peripheral, not in the demo loop)

1. `kilnwatch/ingestion/cli.py` parses `--base-url`, `--dataset-root`, `--width/--height`, optional `--position-endpoint` / `--image-endpoint` overrides.
2. `SimSatClient.get_current_position(...)` and `.fetch_sentinel_tile(...)` — both raise `SimSatUnavailable` on failure.
3. On success: `write_tile_dataset(response, HARYANA_INDIA, dataset_root)` writes raw bytes under `data/raw/simsat/haryana_india/` and metadata JSON under `data/metadata/simsat/haryana_india/`.
4. On failure: `write_smoke_report(reason, dataset_root)` writes `data/smoke/<timestamp>.json` so local workflows do not fail when SimSat isn't running.

### Dataset manifest validation path

1. `scripts/validate_manifest.py` calls `validate_manifest_file(...)` on one or more JSONL paths.
2. `kilnwatch/datasets/manifest.py` accumulates `ManifestIssue` rows for missing/invalid fields, bad split values, out-of-range coordinates, malformed bbox, confidence outside [0,1], and missing honesty notes.
3. With `--check-images`, `kilnwatch/datasets/image_validation.py` requires a real raster extension and a Pillow-readable file.

## State Management

- All cross-layer state is file-backed. There is no database, queue, broker, or shared in-process state.
- Streamlit session state is limited to a couple of `st.session_state` keys inside `app.py` rendering helpers.
- `transmission_queue/*.json` and `transmission_queue/telemetry.jsonl` are the runtime working set. `--reset-queue` deletes payload JSON, telemetry, and the `crops/` directory before a fresh pass.
- `transmission_queue.backup_2026-05-09/` is a transient runtime backup, not part of the architecture.

## Honesty contract (preserved end-to-end)

Every payload and every telemetry row carries the fields below, and the ground station turns them into typed labels.

**Detector honesty fields:** `detector_mode`, `detector_is_real`, `simulated`, `fallback_used`, `fallback_reason`, `detector_version`. Set on `DetectionResult` (`satellite_edge_node/baseline_detector.py:21`, `satellite_edge_node/yolo_detector.py:78`, `satellite_edge_node/detectors.py:58`); copied verbatim into payloads via `_truth_metadata()` (`satellite_edge_node/payloads.py:223`); aggregated into the dashboard chip via `_detector_label()` (`kilnwatch/ground_station.py:352`) which emits exactly one of:

- `STRICT YOLO REAL` — all detectors are YOLO, all `detector_is_real=True`, none `simulated=True`.
- `MIXED DETECTOR METADATA` — at least one real YOLO, but mixed flags.
- `BASELINE SIMULATION` — any `simulated=True` or any baseline/placeholder mode.
- `FALLBACK USED` — any `fallback_used=True`.
- `SAMPLE DATA` — sample-demo records only.
- `DETECTOR METADATA UNKNOWN` — neither real nor simulated detected.

**Reasoner honesty fields:** `vlm_reasoning.reasoner_mode`, `vlm_reasoning.reasoner_is_real`, `vlm_reasoning.model_name` (`satellite_edge_node/liquid_vlm_reasoner.py:24`). Aggregated by `_reasoner_label()` (`kilnwatch/ground_station.py:373`) into one of:

- `LIQUID LFM REAL` — at least one record has `reasoner_is_real=True` (i.e. `--reasoner liquid-local`).
- `LIQUID MOCK` — only `liquid-mock` records present.
- `LFM DISABLED` — no `vlm_reasoning` block on any record.

This honesty contract is the *reason* the queue boundary matters: if the satellite layer could quietly degrade, the ground station could not honestly say "STRICT YOLO REAL" or "LIQUID LFM REAL". The architecture guarantees that any degradation shows up in the chip labels.

## Key Abstractions

**`DetectionResult`** (`satellite_edge_node/baseline_detector.py`) — frozen dataclass; the shared schema every detector returns. Carries detector-honesty metadata.

**`Detector` Protocol + `BaselineDetector` / `YoloDetector` / `FallbackBaselineDetector`** (`satellite_edge_node/detectors.py`) — `detect_tile(Path) -> DetectionResult`.

**`VlmReasoning`** (`satellite_edge_node/liquid_vlm_reasoner.py`) — frozen dataclass; reasoner output schema. `to_payload()` flattens it for JSON.

**`Reasoner` Protocol + `LiquidMockReasoner` / `LiquidLocalReasoner`** (`satellite_edge_node/liquid_vlm_reasoner.py`) — `reason(*, image_path, detection, crop_path) -> VlmReasoning`. `build_reasoner(mode)` is the only public constructor; valid modes are `"disabled"`, `"liquid-mock"`, `"liquid-local"`.

**`CropArtifact`** (`satellite_edge_node/payloads.py`) — frozen dataclass: `path`, `size_bytes`, `error`. Errors are data, not exceptions.

**`TriageDecision` (StrEnum) + `TriageResult` + `BandwidthEstimate`** (`kilnwatch/triage.py`) — generic 4-tier decision model used by `triage_label()` (Gate 2).

**`MissionMetrics`, `ProofStatus`, `MissionProofCounts`, `CropEvidence`** (`kilnwatch/ground_station.py`) — frozen dataclasses; computed once per dashboard render.

**`Region`, `SimSatResponse`, `TileRecord`** (`kilnwatch/ingestion/`) — typed boundary between SimSat HTTP and disk artifacts.

## Entry Points

| Entry | Triggers | Responsibility |
|-------|----------|---------------|
| Primary dashboard | `streamlit run app.py` | Single-page mission proof |
| Simple queue UI | `streamlit run ground_station_ui/app.py` | Replay-an-arbitrary-queue UI |
| Orbital pass | `python -m satellite_edge_node.orbital_pass`, `kilnwatch-orbital-pass` | Run the simulated onboard AI |
| SimSat fetch | `python -m kilnwatch.ingestion.cli`, `kilnwatch-fetch-haryana`, `scripts/smoke_fetch_haryana.py` | Pull one Haryana Sentinel-style tile |
| Manifest validate | `python scripts/validate_manifest.py <jsonl>` | Manifest schema + optional image readability |
| Demo tile builder | `python scripts/fetch_demo_tiles.py ...` | Coordinate CSV → demo tiles + manifest |
| Model readiness | `python scripts/check_model_ready.py [--json]` | Strict YOLO weights + ultralytics check |
| Detector evaluation | `python scripts/evaluate_detector.py --manifest ... --telemetry ...` | Telemetry-vs-manifest accuracy with honesty status |
| APAD batch convert | `python scripts/process_apad.py` | Convert APAD IGP CSVs to manifests |

The orbital-pass CLI exit codes encode the failure mode: `0` ok, `2` `YoloDetectorError`, `3` `LiquidReasonerError`, `4` `RequiredCropUnavailable`.

## Architectural Constraints

- **Threading:** Single-process, synchronous. Detector → reasoner → payload runs sequentially per tile. Streamlit handles its own UI reruns.
- **Global state:** None at the package level. `transmission_queue/`, `telemetry_logs/`, default tile / model / queue paths are constants in their respective modules.
- **Circular imports:** None. Direction of dependency is `app.py` → `kilnwatch.ground_station` → stdlib; `satellite_edge_node.orbital_pass` → `.detectors`, `.liquid_vlm_reasoner`, `.payloads`, `.yolo_detector`. `payloads.py` is the only satellite module that imports from `kilnwatch` (it imports `kilnwatch.triage` for Gate 2 — the triage core lives in the shared package because the same math runs in both directions).
- **Boundary enforcement:** `tests/test_ground_station_boundary.py` is the contract test. Any new ground-station file must pass it.
- **Detector strictness:** YOLO mode raises on any setup problem. Fallback to baseline only happens when `--allow-baseline-fallback` is explicitly passed, and the resulting `FallbackBaselineDetector` stamps `fallback_used=True` and the `fallback_reason` so the dashboard surfaces it.
- **Reasoner strictness:** `--reasoner liquid-local` requires a working local `transformers` install with `AutoModelForImageTextToText`. Failure raises `LiquidReasonerUnavailable` (caught at the CLI boundary, exit code 3). The ollama path is **gone** as of this refresh — the only modes are `disabled`, `liquid-mock`, `liquid-local`.
- **Storage contract:** JSON + JSONL + PNG on disk. Adding a database, broker, or remote service would change the queue boundary contract and would need new boundary tests.

## Anti-Patterns

### Reaching across the queue boundary from the ground station

**What happens:** UI code imports `satellite_edge_node`, opens `data/raw_tiles/`, or follows a tile path string out of the queue.
**Why it's wrong:** Defeats the whole point of the simulation — proof that *only* what was downlinked reached the ground.
**Do this instead:** Add the field to `satellite_edge_node/payloads.py` (payload) or `satellite_edge_node/orbital_pass.py` (telemetry). Read it in `kilnwatch/ground_station.py`. Render in `app.py`. The boundary test will tell you when you slip.

### Conflating Gate 1 with Gate 2

**What happens:** Code starts to assume `triage_decision != "IGNORE"` is the same condition as "this got transmitted", or vice versa.
**Why it's wrong:** Gate 1 (`should_transmit_alert`) is detector-only and binary. Gate 2 (`triage_label`) is a 4-tier label that may downgrade a transmitted record to `JSON_ALERT_ONLY` or upgrade it to `FULL_DOWNLINK` — and is influenced by Liquid when present. Most dropped tiles end up `IGNORE`, but a transmitted alert with low score could in principle land `JSON_ALERT_ONLY`; that is metadata, not a re-routing of bytes.
**Do this instead:** When asking "did this leave the satellite?", check that `transmission_queue/<tile_id>.json` exists or that telemetry's `transmitted_payload_bytes > 0`. When asking "what kind of evidence does the operator see?", read `triage_decision` and apply Gate 3.

### Silent detector or reasoner fallback

**What happens:** A try/except quietly downgrades from real YOLO to baseline, or from `liquid-local` to `liquid-mock`.
**Why it's wrong:** The honesty chip in the dashboard becomes a lie.
**Do this instead:** Let `YoloModelUnavailable` and `LiquidReasonerUnavailable` propagate. The CLI already maps them to specific exit codes and helpful messages. `--allow-baseline-fallback` is the only blessed way to degrade, and it stamps `fallback_used=True`.

### Business logic in Streamlit files

**What happens:** Metric math, decision parsing, or telemetry shaping starts living in `app.py`.
**Why it's wrong:** Untestable without Streamlit; duplicates `kilnwatch/ground_station.py`.
**Do this instead:** Keep `app.py` as a renderer. Put computations in `kilnwatch/ground_station.py` and test them in `tests/test_ground_station.py`.

### Bypassing the manifest validator

**What happens:** A new dataset script writes JSONL with ad-hoc fields or skips the honesty notes.
**Why it's wrong:** Evaluation, demo-tile, and detector scripts assume the schema. Honesty notes are how sample-data is distinguished from real data.
**Do this instead:** Run new manifests through `scripts/validate_manifest.py`; extend the schema in `kilnwatch/datasets/manifest.py` if a field is genuinely needed.

## Error Handling

**Strategy:** Library code raises typed exceptions for setup/state problems; data-shaped errors (bad bbox, unreadable crop, missing field) become metadata in the payload/telemetry. CLI entry points catch the typed exceptions and exit with stable, distinct codes.

| Exception | Raised by | Caught at CLI? | Exit code |
|-----------|-----------|----------------|-----------|
| `YoloModelUnavailable` / `YoloDetectorError` | `satellite_edge_node/yolo_detector.py` | yes | 2 |
| `LiquidReasonerUnavailable` / `LiquidReasonerError` | `satellite_edge_node/liquid_vlm_reasoner.py` | yes | 3 |
| `RequiredCropUnavailable` | `satellite_edge_node/orbital_pass.py` | yes | 4 |
| `SimSatUnavailable` | `kilnwatch/ingestion/simsat_client.py` | yes (writes smoke report) | 0 |
| `ManifestIssue` (collected, not raised) | `kilnwatch/datasets/manifest.py` | n/a | n/a |

Crop generation failures are recorded in `CropArtifact.error` and surfaced as `crop_error` on the payload; they do not abort the orbital pass unless `--require-crops` is set.

## Cross-Cutting Concerns

- **Logging:** `print()` at CLI boundaries; structured JSON/JSONL on disk for everything that needs to outlive the process.
- **Validation:** `kilnwatch/datasets/manifest.py` (schema), `kilnwatch/datasets/image_validation.py` (image readability), `scripts/check_model_ready.py` (YOLO availability), `scripts/evaluate_detector.py` (telemetry-vs-truth accuracy with honesty status).
- **Authentication:** None. Local SimSat defaults to `http://localhost:9005`; no auth handling.
- **External integrations:** Local SimSat HTTP (`kilnwatch/ingestion/simsat_client.py`), local Ultralytics YOLO inference (`satellite_edge_node/yolo_detector.py`), local Hugging Face `transformers` for Liquid LFM2.5-VL-450M (`satellite_edge_node/liquid_vlm_reasoner.py`).
- **Bandwidth accounting:** Computed satellite-side in `satellite_edge_node/payloads.py` (`attach_byte_accounting`, `compression_ratio`, `bandwidth_saved_bytes`) and re-aggregated ground-side in `kilnwatch/ground_station.py` (`calculate_metrics`, `cumulative_series`).

---

*Architecture analysis: 2026-05-09*

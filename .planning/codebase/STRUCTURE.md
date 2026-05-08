# Codebase Structure

**Analysis Date:** 2026-05-09

This is the satellite-edge AI workload (the simulated onboard pipeline) plus its operator dashboard. The two layers communicate only through `transmission_queue/`. Everything in this document is grouped by which side of that boundary it lives on.

## Directory Layout

```text
SpaceAI/
├── app.py                            # Primary Streamlit ground-station dashboard (single page)
├── pyproject.toml                    # Package metadata; console scripts kilnwatch-fetch-haryana, kilnwatch-orbital-pass
├── requirements.txt                  # Streamlit / pandas / Pillow runtime deps
├── README.md                         # User-facing demo walkthrough + honesty disclaimer
│
├── satellite_edge_node/              # ──── SATELLITE LAYER ────
│                                     # Simulated onboard AI: discover → detect → reason → emit
│
├── kilnwatch/                        # ──── SHARED + GROUND LAYER ────
│   ├── ground_station.py             # Queue-only loader + metrics + Gate 3 crop-evidence resolver
│   ├── triage.py                     # Generic 4-tier TriageDecision / compute_triage()
│   ├── ingestion/                    # SimSat HTTP fetch (peripheral, not in demo loop)
│   └── datasets/                     # Manifest validation + dataset adapters
│
├── ground_station_ui/                # Alternate small Streamlit replay UI (any queue dir)
│
├── transmission_queue/               # ──── THE BOUNDARY ────
│                                     # Per-tile JSON payloads, telemetry.jsonl, crops/
├── transmission_queue.backup_2026-05-09/  # Transient runtime backup, not architectural
├── telemetry_logs/                   # Optional sample/external telemetry (sample_mission.jsonl)
│
├── data/                             # Tile sources for the satellite layer
│   ├── raw_tiles/                    # `.tile` placeholders + `.meta.json` sidecars (unit fixtures)
│   ├── final_demo_tiles/             # Real Roboflow brick-kiln `.jpg` (the demo dataset)
│   ├── final_demo_labels/            # YOLO-format labels for final_demo_tiles
│   ├── manual_tiles/                 # Manually placed tiles
│   ├── raw/                          # SimSat-fetched raw bytes (kilnwatch/ingestion writes here)
│   ├── metadata/                     # SimSat-fetched metadata JSON
│   └── smoke/                        # SimSat unreachable smoke reports
│
├── datasets/                         # External dataset materials
│   ├── kilnwatch/                    # Schema + manifests + labels + coordinates + demo images
│   ├── Brick_Kilns/                  # APAD IGP CSV sources (IND/PK/BAN main coal)
│   ├── roboflow/                     # Roboflow brick-kiln dataset (DO NOT read from UI)
│   ├── SentinelKilnDB/               # SentinelKilnDB stub
│   └── SENTINELKILNDB_NeurIPS_2025/  # NeurIPS 2025 release
│
├── models/                           # Local YOLO weights drop point (brick_kiln_yolo.pt)
├── config/regions/                   # Region configuration files
├── scripts/                          # Operational CLIs (thin wrappers around package functions)
├── tests/                            # Boundary, bandwidth, detector, reasoner, manifest, triage
├── docs/                             # Architecture, training, demo, honesty, submission docs
│
├── runs/                             # Ultralytics YOLO training output dir
├── tmp_brick_kiln/                   # Scratch space (transient)
├── yolov8n.pt, yolo26n.pt            # Pretrained YOLO base weights (root-level convenience)
├── Brick Kiln Detection.v1-...yolov8 # Roboflow dataset zip + extracted directory
├── .planning/codebase/               # ← these GSD codebase mapping docs
└── .codex/                           # Project-local GSD/OMX skills, hooks, templates
```

---

## Satellite layer — `satellite_edge_node/`

The simulated onboard AI. Sequential per-tile loop: discover → detect → reason (optional) → emit JSON + crop + telemetry.

| File | Purpose |
|------|---------|
| `satellite_edge_node/__init__.py` | Package marker. |
| `satellite_edge_node/orbital_pass.py` | The orbital-pass loop and CLI. `simulate_orbital_pass(...)` does discover → detect → reason → payload+telemetry write. CLI flags: `--detector {baseline,yolo}`, `--reasoner {disabled,liquid-mock,liquid-local}`, `--model-path`, `--confidence-threshold`, `--reset-queue`, `--allow-baseline-fallback`, `--require-crops`, `--write-drop-payloads`. Exit codes: 2 = `YoloDetectorError`, 3 = `LiquidReasonerError`, 4 = `RequiredCropUnavailable`. |
| `satellite_edge_node/detectors.py` | `Detector` Protocol; `BaselineDetector`, `FallbackBaselineDetector` dataclasses; `build_detector()` and `build_detector_with_fallback()`. The fallback wrapper stamps `fallback_used=True` and `fallback_reason` on the result. |
| `satellite_edge_node/baseline_detector.py` | Simulated detector. `DetectionResult` frozen dataclass (the shared schema). `detect_tile()` reads `<tile>.meta.json` sidecar or falls back to filename hints. Always emits `simulated=True`, `detector_is_real=False`. |
| `satellite_edge_node/yolo_detector.py` | Real Ultralytics YOLO integration. `YoloDetector` raises `YoloModelUnavailable` if weights are missing, `ultralytics` is uninstalled, the model fails to load, or the model has no kiln-named class. `normalize_yolo_results()` maps Ultralytics output to `DetectionResult` with `detector_is_real=True`, `simulated=False`, risk band derived from confidence (`>=0.85` → `high`, else `medium`). |
| `satellite_edge_node/liquid_vlm_reasoner.py` | Optional crop-level reasoner over `LiquidAI/LFM2.5-VL-450M`. `Reasoner` Protocol; `LiquidMockReasoner` (`reasoner_is_real=False`); `LiquidLocalReasoner` (`reasoner_is_real=True`). Local reasoner uses a system+user prompt split from the Liquid satellite-vlm cookbook, deterministic decode (`do_sample=False`), and a strict JSON-only schema (`credible_kiln`, `compliance_risk`, `human_review_needed`, `visual_summary`, `risk_reasoning`, `confidence_note`). `build_reasoner(mode)` accepts only `"disabled"` / `"liquid-mock"` / `"liquid-local"` — the ollama path was removed. |
| `satellite_edge_node/payloads.py` | The three things the satellite emits: payload JSON, crop PNG, telemetry row. **Gate 1** = `should_transmit_alert(detection)` (binary, detector-only). **Gate 2** = `triage_label(detection, vlm_reasoning, *, min_confidence)` calling `kilnwatch.triage.compute_triage()` to produce the 4-tier `triage_decision` + `triage` dict that goes on every payload and telemetry record. `build_transmission_payload()`, `generate_crop_file()`, `attach_byte_accounting()`, `encode_payload()`, `compression_ratio()`, `bandwidth_saved_bytes()`, `telemetry_record()`, `_truth_metadata()` (copies detector-honesty fields). |

---

## Boundary — `transmission_queue/`

The simulated radio link. The only place the satellite layer writes; the only place the ground layer reads.

| Path | Purpose |
|------|---------|
| `transmission_queue/<tile_id>.json` | Per-tile alert (or — only with `--write-drop-payloads` — dropped) payload. Always carries `triage_decision` + `triage{}` + detector-honesty fields. Alerts also carry `vlm_reasoning{}` when a reasoner ran. |
| `transmission_queue/telemetry.jsonl` | One JSONL line per tile processed (alert *and* drop). Carries byte accounting, `triage_decision`, all detector-honesty fields, the serialized `DetectionResult`, and `vlm_reasoning` when present. |
| `transmission_queue/crops/<tile_id>_crop.png` | PNG crop from `bbox`, generated only for alert-worthy detections with a readable image and a valid bbox. |
| `telemetry_logs/sample_mission.jsonl` | Checked-in sample telemetry for empty-queue replay. |
| `transmission_queue.backup_2026-05-09/` | Transient backup directory; not part of the architecture. |

---

## Ground layer — `app.py`, `kilnwatch/ground_station.py`, `ground_station_ui/`

Reads the queue, computes metrics, renders the dashboard. Must not import `satellite_edge_node` or read raw tile paths.

| File | Purpose |
|------|---------|
| `app.py` | Primary Streamlit dashboard. Single page: header chips, hero metrics (bandwidth saved, alerts, etc), honesty panel, imagery provenance disclaimer, alert cards (with crop + Liquid reasoning), downlink chart, diagnostics expander. Pure renderer — no business logic. |
| `kilnwatch/__init__.py` | Package marker. |
| `kilnwatch/ground_station.py` | Domain helpers. `load_ground_station_records()` (queue-only loader), `calculate_metrics()` → `MissionMetrics`, `cumulative_series()`, `received_alert_rows()`, **`safe_review_payloads()`** = Gate 3, `proof_status_summary()` → `ProofStatus`, `mission_proof_counts()` → `MissionProofCounts`, `resolve_crop_evidence()` → `CropEvidence` list, `detector_modes()`, `reasoner_statuses()`, `_detector_label()` (emits `STRICT YOLO REAL` / `MIXED DETECTOR METADATA` / `BASELINE SIMULATION` / `FALLBACK USED` / `SAMPLE DATA` / `DETECTOR METADATA UNKNOWN`), `_reasoner_label()` (emits `LIQUID LFM REAL` / `LIQUID MOCK` / `LFM DISABLED`), `_safe_crop_path()` (rejects forbidden fragments / `.tile` / queue-escapes). The `FORBIDDEN_CROP_SOURCE_FRAGMENTS` constant is the runtime teeth of the boundary. |
| `kilnwatch/triage.py` | Standalone 4-tier triage. `TriageDecision` StrEnum (`IGNORE`, `JSON_ALERT_ONLY`, `CROP_OR_REVIEW`, `FULL_DOWNLINK`). `compute_triage(prediction, *, min_confidence)`. `BandwidthEstimate`, `TriageResult`. Used by `satellite_edge_node/payloads.py` for Gate 2; importable wherever the same decision math is needed. |
| `ground_station_ui/__init__.py` | Package marker. |
| `ground_station_ui/app.py` | Alternate small Streamlit UI. Lets you point at any queue directory and see summary, alerts, telemetry, and raw payload JSON. |
| `ground_station_ui/queue_reader.py` | Minimal queue reader: `read_payloads()`, `read_telemetry()`, `summarize_telemetry()`. |

---

## Shared utilities — `kilnwatch/ingestion/`, `kilnwatch/datasets/`

These are not part of the demo loop but support data sourcing and validation.

### `kilnwatch/ingestion/` — local SimSat HTTP fetch

| File | Purpose |
|------|---------|
| `kilnwatch/ingestion/__init__.py` | Package marker. |
| `kilnwatch/ingestion/cli.py` | CLI for fetching one Haryana Sentinel-style tile. Falls back to a smoke report when SimSat is unreachable. Console script: `kilnwatch-fetch-haryana`. |
| `kilnwatch/ingestion/simsat_client.py` | `SimSatClient` over stdlib `urllib`. `get_current_position()`, `fetch_sentinel_tile()`. Raises `SimSatUnavailable` on any HTTP failure. Default endpoints in `DEFAULT_POSITION_ENDPOINTS` and `DEFAULT_SENTINEL_ENDPOINTS`. |
| `kilnwatch/ingestion/dataset.py` | `write_tile_dataset()` (writes raw bytes under `data/raw/simsat/<region>/` and metadata JSON under `data/metadata/simsat/<region>/`). `write_smoke_report()` (writes `data/smoke/<timestamp>.json`). |
| `kilnwatch/ingestion/regions.py` | `Region` dataclass; constant `HARYANA_INDIA` (the only currently active region). |

### `kilnwatch/datasets/` — manifest schema + dataset adapters

| File | Purpose |
|------|---------|
| `kilnwatch/datasets/__init__.py` | Package marker. |
| `kilnwatch/datasets/manifest.py` | KilnWatch JSONL manifest schema. `validate_manifest_file()` accumulates `ManifestIssue` rows for missing/invalid fields. |
| `kilnwatch/datasets/image_validation.py` | Optional image readability check (real raster extension + Pillow-readable). |
| `kilnwatch/datasets/adapters/__init__.py` | Adapter package. |
| `kilnwatch/datasets/adapters/base.py` | Abstract `DatasetAdapter`. |
| `kilnwatch/datasets/adapters/apad_igp.py` | APAD Indo-Gangetic Plain CSV → KilnWatch manifest converter. |
| `kilnwatch/datasets/adapters/sentinelkilndb.py` | SentinelKilnDB stub. |
| `kilnwatch/datasets/adapters/kdd24_reference.py` | KDD24 reference stub. |
| `kilnwatch/datasets/adapters/sustainbench_geobench.py` | SustainBench / GEO-Bench adapter. |

---

## Operational scripts — `scripts/`

Thin wrappers around package functions; primary user-facing CLIs.

| File | Purpose |
|------|---------|
| `scripts/check_model_ready.py` | Strict YOLO readiness check: `models/brick_kiln_yolo.pt` exists, `ultralytics` importable, model has a kiln-named class. `--json` for machine-readable output. |
| `scripts/evaluate_detector.py` | Compare telemetry predictions to a manifest; emit accuracy + honesty status (e.g. flags simulated/sample evaluations). |
| `scripts/fetch_demo_tiles.py` | Convert coordinate CSV rows into demo tile files + sidecars + a manifest. Local-import or SimSat modes. |
| `scripts/process_apad.py` | Batch-convert all APAD IGP CSVs in `datasets/Brick_Kilns/` to manifests under `datasets/kilnwatch/manifests/`. |
| `scripts/provision_model.py` | Set up local model artifacts. |
| `scripts/smoke_fetch_haryana.py` | Thin wrapper over `kilnwatch.ingestion.cli:main`; runs the SimSat fetch with defaults. |
| `scripts/train_real_model.py` | Train a real YOLO brick-kiln detector. |
| `scripts/validate_manifest.py` | Validate a KilnWatch manifest JSONL file (`--check-images` to also require Pillow-readable imagery). |

---

## Tests — `tests/`

| File | What it pins |
|------|--------------|
| `tests/test_ground_station_boundary.py` | The architectural boundary. Scans `app.py`, `kilnwatch/ground_station.py`, every `ground_station_ui/*.py` for forbidden strings (`satellite_edge_node`, `data/raw_tiles`, `data/final_demo_tiles`, `datasets/roboflow`, `raw_tiles`, `.tile` literals); partitions out the `FORBIDDEN_CROP_SOURCE_FRAGMENTS` constant block in `ground_station.py`. |
| `tests/test_satellite_edge_bandwidth.py` | Byte accounting, telemetry record shape, orbital pass output, crop behavior. |
| `tests/test_ground_station.py` | Mission metrics, sample-data precedence, alert rows, detector mode labels, crop evidence resolution. |
| `tests/test_yolo_detector.py` | YOLO normalization, strict missing-model errors, explicit fallback metadata. |
| `tests/test_liquid_vlm_reasoner.py` | `LiquidMockReasoner` and `LiquidLocalReasoner` behavior, `build_reasoner` mode validation, JSON parsing fallbacks. |
| `tests/test_fetch_demo_tiles.py` | CSV → demo tile conversion, image validation, local-import path. |
| `tests/test_manifest_schema.py` | Manifest schema rules, image validation rules. |
| `tests/test_model_readiness_eval.py` | Model readiness + detector evaluation honesty status. |
| `tests/test_triage.py` | Triage decisions on synthetic predictions. |
| `tests/test_metadata.py` | Metadata helper formatting. |

---

## Docs — `docs/`

| File | Purpose |
|------|---------|
| `docs/architecture.md` | Human-readable architecture notes (older — `.planning/codebase/ARCHITECTURE.md` is canonical). |
| `docs/demo_data_pipeline.md` | Demo data preparation pipeline. |
| `docs/demo_script.md` | Demo recording script. |
| `docs/external_resources.md` | External resources / datasets / references. |
| `docs/final_demo_evidence.md` | Evidence for final demo claims. |
| `docs/model_training.md` | YOLO training notes. |
| `docs/sample_evaluation_baseline.json` | Reference evaluation baseline JSON. |
| `docs/submission_checklist.md` | Hackathon submission checklist. |
| `docs/technical_honesty.md` | Statements of what is/isn't claimed. |
| `docs/youtube_script.md` | Demo recording script for YouTube. |

---

## Data and runtime artifacts

| Path | Purpose | Generated? | Read by ground? |
|------|---------|-----------|-----------------|
| `data/raw_tiles/` | `.tile` placeholders + `.meta.json` sidecars for unit-test/demo flow. | partly | **NO** (boundary test enforces) |
| `data/final_demo_tiles/` | Real Roboflow brick-kiln `.jpg` for the demo. | no (committed) | **NO** (boundary test enforces) |
| `data/final_demo_labels/` | YOLO-format `.txt` labels paired with final_demo_tiles. | no | no |
| `data/manual_tiles/` | Manually placed tiles. | no | no |
| `data/raw/`, `data/metadata/` | SimSat fetch output. | yes (`kilnwatch/ingestion/dataset.py`) | no |
| `data/smoke/` | SimSat-unreachable smoke reports. | yes (`kilnwatch/ingestion/cli.py`) | no |
| `datasets/Brick_Kilns/` | APAD IGP CSV sources. | no | no |
| `datasets/kilnwatch/` | KilnWatch dataset materials (README, schema docs, manifests, labels, coordinates, demo images, scripts). | mixed | no |
| `datasets/roboflow/`, `datasets/SentinelKilnDB/`, `datasets/SENTINELKILNDB_NeurIPS_2025/` | External datasets. | no | **NO** (boundary test enforces `roboflow`) |
| `models/` | Local YOLO weights drop point. Expected file: `models/brick_kiln_yolo.pt`. | no (user-supplied) | no |
| `transmission_queue/` | Downlink queue (the boundary). | yes (`satellite_edge_node/orbital_pass.py`) | **YES (only this)** |
| `transmission_queue.backup_2026-05-09/` | Transient runtime backup. | yes | no (transient) |
| `telemetry_logs/` | Sample/external telemetry. `sample_mission.jsonl` is committed. | mixed | yes (sample fallback) |
| `runs/` | Ultralytics training output dir. | yes | no |
| `tmp_brick_kiln/` | Scratch space. | yes | no |
| `Brick Kiln Detection.v1-dataset_aug.yolov8/`, `.zip` | Roboflow dataset zip + extracted dir. | no (committed) | no |
| `yolov8n.pt`, `yolo26n.pt` | Pretrained YOLO base weights at root. | no (committed) | no |

---

## Naming Conventions

**Files:**
- Python modules: lowercase snake_case (`satellite_edge_node/orbital_pass.py`, `kilnwatch/ground_station.py`).
- Tests: `test_*.py` (e.g. `tests/test_satellite_edge_bandwidth.py`).
- Manifests + labels: JSONL, row-oriented (`datasets/kilnwatch/manifests/sample_demo_manifest.jsonl`).
- Tile metadata sidecars: `<tile>.tile.meta.json` (matches stem of the tile file).
- Demo tile placeholders: `.tile`. Real imagery: `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.webp`.
- Crop artifacts: `<tile_id>_crop.png` under `transmission_queue/crops/`.

**Directories:**
- Python packages: lowercase snake_case (`satellite_edge_node/`, `ground_station_ui/`, `kilnwatch/`).
- Dataset subtree groups by purpose: `manifests/`, `labels/`, `coordinates/`, `images/`, `docs/`, `scripts/` under `datasets/kilnwatch/`.
- Runtime data subtree groups by lifecycle: `data/raw_tiles/`, `data/final_demo_tiles/`, `data/raw/`, `data/metadata/`, `data/smoke/`.
- Generated downlink artifacts go in `transmission_queue/`. Never write raw source imagery there except as the explicit downlinked crop or full-tile artifact.

---

## Where to Add New Code

**New satellite detector**
- Implementation: add a class in `satellite_edge_node/`, register in `build_detector()` in `satellite_edge_node/detectors.py`.
- Output: must return `DetectionResult` (`satellite_edge_node/baseline_detector.py`); set `detector_mode`, `detector_is_real`, `simulated` honestly.
- Tests: add focused tests in `tests/test_yolo_detector.py` style or a new `tests/test_<name>_detector.py`; cover orbital-pass byte accounting changes in `tests/test_satellite_edge_bandwidth.py`.

**New reasoner backend**
- Implementation: add a class in `satellite_edge_node/liquid_vlm_reasoner.py` or a new module; expose via `build_reasoner()`.
- Output: must return `VlmReasoning`; set `reasoner_mode`, `reasoner_is_real`, `model_name` honestly.
- Tests: add cases in `tests/test_liquid_vlm_reasoner.py`.

**New payload or telemetry field**
- Field plumbing: add to `build_transmission_payload()` or `telemetry_record()` in `satellite_edge_node/payloads.py`; ensure `simulate_orbital_pass()` passes the inputs.
- Ground consumption: read in `kilnwatch/ground_station.py`, render in `app.py`. **Do not bypass the queue.**
- Tests: update `tests/test_satellite_edge_bandwidth.py` and `tests/test_ground_station.py`.

**New triage rule (Gate 2)**
- Decision math: edit `compute_triage()` in `kilnwatch/triage.py` — keep it pure.
- Wiring: `triage_label()` in `satellite_edge_node/payloads.py` already calls `compute_triage()`; no changes unless the input shape changes.
- Tests: `tests/test_triage.py`.

**New ground-station metric or view**
- Calculation: add to `kilnwatch/ground_station.py` (must remain queue-only).
- Render: add to `app.py` (no business logic). Tests in `tests/test_ground_station.py`.

**New ingestion source or region**
- Region constant: `kilnwatch/ingestion/regions.py`.
- HTTP/client behavior: extend `kilnwatch/ingestion/simsat_client.py` or add a sibling client.
- Artifact writing: reuse `kilnwatch/ingestion/dataset.py`.

**New dataset adapter**
- Implementation: `kilnwatch/datasets/adapters/<source>.py` implementing `DatasetAdapter` from `base.py`.
- Output: must validate cleanly with `validate_manifest_file()`.
- Tests: add adapter conversion + manifest validation cases.

**New manifest rule**
- Rule: `kilnwatch/datasets/manifest.py`.
- Tests: `tests/test_manifest_schema.py`.

**New operational script**
- Reusable logic in `kilnwatch/` or `satellite_edge_node/`; the script in `scripts/` is a thin CLI.
- Add a `[project.scripts]` entry in `pyproject.toml` only when the command should be installed.

**New documentation**
- Architecture: this file (`.planning/codebase/ARCHITECTURE.md`) is canonical; `docs/architecture.md` is human-narrative.
- Honesty language: `docs/technical_honesty.md`.
- Demo flow: `docs/demo_script.md` or `docs/demo_data_pipeline.md`.

---

## Special Directories (lifecycle summary)

| Dir | Purpose | Generated by | Committed? |
|-----|---------|-------------|-----------|
| `transmission_queue/` | The boundary; orbital-pass output. | `satellite_edge_node/orbital_pass.py` | sample artifacts may be present |
| `transmission_queue/crops/` | Crop PNGs for alerts. | `satellite_edge_node/payloads.py` (`generate_crop_file`) | no |
| `transmission_queue.backup_2026-05-09/` | Transient backup. | manual / runtime | no (runtime) |
| `data/raw_tiles/` | Demo placeholders + sidecars. | manual / `scripts/fetch_demo_tiles.py` | yes |
| `data/final_demo_tiles/` | Real Roboflow demo imagery. | external dataset | yes |
| `data/raw/`, `data/metadata/` | SimSat fetch output. | `kilnwatch/ingestion/dataset.py` | `.gitkeep` only |
| `data/smoke/` | SimSat-unreachable reports. | `kilnwatch/ingestion/cli.py` | sample reports may be present |
| `datasets/kilnwatch/` | Versioned dataset materials. | mixed | yes (templates + samples) |
| `models/` | Local YOLO weights. | user-supplied | no (weights), maybe `.gitkeep` |
| `telemetry_logs/` | Sample/external telemetry. | mixed | `sample_mission.jsonl` |
| `runs/` | Ultralytics training output. | `scripts/train_real_model.py` | no |
| `.planning/codebase/` | These GSD codebase mapping docs. | GSD workflows | yes |
| `.codex/` | Project-local GSD/OMX assets. | OMX/GSD setup | yes |

---

*Structure analysis: 2026-05-09*

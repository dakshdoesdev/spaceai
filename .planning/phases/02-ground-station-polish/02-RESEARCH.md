# Phase 2: Ground Station Polish - Research

**Researched:** 2026-05-06
**Domain:** Streamlit ground-station dashboard, queue-only crop evidence, detector/reasoner honesty display
**Confidence:** HIGH

## User Constraints

### Locked Phase Scope

- Phase 2 goal is: "The Streamlit dashboard clearly demonstrates satellite-side triage, bandwidth savings, alerts, crops, and honesty state from queue artifacts only." [VERIFIED: `.planning/ROADMAP.md`]
- Phase 2 must address `DEMO-05`, `SPACE-02`, and `SPACE-03`. [VERIFIED: `.planning/ROADMAP.md`] [VERIFIED: `.planning/REQUIREMENTS.md`]
- The dashboard is the primary judge-facing proof surface. Detector honesty is priority 1, crop/review evidence is priority 2, dashboard proof hierarchy is priority 3, and queue-only validation is priority 4. [VERIFIED: `.planning/phases/02-ground-station-polish/02-CONTEXT.md`]
- Ground station may read only `transmission_queue/`, `telemetry_logs/`, and actual downlinked crop files referenced by queue payloads. [VERIFIED: `.planning/phases/02-ground-station-polish/02-CONTEXT.md`]
- Ground station must never read `data/raw_tiles/`, `data/final_demo_tiles/`, Roboflow folders, or placeholder `.tile` fixtures. [VERIFIED: `.planning/phases/02-ground-station-polish/02-CONTEXT.md`]
- YOLO remains the localization detector. Optional Liquid LFM reasoning is second-stage advisory reasoning, not a detector replacement. [VERIFIED: `README.md`] [VERIFIED: `satellite_edge_node/liquid_vlm_reasoner.py`]
- Do not claim Liquid fine-tuning unless fine-tuning code, dataset evidence, and integration proof exist. [VERIFIED: `README.md`] [VERIFIED: `.planning/REQUIREMENTS.md`]

### Current-Code Correction to Context

`02-CONTEXT.md` was gathered before the optional Liquid reasoner was implemented and still says Liquid LFM integration is deferred. The live repo now contains `satellite_edge_node/liquid_vlm_reasoner.py`, `--reasoner disabled|liquid-mock|liquid-local`, payload `vlm_reasoning`, and dashboard badges for `LIQUID LFM REAL`, `LIQUID MOCK`, and `LFM DISABLED`. Phase 2 planning must treat Liquid LFM as an optional reasoner status that the dashboard should display honestly, while still avoiding any fine-tuning claim. [VERIFIED: `satellite_edge_node/liquid_vlm_reasoner.py`] [VERIFIED: `satellite_edge_node/orbital_pass.py`] [VERIFIED: `app.py`] [VERIFIED: `README.md`]

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEMO-05 | User can view the resulting alert and bandwidth metrics in the Streamlit ground station. | Reorganize `app.py` so the first screen prioritizes proof status, metrics, edge-to-ground explanation, crop review, then alert/replay details. [VERIFIED: `app.py`] [VERIFIED: `02-CONTEXT.md`] |
| SPACE-02 | Dashboard shows file-size-based raw bytes, downlinked bytes, and bandwidth saved. | `calculate_metrics()` already computes raw/downlinked/saved/compression values; add missing judge-facing counters for detections and crops generated without moving math into Streamlit. [VERIFIED: `kilnwatch/ground_station.py`] |
| SPACE-03 | Ground station reads only `transmission_queue/` and telemetry/downlinked artifacts, not raw onboard inputs. | Add safe crop evidence resolution under `kilnwatch/ground_station.py`, and strengthen tests so crop preview paths cannot resolve outside allowed queue/downlink roots. [VERIFIED: `tests/test_ground_station_boundary.py`] [VERIFIED: `02-CONTEXT.md`] |

</phase_requirements>

## Summary

Phase 2 should be planned as a dashboard proof hardening phase, not a new backend phase. The backend already emits detector truth metadata, crop references, byte accounting, and optional `vlm_reasoning`. The missing work is to make these artifacts clear and safe at the ground-station boundary. [VERIFIED: `satellite_edge_node/payloads.py`] [VERIFIED: `satellite_edge_node/liquid_vlm_reasoner.py`] [VERIFIED: `app.py`]

The core planning approach should split into two executable plans matching the roadmap:

1. **Dashboard proof widgets and hierarchy:** Add a first-screen Proof Status panel, richer metric row, edge-to-ground explanation, and crop review panel in `app.py`, backed by helpers in `kilnwatch/ground_station.py`.
2. **Queue-only validation and tests:** Add helper-level tests for reasoner status, crop evidence path safety, and forbidden raw path access; extend boundary tests beyond `ground_station_ui/` if needed.

## Current Architecture Findings

### Existing Reusable Assets

- `load_ground_station_records()` loads payload JSON and telemetry JSONL from queue/log directories and filters sample data when real records exist. [VERIFIED: `kilnwatch/ground_station.py`]
- `calculate_metrics()` computes tiles processed, raw bytes, downlinked bytes, bandwidth saved, ignored tiles, JSON alerts, review/full alerts, compression ratio, and average latency. [VERIFIED: `kilnwatch/ground_station.py`]
- `detector_modes()` extracts detector mode strings from payloads and telemetry. [VERIFIED: `kilnwatch/ground_station.py`]
- `reasoner_statuses()` now extracts Liquid/LFM reasoner status as `disabled`, `liquid-mock`, or `liquid-real`. [VERIFIED: `kilnwatch/ground_station.py`]
- `safe_review_payloads()` filters imagery references to `CROP_OR_REVIEW` and `FULL_DOWNLINK`, but currently looks for `payload_uri` while newer payloads use `crop_ref`. This mismatch must be corrected in the plan. [VERIFIED: `kilnwatch/ground_station.py`] [VERIFIED: `satellite_edge_node/payloads.py`]
- `app.py` already splits rendering into functions, making refactor scope manageable. [VERIFIED: `app.py`]

### Key Gaps

- Proof status is still rendered as badges rather than a structured panel with raw fields such as `detector_mode`, `detector_is_real`, `simulated`, `fallback_used`, `reasoner_mode`, `reasoner_is_real`, model/version, and confidence threshold. [VERIFIED: `app.py`] [VERIFIED: `02-CONTEXT.md`]
- Crop review still renders JSON references and does not show actual crop images. [VERIFIED: `app.py`]
- Crop evidence helper semantics are incomplete because `safe_review_payloads()` does not use `crop_ref`, and there is no safe path resolver that rejects raw/source folders. [VERIFIED: `kilnwatch/ground_station.py`] [VERIFIED: `satellite_edge_node/payloads.py`]
- Metrics do not yet expose "detections" and "crops generated" as explicit first-screen counts. [VERIFIED: `kilnwatch/ground_station.py`] [VERIFIED: `app.py`]
- Boundary tests currently inspect `ground_station_ui/*.py` for forbidden raw imports/strings, but Phase 2 primary work is in root `app.py` and `kilnwatch/ground_station.py`; tests should cover those surfaces too. [VERIFIED: `tests/test_ground_station_boundary.py`]

## External Reference Findings

- Streamlit `st.image` accepts local image paths, `Path` objects, URLs, arrays, bytes, and lists, so the crop panel can render downlinked crop files directly when the resolved path is allowed and exists. [CITED: https://docs.streamlit.io/develop/api-reference/media/st.image]
- Streamlit local image paths are resolved relative to the working directory when running `streamlit run`, so helper code should normalize paths carefully and prefer queue-relative or repo-relative checks before rendering. [CITED: https://docs.streamlit.io/develop/api-reference/media/st.image]
- The Liquid model card for `LiquidAI/LFM2.5-VL-450M` supports local Transformers-style image-text usage, but Phase 2 should not add more model logic; it only needs to display `vlm_reasoning` truthfully. [CITED: https://huggingface.co/LiquidAI/LFM2.5-VL-450M]

## Recommended Planning Slices

### Plan 02-01: Proof Status, Metrics, and Crop Review UI

**Goal:** Make the dashboard's first screen prove detector/reasoner honesty, downlink savings, and crop evidence from queue artifacts.

**Likely files:**
- `app.py`
- `kilnwatch/ground_station.py`
- `tests/test_ground_station.py`

**Research-backed tasks:**
- Add a domain helper that summarizes proof status from payloads and telemetry:
  - detector labels: `STRICT YOLO REAL`, `BASELINE SIMULATION`, `FALLBACK USED`, `SAMPLE DATA`, `DETECTOR METADATA UNKNOWN`
  - reasoner labels: `LIQUID LFM REAL`, `LIQUID MOCK`, `LFM DISABLED`
  - raw fields: detector mode, detector real/simulated/fallback flags, reasoner mode/real flag, model/version, confidence threshold where available.
- Extend metrics or add a companion helper for detections and crop count:
  - detections: telemetry events/payloads with `kiln_detected=true` or alert actions
  - crops generated: non-null safe crop refs whose files exist and are readable enough to pass existence/non-zero checks.
- Replace or supplement the badge row with a structured Proof Status panel at the top of `app.py`.
- Add a Crop Review panel that calls `st.image()` only for safe downlinked crop files and otherwise shows `no real crop available`.
- Keep alert table and replay after the proof widgets.

### Plan 02-02: Queue-Only Boundary Validation

**Goal:** Make it difficult for future dashboard edits to cheat by reading raw/source imagery.

**Likely files:**
- `kilnwatch/ground_station.py`
- `tests/test_ground_station.py`
- `tests/test_ground_station_boundary.py`

**Research-backed tasks:**
- Add a safe crop resolver that accepts only crop paths under the selected `transmission_queue/` tree or a queue-visible downlinked crop path.
- Reject or return unavailable status for:
  - `data/raw_tiles/...`
  - `data/final_demo_tiles/...`
  - `datasets/roboflow/...`
  - `.tile` fixtures
  - nonexistent crop paths
- Expand boundary tests to scan `app.py`, `kilnwatch/ground_station.py`, and `ground_station_ui/*.py` for forbidden raw-source path usage.
- Add unit tests that a payload with `crop_ref` under queue crops is renderable, while raw/source paths produce `no real crop available`.

## Validation Strategy

Run after execution:

```bash
python -m unittest discover -s tests
python -m py_compile app.py kilnwatch/ground_station.py
python -m satellite_edge_node.orbital_pass \
  --raw-tiles data/final_demo_tiles \
  --transmission-queue /tmp/kilnwatch-phase2-queue \
  --detector yolo \
  --model-path models/brick_kiln_yolo.pt \
  --reasoner disabled
python -m satellite_edge_node.orbital_pass \
  --raw-tiles data/final_demo_tiles \
  --transmission-queue /tmp/kilnwatch-phase2-mock-queue \
  --detector yolo \
  --model-path models/brick_kiln_yolo.pt \
  --reasoner liquid-mock
```

If Streamlit is installed, run a dashboard smoke manually or with a browser tool:

```bash
streamlit run app.py
```

Dashboard smoke should verify visible text includes:

- `STRICT YOLO REAL` or `BASELINE SIMULATION` / `FALLBACK USED`
- `LIQUID LFM REAL`, `LIQUID MOCK`, or `LFM DISABLED`
- raw bytes, downlinked/transmitted bytes, bandwidth saved, compression ratio
- `no real crop available` when no safe crop exists

## Risks and Pitfalls

- **Context drift:** Existing `02-CONTEXT.md` says Liquid LFM is deferred, but live code now implements optional reasoner modes. Planner must include current code refs and avoid treating all Liquid status as future work.
- **Fake crop previews:** The highest-risk dashboard bug is accidentally rendering from `data/final_demo_tiles/` or raw Roboflow folders when `crop_ref` is missing. Use safe path resolution and tests.
- **Status overclaiming:** `liquid-mock` must never display as real Liquid LFM. `liquid-local` output is real local model inference only if `reasoner_is_real=true`; still do not claim fine-tuning.
- **Metrics mismatch:** Existing telemetry and payload schemas vary (`crop_path`, `crop_ref`, `payload_uri`, `transmitted_payload_bytes`, `downlinked_bytes`). Helpers should support current schemas explicitly and tests should cover both where needed.
- **UI-only logic:** Avoid embedding parsing/business rules directly inside Streamlit render functions; put reusable logic in `kilnwatch/ground_station.py`.

## Planning Recommendation

Proceed with two `PLAN.md` files matching the roadmap. The first should implement user-visible proof hierarchy and crop review. The second should harden helper/tests around queue-only crop evidence and forbidden raw paths. Both plans should read `02-CONTEXT.md`, this research file, `app.py`, `kilnwatch/ground_station.py`, `satellite_edge_node/payloads.py`, `satellite_edge_node/liquid_vlm_reasoner.py`, and the relevant tests before editing.

## RESEARCH COMPLETE

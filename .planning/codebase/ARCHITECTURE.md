<!-- refreshed: 2026-05-06 -->
# Architecture

**Analysis Date:** 2026-05-06

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                    Data Sources / Inputs                    │
├──────────────────┬──────────────────┬───────────────────────┤
│  Demo/raw tiles  │  SimSat fetches  │  Dataset manifests    │
│ `data/raw_tiles` │ `kilnwatch/      │ `datasets/kilnwatch/ │
│                  │  ingestion/`     │  manifests/`          │
└────────┬─────────┴────────┬─────────┴──────────┬────────────┘
         │                  │                     │
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 Satellite Edge Processing                   │
│ `satellite_edge_node/orbital_pass.py`                       │
│ `satellite_edge_node/detectors.py`                          │
│ `satellite_edge_node/payloads.py`                           │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                 Downlinked Queue / Telemetry                │
│ `transmission_queue/*.json`                                 │
│ `transmission_queue/telemetry.jsonl`                        │
│ `transmission_queue/crops/`                                 │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                       Ground Station UI                     │
│ `app.py` + `kilnwatch/ground_station.py`                    │
│ `ground_station_ui/app.py` + `ground_station_ui/queue_reader.py` │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Root Streamlit dashboard | Mission replay, status badges, bandwidth chart, alert table, technical-honesty panel | `app.py` |
| Ground-station domain helpers | Load visible payload/telemetry records, compute mission metrics, convert queue events into display decisions | `kilnwatch/ground_station.py` |
| Legacy/simple ground UI | Smaller Streamlit queue viewer for payloads and telemetry from a selected queue directory | `ground_station_ui/app.py` |
| Queue reader | Read downlinked JSON payloads and `telemetry.jsonl`; summarize byte accounting | `ground_station_ui/queue_reader.py` |
| Orbital pass runner | Discover raw tile files, run detector, create payloads, append telemetry, expose CLI | `satellite_edge_node/orbital_pass.py` |
| Detector router | Select baseline or YOLO detector and optionally wrap YOLO setup failures in explicit baseline fallback | `satellite_edge_node/detectors.py` |
| Baseline detector | Deterministic simulated detector using sidecar metadata or filename hints | `satellite_edge_node/baseline_detector.py` |
| YOLO detector | Strict local Ultralytics integration and result normalization to the shared detection schema | `satellite_edge_node/yolo_detector.py` |
| Payload builder | Decide transmit/drop, generate crops, encode payload JSON, calculate byte savings, build telemetry records | `satellite_edge_node/payloads.py` |
| Triage model | Convert generic prediction dictionaries into `IGNORE`, `JSON_ALERT_ONLY`, `CROP_OR_REVIEW`, or `FULL_DOWNLINK` decisions | `kilnwatch/triage.py` |
| SimSat ingestion | Fetch local SimSat current position and Sentinel-style image bytes, then write raw and metadata artifacts | `kilnwatch/ingestion/cli.py`, `kilnwatch/ingestion/simsat_client.py`, `kilnwatch/ingestion/dataset.py` |
| Dataset validation | Validate KilnWatch JSONL manifest schema and optional real-image readability | `kilnwatch/datasets/manifest.py`, `kilnwatch/datasets/image_validation.py` |
| Dataset adapters | Convert or document external local dataset formats into KilnWatch manifest JSONL | `kilnwatch/datasets/adapters/` |
| Utility scripts | Thin CLI wrappers for manifest validation, demo tile fetch, model readiness, detector evaluation, and smoke fetch | `scripts/` |
| Tests | Boundary, bandwidth, detector, ingestion, manifest, metadata, readiness, and triage regression coverage | `tests/` |

## Pattern Overview

**Overall:** File-backed satellite-edge simulation with a strict ground-station boundary.

**Key Characteristics:**
- Use local files as integration contracts: raw inputs live under `data/` and `datasets/`, downlinked artifacts live under `transmission_queue/`, and UI code reads only downlinked artifacts.
- Keep satellite-side concerns in `satellite_edge_node/`; keep ground-station display/accounting in `kilnwatch/ground_station.py` and `ground_station_ui/`.
- Normalize all detector implementations into `satellite_edge_node.baseline_detector.DetectionResult` before payload construction.
- Treat YOLO as strict real-detector mode: missing weights or missing `ultralytics` raises unless `--allow-baseline-fallback` is set.
- Preserve honesty metadata in payloads and telemetry through `detector_mode`, `detector_is_real`, `simulated`, `fallback_used`, and `fallback_reason`.
- Keep scripts as orchestration wrappers around package functions rather than primary business logic.

## Layers

**Input and Dataset Layer:**
- Purpose: Store demo tiles, fetched SimSat artifacts, labels, coordinates, dataset docs, and manifests.
- Location: `data/`, `datasets/kilnwatch/`
- Contains: Raw tile placeholders, readable demo images, metadata sidecars, JSONL manifests, labels, coordinate CSVs, dataset schema docs.
- Depends on: Filesystem and optional Pillow image validation.
- Used by: `satellite_edge_node/orbital_pass.py`, `scripts/fetch_demo_tiles.py`, `scripts/validate_manifest.py`, tests under `tests/`.

**Ingestion Layer:**
- Purpose: Fetch local SimSat data and materialize raw imagery plus metadata.
- Location: `kilnwatch/ingestion/`
- Contains: `SimSatClient`, `SimSatResponse`, `Region`, `TileRecord`, CLI entry point.
- Depends on: Standard-library `urllib`, JSON, filesystem writes under `data/`.
- Used by: `scripts/smoke_fetch_panipat.py`, `scripts/fetch_demo_tiles.py`, package script `kilnwatch-fetch-panipat`.

**Dataset Normalization Layer:**
- Purpose: Validate and convert local datasets into the KilnWatch manifest schema.
- Location: `kilnwatch/datasets/`
- Contains: Manifest validator, image validator, adapter base class, APAD converter, reference stubs for SentinelKilnDB, KDD24, and SustainBench/GEO-Bench.
- Depends on: JSONL files under `datasets/kilnwatch/`; optional Pillow for `--check-images`.
- Used by: `scripts/validate_manifest.py`, `scripts/fetch_demo_tiles.py`, `tests/test_manifest_schema.py`, `tests/test_fetch_demo_tiles.py`.

**Satellite Edge Layer:**
- Purpose: Simulate onboard tile discovery, detection, payload reduction, crop generation, telemetry, and CLI execution.
- Location: `satellite_edge_node/`
- Contains: Detector protocol and routers, baseline detector, YOLO detector, payload/telemetry builders, orbital pass runner.
- Depends on: Raw tile files, optional `ultralytics`, optional Pillow, output queue path.
- Used by: `python -m satellite_edge_node.orbital_pass`, package script `kilnwatch-orbital-pass`, bandwidth and detector tests.

**Downlink Boundary Layer:**
- Purpose: Persist only what the satellite chose to downlink.
- Location: `transmission_queue/`, `telemetry_logs/`, optional `telemetry/`
- Contains: Per-tile JSON payloads, `telemetry.jsonl`, optional crop files under `transmission_queue/crops/`, sample/external telemetry logs.
- Depends on: Satellite edge output writers.
- Used by: `kilnwatch/ground_station.py`, `ground_station_ui/queue_reader.py`, `app.py`, tests enforcing boundary behavior.

**Ground Station Layer:**
- Purpose: Present mission proof and bandwidth accounting from queue-visible files.
- Location: `app.py`, `kilnwatch/ground_station.py`, `ground_station_ui/`
- Contains: Streamlit UI, replay controls, metric calculators, payload readers, alert-row shaping.
- Depends on: `transmission_queue/`, `telemetry_logs/`, pandas, Streamlit.
- Used by: `streamlit run app.py`, `streamlit run ground_station_ui/app.py`, ground-station tests.

**Evaluation and Operations Layer:**
- Purpose: Check model readiness, evaluate telemetry against manifests, validate datasets, fetch demo tiles.
- Location: `scripts/`
- Contains: `check_model_ready.py`, `evaluate_detector.py`, `fetch_demo_tiles.py`, `validate_manifest.py`, `smoke_fetch_panipat.py`.
- Depends on: Package modules and repo-local data paths.
- Used by: README workflows and tests under `tests/`.

## Data Flow

### Primary Orbital Pass Path

1. Discover candidate tile files with `discover_tiles()` from `data/raw_tiles/` or another configured raw tile directory (`satellite_edge_node/orbital_pass.py:16`).
2. Build the selected detector with `build_detector_with_fallback()` when no detector instance is injected (`satellite_edge_node/orbital_pass.py:34`).
3. For each tile, read the file size, run `detector.detect_tile(tile_path)`, and measure inference latency (`satellite_edge_node/orbital_pass.py:43`).
4. Generate a crop only for alert-worthy detections with a bbox (`satellite_edge_node/payloads.py:24`).
5. Build either a dropped-tile payload or alert payload from the normalized `DetectionResult` (`satellite_edge_node/payloads.py:57`).
6. Write `transmission_queue/{tile_id}.json` and append a telemetry JSONL record with original, JSON, crop, transmitted, saved, action, confidence, and detector truth metadata (`satellite_edge_node/orbital_pass.py:51`, `satellite_edge_node/payloads.py:106`).
7. Return telemetry records and print aggregate byte-savings stats in the CLI (`satellite_edge_node/orbital_pass.py:103`).

### Ground Station Display Path

1. Load queue payloads from `transmission_queue/*.json` and telemetry from `transmission_queue/*.jsonl`, `telemetry_logs/*.jsonl`, or fallback `telemetry/*.jsonl` (`kilnwatch/ground_station.py:31`).
2. Prefer real records over sample-demo records when both exist (`kilnwatch/ground_station.py:41`).
3. Calculate mission metrics from telemetry events: raw bytes, downlinked bytes, savings, ignored tiles, JSON alerts, review/full alerts, and latency (`kilnwatch/ground_station.py:52`).
4. Build cumulative chart rows for raw bytes processed in orbit vs actual bytes downlinked (`kilnwatch/ground_station.py:77`).
5. Render status badges, metrics, chart, alert table, replay state, and review payload references in `app.py`.

### SimSat Ingestion Path

1. Parse fetch configuration for base URL, data root, timeout, image size, and endpoint overrides (`kilnwatch/ingestion/cli.py:18`).
2. Query SimSat current-position endpoints; write a smoke report under `data/smoke/` if no endpoint responds (`kilnwatch/ingestion/cli.py:37`).
3. Fetch a Sentinel-style tile for `PANIPAT` and write a smoke report if image endpoints fail (`kilnwatch/ingestion/cli.py:46`).
4. Write raw bytes to `data/raw/simsat/{region}/` and metadata JSON to `data/metadata/simsat/{region}/` via `write_tile_dataset()` (`kilnwatch/ingestion/dataset.py:45`).

### Dataset Manifest Validation Path

1. Scripts call `validate_manifest_file()` with one or more manifest paths (`scripts/validate_manifest.py`).
2. Each JSONL row is parsed as an object and checked against required fields, split values, coordinate bounds, bbox shape, confidence range, and sample-data honesty notes (`kilnwatch/datasets/manifest.py:32`).
3. Optional image validation requires a real raster extension and Pillow-readable image file (`kilnwatch/datasets/image_validation.py`).

**State Management:**
- Runtime mission state is file-backed, not database-backed. `transmission_queue/*.json` and `transmission_queue/telemetry.jsonl` are append/write outputs from the edge pass.
- Streamlit replay state is UI-local via `st.session_state.replay_index` in `app.py`.
- Dataset and ingestion artifacts are plain files under `data/` and `datasets/kilnwatch/`.
- There is no long-lived process state shared between the satellite runner and ground station.

## Key Abstractions

**DetectionResult:**
- Purpose: Shared normalized detector output.
- Examples: `satellite_edge_node/baseline_detector.py`, `satellite_edge_node/yolo_detector.py`, `satellite_edge_node/payloads.py`
- Pattern: Frozen dataclass with detector truth metadata and payload-ready fields.

**Detector Protocol:**
- Purpose: Allows orbital pass code to use baseline, YOLO, or fallback detectors through `detect_tile(Path) -> DetectionResult`.
- Examples: `satellite_edge_node/detectors.py`, `tests/test_yolo_detector.py`
- Pattern: `typing.Protocol` plus dataclass detector implementations.

**CropArtifact:**
- Purpose: Represents optional downlinked crop output and its byte cost or failure reason.
- Examples: `satellite_edge_node/payloads.py`
- Pattern: Frozen dataclass returned from `generate_crop_file()`.

**MissionMetrics:**
- Purpose: Ground-station aggregate byte and decision metrics.
- Examples: `kilnwatch/ground_station.py`, `app.py`, `tests/test_ground_station.py`
- Pattern: Frozen dataclass calculated from telemetry events.

**TriageDecision / TriageResult:**
- Purpose: Generic bandwidth-aware decision model for prediction dictionaries.
- Examples: `kilnwatch/triage.py`, `tests/test_triage.py`
- Pattern: `StrEnum` decisions plus frozen dataclasses for output and bandwidth estimates.

**TileRecord / Region / SimSatResponse:**
- Purpose: Typed ingestion boundary between SimSat HTTP responses and file artifacts.
- Examples: `kilnwatch/ingestion/dataset.py`, `kilnwatch/ingestion/regions.py`, `kilnwatch/ingestion/simsat_client.py`
- Pattern: Frozen dataclasses with filesystem serialization.

**ManifestIssue:**
- Purpose: Return line-specific validation issues without exiting from library code.
- Examples: `kilnwatch/datasets/manifest.py`, `scripts/validate_manifest.py`
- Pattern: Frozen dataclass emitted by a pure validator and formatted by the CLI script.

**DatasetAdapter:**
- Purpose: Standard interface for converting local third-party datasets into KilnWatch manifest JSONL.
- Examples: `kilnwatch/datasets/adapters/base.py`, `kilnwatch/datasets/adapters/apad_pakistan_igp.py`
- Pattern: Abstract base class; unavailable adapters raise `AdapterNotImplementedError` until local layout/license is confirmed.

## Entry Points

**Ground Station Dashboard:**
- Location: `app.py`
- Triggers: `streamlit run app.py`
- Responsibilities: Load queue-visible mission records, support mission replay, render byte-savings proof and alert tables.

**Simple Ground Station UI:**
- Location: `ground_station_ui/app.py`
- Triggers: `streamlit run ground_station_ui/app.py`
- Responsibilities: Read a selected transmission queue and display summary, alerts, telemetry, and raw payload JSON.

**Orbital Pass CLI:**
- Location: `satellite_edge_node/orbital_pass.py`
- Triggers: `python -m satellite_edge_node.orbital_pass`, `kilnwatch-orbital-pass`
- Responsibilities: Run detector over raw tiles, write downlinked payloads, append telemetry, print byte-savings summary.

**SimSat Fetch CLI:**
- Location: `kilnwatch/ingestion/cli.py`
- Triggers: `python -m kilnwatch.ingestion.cli`, `kilnwatch-fetch-panipat`, `scripts/smoke_fetch_panipat.py`
- Responsibilities: Fetch a Panipat Sentinel-style tile from local SimSat or write smoke reports when unavailable.

**Manifest Validator CLI:**
- Location: `scripts/validate_manifest.py`
- Triggers: `python scripts/validate_manifest.py datasets/kilnwatch/manifests/sample_demo_manifest.jsonl`
- Responsibilities: Validate JSONL manifest schema and optionally validate image readability.

**Demo Tile Builder CLI:**
- Location: `scripts/fetch_demo_tiles.py`
- Triggers: `python scripts/fetch_demo_tiles.py ...`
- Responsibilities: Convert coordinate CSV rows into demo tile files, sidecars, and manifests using local-import or SimSat modes.

**Model Readiness CLI:**
- Location: `scripts/check_model_ready.py`
- Triggers: `python scripts/check_model_ready.py`, `python scripts/check_model_ready.py --json`
- Responsibilities: Report whether `models/brick_kiln_yolo.pt` and `ultralytics` are available for strict YOLO mode.

**Detector Evaluation CLI:**
- Location: `scripts/evaluate_detector.py`
- Triggers: `python scripts/evaluate_detector.py --manifest ... --telemetry ...`
- Responsibilities: Compare telemetry predictions to manifest labels and flag simulated/sample evaluations.

## Architectural Constraints

- **Threading:** Single-process, synchronous Python execution. Streamlit manages UI reruns; satellite and ingestion CLIs run sequential file loops.
- **Global state:** Streamlit session state is limited to `st.session_state.replay_index` in `app.py`; filesystem constants live in `kilnwatch/ground_station.py` and model path defaults live in `satellite_edge_node/yolo_detector.py` and `scripts/check_model_ready.py`.
- **Circular imports:** Not detected in the inspected package graph. `satellite_edge_node/orbital_pass.py` depends downward on detector and payload modules; UI code depends on ground-station helpers; ingestion and dataset modules are separate.
- **Ground-station boundary:** Ground-station code must read `transmission_queue/`, `telemetry_logs/`, or `telemetry/` records only. Do not import satellite raw tile modules or inspect `data/raw_tiles/` from UI code.
- **Detector honesty:** Real detector claims require strict YOLO mode with local weights at `models/brick_kiln_yolo.pt` and `ultralytics` installed. Baseline and fallback paths must remain visibly marked as simulated.
- **Storage contract:** Edge output is JSON/JSONL plus optional crop files. Adding databases, queues, or remote services changes the integration contract and needs tests around the ground-station boundary.
- **Generated/runtime data:** `transmission_queue/`, `data/raw/`, `data/metadata/`, and `data/smoke/` are runtime/demo artifact locations; code should tolerate missing directories.

## Anti-Patterns

### Ground Station Reading Raw Satellite Inputs

**What happens:** UI or ground-station code reads `data/raw_tiles/`, `data/raw/`, or imports satellite tile discovery helpers.
**Why it's wrong:** It breaks the proof that only downlinked artifacts reached the ground station.
**Do this instead:** Add queue-visible fields in `satellite_edge_node/payloads.py` or telemetry fields in `satellite_edge_node/orbital_pass.py`, then consume them through `kilnwatch/ground_station.py`.

### Silent Detector Fallback

**What happens:** YOLO setup failure is hidden by baseline simulation.
**Why it's wrong:** It allows simulated detections to look like real model inference.
**Do this instead:** Use strict YOLO mode by default through `satellite_edge_node/detectors.py`; only allow fallback when CLI callers set `--allow-baseline-fallback`, and preserve fallback metadata in `DetectionResult`.

### Putting Business Logic in Streamlit Rendering

**What happens:** Metric, decision, or telemetry parsing logic is added directly to `app.py` or `ground_station_ui/app.py`.
**Why it's wrong:** It becomes hard to test without Streamlit and duplicates package helpers.
**Do this instead:** Put reusable accounting and parsing logic in `kilnwatch/ground_station.py` or `ground_station_ui/queue_reader.py`, then keep Streamlit files as renderers.

### Bypassing Manifest Validators

**What happens:** New dataset scripts write JSONL rows with ad hoc fields or unchecked sample-data claims.
**Why it's wrong:** Evaluation and detector scripts depend on consistent fields like `tile_id`, `image_path`, `split`, `kiln_detected`, `bbox`, and honesty notes.
**Do this instead:** Use `kilnwatch/datasets/manifest.py` schema rules and call `scripts/validate_manifest.py` for new manifests.

## Error Handling

**Strategy:** Library functions raise typed or standard exceptions for invalid data; CLI entry points catch expected external-service/model setup failures and return user-readable status codes or smoke reports.

**Patterns:**
- `satellite_edge_node/yolo_detector.py` raises `YoloModelUnavailable` for missing weights, missing `ultralytics`, or failed model loading.
- `satellite_edge_node/orbital_pass.py` catches `YoloDetectorError` at CLI boundary and exits with code `2`.
- `kilnwatch/ingestion/cli.py` catches `SimSatUnavailable` and writes smoke reports instead of failing the local workflow.
- `kilnwatch/datasets/manifest.py` accumulates `ManifestIssue` values instead of raising for ordinary schema problems.
- `satellite_edge_node/payloads.py` records crop generation errors in payload/telemetry metadata rather than claiming nonexistent crops.

## Cross-Cutting Concerns

**Logging:** Uses CLI `print()` output and JSON/JSONL artifact logs. There is no central logging framework.

**Validation:** Manifest validation lives in `kilnwatch/datasets/manifest.py`; readable image validation lives in `kilnwatch/datasets/image_validation.py`; model readiness lives in `scripts/check_model_ready.py`; detector evaluation honesty checks live in `scripts/evaluate_detector.py`.

**Authentication:** Not applicable for current local workflows. SimSat defaults to `http://localhost:9005` and no auth handling is present in `kilnwatch/ingestion/simsat_client.py`.

**External integrations:** Optional local SimSat HTTP endpoints are used by `kilnwatch/ingestion/simsat_client.py`; optional local Ultralytics YOLO inference is used by `satellite_edge_node/yolo_detector.py`.

**Bandwidth accounting:** Satellite-side byte accounting is produced in `satellite_edge_node/payloads.py`; ground-station aggregate accounting is calculated in `kilnwatch/ground_station.py` and `ground_station_ui/queue_reader.py`.

---

*Architecture analysis: 2026-05-06*

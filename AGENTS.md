<!-- GSD:project-start source:PROJECT.md -->
## Project

**KilnWatch**

KilnWatch is a satellite-side brick kiln compliance triage demo for the Liquid AI x DPhi Space AI in Space hackathon. It simulates an onboard Earth-observation workflow where a satellite edge node inspects imagery, decides what is worth transmitting, and downlinks compact JSON alerts plus targeted crops instead of full raw tiles.

The current codebase is a strong system architecture MVP: satellite edge processing, detector routing, queue artifacts, telemetry, and a Streamlit ground station already exist. The final push is to make the demo polished, technically honest, and submission-ready, with at least one real end-to-end proof chain from real image to detector result to crop to JSON payload to dashboard.

**Core Value:** Prove the satellite/ground boundary correctly: the satellite node decides what is worth transmitting, and the ground station only sees downlinked artifacts.

### Constraints

- **Deadline**: Event materials show the hackathon ending around May 9, 2026 in local GMT+5:30 display, while the submission blast text contains a likely stale "May 9, 2025" date. Submit as early as possible and do not depend on last-hour fixes.
- **Submission honesty**: Do not imply the project uses Liquid LFM, Sentinel imagery, trained YOLO weights, or a deployed satellite payload unless the repo proves it.
- **Detector readiness**: Strict YOLO mode requires `models/brick_kiln_yolo.pt` and `ultralytics`; if absent, real detector claims are blocked.
- **Data proof**: Placeholder `.tile` blobs cannot be described as real Sentinel imagery; the final demo needs at least one real image/crop path or a clearly disclosed manual/simulated fixture.
- **Ground boundary**: The dashboard must read only `transmission_queue/` and telemetry/downlinked artifacts, not raw onboard inputs.
- **Time budget**: Prioritize the minimum real proof chain, README/demo polish, and submission answers over broad refactors.
- **Dependencies**: Avoid adding new dependencies unless they directly support final proof, demo polish, or validation.
- **Coordination**: Multiple Codex/Gemini lanes are active, so edits should stay scoped and commits should be intentional.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python >=3.11 - Required by `pyproject.toml`; used across `app.py`, `satellite_edge_node/`, `kilnwatch/`, `ground_station_ui/`, `scripts/`, and `tests/`.
- Markdown - Project documentation in `README.md`, `docs/architecture.md`, `docs/model_training.md`, `docs/demo_data_pipeline.md`, and dataset documentation under `datasets/kilnwatch/docs/`.
- JSON / JSONL - Local telemetry, manifests, labels, sidecars, and config in `transmission_queue/telemetry.jsonl`, `datasets/kilnwatch/manifests/*.jsonl`, `datasets/kilnwatch/labels/*.jsonl`, `data/raw_tiles/*.meta.json`, and `config/regions/haryana_india.json`.
- CSV - Coordinate templates and demo inputs in `datasets/kilnwatch/coordinates/*.csv`.
## Runtime
- CPython >=3.11.
- Local CLI execution for ingestion, orbital-pass simulation, validation, model readiness checks, and evaluation.
- Streamlit local web runtime for ground-station dashboards.
- pip / virtualenv - Installation flow documented in `README.md`.
- Lockfile: missing. No `requirements.lock`, `uv.lock`, `Pipfile.lock`, or package-manager lockfile is present.
- Editable/package metadata: `pyproject.toml` uses `setuptools>=68` as the build backend.
## Frameworks
- Streamlit >=1.35 - Ground-station dashboard UI in `app.py` and legacy/simple dashboard in `ground_station_ui/app.py`.
- Pandas >=2.2 - DataFrame/chart support for dashboard tables and cumulative telemetry visualization in `app.py`.
- Pillow >=10 - Image readability checks and crop generation in `kilnwatch/datasets/image_validation.py`, `satellite_edge_node/payloads.py`, and tests that create image fixtures.
- Python standard library HTTP client - SimSat ingestion uses `urllib.request`, `urllib.parse`, and `urllib.error` in `kilnwatch/ingestion/simsat_client.py`.
- unittest - Primary checked-in test style under `tests/`.
- pytest - Supported by `pyproject.toml` test discovery and documented in `README.md`; not pinned in `requirements.txt`.
- setuptools >=68 - Build backend in `pyproject.toml`.
- argparse CLIs - Used by `satellite_edge_node/orbital_pass.py`, `kilnwatch/ingestion/cli.py`, `scripts/fetch_demo_tiles.py`, `scripts/validate_manifest.py`, `scripts/check_model_ready.py`, and `scripts/evaluate_detector.py`.
- No lint/format tool configuration detected. No Ruff, Black, mypy, ESLint, Prettier, or Makefile config is present.
## Key Dependencies
- `streamlit>=1.35` - Required to run the ground-station dashboards from `app.py` and `ground_station_ui/app.py`.
- `pandas>=2.2` - Required by `app.py` for alert tables and cumulative downlink chart data.
- `Pillow>=10` - Required for real image validation in `kilnwatch/datasets/image_validation.py` and crop extraction in `satellite_edge_node/payloads.py`.
- `ultralytics` - Optional local YOLO inference package. It is intentionally not pinned in `requirements.txt`; strict YOLO mode in `satellite_edge_node/yolo_detector.py` fails loudly unless the package and `models/brick_kiln_yolo.pt` exist.
- Local model weights at `models/brick_kiln_yolo.pt` - Expected real detector artifact, documented in `README.md`, `docs/model_training.md`, and checked by `scripts/check_model_ready.py`.
- Local filesystem queues and logs - Runtime output uses `transmission_queue/*.json`, `transmission_queue/telemetry.jsonl`, and `telemetry_logs/*.jsonl`.
## Configuration
- No `.env` file detected in the repo root or first three directory levels during this scan.
- No environment variables are required by the checked-in code.
- SimSat connection is configured by CLI arguments, not env vars:
- Ground-station input is configured by local paths:
- YOLO model path is configurable with `--model-path`; the default is `models/brick_kiln_yolo.pt` in `satellite_edge_node/yolo_detector.py`, `satellite_edge_node/orbital_pass.py`, and `scripts/check_model_ready.py`.
- `pyproject.toml` defines package metadata, Python version, build backend, scripts, and pytest testpaths.
- `requirements.txt` defines local runtime dashboard/image dependencies.
- `.gitignore` excludes `.venv/`, Python caches, pytest/mypy/ruff caches, `.omx/`, and generated data under `data/raw/**`, `data/metadata/**`, and `data/smoke/**` while keeping `.gitkeep` placeholders.
## Platform Requirements
- Python 3.11 or newer.
- Create a local virtual environment and install `requirements.txt` before running dashboards.
- Install `ultralytics` separately only when running strict YOLO inference.
- Provide local model weights at `models/brick_kiln_yolo.pt` before claiming real detector availability.
- Run SimSat locally at `http://localhost:9005` only for `--mode simsat` ingestion; placeholder and local-import modes do not need the service.
- Use local, license-compatible imagery for real demo/evaluation data. `docs/external_resources.md` and `docs/demo_data_pipeline.md` explicitly avoid paid API dependencies.
- Not detected. No Dockerfile, deployment config, CI pipeline, cloud target, hosted database, or production service manifest is present.
- Current deployment shape is local execution: `streamlit run app.py`, `python -m satellite_edge_node.orbital_pass`, and Python scripts under `scripts/`.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- Use lowercase snake_case for Python modules: `kilnwatch/ground_station.py`, `satellite_edge_node/orbital_pass.py`, `scripts/fetch_demo_tiles.py`.
- Use package `__init__.py` files as lightweight package markers, not export hubs: `kilnwatch/__init__.py`, `satellite_edge_node/__init__.py`, `ground_station_ui/__init__.py`.
- Use `test_*.py` for test modules under `tests/`: `tests/test_ground_station.py`, `tests/test_yolo_detector.py`, `tests/test_fetch_demo_tiles.py`.
- Keep runnable scripts in `scripts/` and expose package CLIs through `[project.scripts]` in `pyproject.toml`: `scripts/evaluate_detector.py`, `scripts/validate_manifest.py`, `kilnwatch.ingestion.cli:main`, `satellite_edge_node.orbital_pass:main`.
- Use snake_case and explicit verb phrases for public operations: `load_ground_station_records()` in `kilnwatch/ground_station.py`, `simulate_orbital_pass()` in `satellite_edge_node/orbital_pass.py`, `evaluate_detector()` in `scripts/evaluate_detector.py`.
- Use leading underscore for module-private helpers: `_load_payloads()` in `kilnwatch/ground_station.py`, `_extract_detections()` in `satellite_edge_node/yolo_detector.py`, `_truth_positive()` in `scripts/evaluate_detector.py`.
- CLI modules use `main() -> int` and `if __name__ == "__main__": raise SystemExit(main())`: `satellite_edge_node/orbital_pass.py`, `scripts/evaluate_detector.py`, `scripts/check_model_ready.py`.
- Streamlit entry points use `main() -> None` and call `main()` directly under the module guard: `app.py`, `ground_station_ui/app.py`.
- Use descriptive snake_case domain names: `raw_bytes_processed`, `downlinked_bytes`, `telemetry_events`, `confidence_threshold` in `kilnwatch/ground_station.py` and `satellite_edge_node/orbital_pass.py`.
- Use uppercase constants for domain policy and default paths: `TRANSMISSION_QUEUE_DIR`, `REVIEW_DECISIONS` in `kilnwatch/ground_station.py`; `DEFAULT_MODEL_PATH`, `DETECTOR_VERSION` in `satellite_edge_node/yolo_detector.py`; `REQUIRED_FIELDS`, `ALLOWED_SPLITS` in `kilnwatch/datasets/manifest.py`.
- Use plural collection names for lists/sets/dicts: `payloads`, `events`, `detections`, `missing_predictions` in `kilnwatch/ground_station.py`, `satellite_edge_node/yolo_detector.py`, and `scripts/evaluate_detector.py`.
- Use PascalCase for dataclasses, protocols, enums, and exceptions: `MissionMetrics` in `kilnwatch/ground_station.py`, `Detector` in `satellite_edge_node/detectors.py`, `TriageDecision` in `kilnwatch/triage.py`, `YoloModelUnavailable` in `satellite_edge_node/yolo_detector.py`.
- Use frozen dataclasses for immutable domain records: `DetectionResult` in `satellite_edge_node/baseline_detector.py`, `CropArtifact` in `satellite_edge_node/payloads.py`, `ManifestIssue` in `kilnwatch/datasets/manifest.py`.
- Use exception names ending in `Error` or a precise unavailable condition: `ImageValidationError` in `kilnwatch/datasets/image_validation.py`, `SimSatUnavailable` in `kilnwatch/ingestion/simsat_client.py`.
## Code Style
- No formatter configuration is detected in `pyproject.toml`, `.prettierrc`, `ruff.toml`, or `setup.cfg`.
- Follow the existing Black-compatible shape: 4-space indentation, blank line between top-level definitions, trailing commas in multi-line literals/calls, and 88-ish line wrapping where practical. Examples: `satellite_edge_node/payloads.py`, `tests/test_satellite_edge_bandwidth.py`.
- Use `from __future__ import annotations` in production modules to support modern type syntax consistently: `app.py`, `kilnwatch/triage.py`, `satellite_edge_node/yolo_detector.py`, `scripts/fetch_demo_tiles.py`.
- Prefer `Path` over raw string path handling for filesystem code: `kilnwatch/ground_station.py`, `satellite_edge_node/orbital_pass.py`, `scripts/fetch_demo_tiles.py`.
- No lint tool is configured in `pyproject.toml`.
- Keep imports clean manually: standard library first, third-party packages next, local package imports last. Examples: `app.py`, `satellite_edge_node/yolo_detector.py`, `scripts/evaluate_detector.py`.
- Avoid broad dependencies in core package code. Optional imports are localized to the feature using them: `from PIL import Image` inside `satellite_edge_node/payloads.py`, `from ultralytics import YOLO` inside `satellite_edge_node/yolo_detector.py`.
## Import Organization
- No configured path aliases are detected. Import package modules by package name from the repo root: `kilnwatch.ground_station`, `satellite_edge_node.detectors`, `ground_station_ui.queue_reader`.
- Use relative imports inside package modules when importing sibling modules: `.baseline_detector` in `satellite_edge_node/detectors.py`, `.payloads` in `satellite_edge_node/orbital_pass.py`.
## Error Handling
- Raise domain-specific exceptions at integration boundaries: `YoloModelUnavailable` and `YoloDetectorError` in `satellite_edge_node/yolo_detector.py`, `SimSatUnavailable` in `kilnwatch/ingestion/simsat_client.py`, `ImageValidationError` in `kilnwatch/datasets/image_validation.py`.
- Wrap external/library failures with contextual messages and exception chaining: YOLO import/model/inference failures in `satellite_edge_node/yolo_detector.py`; image validation failures in `kilnwatch/datasets/image_validation.py`; SimSat endpoint failures in `kilnwatch/ingestion/simsat_client.py`.
- Return structured issue lists for validators instead of raising on every row-level problem: `validate_manifest_file()` returns `list[ManifestIssue]` in `kilnwatch/datasets/manifest.py`.
- Use conversion helpers that default malformed user/data input safely when metrics should keep rendering: `_as_int()` and `_as_float()` in `kilnwatch/ground_station.py`, `_safe_float()` in `satellite_edge_node/yolo_detector.py`.
- CLI `main()` functions catch expected user-facing failures, print concise messages, and return non-zero status codes: `satellite_edge_node/orbital_pass.py`, `scripts/fetch_demo_tiles.py`, `scripts/validate_manifest.py`.
- Do not hide truth/state transitions. Fallbacks include explicit metadata such as `fallback_used`, `fallback_reason`, `detector_is_real`, and `simulated` in `satellite_edge_node/detectors.py` and `satellite_edge_node/payloads.py`.
## Logging
- CLI tools print human-readable summaries to stdout and errors to stderr when appropriate: `scripts/fetch_demo_tiles.py`, `scripts/validate_manifest.py`, `satellite_edge_node/orbital_pass.py`.
- JSON-producing tools print deterministic JSON with `sort_keys=True` for machine-readable output: `scripts/evaluate_detector.py`, `scripts/check_model_ready.py`.
- Streamlit UI code reports status through `st.error`, `st.warning`, `st.info`, `st.caption`, and metrics instead of logs: `app.py`, `ground_station_ui/app.py`.
## Comments
- Prefer module docstrings that state purpose: `kilnwatch/ground_station.py`, `satellite_edge_node/orbital_pass.py`, `satellite_edge_node/payloads.py`, `scripts/evaluate_detector.py`.
- Use short comments only where a dependency can fail in multiple backend-specific ways: `satellite_edge_node/yolo_detector.py` comments around model loading and inference exceptions.
- Keep inline comments sparse; encode most intent in function names, dataclass fields, and exception messages.
- Not applicable. This repo is Python.
- Python docstrings are used selectively for public behavior and abstract contracts: `load_ground_station_records()` in `kilnwatch/ground_station.py`, `compute_triage()` in `kilnwatch/triage.py`, `DatasetAdapter.convert()` in `kilnwatch/datasets/adapters/base.py`.
## Function Design
## Module Design
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## System Overview
```text
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
- Use local files as integration contracts: raw inputs live under `data/` and `datasets/`, downlinked artifacts live under `transmission_queue/`, and UI code reads only downlinked artifacts.
- Keep satellite-side concerns in `satellite_edge_node/`; keep ground-station display/accounting in `kilnwatch/ground_station.py` and `ground_station_ui/`.
- Normalize all detector implementations into `satellite_edge_node.baseline_detector.DetectionResult` before payload construction.
- Treat YOLO as strict real-detector mode: missing weights or missing `ultralytics` raises unless `--allow-baseline-fallback` is set.
- Preserve honesty metadata in payloads and telemetry through `detector_mode`, `detector_is_real`, `simulated`, `fallback_used`, and `fallback_reason`.
- Keep scripts as orchestration wrappers around package functions rather than primary business logic.
## Layers
- Purpose: Store demo tiles, fetched SimSat artifacts, labels, coordinates, dataset docs, and manifests.
- Location: `data/`, `datasets/kilnwatch/`
- Contains: Raw tile placeholders, readable demo images, metadata sidecars, JSONL manifests, labels, coordinate CSVs, dataset schema docs.
- Depends on: Filesystem and optional Pillow image validation.
- Used by: `satellite_edge_node/orbital_pass.py`, `scripts/fetch_demo_tiles.py`, `scripts/validate_manifest.py`, tests under `tests/`.
- Purpose: Fetch local SimSat data and materialize raw imagery plus metadata.
- Location: `kilnwatch/ingestion/`
- Contains: `SimSatClient`, `SimSatResponse`, `Region`, `TileRecord`, CLI entry point.
- Depends on: Standard-library `urllib`, JSON, filesystem writes under `data/`.
- Used by: `scripts/smoke_fetch_haryana.py`, `scripts/fetch_demo_tiles.py`, package script `kilnwatch-fetch-haryana`.
- Purpose: Validate and convert local datasets into the KilnWatch manifest schema.
- Location: `kilnwatch/datasets/`
- Contains: Manifest validator, image validator, adapter base class, APAD converter, reference stubs for SentinelKilnDB, KDD24, and SustainBench/GEO-Bench.
- Depends on: JSONL files under `datasets/kilnwatch/`; optional Pillow for `--check-images`.
- Used by: `scripts/validate_manifest.py`, `scripts/fetch_demo_tiles.py`, `tests/test_manifest_schema.py`, `tests/test_fetch_demo_tiles.py`.
- Purpose: Simulate onboard tile discovery, detection, payload reduction, crop generation, telemetry, and CLI execution.
- Location: `satellite_edge_node/`
- Contains: Detector protocol and routers, baseline detector, YOLO detector, payload/telemetry builders, orbital pass runner.
- Depends on: Raw tile files, optional `ultralytics`, optional Pillow, output queue path.
- Used by: `python -m satellite_edge_node.orbital_pass`, package script `kilnwatch-orbital-pass`, bandwidth and detector tests.
- Purpose: Persist only what the satellite chose to downlink.
- Location: `transmission_queue/`, `telemetry_logs/`, optional `telemetry/`
- Contains: Per-tile JSON payloads, `telemetry.jsonl`, optional crop files under `transmission_queue/crops/`, sample/external telemetry logs.
- Depends on: Satellite edge output writers.
- Used by: `kilnwatch/ground_station.py`, `ground_station_ui/queue_reader.py`, `app.py`, tests enforcing boundary behavior.
- Purpose: Present mission proof and bandwidth accounting from queue-visible files.
- Location: `app.py`, `kilnwatch/ground_station.py`, `ground_station_ui/`
- Contains: Streamlit UI, replay controls, metric calculators, payload readers, alert-row shaping.
- Depends on: `transmission_queue/`, `telemetry_logs/`, pandas, Streamlit.
- Used by: `streamlit run app.py`, `streamlit run ground_station_ui/app.py`, ground-station tests.
- Purpose: Check model readiness, evaluate telemetry against manifests, validate datasets, fetch demo tiles.
- Location: `scripts/`
- Contains: `check_model_ready.py`, `evaluate_detector.py`, `fetch_demo_tiles.py`, `validate_manifest.py`, `smoke_fetch_haryana.py`.
- Depends on: Package modules and repo-local data paths.
- Used by: README workflows and tests under `tests/`.
## Data Flow
### Primary Orbital Pass Path
### Ground Station Display Path
### SimSat Ingestion Path
### Dataset Manifest Validation Path
- Runtime mission state is file-backed, not database-backed. `transmission_queue/*.json` and `transmission_queue/telemetry.jsonl` are append/write outputs from the edge pass.
- Streamlit replay state is UI-local via `st.session_state.replay_index` in `app.py`.
- Dataset and ingestion artifacts are plain files under `data/` and `datasets/kilnwatch/`.
- There is no long-lived process state shared between the satellite runner and ground station.
## Key Abstractions
- Purpose: Shared normalized detector output.
- Examples: `satellite_edge_node/baseline_detector.py`, `satellite_edge_node/yolo_detector.py`, `satellite_edge_node/payloads.py`
- Pattern: Frozen dataclass with detector truth metadata and payload-ready fields.
- Purpose: Allows orbital pass code to use baseline, YOLO, or fallback detectors through `detect_tile(Path) -> DetectionResult`.
- Examples: `satellite_edge_node/detectors.py`, `tests/test_yolo_detector.py`
- Pattern: `typing.Protocol` plus dataclass detector implementations.
- Purpose: Represents optional downlinked crop output and its byte cost or failure reason.
- Examples: `satellite_edge_node/payloads.py`
- Pattern: Frozen dataclass returned from `generate_crop_file()`.
- Purpose: Ground-station aggregate byte and decision metrics.
- Examples: `kilnwatch/ground_station.py`, `app.py`, `tests/test_ground_station.py`
- Pattern: Frozen dataclass calculated from telemetry events.
- Purpose: Generic bandwidth-aware decision model for prediction dictionaries.
- Examples: `kilnwatch/triage.py`, `tests/test_triage.py`
- Pattern: `StrEnum` decisions plus frozen dataclasses for output and bandwidth estimates.
- Purpose: Typed ingestion boundary between SimSat HTTP responses and file artifacts.
- Examples: `kilnwatch/ingestion/dataset.py`, `kilnwatch/ingestion/regions.py`, `kilnwatch/ingestion/simsat_client.py`
- Pattern: Frozen dataclasses with filesystem serialization.
- Purpose: Return line-specific validation issues without exiting from library code.
- Examples: `kilnwatch/datasets/manifest.py`, `scripts/validate_manifest.py`
- Pattern: Frozen dataclass emitted by a pure validator and formatted by the CLI script.
- Purpose: Standard interface for converting local third-party datasets into KilnWatch manifest JSONL.
- Examples: `kilnwatch/datasets/adapters/base.py`, `kilnwatch/datasets/adapters/apad_pakistan_igp.py`
- Pattern: Abstract base class; unavailable adapters raise `AdapterNotImplementedError` until local layout/license is confirmed.
## Entry Points
- Location: `app.py`
- Triggers: `streamlit run app.py`
- Responsibilities: Load queue-visible mission records, support mission replay, render byte-savings proof and alert tables.
- Location: `ground_station_ui/app.py`
- Triggers: `streamlit run ground_station_ui/app.py`
- Responsibilities: Read a selected transmission queue and display summary, alerts, telemetry, and raw payload JSON.
- Location: `satellite_edge_node/orbital_pass.py`
- Triggers: `python -m satellite_edge_node.orbital_pass`, `kilnwatch-orbital-pass`
- Responsibilities: Run detector over raw tiles, write downlinked payloads, append telemetry, print byte-savings summary.
- Location: `kilnwatch/ingestion/cli.py`
- Triggers: `python -m kilnwatch.ingestion.cli`, `kilnwatch-fetch-haryana`, `scripts/smoke_fetch_haryana.py`
- Responsibilities: Fetch a Haryana, India Sentinel-style tile from local SimSat or write smoke reports when unavailable.
- Location: `scripts/validate_manifest.py`
- Triggers: `python scripts/validate_manifest.py datasets/kilnwatch/manifests/sample_demo_manifest.jsonl`
- Responsibilities: Validate JSONL manifest schema and optionally validate image readability.
- Location: `scripts/fetch_demo_tiles.py`
- Triggers: `python scripts/fetch_demo_tiles.py ...`
- Responsibilities: Convert coordinate CSV rows into demo tile files, sidecars, and manifests using local-import or SimSat modes.
- Location: `scripts/check_model_ready.py`
- Triggers: `python scripts/check_model_ready.py`, `python scripts/check_model_ready.py --json`
- Responsibilities: Report whether `models/brick_kiln_yolo.pt` and `ultralytics` are available for strict YOLO mode.
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
### Silent Detector Fallback
### Putting Business Logic in Streamlit Rendering
### Bypassing Manifest Validators
## Error Handling
- `satellite_edge_node/yolo_detector.py` raises `YoloModelUnavailable` for missing weights, missing `ultralytics`, or failed model loading.
- `satellite_edge_node/orbital_pass.py` catches `YoloDetectorError` at CLI boundary and exits with code `2`.
- `kilnwatch/ingestion/cli.py` catches `SimSatUnavailable` and writes smoke reports instead of failing the local workflow.
- `kilnwatch/datasets/manifest.py` accumulates `ManifestIssue` values instead of raising for ordinary schema problems.
- `satellite_edge_node/payloads.py` records crop generation errors in payload/telemetry metadata rather than claiming nonexistent crops.
## Cross-Cutting Concerns
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->

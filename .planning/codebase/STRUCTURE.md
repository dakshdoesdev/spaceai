# Codebase Structure

**Analysis Date:** 2026-05-06

## Directory Layout

```text
SpaceAI/
├── app.py                         # Primary Streamlit ground-station dashboard
├── pyproject.toml                 # Package metadata, console scripts, pytest config
├── requirements.txt               # Runtime/demo dependencies
├── README.md                      # User-facing overview and local demo workflow
├── docs/                          # Architecture, training, demo, checklist, honesty docs
├── kilnwatch/                     # Domain package for ground station, triage, ingestion, datasets
│   ├── ground_station.py          # Queue-visible telemetry loading and metrics
│   ├── triage.py                  # Bandwidth-aware triage decision model
│   ├── ingestion/                 # SimSat client, region definitions, dataset writers, CLI
│   └── datasets/                  # Manifest validation, image validation, dataset adapters
├── satellite_edge_node/           # Satellite-side detection, payload, telemetry, orbital pass
├── ground_station_ui/             # Smaller Streamlit queue-reader UI
├── scripts/                       # Operational CLIs around package functions
├── tests/                         # Unit and boundary tests
├── data/                          # Local raw/demo/metadata/smoke data artifacts
├── datasets/kilnwatch/            # Dataset docs, coordinates, labels, manifests, demo images
├── models/                        # Expected local YOLO weights location
├── transmission_queue/            # Downlinked payload JSON and telemetry JSONL
├── telemetry_logs/                # Optional sample/external telemetry logs
├── config/regions/                # Region configuration files
├── .planning/codebase/            # Generated codebase map documents
└── .codex/                        # Project-local GSD/OMX skills and hooks
```

## Directory Purposes

**Root:**
- Purpose: Demo entry points, packaging, project docs, and dependency declarations.
- Contains: `app.py`, `README.md`, `pyproject.toml`, `requirements.txt`.
- Key files: `app.py`, `README.md`, `docs/architecture.md`.

**`kilnwatch/`:**
- Purpose: Main reusable domain package for ground-station math, triage, ingestion, and dataset tooling.
- Contains: Pure Python modules and subpackages imported by scripts, Streamlit UI, and tests.
- Key files: `kilnwatch/ground_station.py`, `kilnwatch/triage.py`, `kilnwatch/__init__.py`.

**`kilnwatch/ingestion/`:**
- Purpose: Local SimSat/Sentinel-style fetch workflow and artifact writers.
- Contains: CLI parsing, HTTP client, region definitions, raw/metadata dataset write helpers.
- Key files: `kilnwatch/ingestion/cli.py`, `kilnwatch/ingestion/simsat_client.py`, `kilnwatch/ingestion/dataset.py`, `kilnwatch/ingestion/regions.py`.

**`kilnwatch/datasets/`:**
- Purpose: KilnWatch manifest validation, image validation, and local dataset conversion interfaces.
- Contains: Manifest schema rules, image readability checks, adapter implementations and stubs.
- Key files: `kilnwatch/datasets/manifest.py`, `kilnwatch/datasets/image_validation.py`, `kilnwatch/datasets/adapters/base.py`.

**`kilnwatch/datasets/adapters/`:**
- Purpose: Local-file adapters for external kiln datasets.
- Contains: Abstract adapter base, one implemented APAD CSV converter, reference/stub adapters for datasets requiring local layout/license confirmation.
- Key files: `kilnwatch/datasets/adapters/apad_pakistan_igp.py`, `kilnwatch/datasets/adapters/sentinelkilndb.py`, `kilnwatch/datasets/adapters/kdd24_reference.py`, `kilnwatch/datasets/adapters/sustainbench_geobench.py`.

**`satellite_edge_node/`:**
- Purpose: Satellite-side simulation package.
- Contains: Orbital pass CLI, detector routing, baseline detector, YOLO integration, payload and telemetry construction.
- Key files: `satellite_edge_node/orbital_pass.py`, `satellite_edge_node/detectors.py`, `satellite_edge_node/baseline_detector.py`, `satellite_edge_node/yolo_detector.py`, `satellite_edge_node/payloads.py`.

**`ground_station_ui/`:**
- Purpose: Alternate/simple ground-station dashboard.
- Contains: Streamlit app and queue reader utilities.
- Key files: `ground_station_ui/app.py`, `ground_station_ui/queue_reader.py`.

**`scripts/`:**
- Purpose: User-facing operational commands that wrap package functions.
- Contains: Model readiness check, detector evaluation, demo tile fetch, manifest validation, SimSat smoke fetch.
- Key files: `scripts/check_model_ready.py`, `scripts/evaluate_detector.py`, `scripts/fetch_demo_tiles.py`, `scripts/validate_manifest.py`, `scripts/smoke_fetch_panipat.py`.

**`tests/`:**
- Purpose: Regression tests for architecture boundaries, payload byte accounting, detector behavior, data ingestion, manifest schema, metadata helpers, and triage.
- Contains: `unittest`/pytest-compatible test files named `test_*.py`.
- Key files: `tests/test_ground_station_boundary.py`, `tests/test_satellite_edge_bandwidth.py`, `tests/test_yolo_detector.py`, `tests/test_manifest_schema.py`.

**`docs/`:**
- Purpose: Human-readable architecture, model training, demo, honesty, resources, and submission documentation.
- Contains: Markdown docs and sample evaluation baseline JSON.
- Key files: `docs/architecture.md`, `docs/model_training.md`, `docs/technical_honesty.md`, `docs/demo_data_pipeline.md`, `docs/sample_evaluation_baseline.json`.

**`data/`:**
- Purpose: Local runtime/demo data root for raw tiles, manual tiles, fetched raw SimSat artifacts, metadata, and smoke reports.
- Contains: Placeholder `.gitkeep` files, demo raw tile placeholders, sidecar metadata, smoke reports.
- Key files: `data/raw_tiles/*.tile`, `data/raw_tiles/*.tile.meta.json`, `data/smoke/*.json`.

**`datasets/kilnwatch/`:**
- Purpose: Versioned KilnWatch dataset materials.
- Contains: README, dataset schema docs, labeling guidelines, coordinate CSVs, image assets, labels, manifests, dataset validation script.
- Key files: `datasets/kilnwatch/README.md`, `datasets/kilnwatch/docs/dataset_schema.md`, `datasets/kilnwatch/manifests/sample_demo_manifest.jsonl`, `datasets/kilnwatch/labels/dev.jsonl`.

**`models/`:**
- Purpose: Local model artifact location.
- Contains: Expected user-provided YOLO weights.
- Key files: `models/brick_kiln_yolo.pt` is the expected path; the file is not part of the inspected source listing.

**`transmission_queue/`:**
- Purpose: File-backed downlink queue generated by orbital passes and consumed by ground-station UIs.
- Contains: Per-tile JSON payloads and `telemetry.jsonl`; may contain `crops/` when image crops are generated.
- Key files: `transmission_queue/telemetry.jsonl`, `transmission_queue/*.json`.

**`telemetry_logs/`:**
- Purpose: Optional sample or external telemetry source for ground-station display.
- Contains: JSON/JSONL telemetry logs if present.
- Key files: Not detected in the current file listing.

**`config/regions/`:**
- Purpose: Region configuration surface.
- Contains: Region config files if present.
- Key files: Not detected in the inspected listing.

**`.planning/codebase/`:**
- Purpose: Generated GSD codebase mapping documents.
- Contains: `ARCHITECTURE.md`, `STRUCTURE.md`, and documents written by other mapper agents.
- Key files: `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STRUCTURE.md`.

**`.codex/`:**
- Purpose: Project-local Codex/GSD/OMX workflow assets.
- Contains: Skills, hooks, agents, workflow templates, references.
- Key files: `.codex/skills/gsd-map-codebase/SKILL.md`.

## Key File Locations

**Entry Points:**
- `app.py`: Primary Streamlit ground-station UI.
- `ground_station_ui/app.py`: Simple queue-reader Streamlit UI.
- `satellite_edge_node/orbital_pass.py`: Orbital pass module and CLI.
- `kilnwatch/ingestion/cli.py`: SimSat fetch CLI.
- `scripts/validate_manifest.py`: Manifest validator CLI.
- `scripts/fetch_demo_tiles.py`: Coordinate-to-demo-tile generation CLI.
- `scripts/check_model_ready.py`: Strict YOLO readiness CLI.
- `scripts/evaluate_detector.py`: Telemetry-vs-manifest evaluation CLI.
- `scripts/smoke_fetch_panipat.py`: Thin wrapper around ingestion CLI.

**Configuration:**
- `pyproject.toml`: Build backend, package metadata, console scripts, pytest test path.
- `requirements.txt`: Streamlit, pandas, Pillow demo/runtime dependencies.
- `docs/architecture.md`: Human-maintained architecture notes and boundary statement.
- `README.md`: Demo commands, detector mode contract, and model status guidance.

**Core Logic:**
- `satellite_edge_node/orbital_pass.py`: End-to-end satellite processing loop.
- `satellite_edge_node/detectors.py`: Detector selection and fallback policy.
- `satellite_edge_node/baseline_detector.py`: Simulated detection schema and metadata/filename detection.
- `satellite_edge_node/yolo_detector.py`: Local real-detector integration.
- `satellite_edge_node/payloads.py`: Payload construction, crop generation, and telemetry byte accounting.
- `kilnwatch/ground_station.py`: Ground-station metrics and payload shaping.
- `kilnwatch/triage.py`: Standalone triage decision model.
- `kilnwatch/ingestion/simsat_client.py`: Local SimSat HTTP integration.
- `kilnwatch/ingestion/dataset.py`: Fetched tile and metadata writers.
- `kilnwatch/datasets/manifest.py`: Manifest schema validator.

**Testing:**
- `tests/test_ground_station_boundary.py`: Enforces ground station does not import satellite raw tile modules.
- `tests/test_satellite_edge_bandwidth.py`: Tests byte accounting, telemetry records, orbital pass output, crop behavior.
- `tests/test_ground_station.py`: Tests ground-station metrics, sample precedence, alert rows, detector modes.
- `tests/test_yolo_detector.py`: Tests YOLO normalization, strict missing-model errors, and explicit fallback metadata.
- `tests/test_fetch_demo_tiles.py`: Tests CSV conversion, tile writing, local import, image validation.
- `tests/test_manifest_schema.py`: Tests manifest schema and image validation rules.
- `tests/test_model_readiness_eval.py`: Tests model readiness and detector evaluation honesty status.
- `tests/test_triage.py`: Tests triage decisions.
- `tests/test_metadata.py`: Tests metadata helper formatting.

**Data and Artifacts:**
- `data/raw_tiles/`: Demo raw tile inputs and sidecar metadata for orbital pass runs.
- `data/raw/`: Ingestion output for fetched raw SimSat files.
- `data/metadata/`: Ingestion output for fetched metadata JSON.
- `data/smoke/`: SimSat-unavailable smoke reports.
- `datasets/kilnwatch/manifests/`: Dataset manifest JSONL files.
- `datasets/kilnwatch/labels/`: Label JSON/JSONL files.
- `datasets/kilnwatch/images/`: Demo image assets.
- `transmission_queue/`: Downlinked payload queue and telemetry output.

## Naming Conventions

**Files:**
- Python modules use lowercase snake_case: `satellite_edge_node/orbital_pass.py`, `kilnwatch/ground_station.py`, `scripts/check_model_ready.py`.
- Test files use `test_*.py`: `tests/test_satellite_edge_bandwidth.py`, `tests/test_ground_station_boundary.py`.
- Dataset manifests and labels use JSONL for row-oriented records: `datasets/kilnwatch/manifests/sample_demo_manifest.jsonl`, `datasets/kilnwatch/labels/dev.jsonl`.
- Tile metadata sidecars append `.meta.json` to the tile filename: `data/raw_tiles/kiln_high_demo_001.tile.meta.json`.
- Demo tile placeholders use `.tile`; real image validation expects `.png`, `.jpg`, `.jpeg`, `.tif`, or `.tiff`.
- Docs use lowercase descriptive markdown names under `docs/`: `docs/model_training.md`, `docs/technical_honesty.md`.

**Directories:**
- Python packages use lowercase snake_case or descriptive package names: `satellite_edge_node/`, `ground_station_ui/`, `kilnwatch/`.
- Dataset subtree groups by purpose: `datasets/kilnwatch/manifests/`, `datasets/kilnwatch/labels/`, `datasets/kilnwatch/coordinates/`, `datasets/kilnwatch/images/`, `datasets/kilnwatch/docs/`.
- Runtime/demo data subtree groups by lifecycle: `data/raw_tiles/`, `data/raw/`, `data/metadata/`, `data/smoke/`.
- Generated downlink artifacts go in `transmission_queue/`; do not place raw source imagery there except explicit downlinked crop/full-review artifacts.

## Where to Add New Code

**New Satellite Detector:**
- Primary code: Add a detector implementation in `satellite_edge_node/`, then register selection in `satellite_edge_node/detectors.py`.
- Shared output schema: Return `satellite_edge_node.baseline_detector.DetectionResult` or update all payload/tests if the schema changes.
- Tests: Add focused tests in `tests/test_yolo_detector.py` or a new `tests/test_<detector>_detector.py`; add orbital pass coverage in `tests/test_satellite_edge_bandwidth.py` if byte output changes.

**New Payload or Telemetry Field:**
- Primary code: Add payload fields in `satellite_edge_node/payloads.py` and ensure `satellite_edge_node/orbital_pass.py` passes required inputs.
- Ground station consumption: Add parsing or display shaping in `kilnwatch/ground_station.py`, then render in `app.py`.
- Tests: Update `tests/test_satellite_edge_bandwidth.py` and `tests/test_ground_station.py`.

**New Ground Station Metric or View:**
- Business logic: Put calculations in `kilnwatch/ground_station.py`.
- UI: Render using `app.py`; use `ground_station_ui/app.py` only for the simple queue-reader UI.
- Tests: Add metric and row-shaping tests in `tests/test_ground_station.py`.

**New Ingestion Source or Region:**
- HTTP/client behavior: Add client code in `kilnwatch/ingestion/`.
- Region constants: Add regions in `kilnwatch/ingestion/regions.py` or config-backed loading if region files become active.
- Artifact writing: Reuse `kilnwatch/ingestion/dataset.py`.
- Tests: Add coverage in `tests/test_fetch_demo_tiles.py` or a new ingestion-specific test.

**New Dataset Adapter:**
- Implementation: Add `kilnwatch/datasets/adapters/<source_name>.py` implementing `DatasetAdapter`.
- Adapter registration: Export from `kilnwatch/datasets/adapters/__init__.py` if callers need package-level discovery.
- Output contract: Write KilnWatch manifest JSONL compatible with `kilnwatch/datasets/manifest.py`.
- Tests: Add adapter conversion tests and validate the generated manifest with `validate_manifest_file()`.

**New Manifest Rule:**
- Primary code: `kilnwatch/datasets/manifest.py`.
- CLI behavior: `scripts/validate_manifest.py` already reports `ManifestIssue` values.
- Tests: Add cases in `tests/test_manifest_schema.py`.

**New Operational Script:**
- Implementation: Prefer reusable logic in `kilnwatch/` or `satellite_edge_node/`.
- Script wrapper: Add a thin CLI in `scripts/`.
- Package command: Add console script in `pyproject.toml` only when the command should be installed.
- Tests: Import the package function or script function from `tests/` without shelling out unless CLI parsing is the behavior under test.

**New Documentation:**
- Architecture or boundaries: `docs/architecture.md`.
- Model training/evaluation: `docs/model_training.md`.
- Demo flow: `docs/demo_script.md` or `docs/demo_data_pipeline.md`.
- Technical limitations and honesty language: `docs/technical_honesty.md`.

**Utilities:**
- Shared satellite helpers: `satellite_edge_node/`.
- Shared ground-station helpers: `kilnwatch/ground_station.py`.
- Shared dataset helpers: `kilnwatch/datasets/`.
- Shared ingestion helpers: `kilnwatch/ingestion/`.
- Avoid placing reusable logic only in `scripts/` or Streamlit render functions.

## Special Directories

**`transmission_queue/`:**
- Purpose: Downlink queue and telemetry output consumed by the ground station.
- Generated: Yes, by `satellite_edge_node/orbital_pass.py`.
- Committed: Sample/demo files are present; runtime runs may append or overwrite artifacts.

**`transmission_queue/crops/`:**
- Purpose: Optional crop artifacts generated for alert-worthy detections with readable image tiles and bboxes.
- Generated: Yes.
- Committed: Not required; generated only when crop conditions are met.

**`data/raw_tiles/`:**
- Purpose: Demo/raw tile inputs for local orbital pass simulation.
- Generated: Partly; demo files are present, new files can be written by scripts or manually added.
- Committed: Demo placeholder and sidecar files are present.

**`data/raw/`:**
- Purpose: Raw fetched SimSat artifacts from ingestion.
- Generated: Yes, by `kilnwatch/ingestion/dataset.py`.
- Committed: Contains `.gitkeep`; fetched runtime artifacts are data outputs.

**`data/metadata/`:**
- Purpose: Metadata JSON for fetched SimSat artifacts.
- Generated: Yes, by `kilnwatch/ingestion/dataset.py`.
- Committed: Contains `.gitkeep`; fetched runtime artifacts are data outputs.

**`data/smoke/`:**
- Purpose: Smoke reports when local SimSat is unreachable or lacks matching image endpoints.
- Generated: Yes, by `kilnwatch/ingestion/cli.py`.
- Committed: At least one smoke report is present.

**`datasets/kilnwatch/`:**
- Purpose: Dataset-facing source materials and schemas.
- Generated: Mixed; docs/templates are hand-maintained, some manifests/images can be generated.
- Committed: Yes for templates, docs, demo manifests, labels, and demo images.

**`models/`:**
- Purpose: Local model weight drop location.
- Generated: No, user supplies trained weights.
- Committed: Model weights should not be assumed present; `scripts/check_model_ready.py` checks `models/brick_kiln_yolo.pt`.

**`telemetry_logs/`:**
- Purpose: Optional external/sample telemetry logs used by the root dashboard.
- Generated: Mixed.
- Committed: Directory exists; no key telemetry files were detected in the inspected listing.

**`.planning/codebase/`:**
- Purpose: Generated GSD mapping docs consumed by future planning/execution workflows.
- Generated: Yes.
- Committed: Managed by GSD workflows.

**`.codex/`:**
- Purpose: Project-local workflow, skill, hook, and prompt assets.
- Generated: Yes, by OMX/GSD setup.
- Committed: Project tooling surface; do not edit for application features unless updating workflow tooling.

---

*Structure analysis: 2026-05-06*

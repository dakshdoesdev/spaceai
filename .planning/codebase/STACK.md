# Technology Stack

**Analysis Date:** 2026-05-06

## Languages

**Primary:**
- Python >=3.11 - Required by `pyproject.toml`; used across `app.py`, `satellite_edge_node/`, `kilnwatch/`, `ground_station_ui/`, `scripts/`, and `tests/`.

**Secondary:**
- Markdown - Project documentation in `README.md`, `docs/architecture.md`, `docs/model_training.md`, `docs/demo_data_pipeline.md`, and dataset documentation under `datasets/kilnwatch/docs/`.
- JSON / JSONL - Local telemetry, manifests, labels, sidecars, and config in `transmission_queue/telemetry.jsonl`, `datasets/kilnwatch/manifests/*.jsonl`, `datasets/kilnwatch/labels/*.jsonl`, `data/raw_tiles/*.meta.json`, and `config/regions/panipat_haryana.json`.
- CSV - Coordinate templates and demo inputs in `datasets/kilnwatch/coordinates/*.csv`.

## Runtime

**Environment:**
- CPython >=3.11.
- Local CLI execution for ingestion, orbital-pass simulation, validation, model readiness checks, and evaluation.
- Streamlit local web runtime for ground-station dashboards.

**Package Manager:**
- pip / virtualenv - Installation flow documented in `README.md`.
- Lockfile: missing. No `requirements.lock`, `uv.lock`, `Pipfile.lock`, or package-manager lockfile is present.
- Editable/package metadata: `pyproject.toml` uses `setuptools>=68` as the build backend.

## Frameworks

**Core:**
- Streamlit >=1.35 - Ground-station dashboard UI in `app.py` and legacy/simple dashboard in `ground_station_ui/app.py`.
- Pandas >=2.2 - DataFrame/chart support for dashboard tables and cumulative telemetry visualization in `app.py`.
- Pillow >=10 - Image readability checks and crop generation in `kilnwatch/datasets/image_validation.py`, `satellite_edge_node/payloads.py`, and tests that create image fixtures.
- Python standard library HTTP client - SimSat ingestion uses `urllib.request`, `urllib.parse`, and `urllib.error` in `kilnwatch/ingestion/simsat_client.py`.

**Testing:**
- unittest - Primary checked-in test style under `tests/`.
- pytest - Supported by `pyproject.toml` test discovery and documented in `README.md`; not pinned in `requirements.txt`.

**Build/Dev:**
- setuptools >=68 - Build backend in `pyproject.toml`.
- argparse CLIs - Used by `satellite_edge_node/orbital_pass.py`, `kilnwatch/ingestion/cli.py`, `scripts/fetch_demo_tiles.py`, `scripts/validate_manifest.py`, `scripts/check_model_ready.py`, and `scripts/evaluate_detector.py`.
- No lint/format tool configuration detected. No Ruff, Black, mypy, ESLint, Prettier, or Makefile config is present.

## Key Dependencies

**Critical:**
- `streamlit>=1.35` - Required to run the ground-station dashboards from `app.py` and `ground_station_ui/app.py`.
- `pandas>=2.2` - Required by `app.py` for alert tables and cumulative downlink chart data.
- `Pillow>=10` - Required for real image validation in `kilnwatch/datasets/image_validation.py` and crop extraction in `satellite_edge_node/payloads.py`.

**Infrastructure:**
- `ultralytics` - Optional local YOLO inference package. It is intentionally not pinned in `requirements.txt`; strict YOLO mode in `satellite_edge_node/yolo_detector.py` fails loudly unless the package and `models/brick_kiln_yolo.pt` exist.
- Local model weights at `models/brick_kiln_yolo.pt` - Expected real detector artifact, documented in `README.md`, `docs/model_training.md`, and checked by `scripts/check_model_ready.py`.
- Local filesystem queues and logs - Runtime output uses `transmission_queue/*.json`, `transmission_queue/telemetry.jsonl`, and `telemetry_logs/*.jsonl`.

## Configuration

**Environment:**
- No `.env` file detected in the repo root or first three directory levels during this scan.
- No environment variables are required by the checked-in code.
- SimSat connection is configured by CLI arguments, not env vars:
  - `kilnwatch/ingestion/cli.py` uses `--base-url`, defaulting to `http://localhost:9005`.
  - `scripts/fetch_demo_tiles.py` uses `--simsat-base-url`, defaulting to `http://localhost:9005`.
- Ground-station input is configured by local paths:
  - `app.py` reads the default `transmission_queue/`, `telemetry_logs/`, and fallback `telemetry/` paths via `kilnwatch/ground_station.py`.
  - `ground_station_ui/app.py` exposes a Streamlit sidebar text input for the transmission queue path, defaulting to `transmission_queue`.
- YOLO model path is configurable with `--model-path`; the default is `models/brick_kiln_yolo.pt` in `satellite_edge_node/yolo_detector.py`, `satellite_edge_node/orbital_pass.py`, and `scripts/check_model_ready.py`.

**Build:**
- `pyproject.toml` defines package metadata, Python version, build backend, scripts, and pytest testpaths.
- `requirements.txt` defines local runtime dashboard/image dependencies.
- `.gitignore` excludes `.venv/`, Python caches, pytest/mypy/ruff caches, `.omx/`, and generated data under `data/raw/**`, `data/metadata/**`, and `data/smoke/**` while keeping `.gitkeep` placeholders.

## Platform Requirements

**Development:**
- Python 3.11 or newer.
- Create a local virtual environment and install `requirements.txt` before running dashboards.
- Install `ultralytics` separately only when running strict YOLO inference.
- Provide local model weights at `models/brick_kiln_yolo.pt` before claiming real detector availability.
- Run SimSat locally at `http://localhost:9005` only for `--mode simsat` ingestion; placeholder and local-import modes do not need the service.
- Use local, license-compatible imagery for real demo/evaluation data. `docs/external_resources.md` and `docs/demo_data_pipeline.md` explicitly avoid paid API dependencies.

**Production:**
- Not detected. No Dockerfile, deployment config, CI pipeline, cloud target, hosted database, or production service manifest is present.
- Current deployment shape is local execution: `streamlit run app.py`, `python -m satellite_edge_node.orbital_pass`, and Python scripts under `scripts/`.

---

*Stack analysis: 2026-05-06*

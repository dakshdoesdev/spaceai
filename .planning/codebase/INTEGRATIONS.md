# External Integrations

**Analysis Date:** 2026-05-06

## APIs & External Services

**Local SimSat / Sentinel-2 tile service:**
- SimSat - Local HTTP service used to fetch current satellite position and Sentinel-style tile bytes for demo ingestion.
  - SDK/Client: Standard library `urllib.request` client implemented in `kilnwatch/ingestion/simsat_client.py`.
  - Auth: None detected.
  - Default base URL: `http://localhost:9005`.
  - Position endpoints tried by default: `/current_position`, `/satellite/current_position`, `/api/current_position`, and `/position`.
  - Sentinel image endpoints tried by default: `/sentinel-2/image`, `/sentinel2/image`, `/api/sentinel-2/image`, `/api/sentinel2/image`, and `/image/sentinel-2`.
  - Call sites: `kilnwatch/ingestion/cli.py` and `scripts/fetch_demo_tiles.py`.
  - Failure behavior: `kilnwatch/ingestion/cli.py` writes a smoke report under `data/smoke/`; `scripts/fetch_demo_tiles.py` exits with an error unless rerun in placeholder mode.

**Optional local YOLO inference:**
- Ultralytics YOLO - Optional local object-detector runtime for real brick-kiln inference.
  - SDK/Client: `ultralytics.YOLO` imported lazily inside `satellite_edge_node/yolo_detector.py`.
  - Auth: None detected.
  - Required local artifact: `models/brick_kiln_yolo.pt`.
  - Readiness check: `scripts/check_model_ready.py`.
  - Evaluation path: `scripts/evaluate_detector.py`.
  - Fallback policy: strict YOLO mode fails if dependencies or weights are unavailable; baseline fallback only occurs when `--allow-baseline-fallback` is explicitly passed to `satellite_edge_node/orbital_pass.py`.

**Reference-only external datasets and papers:**
- SentinelKilnDB - Documented as the best-fit future dataset source in `docs/external_resources.md`.
  - SDK/Client: None in runtime code.
  - Auth: Not detected.
  - Adapter: `kilnwatch/datasets/adapters/sentinelkilndb.py` is a stub/reference adapter, not a downloader.
- APAD Pakistan IGP / Zenodo - Documented as coordinate-grounded future source in `docs/external_resources.md`.
  - SDK/Client: Local CSV adapter in `kilnwatch/datasets/adapters/apad_pakistan_igp.py`.
  - Auth: None detected.
  - Runtime stance: use manually prepared local CSV exports; do not wire Google Static Maps or Earth Engine notebooks into this MVP.
- KDD24 brick-kiln resources, GEO-Bench, SustainBench, Space to Policy, and Eye in the Sky - Listed in `docs/external_resources.md` for reference and future manual integration.
  - SDK/Client: None in runtime code.
  - Auth: None detected.
  - Runtime stance: no paid API dependency and no upstream code/data copy unless license terms are clear.

**Explicitly avoided external APIs:**
- Mapbox, Google Maps Static API, Sentinel Hub, OpenAI, Anthropic, Gemini, and paid API keys are explicitly excluded by `docs/external_resources.md` and `docs/demo_data_pipeline.md`.
- Google Earth Engine is documented as out of scope for the MVP in `docs/external_resources.md` and `docs/demo_data_pipeline.md`.

## Data Storage

**Databases:**
- Not detected.
  - Connection: Not applicable.
  - Client: Not applicable.

**File Storage:**
- Local filesystem only.
  - Raw/demo tile inputs: `data/raw_tiles/`, `data/manual_tiles/`.
  - Generated sidecars: `data/raw_tiles/*.meta.json`.
  - Downlinked payload queue: `transmission_queue/*.json`.
  - Telemetry: `transmission_queue/telemetry.jsonl` and `telemetry_logs/*.jsonl`.
  - Dataset manifests: `datasets/kilnwatch/manifests/*.jsonl`.
  - Dataset labels: `datasets/kilnwatch/labels/*.jsonl` and `datasets/kilnwatch/labels/*.json`.
  - Region config: `config/regions/panipat_haryana.json`.
  - Optional model weights: `models/brick_kiln_yolo.pt`.

**Caching:**
- None as an application service.
- Python/test/tool caches are ignored by `.gitignore`: `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, and `.ruff_cache/`.

## Authentication & Identity

**Auth Provider:**
- None detected.
  - Implementation: No login/session/auth middleware exists in `app.py`, `ground_station_ui/app.py`, `kilnwatch/`, `satellite_edge_node/`, or `scripts/`.
  - SimSat calls in `kilnwatch/ingestion/simsat_client.py` send only a `User-Agent` header and no credentials.

## Monitoring & Observability

**Error Tracking:**
- None detected.

**Logs:**
- Local JSONL telemetry is the primary observability mechanism.
  - `satellite_edge_node/orbital_pass.py` appends telemetry records to `transmission_queue/telemetry.jsonl`.
  - `satellite_edge_node/payloads.py` records detector mode, fallback metadata, latency, payload byte counts, crop status, action, confidence, risk, and output paths.
  - `kilnwatch/ground_station.py` loads `transmission_queue/telemetry.jsonl`, `telemetry_logs/*.jsonl`, and fallback `telemetry/*.jsonl` for dashboard metrics.
  - `data/smoke/` stores SimSat reachability smoke reports created by `kilnwatch/ingestion/cli.py`.
- Console output is used by CLI commands in `satellite_edge_node/orbital_pass.py`, `kilnwatch/ingestion/cli.py`, `scripts/check_model_ready.py`, `scripts/evaluate_detector.py`, and `scripts/fetch_demo_tiles.py`.

## CI/CD & Deployment

**Hosting:**
- Not detected.
- Local dashboard command is `streamlit run app.py` as documented in `README.md` and `docs/demo_script.md`.

**CI Pipeline:**
- None detected. No GitHub Actions, Dockerfile, Makefile, tox, or dedicated CI config appears in the scanned repo files.

## Environment Configuration

**Required env vars:**
- None detected.

**Runtime config values:**
- SimSat base URL:
  - `--base-url` in `kilnwatch/ingestion/cli.py`, default `http://localhost:9005`.
  - `--simsat-base-url` in `scripts/fetch_demo_tiles.py`, default `http://localhost:9005`.
- Dataset and queue paths:
  - `--dataset-root` in `kilnwatch/ingestion/cli.py`, default `data`.
  - `--coordinates-csv`, `--tile-dir`, and `--manifest` in `scripts/fetch_demo_tiles.py`.
  - `--raw-tiles` and `--transmission-queue` in `satellite_edge_node/orbital_pass.py`.
- Detector config:
  - `--detector baseline|yolo`, `--model-path`, `--confidence-threshold`, and `--allow-baseline-fallback` in `satellite_edge_node/orbital_pass.py`.
  - `--model-path` and `--json` in `scripts/check_model_ready.py`.

**Secrets location:**
- Not applicable. No secret files or env-var based credentials were detected, and the code does not require API keys.

## Webhooks & Callbacks

**Incoming:**
- None detected.
- The Streamlit apps in `app.py` and `ground_station_ui/app.py` are local dashboards, not webhook receivers.
- SimSat endpoints are consumed by this repo; they are not implemented by this repo.

**Outgoing:**
- SimSat HTTP GET requests from `kilnwatch/ingestion/simsat_client.py` to local endpoints under `http://localhost:9005`.
- No outbound webhook callbacks, cloud uploads, model API calls, email/SMS notifications, or third-party API writes were detected.

---

*Integration audit: 2026-05-06*

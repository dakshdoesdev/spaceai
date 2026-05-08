# External Integrations

**Analysis Date:** 2026-05-09

## Pipeline at a Glance

KilnWatch is the satellite-edge AI submission for the Liquid AI × DPhi Space *AI in Space* hackathon (2026-04-13 → 2026-05-08). Its end-to-end pipeline is:

```
raw tile  →  YOLO (strict, ultralytics)  →  Liquid LFM2.5-VL-450M (optional, transformers)
          →  4-tier triage label (kilnwatch.triage.compute_triage)
          →  JSON payload + PNG crop  →  transmission_queue/  (filesystem boundary)
          →  Streamlit dashboard (app.py)  reads the queue ONLY
```

Every external integration below is either (a) a local lazy import behind an explicit CLI flag, (b) a model artifact pulled from Hugging Face Hub on first use, (c) a local image fixture, or (d) the future-only DPhi SimSat HTTP endpoint stub. **No paid API is used.** No outbound calls leave localhost in default operation.

## Model Artifacts

**Custom YOLOv8n brick-kiln detector:**
- Path: `models/brick_kiln_yolo.pt`.
- Format: Ultralytics PyTorch checkpoint (`.pt`).
- Source: produced locally by `scripts/train_real_model.py`, which fine-tunes `yolov8n.pt` on the Roboflow `Brick Kiln Detection.v1-dataset_aug.yolov8/` dataset for 5 epochs at `imgsz=512`, then copies `runs/brick_kiln_custom/weights/best.pt` to `models/brick_kiln_yolo.pt`.
- Loaded by: `satellite_edge_node/yolo_detector.py::YoloDetector.__init__` via `from ultralytics import YOLO; YOLO(str(model_path))`.
- Class-name validation: `satellite_edge_node/yolo_detector.py::has_kiln_class` requires the model to expose at least one of `{brick kiln, brick-kiln, brick_kiln, brickkiln, kiln}`.
- Readiness probe: `scripts/check_model_ready.py` reports `weights_exist`, `ultralytics_available`, `model_loads`, `model_sha256`, `class_names`, `kiln_class_available`, and a single `ready_for_strict_yolo` boolean.
- Failure mode: `YoloModelUnavailable` is loud. Fallback to baseline only happens with explicit `--allow-baseline-fallback` on `satellite_edge_node/orbital_pass.py`.
- Git: excluded by `.gitignore` (`*.pt`); the file is local-only, never committed.

**Stock YOLOv8n smoke-test weights:**
- Path: `yolov8n.pt` (repo root) and `models/yolov8n_stock_smoke.pt`.
- Source: downloaded by `scripts/provision_model.py` via `ultralytics.YOLO("yolov8n.pt")` from the Ultralytics asset CDN on first use. The script explicitly prints "This does not create models/brick_kiln_yolo.pt and must not be claimed as a kiln detector."
- Use: smoke-test only. Not wired into the orbital-pass detector.

**Liquid LFM2.5-VL-450M (vision-language reasoner):**
- Hub identifier: `LiquidAI/LFM2.5-VL-450M` (constant `MODEL_NAME` in `satellite_edge_node/liquid_vlm_reasoner.py`).
- Format: Hugging Face Hub repo, loaded with `transformers.AutoProcessor.from_pretrained` and `transformers.AutoModelForImageTextToText.from_pretrained`, both with `trust_remote_code=True`.
- Loaded by: `satellite_edge_node/liquid_vlm_reasoner.py::LiquidLocalReasoner.__init__`.
- Inference: `LiquidLocalReasoner.reason()` opens the crop with PIL (`Image.open(...).convert("RGB")`), builds a system+user `apply_chat_template` conversation aligned with the official Liquid cookbook satellite-VLM pattern (system prompt enumerates kiln visual features; user prompt requires a single JSON object with keys `credible_kiln`, `compliance_risk`, `human_review_needed`, `visual_summary`, `risk_reasoning`, `confidence_note`), and generates with `do_sample=False, max_new_tokens=256` for deterministic JSON.
- Output normalisation: `satellite_edge_node/liquid_vlm_reasoner.py::_parse_local_response` extracts the JSON, clamps `compliance_risk` to `{low, medium, high}`, coerces booleans, and packs the result into a frozen `VlmReasoning` dataclass with `reasoner_is_real=True`.
- Failure mode: `LiquidReasonerUnavailable` (missing `transformers`) and `LiquidReasonerError` (load or inference failure) are both loud. The CLI catches them in `satellite_edge_node/orbital_pass.py::main` and prints the suggested fallback (`--reasoner disabled` or `--reasoner liquid-mock`).

**Liquid LFM2.5-VL-450M GGUF artifacts (DORMANT — no code references them):**
- Files present: `models/liquid/LFM2.5-VL-450M-Q4_0.gguf`, `models/liquid/mmproj-LFM2.5-VL-450m-F16.gguf`, `models/liquid/Modelfile` (`FROM ./LFM2.5-VL-450M-Q4_0.gguf` / `ADAPTER ./mmproj-LFM2.5-VL-450m-F16.gguf`).
- Status: **inert**. The `LiquidOllamaReasoner` class and `--reasoner liquid-ollama` CLI choice were removed from `satellite_edge_node/liquid_vlm_reasoner.py` and `satellite_edge_node/orbital_pass.py` because Ollama 0.17.5 cannot load this architecture (`missing tensor 'output_norm'`, verified on both Q4_0 and Q8_0 official `LiquidAI/LFM2.5-VL-450M-GGUF` files). No Python module imports `requests` or `ollama` in `satellite_edge_node/`, `kilnwatch/`, `scripts/`, or `app.py` anymore.
- Action: leave on disk for future llama.cpp / vllm experimentation, but do not reference them from runtime code or documentation as a working backend.

**Mock Liquid reasoner:**
- `satellite_edge_node/liquid_vlm_reasoner.py::LiquidMockReasoner` returns a deterministic `VlmReasoning` with `reasoner_is_real=False` and `model_name="LiquidAI/LFM2.5-VL-450M (mock)"`. No external dependency at all. Used for end-to-end demo flow when the real model is unavailable.

## Hugging Face Hub

- **Inbound:** `transformers.AutoProcessor.from_pretrained("LiquidAI/LFM2.5-VL-450M", trust_remote_code=True)` and `transformers.AutoModelForImageTextToText.from_pretrained(...)` in `satellite_edge_node/liquid_vlm_reasoner.py`. First call downloads the model and tokenizer/processor files into the local Hugging Face cache (`~/.cache/huggingface/`). Subsequent calls are offline.
- **Auth:** none. The model is publicly accessible.
- **Failure modes wrapped:** any exception from `from_pretrained` is converted to `LiquidReasonerUnavailable(f"Liquid local model could not be loaded from {model_name}: {exc}")`.
- **No `huggingface_hub` package is imported directly** — the dependency comes in transitively with `transformers`.

## DPhi SimSat (intended future input)

- **Status:** *intended* future input source. Current ground-truth input is local image fixtures (Roboflow optical tiles under `Brick Kiln Detection.v1-dataset_aug.yolov8/`) and the YOLO model is trained on that. The dashboard's "Imagery provenance" section in `app.py::_render_imagery_provenance` makes this explicit to the judge.
- **Production path documented:** swap the tile source for the DPhi SimSat `/data/image/sentinel` endpoint; fine-tune YOLO + Liquid LFM2-VL on Sentinel-domain kiln labels. Triage, queue, and ground-station accounting are unchanged.
- **Existing client implementation:** `kilnwatch/ingestion/simsat_client.py` (`SimSatClient`, `SimSatResponse`, `SimSatUnavailable`, `SimSatError`).
  - Transport: stdlib `urllib.request.Request` + `urlopen`. No `requests` or `httpx`.
  - Auth: none — only a `User-Agent` header is sent.
  - Default base URL: `http://localhost:9005` (a locally-hosted SimSat mock).
  - Position endpoints attempted: `/current_position`, `/satellite/current_position`, `/api/current_position`, `/position`.
  - Sentinel image endpoints attempted: `/sentinel-2/image`, `/sentinel2/image`, `/api/sentinel-2/image`, `/api/sentinel2/image`, `/image/sentinel-2`.
  - Call sites: `kilnwatch/ingestion/cli.py` (the `kilnwatch-fetch-haryana` entry point) and `scripts/fetch_demo_tiles.py` (only when `--mode simsat`).
  - Region defaults: `kilnwatch/ingestion/regions.py::HARYANA_INDIA` (`lat=29.3909, lon=76.9635`).
  - Failure handling: `SimSatUnavailable` falls through to `kilnwatch/ingestion/dataset.py::write_smoke_report`, which writes a JSON smoke report under `data/smoke/`.

## Image Datasets (reference + training inputs)

**Roboflow brick-kiln dataset (training input):**
- Folder: `Brick Kiln Detection.v1-dataset_aug.yolov8/` and the matching `.zip` at the repo root. Both are `.gitignore`d.
- Layout: standard YOLOv8 export with `train/images`, `valid/images`, `test/images`, and `data.yaml`.
- Used by: `scripts/train_real_model.py` (rewrites `data.yaml` paths to absolute, then trains `yolov8n.pt` for 5 epochs).
- Provenance disclosure: `app.py::_render_imagery_provenance` declares "Open-source brick-kiln imagery (Roboflow optical tiles, Indo-Gangetic Plain morphology). These are real overhead images of brick kilns used to wire and prove the satellite-edge pipeline end-to-end. Not Sentinel-2 or DPhi SimSat live imagery."

**Reference-only datasets (documented in `docs/external_resources.md`, optional adapters in `kilnwatch/datasets/adapters/`):**
- SentinelKilnDB (NeurIPS 2025) - cloned under `datasets/SENTINELKILNDB_NeurIPS_2025/` (gitignored) for reference; adapter stub at `kilnwatch/datasets/adapters/sentinelkilndb.py`. The dataset's own `data_scripts/*.py` files import `requests` to download tiles, but those scripts are vendored upstream code, not part of the KilnWatch runtime.
- APAD Pakistan/India/Bangladesh IGP coordinate dataset (Zenodo) - adapter at `kilnwatch/datasets/adapters/apad_igp.py` reads local CSV exports (no network), processed by `scripts/process_apad.py`. Coordinate templates in `datasets/kilnwatch/coordinates/apad_coordinates_template.csv`.
- SustainBench / GEO-Bench - adapter at `kilnwatch/datasets/adapters/sustainbench_geobench.py` reads local CSVs.
- KDD24 brick-kiln resources - reference docs only, adapter at `kilnwatch/datasets/adapters/kdd24_reference.py`.
- Eye in the Sky, Space to Policy - listed in `docs/external_resources.md` for context only; no code path.

**Local image fixtures (runtime input):**
- `data/raw_tiles/`, `data/manual_tiles/`, `data/final_demo_tiles/` (paths referenced in `app.py` empty-state and `satellite_edge_node/orbital_pass.py` defaults).
- Sidecar metadata: `<tile>.meta.json` next to each tile, parsed by `satellite_edge_node/baseline_detector.py::_read_sidecar` for the placeholder mode.

**Explicitly avoided external services:**
- Mapbox, Google Maps Static API, Sentinel Hub, OpenAI, Anthropic, Gemini, paid API keys - explicitly excluded by `docs/external_resources.md` and `docs/demo_data_pipeline.md`.
- Google Earth Engine - documented as out of scope for the MVP.

## Streamlit (ground-station UI)

- Process: `streamlit run app.py`. Streamlit (>=1.35) is the only web runtime; there is no Flask/FastAPI server, no static-site build, no separate frontend bundle.
- Page config: `st.set_page_config(page_title="KilnWatch — Satellite-Edge Triage", layout="wide", initial_sidebar_state="collapsed")`.
- Styling: dark-mode design system injected as a single `<style>` block in `app.py::_inject_css`. No external CSS, no static assets folder. Streamlit's default toolbar/header are hidden via CSS.
- Inputs: only the local filesystem queue. `kilnwatch/ground_station.py::load_ground_station_records` reads `transmission_queue/*.json`, `transmission_queue/telemetry.jsonl`, and falls back to `telemetry_logs/*.jsonl` then `telemetry/*.jsonl`. Crop image bytes are read with `Path.read_bytes()` and base64-embedded inline by `app.py::_crop_img_html`.
- Crop sandboxing: `kilnwatch/ground_station.py::_safe_crop_path` resolves any `crop_ref`/`crop_path`/`payload_uri` against the queue root and refuses paths that escape it or contain `data/raw_tiles`, `data/final_demo_tiles`, or `datasets/roboflow` fragments. Enforcement is covered by `tests/test_ground_station_boundary.py`.
- No Streamlit auth, no session state beyond the implicit per-render cache, no external integration.

## Ultralytics YOLO (real detector)

- Package: `ultralytics` (lazy-imported, not pinned).
- Entry points:
  - Inference: `satellite_edge_node/yolo_detector.py::YoloDetector` (`predict(..., conf=self.confidence_threshold, verbose=False)`).
  - Readiness: `scripts/check_model_ready.py` (uses `importlib.util.find_spec("ultralytics")` to avoid importing on absence).
  - Training: `scripts/train_real_model.py` (Ultralytics CLI-style API: `model.train(data=..., epochs=5, imgsz=512, batch=16, project="runs", name="brick_kiln_custom")`).
  - Provisioning: `scripts/provision_model.py` (downloads stock `yolov8n.pt` via `ultralytics`).
  - Evaluation: `scripts/evaluate_detector.py`.
- Result normalisation: `satellite_edge_node/yolo_detector.py::normalize_yolo_results` filters detections by confidence threshold AND class-name allowlist, then collapses to the highest-confidence box. Risk band is derived from confidence: `confidence >= 0.85 → high`, otherwise `medium`. Tensor extraction (`_to_python_list`) handles `.detach().cpu().numpy().tolist()` chains so the rest of the codebase never imports torch.

## Filesystem Boundary (the central "integration")

The repo treats the local filesystem as a hard boundary between "satellite onboard" and "ground station". This is enforced in code, not just docs.

- **Onboard side writes:**
  - `transmission_queue/<tile_id>.json` - alert payload (`satellite_edge_node/payloads.py::build_transmission_payload`).
  - `transmission_queue/crops/<tile_id>_crop.png` - PNG crop (`satellite_edge_node/payloads.py::generate_crop_file` via Pillow).
  - `transmission_queue/telemetry.jsonl` - one JSON line per processed tile, written by `satellite_edge_node/orbital_pass.py::simulate_orbital_pass`.
- **Ground-station side reads (only):** the three artifacts above, plus optional `telemetry_logs/*.jsonl` and `telemetry/*.jsonl` aggregates. Reads are gated by `kilnwatch/ground_station.py::load_ground_station_records`. Crop path resolution is sandboxed by `_safe_crop_path`.
- **Triage labels travel through the boundary:** every payload and telemetry row carries `triage_decision` (one of `IGNORE`, `JSON_ALERT_ONLY`, `CROP_OR_REVIEW`, `FULL_DOWNLINK` — the `kilnwatch/triage.py::TriageDecision` StrEnum) and a nested `triage` block (`decision`, `reason`, `risk_band_used`, `risk_score_used`, `driven_by`). The transmit/drop decision itself is still binary (`should_transmit_alert`), but the 4-tier label tells the dashboard what an integrated Liquid+YOLO system would have chosen. `triage_min_confidence` is plumbed from `--confidence-threshold` so the IGNORE band matches the YOLO floor (default `0.45` for standalone callers of `compute_triage`, `0.25` when called from the orbital pass).
- **Boundary tests:** `tests/test_ground_station_boundary.py`, `tests/test_satellite_edge_bandwidth.py`, and the new payload tests `test_telemetry_record_includes_triage_decision_label`, `test_telemetry_record_low_confidence_below_detector_floor_is_ignored`, `test_alert_rows_use_orbital_pass_triage_label` (66 passing total).

## Authentication & Identity

- None. No login, no session, no auth middleware in `app.py`, `kilnwatch/`, `satellite_edge_node/`, or `scripts/`.
- SimSat HTTP requests in `kilnwatch/ingestion/simsat_client.py` send only a `User-Agent` header.
- Hugging Face Hub access for `LiquidAI/LFM2.5-VL-450M` is anonymous (the model is public).

## Monitoring & Observability

- **Local JSONL telemetry is the sole observability channel.**
  - `transmission_queue/telemetry.jsonl` - one row per processed tile, fields include `detector_mode`, `detector_is_real`, `simulated`, `fallback_used`, `inference_latency_ms`, `original_payload_bytes`, `json_payload_bytes`, `crop_payload_bytes`, `transmitted_payload_bytes`, `bandwidth_saved_bytes`, `compression_ratio`, `action`, `triage_decision`, `triage`, `kiln_detected`, `confidence`, `compliance_risk`, full `detection` dump, optional `vlm_reasoning`, plus `requested_detector_mode` and `requested_reasoner_mode` from the orbital-pass driver.
  - `data/smoke/*.json` - SimSat reachability smoke reports (`kilnwatch/ingestion/dataset.py::write_smoke_report`).
- **No external monitoring service.** No Sentry, no Datadog, no OpenTelemetry, no Prometheus exporter.
- **Console output** is the secondary channel: every CLI in `scripts/` and `satellite_edge_node/orbital_pass.py::main` prints a human-readable summary (tile count, byte totals, compression ratio, fallback reason if any).

## CI/CD & Deployment

- **CI:** none. No `.github/workflows/`, no GitLab CI, no CircleCI, no Travis, no Makefile, no tox.
- **Deployment:** none. No Dockerfile, no docker-compose, no Kubernetes manifest, no serverless config.
- **Operational shape:** local-only invocation:
  - `streamlit run app.py` — judge dashboard.
  - `python -m satellite_edge_node.orbital_pass --raw-tiles data/final_demo_tiles --detector yolo --reasoner liquid-local --require-crops --reset-queue` — full real-stack pass.
  - `python -m kilnwatch.ingestion.cli` (or `kilnwatch-fetch-haryana`) — SimSat smoke fetch.
  - `python scripts/check_model_ready.py --json` — strict-YOLO readiness probe.

## Environment Configuration

**Required env vars:** none. All config is via CLI flags or default constants.

**Runtime config knobs:**
- SimSat: `--base-url` / `--simsat-base-url` (default `http://localhost:9005`).
- Dataset paths: `--dataset-root` (default `data`), `--coordinates-csv`, `--tile-dir`, `--manifest`, `--local-image-dir`.
- Pipeline paths: `--raw-tiles` (default `data/raw_tiles`), `--transmission-queue` (default `transmission_queue`).
- Detector: `--detector {baseline,yolo}`, `--model-path`, `--confidence-threshold`, `--allow-baseline-fallback`.
- Reasoner: `--reasoner {disabled,liquid-mock,liquid-local}`. The historical `liquid-ollama` choice has been removed from `argparse choices`.
- Queue lifecycle: `--reset-queue`, `--require-crops`, `--write-drop-payloads`.

**Secrets location:** not applicable. No `.env`, no `.env.*`, no credential file, no secret store. The runtime does not need API keys.

## Webhooks & Callbacks

**Incoming:** none. The Streamlit dashboard is a local UI, not a webhook receiver. The SimSat HTTP endpoints are *consumed* by this repo, not implemented by it.

**Outgoing:**
- SimSat HTTP GETs to `http://localhost:9005` (only when `--mode simsat`).
- Hugging Face Hub model download (only on first `--reasoner liquid-local` run; uses the standard `transformers` cache).
- Ultralytics asset download for stock `yolov8n.pt` (only when `scripts/provision_model.py` is run).
- No outbound webhooks, no email/SMS, no cloud uploads, no third-party API writes.

---

*Integration audit: 2026-05-09*

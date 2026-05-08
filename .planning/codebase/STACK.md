# Technology Stack

**Analysis Date:** 2026-05-09

## Languages

**Primary:**
- Python >=3.11 - Pinned by `pyproject.toml`. Used across `app.py`, `satellite_edge_node/`, `kilnwatch/`, `scripts/`, and `tests/`. Modern syntax in active use: `from __future__ import annotations`, `dataclass(frozen=True)`, `enum.StrEnum` (`kilnwatch/triage.py`), PEP 604 union types (`X | None`), and `typing.Protocol` (`satellite_edge_node/detectors.py`, `satellite_edge_node/liquid_vlm_reasoner.py`).

**Secondary:**
- Markdown - Project narrative and demo evidence in `README.md`, `docs/architecture.md`, `docs/demo_script.md`, `docs/technical_honesty.md`, `docs/external_resources.md`, `docs/model_training.md`, and `docs/final_demo_evidence.md`.
- JSON / JSONL - Runtime payload format (`transmission_queue/*.json`), telemetry stream (`transmission_queue/telemetry.jsonl`), dataset manifests (`datasets/kilnwatch/manifests/*.jsonl`), and tile sidecars (`data/raw_tiles/*.meta.json`).
- CSV - Coordinate inputs to `scripts/fetch_demo_tiles.py`, e.g. `datasets/kilnwatch/coordinates/haryana_demo_coordinates.csv` and `apad_coordinates_template.csv`.
- HTML+CSS (inline) - The Streamlit dashboard `app.py` injects a custom dark-mode design system via `st.markdown(..., unsafe_allow_html=True)`; there is no separate stylesheet file.

## Runtime

**Environment:**
- CPython >=3.11.
- Local CLI execution for ingestion, orbital-pass simulation, model readiness checks, manifest validation, and detector evaluation.
- Local Streamlit web runtime for the ground-station dashboard.
- All runtime is local — no container, no cloud target, no managed service is wired in.

**Package Manager:**
- pip / virtualenv. Setup is documented in `README.md` ("Quickstart" section).
- Lockfile: missing. There is no `requirements.lock`, `uv.lock`, `Pipfile.lock`, or `poetry.lock`.
- Build backend: `setuptools>=68` (declared in `pyproject.toml`).

## Frameworks

**Core (declared, always-on):**
- Streamlit >=1.35 - Single-page mission dashboard in `app.py`. Pinned in `requirements.txt`.
- Pandas >=2.2 - Pinned in `requirements.txt` (used historically for cumulative-downlink chart data; current `app.py` builds the chart from raw lists, so pandas remains a transitive dashboard dependency).
- Pillow >=10 - Real image validation (`kilnwatch/datasets/image_validation.py`), crop generation in `satellite_edge_node/payloads.py::generate_crop_file`, crop-image opening for the Liquid local reasoner (`satellite_edge_node/liquid_vlm_reasoner.py`), and PNG/JPEG/TIFF rendering for test fixtures.
- Python standard library HTTP client - SimSat ingestion uses `urllib.request`, `urllib.parse`, and `urllib.error` in `kilnwatch/ingestion/simsat_client.py`. No `requests`, no `httpx` in runtime code.

**Optional ML stack (lazy-imported, not in `requirements.txt`):**
- Ultralytics YOLO - Imported lazily inside `satellite_edge_node/yolo_detector.py::YoloDetector.__init__` and `scripts/check_model_ready.py`. Required only for `--detector yolo` strict mode and for `scripts/train_real_model.py` / `scripts/provision_model.py`. Missing package raises a loud `YoloModelUnavailable`.
- Hugging Face Transformers (with `AutoModelForImageTextToText` support) - Imported lazily inside `satellite_edge_node/liquid_vlm_reasoner.py::LiquidLocalReasoner.__init__`. Required only for `--reasoner liquid-local`. Loads `LiquidAI/LFM2.5-VL-450M` from the Hugging Face Hub via `from_pretrained(..., trust_remote_code=True)`. Implies torch + safetensors transitively.

**Removed / dormant:**
- Ollama HTTP client (previously `LiquidOllamaReasoner` + `--reasoner liquid-ollama`) - Removed because Ollama 0.17.5 cannot load the LFM2 GGUF architecture (`missing tensor 'output_norm'` on official `LiquidAI/LFM2.5-VL-450M-GGUF` Q4_0 and Q8_0). The `requests` dependency is no longer imported anywhere in `satellite_edge_node/`, `kilnwatch/`, `scripts/`, or `app.py`. Local GGUF + Modelfile artifacts under `models/liquid/` are inert — see INTEGRATIONS.md.

**Testing:**
- unittest (stdlib) - Test style used by every file under `tests/`.
- pytest - Test discovery is configured by `pyproject.toml` (`[tool.pytest.ini_options] testpaths = ["tests"]`) and is the documented runner in `README.md`. Not pinned in `requirements.txt`; assumed present in the developer venv. Current count: 66 passing tests across 10 files.

**Build/Dev:**
- setuptools >=68 - Build backend in `pyproject.toml`.
- argparse CLIs - All entry points use `argparse`: `satellite_edge_node/orbital_pass.py`, `kilnwatch/ingestion/cli.py`, `scripts/fetch_demo_tiles.py`, `scripts/check_model_ready.py`, `scripts/evaluate_detector.py`, `scripts/validate_manifest.py`, `scripts/process_apad.py`.
- No lint/format tool config detected. No Ruff, Black, isort, mypy, pre-commit, Makefile, tox, or nox file is present in the repo root.

## Key Dependencies

**Critical (declared in `requirements.txt`):**
- `streamlit>=1.35` - Required to run `streamlit run app.py`. The dashboard is the judge-facing surface.
- `pandas>=2.2` - Declared dashboard dependency; current `app.py` does not import it directly but the package remains pinned for chart/table compatibility and historical use.
- `Pillow>=10` - Required for real image validation, crop generation, and Liquid local reasoner image input. Without Pillow, the orbital pass still runs but `generate_crop_file` returns a `CropArtifact` with `error="Pillow is not installed; cannot generate crop"`, and `--reasoner liquid-local` raises `LiquidReasonerUnavailable`.

**Optional ML (must be installed manually for "real" modes):**
- `ultralytics` - Strict YOLO inference. Required by `--detector yolo` (default `--confidence-threshold 0.25`). Loaded from `models/brick_kiln_yolo.pt`.
- `transformers` (a build that exposes `AutoModelForImageTextToText`) - Liquid LFM2.5-VL-450M reasoner. Required by `--reasoner liquid-local`.
- `torch` - Pulled in transitively by both `ultralytics` and `transformers`. Not directly imported by repo code; tensor handling is delegated to ultralytics/transformers.
- `safetensors` / `tokenizers` - Implicit transitive deps of the Liquid load path.

**Local runtime artifacts (filesystem, not pip):**
- `models/brick_kiln_yolo.pt` - Custom YOLOv8n brick-kiln weights produced by `scripts/train_real_model.py`. Detection of presence and class-name validation lives in `satellite_edge_node/yolo_detector.py` and `scripts/check_model_ready.py`. Excluded from git by `.gitignore` (`*.pt`).
- `models/liquid/LFM2.5-VL-450M-Q4_0.gguf`, `models/liquid/mmproj-LFM2.5-VL-450m-F16.gguf`, `models/liquid/Modelfile` - Dormant local GGUF artifacts left over from the removed Ollama path. **No code references them.** Document them as inert; `--reasoner liquid-local` always pulls from Hugging Face Hub instead.
- `transmission_queue/*.json`, `transmission_queue/telemetry.jsonl`, `transmission_queue/crops/*.png` - Generated runtime queue and crop evidence; the only files the dashboard is allowed to read.

## Configuration

**Environment:**
- No `.env`, `.env.*`, or environment-variable-based secret file is present in the repo.
- No environment variables are required by the runtime code. SimSat URL, model paths, queue paths, detector mode, reasoner mode, and confidence threshold are all CLI flags.
- SimSat connection (only consumed by `--mode simsat`):
  - `kilnwatch/ingestion/cli.py` uses `--base-url`, default `http://localhost:9005`.
  - `scripts/fetch_demo_tiles.py` uses `--simsat-base-url`, default `http://localhost:9005`.
  - Default position endpoints tried: `/current_position`, `/satellite/current_position`, `/api/current_position`, `/position`.
  - Default Sentinel image endpoints tried: `/sentinel-2/image`, `/sentinel2/image`, `/api/sentinel-2/image`, `/api/sentinel2/image`, `/image/sentinel-2`.
- Ground-station input is local-only:
  - `app.py` reads `transmission_queue/`, `telemetry_logs/`, and falls back to `telemetry/` via `kilnwatch/ground_station.py::load_ground_station_records`.
  - Crop paths are sandboxed by `kilnwatch/ground_station.py::_safe_crop_path` to live strictly inside `transmission_queue/`; `data/raw_tiles`, `data/final_demo_tiles`, and `datasets/roboflow` are forbidden source fragments.

**Detector + reasoner config (CLI flags on `python -m satellite_edge_node.orbital_pass`):**
- `--detector {baseline,yolo}` (default `baseline`).
- `--reasoner {disabled,liquid-mock,liquid-local}` (default `disabled`). The historical `liquid-ollama` choice has been removed.
- `--model-path` (default `models/brick_kiln_yolo.pt`).
- `--confidence-threshold` (default `0.25`). Same value is propagated as `triage_min_confidence` to `satellite_edge_node/payloads.py::triage_label` and `satellite_edge_node/payloads.py::telemetry_record`, which forward it to `kilnwatch/triage.py::compute_triage(min_confidence=...)`. The triage function's own default is `0.45` for standalone callers.
- `--reset-queue`, `--require-crops`, `--write-drop-payloads`, `--allow-baseline-fallback` flags control queue lifecycle and strictness.

**Build:**
- `pyproject.toml` declares package metadata, Python version, `setuptools>=68` build backend, the two console scripts (`kilnwatch-fetch-haryana`, `kilnwatch-orbital-pass`), and pytest discovery.
- `requirements.txt` declares the always-on dashboard runtime (`streamlit>=1.35`, `pandas>=2.2`, `Pillow>=10`).
- `.gitignore` excludes `.venv/`, Python caches (`__pycache__/`, `*.py[cod]`), tooling caches (`.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.omx/`), generated data folders (`data/raw/**`, `data/metadata/**`, `data/smoke/**` while keeping their `.gitkeep` placeholders), all `*.pt` weight files, `runs/`, and the large dataset clones (`datasets/roboflow/`, `datasets/SentinelKilnDB/`, `datasets/SENTINELKILNDB_NeurIPS_2025/`, `Brick Kiln Detection.v1-dataset_aug.yolov8/` and its `.zip`).

## Platform Requirements

**Development:**
- Python 3.11 or newer with a local virtual environment.
- `pip install -r requirements.txt` for the always-on dashboard runtime.
- `pip install ultralytics` only when `--detector yolo` is desired; provide weights at `models/brick_kiln_yolo.pt`. Use `python scripts/check_model_ready.py` to verify weights load and that the model exposes a brick-kiln class name (`brick kiln`, `brick-kiln`, `brick_kiln`, `brickkiln`, or `kiln`).
- `pip install transformers torch` only when `--reasoner liquid-local` is desired. The reasoner pulls `LiquidAI/LFM2.5-VL-450M` from the Hugging Face Hub on first use; deterministic generation (`do_sample=False`, `max_new_tokens=256`) is enforced for JSON reliability.
- SimSat is only required for `--mode simsat` ingestion in `scripts/fetch_demo_tiles.py` and for `kilnwatch-fetch-haryana`. `--mode placeholder` and `--mode local-import` work with no service.
- No paid API keys are needed. OpenAI, Anthropic, Gemini, Sentinel Hub, Mapbox, Google Static Maps, and Google Earth Engine are explicitly out of scope (see `docs/external_resources.md`).
- Hardware target is a developer laptop. The Liquid LFM2.5-VL-450M reasoner is small (~450M params) and runs on CPU, but GPU is faster; model load happens once per `LiquidLocalReasoner` instance. A 4 GB GPU is sufficient for inference; YOLO training in `scripts/train_real_model.py` defaults to `epochs=5, imgsz=512, batch=16` and is also feasible on consumer hardware.

**Production:**
- Not detected. No Dockerfile, no docker-compose, no Kubernetes manifest, no GitHub Actions workflow, no CI config of any kind.
- Operational shape is local invocation: `streamlit run app.py`, `python -m satellite_edge_node.orbital_pass ...`, and the scripts under `scripts/`.
- Future production path documented in `app.py::_render_imagery_provenance` and `README.md`: replace the local tile source with the DPhi SimSat `/data/image/sentinel` endpoint and fine-tune YOLO + Liquid LFM2.5-VL on Sentinel-domain kiln labels. Triage architecture, queue boundary, and ground-station accounting are unchanged by that swap.

---

*Stack analysis: 2026-05-09*

# Codebase Concerns

**Analysis Date:** 2026-05-06

## Tech Debt

**Baseline detector is the default production path:**
- Issue: The default orbital pass uses the explicit placeholder detector, and the baseline detector derives detections from sidecar metadata or filename tokens rather than imagery.
- Files: `satellite_edge_node/orbital_pass.py`, `satellite_edge_node/baseline_detector.py`, `README.md`, `docs/technical_honesty.md`, `docs/model_training.md`
- Impact: A normal `python -m satellite_edge_node.orbital_pass` run produces plausible queue artifacts without real model inference. The repo labels this honestly, but any future feature that consumes queue output must treat `detector_is_real=false`, `simulated=true`, and `detector_mode=baseline` as non-production data.
- Fix approach: Make real detector readiness the release gate for non-demo flows. Keep `--detector baseline` for demos, but add a separate `--demo` or `--simulation` path and require strict YOLO metadata for any evaluation or submission artifact that claims detector performance.

**Multiple ground-station readers implement overlapping schemas:**
- Issue: `app.py` uses `kilnwatch.ground_station`, while `ground_station_ui/app.py` uses `ground_station_ui.queue_reader`. Both parse queue/telemetry data and calculate bandwidth summaries with different abstractions.
- Files: `app.py`, `kilnwatch/ground_station.py`, `ground_station_ui/app.py`, `ground_station_ui/queue_reader.py`, `tests/test_ground_station.py`, `tests/test_satellite_edge_bandwidth.py`
- Impact: Schema changes must be patched in more than one place. `kilnwatch.ground_station.calculate_metrics` supports mission-style and orbital-pass-style records, while `ground_station_ui.queue_reader.summarize_telemetry` only summarizes the orbital-pass telemetry fields.
- Fix approach: Treat `kilnwatch.ground_station` as the canonical reader and migrate `ground_station_ui/app.py` or remove it if the root Streamlit app is the supported dashboard.

**Telemetry append mode accumulates stale runs:**
- Issue: `simulate_orbital_pass` opens `transmission_queue/telemetry.jsonl` in append mode and overwrites per-tile payload JSON files.
- Files: `satellite_edge_node/orbital_pass.py`, `transmission_queue/telemetry.jsonl`, `tests/test_satellite_edge_bandwidth.py`
- Impact: Repeated local runs can mix telemetry from old and new detector modes while payload files only reflect the latest tile IDs. Evaluation can report results against stale telemetry rows when `tile_id` values repeat.
- Fix approach: Add explicit run IDs and timestamps to telemetry records, write each run under `transmission_queue/runs/<run_id>/`, or add a documented `--reset-queue` option that deletes only queue artifacts before a run.

**Demo data is committed as operational-looking state:**
- Issue: `data/raw_tiles/`, `datasets/kilnwatch/manifests/`, `telemetry_logs/`, and `transmission_queue/` contain placeholder tiles, sample manifests, sample telemetry, and queue payloads that look like a completed mission run.
- Files: `data/raw_tiles/*`, `datasets/kilnwatch/manifests/baseline_sample_eval_manifest.jsonl`, `datasets/kilnwatch/manifests/panipat_demo_manifest.jsonl`, `telemetry_logs/sample_mission.jsonl`, `transmission_queue/telemetry.jsonl`, `.gitignore`
- Impact: Demo artifacts are useful for judging, but future contributors can accidentally treat them as real labels, real satellite imagery, or current run outputs. Several files are also owned by `root`, which can block normal user edits or cleanup.
- Fix approach: Keep committed demo fixtures under `data/demo/` or `fixtures/`, add a clear generated-output directory for queue runs, and normalize file ownership before future edits. Add `.gitignore` rules for new generated queue/crop outputs while keeping small fixture files intentional.

**Dataset adapters are placeholders by design:**
- Issue: External dataset adapters raise `AdapterNotImplementedError` instead of fetching or normalizing rows.
- Files: `kilnwatch/datasets/adapters/base.py`, `kilnwatch/datasets/adapters/sentinelkilndb.py`, `kilnwatch/datasets/adapters/kdd24_reference.py`, `kilnwatch/datasets/adapters/sustainbench_geobench.py`
- Impact: The repo documents plausible dataset sources, but the ingestion surface is not ready for automated dataset preparation or reproducible training.
- Fix approach: Implement one adapter at a time behind explicit license checks. Each adapter should write manifest rows through `kilnwatch.datasets.manifest` and require image validation before marking `is_real_imagery=true`.

## Known Bugs

**Fallback smoke command exits successfully when SimSat is unavailable:**
- Symptoms: `kilnwatch.ingestion.cli.main` writes a fallback smoke report and returns `0` when the SimSat position endpoint or Sentinel image endpoint is unavailable.
- Files: `kilnwatch/ingestion/cli.py`, `kilnwatch/ingestion/simsat_client.py`, `data/smoke/simsat_unreachable_2026-05-05T17-13-39Z.json`
- Trigger: Run the Panipat smoke fetch without a local SimSat service at `http://localhost:9005`.
- Workaround: Treat the generated smoke report as diagnostics only. Use `scripts/fetch_demo_tiles.py --mode simsat` for real tile ingestion because it fails with exit code `2` when SimSat is unavailable or returns non-image bytes.

**High-risk filename tokens can mark non-kiln files as high risk internally:**
- Symptoms: `_from_filename` sets `compliance_risk="high"` for names containing tokens such as `settlement` or `active` even when `kiln_detected` is false.
- Files: `satellite_edge_node/baseline_detector.py`, `transmission_queue/telemetry.jsonl`, `data/raw_tiles/settlement_negative_demo_001.tile`
- Trigger: Run baseline detection on a filename such as `settlement_negative_demo_001.tile`; telemetry can contain `compliance_risk=high` with `kiln_detected=false` and action `DROP_RAW_TILE`.
- Workaround: Use sidecar metadata for demo rows and do not interpret baseline `compliance_risk` as an evaluated compliance score. Fix by computing high risk only after a positive kiln signal exists.

**Evaluator can report `real_yolo` from metadata-only test rows:**
- Symptoms: `evaluate_detector` classifies a result as `real_yolo` when telemetry mode/version says YOLO and manifest rows are not marked sample/placeholder.
- Files: `scripts/evaluate_detector.py`, `tests/test_model_readiness_eval.py`, `docs/model_training.md`
- Trigger: Provide synthetic telemetry with `detector_version="yolo_ultralytics:v0.1"` and non-sample manifest rows; no model file, image readability, or strict-run provenance is checked by the evaluator.
- Workaround: Run `scripts/check_model_ready.py`, strict `satellite_edge_node.orbital_pass --detector yolo` with no fallback, and image validation separately before trusting evaluation output.

## Security Considerations

**User-provided paths are written without sandboxing:**
- Risk: CLI arguments can write manifests, tiles, queue payloads, crop files, smoke reports, or evaluation JSON to arbitrary filesystem paths available to the process.
- Files: `scripts/fetch_demo_tiles.py`, `satellite_edge_node/orbital_pass.py`, `scripts/evaluate_detector.py`, `kilnwatch/ingestion/cli.py`
- Current mitigation: Commands are local developer tools and do not expose a network service. Tests use temporary directories for most write paths.
- Recommendations: For any hosted or shared execution path, restrict output paths to a configured workspace root, reject path traversal for generated `tile_id` and output filenames, and fail if target paths resolve outside the workspace.

**SimSat base URL accepts arbitrary URL input:**
- Risk: `SimSatClient` accepts a caller-provided `base_url` and then probes multiple endpoints with `urlopen`, which is acceptable for local CLI use but becomes SSRF-like if exposed through a UI or API.
- Files: `kilnwatch/ingestion/simsat_client.py`, `kilnwatch/ingestion/cli.py`, `scripts/fetch_demo_tiles.py`
- Current mitigation: The default URL is `http://localhost:9005`, and there is no server endpoint that accepts this value from remote users.
- Recommendations: Keep SimSat fetching as a local-only tool. If a future dashboard exposes ingestion, allowlist localhost or configured trusted hosts and block private-network hopping from untrusted input.

**Dashboard renders generated HTML with `unsafe_allow_html=True`:**
- Risk: `app.py` uses `st.markdown(..., unsafe_allow_html=True)` for status badges. Current badge labels and colors are generated internally, but future use of telemetry-derived strings in this HTML block would create an injection risk.
- Files: `app.py`
- Current mitigation: The current HTML uses fixed labels and fixed colors from internal detector-mode checks.
- Recommendations: Keep telemetry values out of unsafe HTML. Use native Streamlit components or escape any data-derived text before rendering with unsafe HTML.

**Telemetry exposes local file paths and coordinates:**
- Risk: Queue and telemetry records include `tile_file`, `output_path`, `crop_path`, `coordinates`, `lat`, and `lon`, which can reveal local directory layout and sensitive site coordinates.
- Files: `satellite_edge_node/payloads.py`, `transmission_queue/telemetry.jsonl`, `datasets/kilnwatch/manifests/*.jsonl`, `scripts/fetch_demo_tiles.py`
- Current mitigation: Current committed data is sample/demo data around the Panipat demo geography.
- Recommendations: Redact or relativize local paths in shareable telemetry. Add a public-export command that strips absolute paths, sensitive coordinates, and analyst notes before publishing artifacts.

## Performance Bottlenecks

**Orbital pass is single-threaded and loads one inference at a time:**
- Problem: `simulate_orbital_pass` discovers all tile files, then runs detection, crop generation, payload serialization, and telemetry writes sequentially.
- Files: `satellite_edge_node/orbital_pass.py`, `satellite_edge_node/yolo_detector.py`, `satellite_edge_node/payloads.py`
- Cause: The current implementation is optimized for a small local demo, not large tile batches or real edge latency targets.
- Improvement path: Add batch inference for YOLO, stream telemetry per tile with run IDs, and bound crop generation cost. Keep the sequential path for deterministic tests.

**Tile discovery recursively scans all raw tile descendants:**
- Problem: `discover_tiles` uses `raw_tiles_dir.rglob("*")` and accepts `.png`, `.jpg`, `.jpeg`, `.webp`, `.tif`, `.tiff`, `.bin`, `.tile`, and `.txt`.
- Files: `satellite_edge_node/orbital_pass.py`, `satellite_edge_node/baseline_detector.py`
- Cause: Demo convenience accepts many file extensions and has no maximum file count, maximum bytes, or depth control.
- Improvement path: Add a manifest-driven run mode for real datasets. For directory mode, add extension filtering by detector mode, max file count, and explicit skip rules for generated sidecars/crops.

**Ground station loads all telemetry into memory:**
- Problem: `_load_telemetry_events` and `read_telemetry` read every JSONL event into lists before rendering or summarizing.
- Files: `kilnwatch/ground_station.py`, `ground_station_ui/queue_reader.py`, `app.py`
- Cause: Streamlit dashboard is designed around small sample telemetry.
- Improvement path: For larger missions, summarize telemetry incrementally, page records in the UI, and keep recent event windows separate from aggregate metrics.

## Fragile Areas

**Technical-honesty boundary depends on metadata propagation:**
- Files: `satellite_edge_node/baseline_detector.py`, `satellite_edge_node/detectors.py`, `satellite_edge_node/yolo_detector.py`, `satellite_edge_node/payloads.py`, `app.py`, `scripts/evaluate_detector.py`
- Why fragile: The repo correctly labels baseline, fallback, simulated, and real YOLO records, but that correctness depends on every detector and payload path preserving the same fields.
- Safe modification: When adding a detector or Liquid/LFM stage, update `DetectionResult`, `_truth_metadata`, telemetry records, dashboard badges, and evaluator classification together.
- Test coverage: `tests/test_yolo_detector.py`, `tests/test_satellite_edge_bandwidth.py`, `tests/test_model_readiness_eval.py`, and `tests/test_ground_station.py` cover current metadata paths. Add tests before changing truth metadata names or detector mode semantics.

**Ground-station boundary tests are string-based:**
- Files: `tests/test_ground_station_boundary.py`, `ground_station_ui/app.py`, `ground_station_ui/queue_reader.py`, `app.py`, `kilnwatch/ground_station.py`
- Why fragile: The boundary test only scans files in `ground_station_ui/*.py` for forbidden strings. The primary root dashboard imports `kilnwatch.ground_station`, and future code can read raw tiles indirectly without matching those strings.
- Safe modification: Replace string scanning with behavior tests that construct raw-tile and queue directories, then assert the dashboard/reader only opens queue and telemetry files.
- Test coverage: Current tests enforce the narrow `ground_station_ui` import boundary, not the full root Streamlit app or file-open behavior.

**Evaluator assumes `tile_id` is the join key and silently drops duplicates:**
- Files: `scripts/evaluate_detector.py`, `datasets/kilnwatch/manifests/*.jsonl`, `transmission_queue/telemetry.jsonl`
- Why fragile: `telemetry_by_tile = {tile_id: row}` keeps only the last telemetry row per tile ID. Appended multi-run telemetry can override earlier predictions without run-level selection.
- Safe modification: Add `run_id`, `timestamp_utc`, and detector mode filters to evaluation. Reject duplicate `tile_id` rows unless a run ID is specified.
- Test coverage: Tests cover missing predictions and simulated-vs-real classification, but not duplicate telemetry rows or mixed-run evaluation.

**Crop generation only supports 4-point and 8-point boxes despite validator allowing 5-point boxes:**
- Files: `kilnwatch/datasets/manifest.py`, `satellite_edge_node/payloads.py`, `tests/test_satellite_edge_bandwidth.py`
- Why fragile: Manifest validation allows bbox lengths of `4`, `5`, or `8`, but `_crop_box_from_bbox` returns `None` for length `5`.
- Safe modification: Decide what 5-value boxes mean, document it, and update both validator and crop conversion together.
- Test coverage: Crop tests cover 4-value bboxes and unreadable images; they do not cover 5-value bbox manifests.

**Root-owned generated artifacts can block normal local development:**
- Files: `data/raw_tiles/*`, `datasets/kilnwatch/coordinates/*.csv`, `datasets/kilnwatch/manifests/*.jsonl`, `telemetry_logs/sample_mission.jsonl`, `transmission_queue/*.json`, `transmission_queue/telemetry.jsonl`, `models/.gitkeep`
- Why fragile: Several generated/demo files are owned by `root` while source files are mostly owned by `dux`.
- Safe modification: Normalize ownership before running generators or editing fixtures. Avoid future use of privileged commands in the repo.
- Test coverage: No tests cover file ownership or permission failures.

## Scaling Limits

**Committed fixture scale is tiny:**
- Current capacity: The sample evaluation manifest contains 3 rows, and the Panipat demo manifest contains 5 placeholder rows.
- Limit: Detector metrics and bandwidth savings are not statistically meaningful at this scale.
- Scaling path: Build train/dev/test manifests under `datasets/kilnwatch/labels/` and `datasets/kilnwatch/manifests/` from license-checked real imagery, then run strict YOLO evaluation into `docs/latest_evaluation.json`.

**No hardware-aware edge profiling exists:**
- Current capacity: Telemetry records per-tile wall-clock inference latency in milliseconds.
- Limit: There is no memory, CPU/GPU, power, thermal, or batch-throughput profiling for satellite-edge constraints.
- Scaling path: Add profiling fields to `satellite_edge_node/payloads.py`, capture model/device metadata in `satellite_edge_node/yolo_detector.py`, and add a profiling script under `scripts/`.

## Dependencies at Risk

**Ultralytics is optional and unpinned:**
- Risk: Real detection depends on `ultralytics`, but `requirements.txt` only includes Streamlit, pandas, and Pillow. The docs instruct manual `pip install ultralytics`.
- Impact: Strict YOLO mode fails on clean installs even when the rest of the app works. Version drift can change result object shapes used by `_extract_detections`.
- Migration plan: Add an optional requirements file such as `requirements-yolo.txt` with tested versions, or document a lockfile/constraints file for real detector runs.

**Pillow is required for crop generation and image validation:**
- Risk: `generate_crop_file` silently emits a crop error when Pillow is unavailable, while image validation raises an error.
- Impact: A minimal install without Pillow cannot produce crop artifacts, and telemetry may still show alerts with `crop_ref=null`.
- Migration plan: Keep Pillow in `requirements.txt`, add readiness checks for crop support, and surface crop-generation failures prominently in the dashboard.

**Streamlit API compatibility is assumed:**
- Risk: `app.py` uses Streamlit parameters such as `width="stretch"` in buttons/dataframes.
- Impact: Older Streamlit versions may break the dashboard even if tests pass, because tests do not launch Streamlit.
- Migration plan: Pin a tested Streamlit range and add a smoke test that imports the app or runs `streamlit run app.py --server.headless true` in CI.

## Missing Critical Features

**No trained brick-kiln model artifact or verified model card:**
- Problem: `models/brick_kiln_yolo.pt` is absent, and `scripts/check_model_ready.py` reports real detector unavailable until weights and `ultralytics` are present.
- Blocks: Real detector claims, accuracy reporting, strict YOLO demo, and production-like end-to-end validation.

**No real labeled image dataset is present:**
- Problem: Current Panipat manifests are placeholder or sample rows marked not ground truth.
- Blocks: Training, validation metrics, threshold calibration, false-positive analysis, and compliance-risk claims.

**Liquid/LFM integration is documented but not implemented:**
- Problem: README and technical-honesty docs list Liquid/LFM reasoning as future work.
- Blocks: Any claim that the project uses Liquid models for risk summarization, multimodal review, or onboard reasoning.

**No CI workflow is detected:**
- Problem: No GitHub Actions or equivalent CI configuration is present in the scanned tree.
- Blocks: Automatic enforcement of tests, manifest validation, model-readiness checks, and dashboard smoke checks on changes.

## Test Coverage Gaps

**No real YOLO inference test:**
- What's not tested: Loading `models/brick_kiln_yolo.pt`, running Ultralytics inference on a real image, producing bboxes, and generating crop payloads from YOLO output.
- Files: `satellite_edge_node/yolo_detector.py`, `satellite_edge_node/orbital_pass.py`, `tests/test_yolo_detector.py`
- Risk: Real detector integration can break while unit tests still pass with mocked/normalized result objects.
- Priority: High

**No mixed-run telemetry evaluation test:**
- What's not tested: Duplicate tile IDs across appended telemetry runs, mixed baseline/YOLO telemetry, and evaluation run selection.
- Files: `scripts/evaluate_detector.py`, `satellite_edge_node/orbital_pass.py`, `transmission_queue/telemetry.jsonl`
- Risk: Evaluation can silently use stale or wrong records.
- Priority: High

**No Streamlit runtime smoke test:**
- What's not tested: Launching `app.py`, rendering the dashboard, and verifying charts/tables with current Streamlit and pandas versions.
- Files: `app.py`, `kilnwatch/ground_station.py`, `requirements.txt`
- Risk: UI can break from dependency/API drift while unit tests pass.
- Priority: Medium

**No ingestion network integration test:**
- What's not tested: A local fake SimSat server returning position JSON and image bytes through the supported endpoint variants.
- Files: `kilnwatch/ingestion/simsat_client.py`, `scripts/fetch_demo_tiles.py`, `kilnwatch/ingestion/cli.py`
- Risk: Endpoint probing, content-type handling, and timeout behavior can regress unnoticed.
- Priority: Medium

**No path safety or permissions test:**
- What's not tested: Output path containment, malicious `tile_id` values in sidecars/manifests, unwritable queue directories, and root-owned fixture failures.
- Files: `scripts/fetch_demo_tiles.py`, `satellite_edge_node/orbital_pass.py`, `satellite_edge_node/payloads.py`
- Risk: Local tools fail unclearly or write outside intended areas when reused in shared automation.
- Priority: Medium

---

*Concerns audit: 2026-05-06*

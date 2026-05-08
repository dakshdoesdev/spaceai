# Coding Conventions

**Analysis Date:** 2026-05-09

## Naming Patterns

**Files:**
- Lowercase snake_case for Python modules: `kilnwatch/ground_station.py`, `kilnwatch/triage.py`, `satellite_edge_node/orbital_pass.py`, `satellite_edge_node/liquid_vlm_reasoner.py`, `scripts/fetch_demo_tiles.py`.
- Package `__init__.py` files are lightweight package markers, never export hubs: `kilnwatch/__init__.py`, `satellite_edge_node/__init__.py`, `ground_station_ui/__init__.py`.
- Test modules under `tests/` use `test_*.py`: `tests/test_ground_station.py`, `tests/test_yolo_detector.py`, `tests/test_satellite_edge_bandwidth.py`.
- Runnable scripts live in `scripts/`. Package CLIs are exposed through `[project.scripts]` in `pyproject.toml`: `kilnwatch-fetch-haryana = "kilnwatch.ingestion.cli:main"`, `kilnwatch-orbital-pass = "satellite_edge_node.orbital_pass:main"`.

**Functions:**
- snake_case verb phrases for public operations: `load_ground_station_records()` in `kilnwatch/ground_station.py`, `simulate_orbital_pass()` in `satellite_edge_node/orbital_pass.py`, `compute_triage()` in `kilnwatch/triage.py`, `evaluate_detector()` in `scripts/evaluate_detector.py`, `triage_label()` and `telemetry_record()` in `satellite_edge_node/payloads.py`.
- Leading underscore for module-private helpers: `_load_payloads()` in `kilnwatch/ground_station.py`, `_extract_detections()` in `satellite_edge_node/yolo_detector.py`, `_parse_local_response()` and `_extract_json_object()` in `satellite_edge_node/liquid_vlm_reasoner.py`, `_truth_positive()` in `scripts/evaluate_detector.py`.
- CLI modules use `def main() -> int:` and exit through `if __name__ == "__main__": raise SystemExit(main())`. Verified in `satellite_edge_node/orbital_pass.py:167,245`, `scripts/evaluate_detector.py:95,193`, `scripts/fetch_demo_tiles.py:295,322`, `scripts/check_model_ready.py:74,91`, `scripts/validate_manifest.py:13,32`, `kilnwatch/ingestion/cli.py:30,66`, `scripts/process_apad.py:12`.
- Streamlit entry points use `def main() -> None:` and call `main()` (no `SystemExit` wrap). Verified in `app.py:37` and `ground_station_ui/app.py:13`.

**Variables:**
- Descriptive snake_case domain names throughout the byte-accounting/telemetry pipeline: `original_payload_bytes`, `transmitted_payload_bytes`, `bandwidth_saved_bytes`, `crop_payload_bytes`, `inference_latency_ms`, `triage_decision`, `triage_min_confidence`, `requested_detector_mode`, `confidence_threshold` (see `satellite_edge_node/payloads.py`, `satellite_edge_node/orbital_pass.py`).
- Module-level constants are uppercase and group domain policy or default paths: `TRANSMISSION_QUEUE_DIR`, `TELEMETRY_LOG_DIR`, `REVIEW_DECISIONS`, `CROP_REFERENCE_FIELDS`, `NO_REAL_CROP_AVAILABLE`, `FORBIDDEN_CROP_SOURCE_FRAGMENTS` in `kilnwatch/ground_station.py`; `DEFAULT_MODEL_PATH`, `DETECTOR_VERSION`, `KILN_CLASS_NAMES` in `satellite_edge_node/yolo_detector.py`; `ALERT_RISKS`, `_RISK_BAND_TO_SCORE` in `satellite_edge_node/payloads.py`; `MODEL_NAME` in `satellite_edge_node/liquid_vlm_reasoner.py`; `IMAGE_EXTENSIONS`, `DETECTOR_VERSION` in `satellite_edge_node/baseline_detector.py`.
- Plural collection names: `payloads`, `events`, `records`, `detections`, `signals`, `telemetry_events`, `forbidden_paths`.

**Types:**
- PascalCase for dataclasses, protocols, enums, and exceptions.
- Frozen dataclasses for immutable domain records, all decorated `@dataclass(frozen=True)`:
  - `DetectionResult` in `satellite_edge_node/baseline_detector.py:21`
  - `BaselineDetector`, `FallbackBaselineDetector` in `satellite_edge_node/detectors.py:21,58`
  - `CropArtifact` in `satellite_edge_node/payloads.py:57`
  - `VlmReasoning`, `LiquidMockReasoner` in `satellite_edge_node/liquid_vlm_reasoner.py:24,52`
  - `MissionMetrics`, `ProofStatus`, `MissionProofCounts`, `CropEvidence` in `kilnwatch/ground_station.py:24,38,46,52`
  - `BandwidthEstimate`, `TriageResult` in `kilnwatch/triage.py:17,26`
  - `ManifestIssue` in `kilnwatch/datasets/manifest.py`
  - `SimSatResponse` in `kilnwatch/ingestion/simsat_client.py:35`
- `StrEnum` for value-bearing closed sets that need string-equality with payload data: `TriageDecision(StrEnum)` in `kilnwatch/triage.py:10`.
- `Protocol` for structural collaborator interfaces: `Detector` in `satellite_edge_node/detectors.py:14`, `Reasoner` in `satellite_edge_node/liquid_vlm_reasoner.py:39`.

**Exceptions:**
- Domain-specific names ending in `Error` for the base, `Unavailable` for the "external thing not present" subclass:
  - `YoloDetectorError` / `YoloModelUnavailable` in `satellite_edge_node/yolo_detector.py:22,26`
  - `LiquidReasonerError` / `LiquidReasonerUnavailable` in `satellite_edge_node/liquid_vlm_reasoner.py:16,20`
  - `SimSatError` / `SimSatUnavailable` in `kilnwatch/ingestion/simsat_client.py:27,31`
- Single-purpose runtime errors: `RequiredCropUnavailable(RuntimeError)` in `satellite_edge_node/orbital_pass.py:25`.
- Validation errors subclass `ValueError`: `ImageValidationError(ValueError)` in `kilnwatch/datasets/image_validation.py:10`.
- `AdapterNotImplementedError(NotImplementedError)` in `kilnwatch/datasets/adapters/base.py:21`.

## Code Style

**Formatting:**
- No formatter or linter is configured: `pyproject.toml` has no `[tool.black]`, `[tool.ruff]`, or `[tool.isort]` sections. The only `[tool.*]` block is `[tool.pytest.ini_options] testpaths = ["tests"]`.
- Match the existing Black-compatible shape: 4-space indentation, blank line between top-level definitions, trailing commas in multi-line literals/calls, ~88-char wrapping. See `satellite_edge_node/payloads.py`, `satellite_edge_node/orbital_pass.py`, `tests/test_satellite_edge_bandwidth.py`.
- `from __future__ import annotations` is the first import in every production module. Verified across `app.py`, `kilnwatch/ground_station.py`, `kilnwatch/triage.py`, `satellite_edge_node/orbital_pass.py`, `satellite_edge_node/payloads.py`, `satellite_edge_node/yolo_detector.py`, `satellite_edge_node/liquid_vlm_reasoner.py`, `satellite_edge_node/baseline_detector.py`, `satellite_edge_node/detectors.py`, `ground_station_ui/app.py`, `ground_station_ui/queue_reader.py`, and every script in `scripts/`.
- Tests do not use `from __future__ import annotations` — they keep concrete imports and `unittest.TestCase` inheritance only.
- `pathlib.Path` for all filesystem code, never raw strings: `kilnwatch/ground_station.py`, `satellite_edge_node/orbital_pass.py`, `scripts/fetch_demo_tiles.py`. Conversion to `str()` happens only at the API boundary (e.g., `YOLO(str(self.model_path))` in `satellite_edge_node/yolo_detector.py:46`).
- No emoji literals in production source code. CLI output and Streamlit captions use plain ASCII text.

**Linting:**
- No lint tool configured. Keep imports manually grouped; do not introduce ad-hoc autoformatter sections to `pyproject.toml` without raising it explicitly.
- Avoid broad heavyweight imports at module top in core packages. Optional deps are imported inside the function or class that needs them: `from PIL import Image` inside `generate_crop_file()` in `satellite_edge_node/payloads.py:68`; `from ultralytics import YOLO` inside `YoloDetector.__init__` in `satellite_edge_node/yolo_detector.py:39`; `from transformers import AutoModelForImageTextToText, AutoProcessor` inside `LiquidLocalReasoner.__init__` in `satellite_edge_node/liquid_vlm_reasoner.py:91`.

## Import Organization

**Order (apply in this exact order, blank line between groups):**
1. `from __future__ import annotations` (production modules only).
2. Standard library imports: `argparse`, `json`, `tempfile`, `unittest`, `dataclasses`, `pathlib`, `typing`, `enum`, `html`, `time`, `shutil`, `subprocess`, `sys`, `importlib.util`, `builtins`.
3. Third-party imports: `streamlit`, `pandas`, `PIL`, `ultralytics`, `transformers` (the last three are localized into functions, not module top).
4. Local package imports — relative inside the same package, absolute across packages.

**Path Aliases:**
- None configured. Import package modules by package name from the repo root: `from kilnwatch.ground_station import ...`, `from satellite_edge_node.payloads import ...`, `from ground_station_ui.queue_reader import ...`.
- Use relative imports inside a package for siblings: `from .baseline_detector import is_tile_file` and `from .detectors import Detector, build_detector_with_fallback` in `satellite_edge_node/orbital_pass.py:11-12`; `from .liquid_vlm_reasoner import LiquidReasonerError, Reasoner, build_reasoner` at line 13.
- Cross-package downward imports go through the package root, e.g. `from kilnwatch.triage import TriageDecision, compute_triage` inside `satellite_edge_node/payloads.py:13`.

## Error Handling

**Patterns:**
- Raise domain-specific exceptions at integration boundaries: `YoloModelUnavailable` and `YoloDetectorError` in `satellite_edge_node/yolo_detector.py`; `LiquidReasonerUnavailable` and `LiquidReasonerError` in `satellite_edge_node/liquid_vlm_reasoner.py`; `SimSatUnavailable` in `kilnwatch/ingestion/simsat_client.py`; `ImageValidationError` in `kilnwatch/datasets/image_validation.py`; `RequiredCropUnavailable` in `satellite_edge_node/orbital_pass.py`.
- Wrap external/library failures with contextual messages and exception chaining (`raise X(...) from exc`). Verified in `YoloDetector.__init__` (`satellite_edge_node/yolo_detector.py:38-54`) and `LiquidLocalReasoner.__init__/.reason` (`satellite_edge_node/liquid_vlm_reasoner.py:90-105,176-177`).
- Validators return structured issue lists instead of raising on every row-level problem: `validate_manifest_file()` returns `list[ManifestIssue]` in `kilnwatch/datasets/manifest.py`; the caller decides what to do with the issues.
- Conversion helpers that default malformed user/data input safely so dashboards keep rendering: `_as_int()`, `_as_float()` in `kilnwatch/ground_station.py`; `_as_float()` in `kilnwatch/triage.py:137`; `_safe_float()` in `satellite_edge_node/yolo_detector.py`.
- CLI `main()` functions catch known exception types, print a one-line cause + actionable hint, and return a numeric exit code. `satellite_edge_node/orbital_pass.py:202-226` exits 2 on `YoloDetectorError`, 3 on `LiquidReasonerError`, 4 on `RequiredCropUnavailable`, 0 on success. Mirror this pattern when adding new failure modes.
- Honesty metadata is preserved through the pipeline and never silently flipped. Required fields, originating from `DetectionResult` defaults in `satellite_edge_node/baseline_detector.py:30-35` and threaded through `satellite_edge_node/payloads.py` + `kilnwatch/ground_station.py`:
  - `detector_version`, `detector_mode`, `detector_is_real`, `simulated`, `fallback_used`, `fallback_reason`
  - `vlm_reasoning.reasoner_mode`, `vlm_reasoning.reasoner_is_real`, `vlm_reasoning.model_name`
  - `triage_decision`, `triage.driven_by` (`"yolo-only"` vs `"liquid+yolo"`), `triage.risk_band_used`, `triage.risk_score_used`
  - `requested_detector_mode`, `requested_reasoner_mode` (preserve the user's intent even after fallback)
  - `crop_ref`, `crop_error`, `crop_path`, `byte_accounting`
- `compute_triage()` in `kilnwatch/triage.py:45` accepts a keyword-only `min_confidence` (default `0.45`) so callers can align the IGNORE band with the detector's gating threshold. `triage_label()` in `satellite_edge_node/payloads.py:20` and `telemetry_record()` at line 176 both forward this through a `triage_min_confidence` parameter (default `0.25` to match the YOLO confidence threshold).

## Logging

**Framework:** No `logging` module use detected anywhere in `kilnwatch/`, `satellite_edge_node/`, `ground_station_ui/`, or `scripts/`. All status output is via `print` for CLIs and `st.error/st.warning/st.info/st.caption` for Streamlit UIs.

**Patterns:**
- CLI tools print human-readable summaries to stdout. See `satellite_edge_node/orbital_pass.py:227-241` (post-run bandwidth/savings/ratio summary).
- JSON-producing tools print deterministic JSON with `sort_keys=True`: `scripts/evaluate_detector.py`, `scripts/check_model_ready.py`. Payload encoding for transmission uses the same shape: `json.dumps(payload, sort_keys=True, separators=(",", ":"))` in `satellite_edge_node/payloads.py:163`.
- Streamlit UIs report status through `st.metric`, `st.caption`, `st.error`, `st.warning`, `st.info` instead of print or logs: `app.py`, `ground_station_ui/app.py`.

## Comments

**When to Comment:**
- Module docstrings state purpose in one or two sentences. Verified on `kilnwatch/ground_station.py`, `kilnwatch/triage.py`, `satellite_edge_node/orbital_pass.py`, `satellite_edge_node/payloads.py`, `satellite_edge_node/yolo_detector.py`, `satellite_edge_node/liquid_vlm_reasoner.py`, `satellite_edge_node/baseline_detector.py`.
- Inline comments are reserved for two cases:
  1. External dependency failure modes that span multiple exception classes (e.g. `# Weight loading can fail on corrupt or incompatible local files.` in `satellite_edge_node/yolo_detector.py:47`; `# Ultralytics raises several backend-specific exceptions.` at line 59).
  2. Anchoring a non-obvious design choice to a primary source — e.g. the multi-line comment in `satellite_edge_node/liquid_vlm_reasoner.py:122-124` cites the Liquid cookbook examples (`car-maker-identification` and `prepare_vrsbench.py`) that justify the system+user split.
- Top-level emojis are not used in source. Do not introduce them.

**Docstrings:**
- Function docstrings are present where the public contract needs explanation: `compute_triage()` in `kilnwatch/triage.py:50`, `triage_label()` in `satellite_edge_node/payloads.py:26-33`, `load_ground_station_records()` in `kilnwatch/ground_station.py:65`, `detect_tile()` in `satellite_edge_node/baseline_detector.py:39`.
- One-line docstrings are acceptable for self-evident helpers; do not pad them.

## Function Design

**Size:** Each function owns one transformation, one IO boundary, or one UI section. Streamlit rendering is split into `_inject_css()`, `_render_*` helpers in `app.py` and `ground_station_ui/app.py`. Payload assembly, byte accounting, encoding, and telemetry recording are separate functions in `satellite_edge_node/payloads.py` (`build_transmission_payload`, `attach_byte_accounting`, `encode_payload`, `telemetry_record`).

**Parameters:**
- Required positional args first, optional behavior gated behind keyword-only `*,` separators. Examples:
  - `simulate_orbital_pass(raw_tiles_dir, transmission_queue, *, detector=None, detector_mode="baseline", model_path=DEFAULT_MODEL_PATH, confidence_threshold=0.25, allow_baseline_fallback=False, reasoner=None, reasoner_mode="disabled", reset_queue=False, require_crops=False, write_drop_payloads=False)` in `satellite_edge_node/orbital_pass.py:33`.
  - `compute_triage(prediction, *, min_confidence=0.45)` in `kilnwatch/triage.py:45`.
  - `telemetry_record(*, tile_path, detection, inference_latency_ms, ...)` (entirely keyword-only) in `satellite_edge_node/payloads.py:176`.
  - `build_demo_tiles(rows, *, mode, tile_dir, manifest_path, local_image_dir=None, simsat_client=None, ...)` in `scripts/fetch_demo_tiles.py`.
- Inject collaborators rather than constructing them inside business logic. `simulate_orbital_pass()` accepts pre-built `detector` and `reasoner` objects and only constructs them via `build_detector_with_fallback()` / `build_reasoner()` if the caller passes `None`.

**Return Values:**
- Frozen dataclasses for in-process domain records: `MissionMetrics`, `TriageResult`, `CropEvidence`, `MissionProofCounts`, `ProofStatus`, `DetectionResult`, `VlmReasoning`, `CropArtifact`.
- Plain `dict[str, Any]` / `list[dict]` for serializable payloads, telemetry rows, and JSON-bound returns: `build_transmission_payload()`, `telemetry_record()`, `triage_label()` all return dicts because they are written straight to the wire.
- CLI `main()` returns `int` (process exit code). Streamlit `main()` returns `None`.

## Module Design

**Exports:**
- Public functions/classes are exported directly from their defining modules with no aliasing. Module-private helpers stay underscore-prefixed (`_truth_metadata`, `_attach_vlm_reasoning`, `_crop_box_from_bbox`, `_load_payloads`, `_decision`, `_extract_detections`, `_extract_json_object`, `_risk_value`, `_bool_value`).
- Group related helpers in the same module. Do not split a single concern across packages.

**Barrel Files:**
- Not used. `kilnwatch/__init__.py`, `satellite_edge_node/__init__.py`, and `ground_station_ui/__init__.py` are empty markers. Do not add aggregate re-export files; the package surface is defined by the modules themselves.

**Architectural boundary (enforced by test):**
- The ground-station surface (`app.py`, `kilnwatch/ground_station.py`, `ground_station_ui/*.py`) MUST NOT import `satellite_edge_node` and MUST NOT reference satellite-side filesystem paths (`data/raw_tiles`, `data/final_demo_tiles`, `datasets/roboflow`, `raw_tiles`). Enforced by `tests/test_ground_station_boundary.py`. The substring check is literal — even a documentation snippet inside HTML strings will fail it. Use neutral wording like `python -m <satellite module>` if you must reference the satellite CLI from a UI string.
- Crop evidence resolution rejects raw/roboflow/final-demo paths via `FORBIDDEN_CROP_SOURCE_FRAGMENTS` in `kilnwatch/ground_station.py:17`. Add new forbidden source roots there if more imagery directories are introduced.

---

*Convention analysis: 2026-05-09*

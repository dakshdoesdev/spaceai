# Coding Conventions

**Analysis Date:** 2026-05-06

## Naming Patterns

**Files:**
- Use lowercase snake_case for Python modules: `kilnwatch/ground_station.py`, `satellite_edge_node/orbital_pass.py`, `scripts/fetch_demo_tiles.py`.
- Use package `__init__.py` files as lightweight package markers, not export hubs: `kilnwatch/__init__.py`, `satellite_edge_node/__init__.py`, `ground_station_ui/__init__.py`.
- Use `test_*.py` for test modules under `tests/`: `tests/test_ground_station.py`, `tests/test_yolo_detector.py`, `tests/test_fetch_demo_tiles.py`.
- Keep runnable scripts in `scripts/` and expose package CLIs through `[project.scripts]` in `pyproject.toml`: `scripts/evaluate_detector.py`, `scripts/validate_manifest.py`, `kilnwatch.ingestion.cli:main`, `satellite_edge_node.orbital_pass:main`.

**Functions:**
- Use snake_case and explicit verb phrases for public operations: `load_ground_station_records()` in `kilnwatch/ground_station.py`, `simulate_orbital_pass()` in `satellite_edge_node/orbital_pass.py`, `evaluate_detector()` in `scripts/evaluate_detector.py`.
- Use leading underscore for module-private helpers: `_load_payloads()` in `kilnwatch/ground_station.py`, `_extract_detections()` in `satellite_edge_node/yolo_detector.py`, `_truth_positive()` in `scripts/evaluate_detector.py`.
- CLI modules use `main() -> int` and `if __name__ == "__main__": raise SystemExit(main())`: `satellite_edge_node/orbital_pass.py`, `scripts/evaluate_detector.py`, `scripts/check_model_ready.py`.
- Streamlit entry points use `main() -> None` and call `main()` directly under the module guard: `app.py`, `ground_station_ui/app.py`.

**Variables:**
- Use descriptive snake_case domain names: `raw_bytes_processed`, `downlinked_bytes`, `telemetry_events`, `confidence_threshold` in `kilnwatch/ground_station.py` and `satellite_edge_node/orbital_pass.py`.
- Use uppercase constants for domain policy and default paths: `TRANSMISSION_QUEUE_DIR`, `REVIEW_DECISIONS` in `kilnwatch/ground_station.py`; `DEFAULT_MODEL_PATH`, `DETECTOR_VERSION` in `satellite_edge_node/yolo_detector.py`; `REQUIRED_FIELDS`, `ALLOWED_SPLITS` in `kilnwatch/datasets/manifest.py`.
- Use plural collection names for lists/sets/dicts: `payloads`, `events`, `detections`, `missing_predictions` in `kilnwatch/ground_station.py`, `satellite_edge_node/yolo_detector.py`, and `scripts/evaluate_detector.py`.

**Types:**
- Use PascalCase for dataclasses, protocols, enums, and exceptions: `MissionMetrics` in `kilnwatch/ground_station.py`, `Detector` in `satellite_edge_node/detectors.py`, `TriageDecision` in `kilnwatch/triage.py`, `YoloModelUnavailable` in `satellite_edge_node/yolo_detector.py`.
- Use frozen dataclasses for immutable domain records: `DetectionResult` in `satellite_edge_node/baseline_detector.py`, `CropArtifact` in `satellite_edge_node/payloads.py`, `ManifestIssue` in `kilnwatch/datasets/manifest.py`.
- Use exception names ending in `Error` or a precise unavailable condition: `ImageValidationError` in `kilnwatch/datasets/image_validation.py`, `SimSatUnavailable` in `kilnwatch/ingestion/simsat_client.py`.

## Code Style

**Formatting:**
- No formatter configuration is detected in `pyproject.toml`, `.prettierrc`, `ruff.toml`, or `setup.cfg`.
- Follow the existing Black-compatible shape: 4-space indentation, blank line between top-level definitions, trailing commas in multi-line literals/calls, and 88-ish line wrapping where practical. Examples: `satellite_edge_node/payloads.py`, `tests/test_satellite_edge_bandwidth.py`.
- Use `from __future__ import annotations` in production modules to support modern type syntax consistently: `app.py`, `kilnwatch/triage.py`, `satellite_edge_node/yolo_detector.py`, `scripts/fetch_demo_tiles.py`.
- Prefer `Path` over raw string path handling for filesystem code: `kilnwatch/ground_station.py`, `satellite_edge_node/orbital_pass.py`, `scripts/fetch_demo_tiles.py`.

**Linting:**
- No lint tool is configured in `pyproject.toml`.
- Keep imports clean manually: standard library first, third-party packages next, local package imports last. Examples: `app.py`, `satellite_edge_node/yolo_detector.py`, `scripts/evaluate_detector.py`.
- Avoid broad dependencies in core package code. Optional imports are localized to the feature using them: `from PIL import Image` inside `satellite_edge_node/payloads.py`, `from ultralytics import YOLO` inside `satellite_edge_node/yolo_detector.py`.

## Import Organization

**Order:**
1. Future annotations: `from __future__ import annotations` in production modules such as `kilnwatch/ground_station.py` and `scripts/evaluate_detector.py`.
2. Standard library imports: `json`, `argparse`, `tempfile`, `unittest`, `dataclasses`, `pathlib`, `typing`.
3. Third-party imports: `pandas`, `streamlit`, `PIL` where needed.
4. Local package imports: `from kilnwatch.ground_station import ...`, `from satellite_edge_node.payloads import ...`, `from ground_station_ui.queue_reader import ...`.

**Path Aliases:**
- No configured path aliases are detected. Import package modules by package name from the repo root: `kilnwatch.ground_station`, `satellite_edge_node.detectors`, `ground_station_ui.queue_reader`.
- Use relative imports inside package modules when importing sibling modules: `.baseline_detector` in `satellite_edge_node/detectors.py`, `.payloads` in `satellite_edge_node/orbital_pass.py`.

## Error Handling

**Patterns:**
- Raise domain-specific exceptions at integration boundaries: `YoloModelUnavailable` and `YoloDetectorError` in `satellite_edge_node/yolo_detector.py`, `SimSatUnavailable` in `kilnwatch/ingestion/simsat_client.py`, `ImageValidationError` in `kilnwatch/datasets/image_validation.py`.
- Wrap external/library failures with contextual messages and exception chaining: YOLO import/model/inference failures in `satellite_edge_node/yolo_detector.py`; image validation failures in `kilnwatch/datasets/image_validation.py`; SimSat endpoint failures in `kilnwatch/ingestion/simsat_client.py`.
- Return structured issue lists for validators instead of raising on every row-level problem: `validate_manifest_file()` returns `list[ManifestIssue]` in `kilnwatch/datasets/manifest.py`.
- Use conversion helpers that default malformed user/data input safely when metrics should keep rendering: `_as_int()` and `_as_float()` in `kilnwatch/ground_station.py`, `_safe_float()` in `satellite_edge_node/yolo_detector.py`.
- CLI `main()` functions catch expected user-facing failures, print concise messages, and return non-zero status codes: `satellite_edge_node/orbital_pass.py`, `scripts/fetch_demo_tiles.py`, `scripts/validate_manifest.py`.
- Do not hide truth/state transitions. Fallbacks include explicit metadata such as `fallback_used`, `fallback_reason`, `detector_is_real`, and `simulated` in `satellite_edge_node/detectors.py` and `satellite_edge_node/payloads.py`.

## Logging

**Framework:** console output via `print`; no `logging` framework usage detected.

**Patterns:**
- CLI tools print human-readable summaries to stdout and errors to stderr when appropriate: `scripts/fetch_demo_tiles.py`, `scripts/validate_manifest.py`, `satellite_edge_node/orbital_pass.py`.
- JSON-producing tools print deterministic JSON with `sort_keys=True` for machine-readable output: `scripts/evaluate_detector.py`, `scripts/check_model_ready.py`.
- Streamlit UI code reports status through `st.error`, `st.warning`, `st.info`, `st.caption`, and metrics instead of logs: `app.py`, `ground_station_ui/app.py`.

## Comments

**When to Comment:**
- Prefer module docstrings that state purpose: `kilnwatch/ground_station.py`, `satellite_edge_node/orbital_pass.py`, `satellite_edge_node/payloads.py`, `scripts/evaluate_detector.py`.
- Use short comments only where a dependency can fail in multiple backend-specific ways: `satellite_edge_node/yolo_detector.py` comments around model loading and inference exceptions.
- Keep inline comments sparse; encode most intent in function names, dataclass fields, and exception messages.

**JSDoc/TSDoc:**
- Not applicable. This repo is Python.
- Python docstrings are used selectively for public behavior and abstract contracts: `load_ground_station_records()` in `kilnwatch/ground_station.py`, `compute_triage()` in `kilnwatch/triage.py`, `DatasetAdapter.convert()` in `kilnwatch/datasets/adapters/base.py`.

## Function Design

**Size:** Keep functions focused on one transformation, IO boundary, or UI section. UI rendering is split into `render_*` functions in `app.py`; metric calculation, payload loading, and row formatting are separate in `kilnwatch/ground_station.py`.

**Parameters:** Use explicit typed parameters and keyword-only options for configurable behavior. Examples: `simulate_orbital_pass(..., *, detector=None, detector_mode="baseline", model_path=DEFAULT_MODEL_PATH, confidence_threshold=0.25, allow_baseline_fallback=False)` in `satellite_edge_node/orbital_pass.py`; `build_demo_tiles(..., *, mode, local_image_dir, simsat_client)` in `scripts/fetch_demo_tiles.py`.

**Return Values:** Return typed dataclasses for domain records and plain dict/list structures for JSON/UI surfaces. Examples: `MissionMetrics` in `kilnwatch/ground_station.py`, `TriageResult` in `kilnwatch/triage.py`, JSON-ready dicts in `satellite_edge_node/payloads.py` and `scripts/evaluate_detector.py`.

## Module Design

**Exports:** Export public functions/classes directly from their defining modules. Keep module-private helpers prefixed with `_`. Examples: public `calculate_metrics()` and private `_decision()` in `kilnwatch/ground_station.py`; public `normalize_yolo_results()` and private `_extract_detections()` in `satellite_edge_node/yolo_detector.py`.

**Barrel Files:** Barrel files are not used. Do not add aggregate re-export files unless a package-level API becomes necessary; current `__init__.py` files are minimal markers in `kilnwatch/`, `satellite_edge_node/`, and `ground_station_ui/`.

---

*Convention analysis: 2026-05-06*

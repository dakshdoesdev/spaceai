# Testing Patterns

**Analysis Date:** 2026-05-06

## Test Framework

**Runner:**
- pytest is configured through `pyproject.toml` with `testpaths = ["tests"]`.
- Tests themselves are written with stdlib `unittest.TestCase`, so they can run under both pytest discovery and unittest discovery.
- Config: `pyproject.toml`

**Assertion Library:**
- stdlib `unittest` assertions: `self.assertEqual`, `self.assertAlmostEqual`, `self.assertTrue`, `self.assertFalse`, `self.assertIn`, `self.assertRaises`, and `self.assertRaisesRegex`.

**Run Commands:**
```bash
python -m pytest              # Run all tests through pytest using pyproject.toml testpaths
python -m pytest tests -q     # Run all tests with concise pytest output
python -m unittest discover -s tests -p 'test*.py'  # Documented fallback in docs/submission_checklist.md
```

## Test File Organization

**Location:**
- Tests live in the top-level `tests/` directory.
- Tests are organized by behavior/module area rather than mirroring the full package tree.
- Production code is covered from `kilnwatch/`, `satellite_edge_node/`, `ground_station_ui/`, and `scripts/`.

**Naming:**
- Test files use `test_*.py`: `tests/test_ground_station.py`, `tests/test_satellite_edge_bandwidth.py`, `tests/test_yolo_detector.py`.
- Test case classes use PascalCase names ending in `Tests` or `Test`: `GroundStationTests`, `OrbitalPassTests`, `ManifestSchemaTest`.
- Test methods use `test_<expected_behavior>` with readable behavior names: `test_real_records_take_precedence_over_sample_records`, `test_unreadable_crop_does_not_claim_crop_file`.

**Structure:**
```text
tests/
├── test_fetch_demo_tiles.py          # Demo tile ingestion and manifest generation
├── test_ground_station.py            # Ground-station metrics and payload filtering
├── test_ground_station_boundary.py   # Boundary/import dependency protection
├── test_manifest_schema.py           # Manifest row/file validation
├── test_metadata.py                  # Dataset metadata helpers
├── test_model_readiness_eval.py      # Model readiness and evaluator truth labels
├── test_satellite_edge_bandwidth.py  # Payload math and orbital pass integration
├── test_triage.py                    # Triage decision thresholds
└── test_yolo_detector.py             # YOLO normalization and fallback behavior
```

## Test Structure

**Suite Organization:**
```python
import unittest

from kilnwatch.ground_station import calculate_metrics


class GroundStationTests(unittest.TestCase):
    def test_metrics_summarize_downlink_savings(self):
        metrics = calculate_metrics(
            [
                {"triage_decision": "IGNORE", "raw_bytes_processed": 1000, "downlinked_bytes": 0},
                {"triage_decision": "JSON_ALERT_ONLY", "raw_bytes_processed": 1000, "downlinked_bytes": 10},
            ]
        )

        self.assertEqual(metrics.raw_bytes_processed, 2000)
        self.assertEqual(metrics.downlinked_bytes, 10)


if __name__ == "__main__":
    unittest.main()
```

**Patterns:**
- Put imports at the top, then one or more `unittest.TestCase` classes, then an optional `unittest.main()` guard.
- Arrange inline data dictionaries directly in the test when the scenario is small: `tests/test_ground_station.py`, `tests/test_triage.py`.
- Use `tempfile.TemporaryDirectory()` for filesystem integration tests that write queues, manifests, raw tiles, crops, or telemetry: `tests/test_satellite_edge_bandwidth.py`, `tests/test_fetch_demo_tiles.py`, `tests/test_model_readiness_eval.py`.
- Assert both domain behavior and truthfulness metadata. Examples: `detector_is_real`, `simulated`, `fallback_used`, and `fallback_reason` in `tests/test_yolo_detector.py` and `tests/test_satellite_edge_bandwidth.py`.

## Mocking

**Framework:** No `unittest.mock` or pytest monkeypatch pattern is currently used.

**Patterns:**
```python
class FakeTensor:
    def __init__(self, value):
        self.value = value

    def detach(self):
        return self

    def cpu(self):
        return self

    def tolist(self):
        return self.value


class FakeBoxes:
    xyxy = FakeTensor([[10, 20, 110, 120]])
    conf = FakeTensor([0.91])
    cls = FakeTensor([0])
```

**What to Mock:**
- Prefer small fake objects for external result shapes when testing normalization logic. `tests/test_yolo_detector.py` uses `FakeTensor`, `FakeBoxes`, and `FakeResult` to test `satellite_edge_node/yolo_detector.py` without loading Ultralytics.
- Prefer temporary files and real local IO over mocks for filesystem behavior. `tests/test_satellite_edge_bandwidth.py` writes `.tile`, `.png`, `.meta.json`, queue JSON, and telemetry files.
- Pass explicit collaborators where production code supports injection. `simulate_orbital_pass()` accepts `detector` and detector settings in `satellite_edge_node/orbital_pass.py`.

**What NOT to Mock:**
- Do not mock core byte math, JSON encoding, or manifest validation; test those functions directly with concrete inputs: `tests/test_satellite_edge_bandwidth.py`, `tests/test_manifest_schema.py`.
- Do not mock the ground-station/satellite boundary; assert the boundary directly as in `tests/test_ground_station_boundary.py`.
- Do not require optional local YOLO dependencies for normal CI/test runs; skip real inference checks when `ultralytics` or `models/brick_kiln_yolo.pt` is unavailable in `tests/test_yolo_detector.py`.

## Fixtures and Factories

**Test Data:**
```python
with tempfile.TemporaryDirectory() as temp_dir:
    root = Path(temp_dir)
    raw_tiles = root / "raw_tiles"
    queue = root / "queue"
    raw_tiles.mkdir()
    (raw_tiles / "farm_negative_001.tile").write_bytes(b"y" * 1024)

    records = simulate_orbital_pass(raw_tiles, queue, detector_mode="baseline")

    self.assertEqual(len(records), 1)
```

**Location:**
- Inline fixtures live in individual test methods for most scenarios: `tests/test_ground_station.py`, `tests/test_triage.py`, `tests/test_satellite_edge_bandwidth.py`.
- Shared helper functions are local to the test module when needed: `_write_one_row_csv()` and `write_test_png()` in `tests/test_fetch_demo_tiles.py`; `write_test_png()` in `tests/test_manifest_schema.py`.
- Repository sample data is used for schema validation where it is part of the product surface: `datasets/kilnwatch/manifests/sample_demo_manifest.jsonl` in `tests/test_manifest_schema.py`.

## Coverage

**Requirements:** No coverage threshold or coverage tool configuration is detected in `pyproject.toml`.

**View Coverage:**
```bash
python -m pytest              # Primary available verification command
# No configured coverage command detected
```

## Test Types

**Unit Tests:**
- Pure decision and math tests cover threshold behavior and utility functions: `tests/test_triage.py`, `tests/test_metadata.py`, `tests/test_ground_station.py`.
- Validator tests check row-level schema failures and image validation branches: `tests/test_manifest_schema.py`.
- YOLO normalization tests cover model-result conversion without loading the real model: `tests/test_yolo_detector.py`.

**Integration Tests:**
- Filesystem integration tests cover orbital pass output, queue files, crop generation, telemetry records, and manifest generation: `tests/test_satellite_edge_bandwidth.py`, `tests/test_fetch_demo_tiles.py`.
- Evaluator tests cover manifest/telemetry classification, missing predictions, and real-vs-simulated detector status: `tests/test_model_readiness_eval.py`.
- Boundary tests protect architecture constraints, such as keeping ground station code from importing satellite raw tile modules: `tests/test_ground_station_boundary.py`.

**E2E Tests:**
- No browser/UI E2E framework is detected.
- Streamlit UI modules `app.py` and `ground_station_ui/app.py` are indirectly supported through tested data loaders and metric helpers in `kilnwatch/ground_station.py` and `ground_station_ui/queue_reader.py`, but the rendered UI is not directly exercised.

## Common Patterns

**Async Testing:**
```python
# Not detected. The codebase uses synchronous file, CLI, and data-processing flows.
```

**Error Testing:**
```python
with self.assertRaises(YoloModelUnavailable) as ctx:
    build_detector_with_fallback("yolo", model_path=missing)
self.assertIn("YOLO model weights not found", str(ctx.exception))
```

```python
with self.assertRaisesRegex(ValueError, "readable image"):
    build_demo_tiles(...)
```

```python
issues = validate_manifest_file(path)
self.assertEqual(len(issues), 1)
self.assertIn("invalid JSON", issues[0].message)
```

---

*Testing analysis: 2026-05-06*

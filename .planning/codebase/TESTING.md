# Testing Patterns

**Analysis Date:** 2026-05-09

## Test Framework

**Runner:**
- pytest, configured via `pyproject.toml`:
  ```toml
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  ```
- No `conftest.py`, no fixtures, no plugins. Pure stdlib `unittest.TestCase` classes that pytest discovers and runs.
- Suite is therefore portable to `python -m unittest discover -s tests` as a fallback (documented in `docs/submission_checklist.md`).

**Assertion Library:**
- Stdlib `unittest` assertions only: `self.assertEqual`, `self.assertAlmostEqual`, `self.assertTrue`, `self.assertFalse`, `self.assertIn`, `self.assertNotIn`, `self.assertIs`, `self.assertIsNone`, `self.assertGreater`, `self.assertRaises`, `self.assertRaisesRegex`, `self.subTest`.
- No `pytest.mark.parametrize`, no `pytest.fixture`, no `pytest.raises`.

**Run Commands:**
```bash
# Full suite via the project venv (preferred — system python lacks pytest)
.venv/bin/python -m pytest

# Verbose, single-line per test
.venv/bin/python -m pytest -v

# Just one file
.venv/bin/python -m pytest tests/test_satellite_edge_bandwidth.py -v

# Collect-only (count tests without running)
.venv/bin/python -m pytest --collect-only -q

# Stdlib fallback (no pytest needed)
python -m unittest discover -s tests -p 'test*.py'
```

## Current State (verified 2026-05-09)

- `pytest --collect-only` reports **66 tests collected** across 9 files.
- Last full run: **65 passed, 1 failed**, 4 subtests passed.
- The single failure is `tests/test_ground_station_boundary.py::GroundStationBoundaryTests::test_ground_station_does_not_import_satellite_raw_tile_modules`. Cause: `app.py` line 544 contains the string `python -m satellite_edge_node.orbital_pass` inside an HTML help block. The boundary test does a literal substring scan (`self.assertNotIn("satellite_edge_node", source)`) and does not distinguish docstring/HTML text from actual imports. Either the help text needs to be reworded (e.g. "the satellite-edge orbital pass CLI") or the boundary helper needs to strip docstrings/HTML before scanning. This is a real regression introduced alongside the recent dashboard rewrite, not a flake.
- The three tests added today are present and passing:
  - `tests/test_satellite_edge_bandwidth.py::BandwidthMathTests::test_telemetry_record_includes_triage_decision_label`
  - `tests/test_satellite_edge_bandwidth.py::BandwidthMathTests::test_telemetry_record_low_confidence_below_detector_floor_is_ignored`
  - `tests/test_ground_station.py::GroundStationTests::test_alert_rows_use_orbital_pass_triage_label`

## Test File Organization

**Location:**
- All tests live in the top-level `tests/` directory. No mirrored package tree.
- Tests are organized by behavior/module area, not by file-for-file pairing with source.

**Naming:**
- Files: `test_*.py`.
- Classes: PascalCase ending in `Tests` (or `Test` for the older `test_metadata.py` and `test_manifest_schema.py`): `GroundStationTests`, `OrbitalPassTests`, `BandwidthMathTests`, `YoloDetectorTests`, `LiquidVlmReasonerTests`, `TriageTests`, `FetchDemoTilesTests`, `ManifestSchemaTest`, `MetadataHelpersTest`, `GroundStationBoundaryTests`, `ModelReadinessAndEvaluationTests`.
- Methods: `test_<behavior>` written as readable English: `test_real_records_take_precedence_over_sample_records`, `test_unreadable_crop_does_not_claim_crop_file`, `test_strict_yolo_cli_fails_loudly_without_fallback`, `test_telemetry_record_low_confidence_below_detector_floor_is_ignored`.

**Structure:**
```text
tests/
├── test_fetch_demo_tiles.py          # CSV→manifest, placeholder vs local-import vs simsat modes
├── test_ground_station.py            # Metrics, cumulative series, alert rows, proof status,
│                                       crop-evidence resolution, sample-vs-real precedence
├── test_ground_station_boundary.py   # Architectural boundary: ground station must not import
│                                       satellite_edge_node or reference raw_tile paths
├── test_liquid_vlm_reasoner.py       # Mock reasoner metadata, transformers-unavailable branch,
│                                       orbital-pass integration with reasoner_mode=disabled/mock
├── test_manifest_schema.py           # Required-field, bbox-type, JSON, image-readability checks
├── test_metadata.py                  # safe_timestamp + extension_for_content_type helpers
├── test_model_readiness_eval.py      # check_model_ready + evaluate_detector classification
├── test_satellite_edge_bandwidth.py  # bandwidth math, triage_decision telemetry, orbital pass
│                                       crop generation, reset_queue, require_crops failure
├── test_triage.py                    # 4-tier decision thresholds (IGNORE / JSON_ALERT_ONLY /
│                                       CROP_OR_REVIEW / FULL_DOWNLINK)
└── test_yolo_detector.py             # Strict-fail without weights, fallback metadata,
                                        normalize_yolo_results, CLI exit-2 behavior
```

## Test Structure

**Suite shape (canonical):**
```python
import json
import tempfile
import unittest
from pathlib import Path

from kilnwatch.triage import TriageDecision, compute_triage


class TriageTests(unittest.TestCase):
    def test_ignore_when_no_kiln(self):
        result = compute_triage({"kiln_detected": False, "confidence": 0.99, "compliance_risk_score": 1.0})
        self.assertEqual(result.decision, TriageDecision.IGNORE)


if __name__ == "__main__":
    unittest.main()
```

**Patterns:**
- Imports first (no `from __future__` in tests), then one or more `unittest.TestCase` classes, then an `if __name__ == "__main__": unittest.main()` guard.
- Build inline data dicts directly inside the test when the scenario is small (`tests/test_triage.py`, `tests/test_ground_station.py::test_metrics_summarize_downlink_savings`).
- Use `tempfile.TemporaryDirectory()` for any test that touches the filesystem (queue, raw tiles, sidecars, telemetry, manifests, crops). Verified across `tests/test_satellite_edge_bandwidth.py`, `tests/test_fetch_demo_tiles.py`, `tests/test_model_readiness_eval.py`, `tests/test_manifest_schema.py`, `tests/test_liquid_vlm_reasoner.py`, `tests/test_ground_station.py` (the crop-evidence and real-vs-sample tests).
- Always assert truthfulness metadata alongside domain behavior. Every detector/reasoner test that builds a `DetectionResult` or runs `simulate_orbital_pass` checks at least one of `detector_is_real`, `simulated`, `fallback_used`, `fallback_reason`, `reasoner_is_real`, or `reasoner_mode`. Examples: `test_telemetry_record_contains_detector_version_and_sizes`, `test_explicit_fallback_marks_detection_truthfully`, `test_mock_reasoner_is_marked_simulated`, `test_evaluator_marks_baseline_sample_as_simulated`.
- Triage payload assertions check both the flat `triage_decision` field and the structured `triage` sub-dict (`triage["driven_by"]`, `triage["risk_band_used"]`). See `test_telemetry_record_includes_triage_decision_label` and `test_alert_rows_use_orbital_pass_triage_label`.
- Use `self.subTest(...)` inside parametric-style loops instead of repeating tests. Example: `tests/test_ground_station.py::test_crop_evidence_rejects_raw_final_roboflow_and_tile_paths` iterates over `forbidden_paths` with `subTest(candidate=candidate)`.

## Mocking

**Framework:**
- `unittest.mock.patch` is used in exactly one place: `tests/test_liquid_vlm_reasoner.py::test_local_reasoner_fails_honestly_when_transformers_unavailable` patches `builtins.__import__` to raise `ImportError("no transformers here")` only for the `transformers` module name, then asserts `LiquidLocalReasoner()` raises `LiquidReasonerUnavailable`.
- No pytest `monkeypatch`, no `MagicMock`. The rest of the suite uses hand-rolled fakes or temp files.

**Hand-rolled fakes (preferred for external SDK shapes):**
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


class FakeResult:
    boxes = FakeBoxes()
    names = {0: "brick_kiln"}


class FakeNonKilnResult:
    boxes = FakeBoxes()
    names = {0: "person"}
```
Defined at module top of `tests/test_yolo_detector.py`. Used to test `normalize_yolo_results()` without loading Ultralytics. Mirror this pattern for any new external-SDK normalization layer (e.g. a different detector backend).

**Subprocess invocation as integration mock:**
- `tests/test_yolo_detector.py::test_strict_yolo_cli_fails_loudly_without_fallback` calls `subprocess.run([sys.executable, "-m", "satellite_edge_node.orbital_pass", ...])` against a temp directory and asserts `returncode == 2`, `"Detector setup failed"` in output, `"--allow-baseline-fallback"` in output, and that `telemetry.jsonl` was not written. This is the canonical pattern for testing CLI exit codes and stderr surfaces.

**Inline test-double for SimSat client:**
```python
class BadImageClient:
    base_url = "http://localhost:9005/"
    def fetch_sentinel_tile(self, lat, lon, width=512, height=512):
        return SimSatResponse("/sentinel-2/image", "http://localhost:9005/sentinel-2/image", "text/plain", b"nope")
```
Defined inline inside `tests/test_fetch_demo_tiles.py::test_simsat_non_image_bytes_fail_real_mode`. Use this pattern (a tiny class with the right method signature) when injecting collaborators into `build_demo_tiles()` or `simulate_orbital_pass()`.

**What to mock:**
- External SDK result shapes (Ultralytics `Results`, transformers `AutoModel*`).
- HTTP clients used at ingestion boundaries (`SimSatClient`).
- Module imports for "library not installed" branches — patch `builtins.__import__`, not the symbol.

**What NOT to mock:**
- Filesystem behavior. Use `tempfile.TemporaryDirectory()` and write real bytes/JSON/PNG. The crop-generation, reset-queue, telemetry-jsonl, and manifest-validation tests all do real IO end-to-end.
- Byte math, JSON encoding, or manifest validation. Test them directly with concrete inputs (`tests/test_satellite_edge_bandwidth.py::BandwidthMathTests`, `tests/test_manifest_schema.py`).
- The ground-station/satellite import boundary. Assert it directly (`tests/test_ground_station_boundary.py`) rather than mocking imports.
- The optional real YOLO model. Skip with `self.skipTest(...)` when `ultralytics` or `models/brick_kiln_yolo.pt` is missing — see `test_real_yolo_inference_requires_optional_local_setup`.

## Fixtures and Factories

**Test data:**
- All fixtures are inline. No `tests/fixtures/` directory, no shared `conftest.py`.

**Canonical filesystem fixture:**
```python
with tempfile.TemporaryDirectory() as temp_dir:
    root = Path(temp_dir)
    raw_tiles = root / "raw_tiles"
    queue = root / "queue"
    raw_tiles.mkdir()

    tile = raw_tiles / "kiln_high_001.tile"
    tile.write_bytes(b"x" * 2048)
    tile.with_suffix(tile.suffix + ".meta.json").write_text(
        json.dumps({
            "tile_id": "kiln_high_001",
            "kiln_detected": True,
            "confidence": 0.88,
            "compliance_risk": "high",
            "bbox": [4, 4, 20, 20],
            "signals": ["sidecar_test"],
        }),
        encoding="utf-8",
    )

    records = simulate_orbital_pass(raw_tiles, queue, detector_mode="baseline")
```
Used in nearly every orbital-pass-touching test. Note the `.tile.meta.json` sidecar pattern — `satellite_edge_node/baseline_detector.py` reads sidecar JSON next to the raw tile to drive deterministic detection without a real model.

**Real PNG factory (used when image readability matters):**
```python
def write_test_png(path: Path) -> None:
    from PIL import Image
    image = Image.new("RGB", (1, 1), color=(255, 0, 0))
    image.save(path, format="PNG")
```
Defined locally in both `tests/test_fetch_demo_tiles.py:144` and `tests/test_manifest_schema.py:80`. Pillow is imported lazily inside the function so the helper can be referenced even when the image-readability path of a test is skipped. If a third test needs this, copy the helper rather than introducing a `conftest.py` — the suite intentionally avoids shared test infrastructure.

**Repo sample data used as fixture:**
- `datasets/kilnwatch/manifests/sample_demo_manifest.jsonl` — referenced by `tests/test_manifest_schema.py::test_sample_manifest_is_valid` to lock the published sample manifest schema.
- `datasets/kilnwatch/manifests/baseline_sample_eval_manifest.jsonl` — referenced by `tests/test_model_readiness_eval.py::test_evaluator_marks_baseline_sample_as_simulated`. Modifying these files is a wire-format change and breaks tests on purpose.

**CSV factory:**
- `_write_one_row_csv()` in `tests/test_fetch_demo_tiles.py:135` writes a single-row coordinates CSV inline. Mirror this when adding new row-shape tests for `read_coordinate_csv()`.

## Coverage

**Requirements:** No coverage threshold or coverage tool is configured in `pyproject.toml`.

**View coverage:** Not wired up. If needed, run `coverage run -m pytest && coverage report` from the venv after `pip install coverage`, but no Make/CI target exists today.

## Test Types

**Unit (pure logic, no IO):**
- 4-tier triage thresholds: `tests/test_triage.py` — IGNORE / JSON_ALERT_ONLY / CROP_OR_REVIEW / FULL_DOWNLINK gating.
- Bandwidth math: `tests/test_satellite_edge_bandwidth.py::BandwidthMathTests` — `bandwidth_saved_bytes`, `compression_ratio`, `telemetry_record` field shape, including the new `triage_decision` and `triage_min_confidence` invariants.
- Mission metrics: `tests/test_ground_station.py::test_metrics_summarize_downlink_savings`, `test_cumulative_series_tracks_raw_vs_downlinked_bytes`, `test_metrics_accept_orbital_pass_telemetry_schema`.
- YOLO normalization: `tests/test_yolo_detector.py::test_yolo_results_normalize_to_payload_schema`, `test_yolo_low_confidence_result_becomes_negative`, `test_yolo_non_kiln_class_is_not_counted_as_detection`.
- Metadata helpers: `tests/test_metadata.py` — `safe_timestamp`, `extension_for_content_type`.

**Integration (filesystem, sidecars, queues, subprocess):**
- Orbital pass end-to-end: `tests/test_satellite_edge_bandwidth.py::OrbitalPassTests::test_orbital_pass_uses_file_sizes_and_queue_outputs`, `test_real_crop_file_is_created_from_png_and_counted_in_bytes` (real PNG → real crop → byte_accounting reconciliation), `test_reset_queue_removes_only_generated_queue_artifacts`, `test_unreadable_crop_does_not_claim_crop_file`, `test_require_crops_fails_for_alert_without_real_crop`.
- Liquid mock + parsing path: `tests/test_liquid_vlm_reasoner.py::test_disabled_orbital_pass_produces_no_vlm_reasoning`, `test_mock_reasoner_metadata_is_written_to_payload_and_telemetry`, `test_local_reasoner_fails_honestly_when_transformers_unavailable`.
- Demo tile ingestion: `tests/test_fetch_demo_tiles.py` — placeholder mode, local-import mode, simsat-mode failure, manifest validator round-trip.
- Manifest validation: `tests/test_manifest_schema.py` — required fields, bbox typing, invalid JSON line, real-image acceptance, placeholder-tile rejection.
- Evaluator + readiness: `tests/test_model_readiness_eval.py` — missing-model status, `simulated_baseline` evaluation, `real_yolo` evaluation.
- Real-vs-sample precedence: `tests/test_ground_station.py::test_real_records_take_precedence_over_sample_records`, `test_proof_status_reports_sample_data`.
- Ground-station/satellite boundary: `tests/test_ground_station_boundary.py` — see Failure note in "Current State" above.
- CLI exit codes: `tests/test_yolo_detector.py::test_strict_yolo_cli_fails_loudly_without_fallback` invokes `python -m satellite_edge_node.orbital_pass` via `subprocess.run` and asserts exit code 2 + stderr substrings.

**E2E:**
- No browser/UI E2E framework. Streamlit `app.py` and `ground_station_ui/app.py` are exercised indirectly through `kilnwatch/ground_station.py` helpers (`load_ground_station_records`, `mission_proof_counts`, `proof_status_summary`, `resolve_crop_evidence`) and `ground_station_ui/queue_reader.py` (`summarize_telemetry`). The rendered HTML is not asserted.

## Common Patterns

**Async testing:**
- Not present. The codebase is fully synchronous (file IO, CLI, Streamlit single-process, subprocess for one CLI test).

**Error testing:**
```python
# Domain exception with substring match on the message
with self.assertRaises(YoloModelUnavailable) as ctx:
    build_detector_with_fallback("yolo", model_path=missing)
self.assertIn("YOLO model weights not found", str(ctx.exception))

# Regex match for raised messages
with self.assertRaisesRegex(ValueError, "readable image"):
    build_demo_tiles(...)

with self.assertRaisesRegex(RequiredCropUnavailable, "not a readable image"):
    simulate_orbital_pass(raw_tiles, queue, detector_mode="baseline", require_crops=True)

# Validators return issue lists rather than raising — assert on the list shape
issues = validate_manifest_file(path)
self.assertEqual(len(issues), 1)
self.assertIn("invalid JSON", issues[0].message)

# CLI exit code + stderr substring
result = subprocess.run([sys.executable, "-m", "satellite_edge_node.orbital_pass", ...],
                        check=False, text=True, capture_output=True)
self.assertEqual(result.returncode, 2)
self.assertIn("Detector setup failed", result.stdout + result.stderr)
```

**Skip patterns (optional dependencies):**
```python
# Skip when transitive optional dep is missing
try:
    from PIL import Image
except ImportError:
    self.skipTest("Pillow is not installed")

# Skip when local model artifacts aren't on this machine
if importlib.util.find_spec("ultralytics") is None:
    self.skipTest("ultralytics is not installed")
if not Path("models/brick_kiln_yolo.pt").exists():
    self.skipTest("local YOLO weights are not installed")
```

## Notable Invariants Under Test

These are the load-bearing properties — break them and the demo's honesty story breaks:

- **Queue-only ground-station boundary** (`tests/test_ground_station_boundary.py`): `app.py`, `kilnwatch/ground_station.py`, and `ground_station_ui/*.py` must not contain the substring `satellite_edge_node` or any of `data/raw_tiles`, `data/final_demo_tiles`, `datasets/roboflow`, `raw_tiles`. Currently failing — see "Current State".
- **Strict-fail without YOLO weights** (`tests/test_yolo_detector.py::test_missing_yolo_weights_raise_clean_error`, `test_strict_yolo_cli_fails_loudly_without_fallback`): `--detector yolo` without `--allow-baseline-fallback` must raise `YoloModelUnavailable` with `"YOLO model weights not found"` and the CLI must exit 2 without writing telemetry.
- **Fallback honesty** (`tests/test_yolo_detector.py::test_explicit_fallback_marks_detection_truthfully`): when `--allow-baseline-fallback` is used, every emitted detection has `detector_mode == "fallback"`, `detector_is_real == False`, `simulated == True`, `fallback_used == True`, and a non-empty `fallback_reason`.
- **Require-crops fails when alert lacks crop** (`tests/test_satellite_edge_bandwidth.py::test_require_crops_fails_for_alert_without_real_crop`): `simulate_orbital_pass(..., require_crops=True)` must raise `RequiredCropUnavailable("not a readable image")` and must NOT write the alert payload to the queue.
- **Liquid mock honesty** (`tests/test_liquid_vlm_reasoner.py::test_mock_reasoner_is_marked_simulated`, `test_mock_reasoner_metadata_is_written_to_payload_and_telemetry`): `LiquidMockReasoner` always emits `reasoner_is_real == False`, `reasoner_mode == "liquid-mock"`, model_name containing "mock", and `confidence_note` containing "simulated". The metadata is mirrored into both the payload JSON and the telemetry row.
- **Liquid local fails when transformers missing** (`tests/test_liquid_vlm_reasoner.py::test_local_reasoner_fails_honestly_when_transformers_unavailable`): instantiating `LiquidLocalReasoner` without `transformers` raises `LiquidReasonerUnavailable("requires `transformers`")`. It does not silently downgrade to mock.
- **Triage decision logic** (`tests/test_triage.py`): the four bands are gated by `kiln_detected`, `confidence`, and `compliance_risk_score`. The new `min_confidence` kwarg defaults to `0.45` and is validated implicitly by these tests still passing — anything stricter would push `test_json_alert_for_low_risk_kiln` (confidence 0.72) into IGNORE.
- **Triage label baked into payload + telemetry** (`tests/test_satellite_edge_bandwidth.py::test_telemetry_record_includes_triage_decision_label`, `tests/test_ground_station.py::test_alert_rows_use_orbital_pass_triage_label`): every record carries `triage_decision` (string) and `triage` (dict with `driven_by` ∈ {`yolo-only`, `liquid+yolo`} and `risk_band_used`). Dashboard alert rows source their decision from `triage_decision`, not from legacy `payload_type`.
- **Detector floor honored by triage label** (`tests/test_satellite_edge_bandwidth.py::test_telemetry_record_low_confidence_below_detector_floor_is_ignored`): a 0.1-confidence detection with `triage_min_confidence=0.25` produces `triage_decision == "IGNORE"`. This protects against the dashboard advertising "alerts" for sub-threshold noise.
- **Real records preempt sample data** (`tests/test_ground_station.py::test_real_records_take_precedence_over_sample_records`): when both real and sample-flagged records exist in the queue/logs, only real records survive `load_ground_station_records()` and `sample_data` is `False`.
- **Crop evidence cannot be raw imagery** (`tests/test_ground_station.py::test_crop_evidence_rejects_raw_final_roboflow_and_tile_paths`): `resolve_crop_evidence` returns `available=False` for any crop_ref under `data/raw_tiles/`, `data/final_demo_tiles/`, `datasets/roboflow/`, or with a `.tile` suffix. Adding new imagery roots requires adding them to `FORBIDDEN_CROP_SOURCE_FRAGMENTS`.
- **Manifest schema** (`tests/test_manifest_schema.py`): required fields enforced; bbox values must be numeric; invalid JSON lines reported; image-readability check rejects `.tile` placeholders and accepts real PNGs.

## Gaps

- **Boundary test is brittle.** It substring-scans source code, so unrelated documentation/HTML strings can fail it. Today's failure (`app.py:544` mentions `satellite_edge_node.orbital_pass` in user-facing CLI help) is a real example. Consider stripping comments/docstrings/HTML before scanning, or moving the prohibition to an AST-level check.
- **Liquid local reasoner real-inference path is untested.** Only the import-fail branch (`test_local_reasoner_fails_honestly_when_transformers_unavailable`) and the JSON parser shape are exercised. The recently-rewritten system+user prompt (`satellite_edge_node/liquid_vlm_reasoner.py:122-148`), the `apply_chat_template` invocation, and the `_parse_local_response` happy path with a real model output are not under test. If the prompt is changed again, no test will catch a regression in JSON-extraction reliability beyond `_extract_json_object`'s implicit coverage. Worth adding at minimum a `_parse_local_response`-with-fixture-string test that feeds the JSON-shaped string the prompt asks for, plus a malformed-JSON fallback case.
- **`compute_triage(min_confidence=...)` non-default values are not directly exercised.** `tests/test_triage.py` only uses the default 0.45. The 0.25 floor used by `triage_label()` is exercised end-to-end via `test_telemetry_record_low_confidence_below_detector_floor_is_ignored`, but no test pins boundary behavior at exactly `min_confidence` (e.g. confidence equal to the threshold).
- **Streamlit rendering has no UI-level tests.** `app.py` and `ground_station_ui/app.py` are exercised only through their data-loader dependencies. The `_inject_css`, `_render_*` helpers, and HTML-escape paths in `app.py` are unverified. A boundary failure inside `_render_mission_controls` would not be caught.
- **No coverage tool is configured.** Adding `coverage run -m pytest && coverage report` would surface dead-code paths without changing CI.
- **`scripts/process_apad.py`, `scripts/train_real_model.py`, `scripts/provision_model.py`, `scripts/smoke_fetch_haryana.py`, `scripts/check_model_ready.py` (CLI surface)** have no direct tests of their `main()` exit codes. Only `check_model_ready.check_model_ready()` (the underlying function) is tested.
- **`kilnwatch/datasets/adapters/sustainbench_geobench.py`** has no test. The deleted `apad_pakistan_igp.py` adapter had none either; if APAD is reintroduced, add a test for the adapter's `convert()` contract.

---

*Testing analysis: 2026-05-09*

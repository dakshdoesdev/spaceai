# Plan 01-03 Summary: Crop Payload Proof

## Completed

- Added payload-side byte accounting so alert and dropped payload JSON can be inspected without relying only on telemetry.
- Added top-level alert `action` so the triage decision is visible directly in payload JSON.
- Stabilized payload encoding so `byte_accounting.json_payload_bytes` matches the final encoded JSON size.
- Extended the readable PNG crop test to prove:
  - `reset_queue=True` is used for the fresh demo run.
  - `crop_ref` points to a real non-empty crop file.
  - detector truth metadata remains visible in payload JSON.
  - payload byte accounting matches telemetry fields.

## Verification

- `python -m unittest tests.test_satellite_edge_bandwidth -q`
  - Passed: 8 tests.
- `python -m unittest tests.test_yolo_detector tests.test_model_readiness_eval tests.test_satellite_edge_bandwidth -q`
  - Passed: 18 tests, 1 skipped.
- `rg -n "original_payload_bytes|json_payload_bytes|crop_payload_bytes|transmitted_payload_bytes|bandwidth_saved_bytes|crop_ref" satellite_edge_node/payloads.py tests/test_satellite_edge_bandwidth.py`
  - Confirmed payload implementation and test coverage for byte accounting and crop references.

## Notes

- `pytest` is not installed in the system Python or project `.venv`, so verification used `unittest`.
- The crop proof uses a real readable PNG fixture generated in the test with Pillow.

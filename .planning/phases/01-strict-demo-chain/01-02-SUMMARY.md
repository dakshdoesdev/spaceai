# Plan 01-02 Summary: Detector Readiness And Strict Failure

## Completed

- Added CLI-level regression coverage proving `--detector yolo` exits loudly when model weights are missing and fallback is not explicitly requested.
- Verified existing readiness preflight reports `ready_for_strict_yolo=false`, missing weights, and missing `ultralytics` as structured JSON.
- Confirmed existing detector and payload metadata preserve explicit simulation/fallback truth fields.
- Confirmed judge-facing docs state baseline mode is simulated, strict YOLO requires local weights plus `ultralytics`, and `--allow-baseline-fallback` is simulated fallback.

## Verification

- `python -m unittest tests.test_yolo_detector tests.test_model_readiness_eval tests.test_satellite_edge_bandwidth -q`
  - Passed: 18 tests, 1 skipped.
- `python scripts/check_model_ready.py --json`
  - Exited non-zero as expected for this machine.
  - Reported missing `models/brick_kiln_yolo.pt` and missing `ultralytics`.

## Notes

- `pytest` is not installed in the system Python or project `.venv`, so verification used the repo's `unittest`-compatible test modules.
- No dependency install was performed; strict YOLO remains an honest optional local setup path.

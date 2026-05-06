# Phase 1, Plan 01: Fresh Queue Reset

**Status:** Completed

## Work completed

- Added `reset_queue` support to `simulate_orbital_pass()`.
- Added the `--reset-queue` CLI flag for fresh demo runs.
- Implemented scoped queue cleanup for generated payload JSON, `telemetry.jsonl`, and the runner-owned `crops/` directory only.
- Added regression coverage proving reset removes stale queue artifacts while preserving raw inputs, metadata sidecars, and unrelated queue files.
- Updated `docs/demo_data_pipeline.md` with the fresh demo command and reset scope.

## Files modified

- `satellite_edge_node/orbital_pass.py`
- `tests/test_satellite_edge_bandwidth.py`
- `docs/demo_data_pipeline.md`

## Verification

- `python -m unittest tests.test_satellite_edge_bandwidth -q` passed.
- `python -m pytest tests/test_satellite_edge_bandwidth.py -q` could not run because `pytest` is not installed in system Python.
- `.venv/bin/python -m pytest tests/test_satellite_edge_bandwidth.py -q` could not run because `pytest` is not installed in `.venv`.

## Notes

The reset implementation deliberately does not delete raw tile inputs, dataset files, source files, docs, or arbitrary queue subdirectories.

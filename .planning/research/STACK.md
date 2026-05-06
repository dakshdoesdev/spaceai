# Stack Research: KilnWatch

**Date:** 2026-05-06

## Recommendation

Keep the current Python-first stack and harden it for a final hackathon demo instead of migrating frameworks.

## Current Stack

- Python 3.11+ package structure in `pyproject.toml`
- Streamlit dashboard in `app.py`
- Satellite edge simulation in `satellite_edge_node/`
- Domain helpers in `kilnwatch/`
- SimSat/local ingestion helpers in `kilnwatch/ingestion/`
- Dataset validation in `kilnwatch/datasets/`
- File-backed queue in `transmission_queue/`
- Tests under `tests/`

## Final Sprint Stack Decisions

- Use Streamlit as the only supported demo UI.
- Treat `kilnwatch.ground_station` as the canonical queue reader.
- Keep YOLO as the strict real-detector path only if weights and `ultralytics` are present.
- Keep baseline detector as simulation and label it everywhere.
- Use local JSON/JSONL artifacts for the satellite-ground contract.
- Use SimSat Sentinel endpoints only when actually exercised and documented.

## Do Not Add

- A database.
- A cloud backend.
- A second dashboard framework.
- Liquid LFM integration unless it can be implemented and proved before submission.

## Evidence

- `.planning/codebase/STACK.md`
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/CONCERNS.md`
- Liquid AI event materials and official wildfire architecture pattern


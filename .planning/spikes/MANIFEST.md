# Spike Manifest

## Idea

Pre-deadline spikes for the KilnWatch hackathon submission (Liquid AI × DPhi Space, *AI in Space*). Spikes target the highest-leverage gaps remaining after Phase 1–2 are complete: getting **real DPhi/Sentinel imagery** into the demo path, getting **VRSBench (the cookbook's reference dataset) accessible**, optionally improving Liquid output with structured generation, and (out-of-budget) matching the cookbook's `llama-server` deployment runtime.

## Requirements

(established as user choices emerge during spiking)

- Spikes must not break the working baseline demo (5/5 alerts with real Liquid reasoning, 99.1% bandwidth saved, 116× compression).
- Spikes must finish or land in a clean PARTIAL state before submission deadline.
- Spike artifacts go in `.planning/spikes/NNN-name/` and the SimSat clone goes in `~/Work/tries/SimSat/`, NOT inside the SpaceAI repo.
- DPhi imagery, if reachable, must be ingested honestly — telemetry must distinguish DPhi-served vs Roboflow-fixture tiles.

## Spikes

| #   | Name                          | Type     | Validates                                                                                              | Verdict | Tags |
|-----|-------------------------------|----------|--------------------------------------------------------------------------------------------------------|---------|------|
| 001 | simsat-live-tile              | standard | Given DPhi `DPhi-Space/SimSat` running locally, when we hit `/data/image/sentinel`, then we receive a real Sentinel-2 tile that can drive `orbital_pass.py`. | **VALIDATED ✓** | dphi, sentinel, deadline-critical |
| 004 | vrsbench-eval-sample          | standard | Given the cookbook's reference dataset `xiang709/VRSBench` on HuggingFace, when we pull the eval annotations, then we have format and adapter for running our pipeline on real EO imagery. | PARTIAL ⚠ | vrsbench, cookbook-alignment, satellite-imagery |
| 002 | outlines-structured-liquid    | standard | Given `outlines.from_transformers` wrapping LFM2.5-VL-450M, when we generate against a Pydantic schema, then output is decode-time-guaranteed valid JSON matching the cookbook `car-maker-identification` pattern. | INVALIDATED ✗ (Python 3.14 wheel) | liquid, structured-generation, optional |
| 003 | gguf-llama-server-liquid      | standard | Given LFM2.5-VL-450M GGUF + llama-server, when we serve it locally, then we match the cookbook `wildfire-prevention` deployment runtime. | OUT-OF-BUDGET | liquid, gguf, llama-cpp, deployment |

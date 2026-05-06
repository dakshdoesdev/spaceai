# Technical Honesty

## Safe Claims

- KilnWatch is a local simulation of satellite-side brick-kiln triage.
- The satellite-edge simulation writes compact payloads and telemetry into `transmission_queue/`.
- The ground-station dashboard reads only downlinked queue/log artifacts.
- The dashboard proves payload reduction math from telemetry.
- The current detector path is a baseline placeholder unless detector metadata says a real YOLO mode was used.

## Unsafe Claims

- Do not claim real satellite deployment.
- Do not claim Liquid/LFM fine-tuning is complete.
- Do not claim validated brick-kiln detection accuracy without evaluation artifacts.
- Do not claim placeholder tile bytes are real Sentinel imagery.
- Do not claim crop payloads are real image crops until crop files are generated.

## Current Real Components

- `satellite_edge_node/` local orbital-pass simulation.
- `transmission_queue/` downlinked payload representation.
- `telemetry_logs/` sample fallback telemetry.
- `app.py` ground-station dashboard.
- Manifest validation and tests.
- YOLO detector integration path and strict mode.
- Model readiness and evaluation scripts.

## Current Simulated Components

- Baseline detector.
- Placeholder raw tiles.
- Compliance-risk scoring.
- Local edge runtime.
- Crop/full-review references.
- Any detection result produced without `models/brick_kiln_yolo.pt` and strict YOLO mode.

## Future Integrations

- YOLO object detector for brick-kiln bounding boxes.
- Real local Sentinel-style tiles.
- Crop generation.
- Liquid/LFM risk summarization or multimodal review.
- Hardware-aware latency and memory profiling.

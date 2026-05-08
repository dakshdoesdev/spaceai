# Technical Honesty

## Safe Claims

- KilnWatch is a local simulation of satellite-side brick-kiln triage.
- The satellite-edge simulation writes compact payloads and telemetry into `transmission_queue/`.
- The ground-station dashboard reads only downlinked queue/log artifacts.
- The dashboard proves payload reduction math from telemetry (~99% bandwidth saved on the demo set).
- **Strict YOLO** is real only when `scripts/check_model_ready.py --json` passes and telemetry says `detector_is_real=true`.
- **Liquid LFM2-VL** is real only when `--reasoner liquid-local` succeeds and each alert payload's `vlm_reasoning.reasoner_is_real == true`. The base model is `LiquidAI/LFM2.5-VL-450M` running locally via `transformers.AutoModelForImageTextToText`.
- **Structured Liquid crop reasoning** is real only when `vlm_reasoning.reasoner_output_valid == true`, `vlm_reasoning.reasoned_over == "crop"`, and `vlm_reasoning.crop_path_used` points to the generated crop artifact. If the Liquid call succeeds but parsing fails, telemetry must say `reasoner_output_valid=false` and include `raw_output_excerpt`.
- Baseline detector mode, fallback mode, and `liquid-mock` reasoner mode are simulated and labelled so in telemetry.

## Unsafe Claims

- Do not claim real satellite deployment.
- Do not claim Liquid/LFM **fine-tuning** is complete — the model is the open base, no domain fine-tune was performed.
- Do not claim validated brick-kiln detection accuracy without evaluation artifacts (no `docs/latest_evaluation.json` exists).
- Do not claim placeholder `.tile` bytes are real Sentinel imagery.
- Do not claim crop payloads are real image crops until crop files are generated.
- Do not claim Liquid emitted structured reasoning when `reasoner_output_valid=false`; say "Liquid call succeeded, structured parse failed."
- Do not claim Roboflow/demo fixture images are Haryana or Sentinel imagery without separate provenance.
- Do not present `liquid-mock` output as real Liquid inference.

## Current Real Components

- `satellite_edge_node/` local orbital-pass simulation.
- `transmission_queue/` downlinked payload representation.
- `telemetry_logs/` sample fallback telemetry.
- `app.py` ground-station dashboard (single-page mission view, post-2026-05-09 rewrite).
- Manifest validation and tests.
- **Strict YOLO real detector** — `models/brick_kiln_yolo.pt` + `ultralytics`, no silent fallback.
- **Liquid LFM2-VL onboard reasoning** — `LiquidAI/LFM2.5-VL-450M` via Transformers, real inference over generated crop artifacts when the crop exists; structured `vlm_reasoning` is claimed only when `reasoner_output_valid=true`.
- **DPhi SimSat live Sentinel-2 ingest** (verified 2026-05-09) — `docker compose up` brings the official `DPhi-Space/SimSat` simulator up locally; the historical Sentinel endpoint serves real Sentinel-2 RGB tiles for arbitrary IGP coordinates; `satellite_edge_node.orbital_pass` ingests them unchanged. Caveat: SimSat sim container requires a `MAPBOX_ACCESS_TOKEN` env var to start (any non-empty value works for the Sentinel-only path).
- Model readiness and evaluation scripts.
- Real crop generation for readable local image tiles with detector bounding boxes.
- Queue-only ground-station boundary, enforced by `kilnwatch.ground_station._safe_crop_path`.

## Current Simulated Components

- Baseline detector (filename hint / sidecar metadata).
- Placeholder `.tile` raw tiles in `data/raw_tiles/`.
- Compliance-risk band heuristics (medium/high derived from confidence + signals; not a calibrated risk score).
- Local edge runtime (CPU laptop, not satellite hardware).
- Any detection result produced without `models/brick_kiln_yolo.pt` and strict YOLO mode.
- `liquid-mock` reasoner output (explicit simulated demo path).
- `liquid-ollama` reasoner backend (path exists in code; broken on Ollama 0.17.5 LFM2 support — use `liquid-local`).

## Future Integrations

- ~~DPhi SimSat `/data/image/sentinel` as the primary tile source~~ — **integration is real** (verified 2026-05-09). The remaining work is making it the **primary** source for the demo, which requires the next item.
- **Liquid LFM2-VL + YOLO fine-tune on Sentinel-domain brick-kiln labels.** Current YOLO weights (trained on Roboflow optical morphology at ~0.3-1 m/pixel) produce 0 detections on Sentinel-2 RGB at ~10 m/pixel in the local SimSat check. Cookbook recipe at `Liquid4All/cookbook/examples/satellite-vlm` (VRSBench + leap-finetune on Modal H100s) is the exact path.
- Hardware-aware latency, memory, and energy profiling for satellite-edge constraints.
- Run-IDs and per-run telemetry directories under `transmission_queue/runs/` (currently flat).
- llama-server / llama.cpp deployment runtime (cookbook `wildfire-prevention` parallel).

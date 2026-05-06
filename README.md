# KilnWatch

**One-line pitch:** KilnWatch simulates a satellite edge node that detects brick-kiln risk onboard and downlinks only the JSON alerts, crops, or full imagery that are worth the bandwidth.

KilnWatch was built for the Liquid AI x DPhi Space "AI in Space" hackathon. The important idea is not just "detect brick kilns." The differentiator is bandwidth-aware satellite-side triage: process imagery in orbit, decide what matters, and prove at the ground station how many bytes were avoided.

## Problem

Brick kilns across Panipat, Haryana, Delhi NCR, and the wider Indo-Gangetic Plain can create serious air-quality and compliance problems. Regulators and researchers need scalable monitoring, but manual inspection is slow and repeated satellite imagery can be expensive to move from orbit to ground.

For a space AI system, the constraint is not only detection accuracy. The satellite has limited compute, storage, and downlink bandwidth. Sending every raw tile is wasteful when many tiles contain no actionable kiln signal.

## Why Satellites

Satellites can repeatedly observe kiln clusters, nearby settlements, agricultural edges, and regional activity patterns. A satellite-first workflow is useful because it can cover large areas where ground inspection is hard to scale.

KilnWatch starts with Panipat/Haryana/NCR as the demo geography because the compliance problem is personally understandable, regionally relevant, and a practical target for later dataset collection.

## Why Onboard Edge Triage

Ground-based batch pipelines usually assume imagery has already been downlinked. KilnWatch instead asks what the satellite should transmit in the first place.

The onboard node can choose:

- `IGNORE`: do not downlink a tile when no kiln or low-confidence signal is present.
- `JSON_ALERT_ONLY`: send a compact alert for likely low-risk detections.
- `CROP_OR_REVIEW`: send a small crop/reference for medium or review-worthy risk.
- `FULL_DOWNLINK`: send full imagery only for high-confidence, high-risk cases.

This matches the AI-in-space constraint: raw imagery is expensive, compact telemetry is cheap.

## Architecture

```text
data/raw_tiles/
  placeholder or future Sentinel-style local tiles
        |
        v
satellite_edge_node/
  baseline detector for explicit simulation
  YOLO detector for local real weights
  Liquid/LFM reasoning extension later
        |
        v
transmission_queue/
  compact JSON alerts
  drop records
  optional real crop files under crops/
  telemetry.jsonl
        |
        v
app.py or ground_station_ui/
  reads only downlinked payloads and telemetry
  shows bandwidth saved
  shows received alerts
```

Ground-station boundary: the dashboard must read only from `transmission_queue/` and telemetry logs. It should not inspect raw satellite tiles directly.

## How It Works

1. `satellite_edge_node/orbital_pass.py` scans local raw tile files.
2. `satellite_edge_node/detectors.py` selects either explicit baseline simulation or strict YOLO mode.
3. `satellite_edge_node/payloads.py` builds a downlinked payload, writes real crops when a readable image and bbox exist, and records telemetry.
4. `transmission_queue/telemetry.jsonl` records original bytes, JSON bytes, crop bytes, transmitted bytes, saved bytes, detector truth flags, latency, and action.
5. `app.py` behaves like a ground station and visualizes only what reached the queue/logs.

## What Is Real Today

- Local satellite-edge simulation path exists.
- Transmission queue and telemetry logs exist.
- Ground-station dashboard proves byte-reduction math from telemetry.
- Dataset manifest format and validator exist.
- Tests enforce bandwidth accounting and ground-station boundary behavior.
- The dashboard labels sample/baseline status instead of hiding it.
- YOLO mode fails loudly unless local weights and dependencies are present, unless explicit fallback is requested.

## What Is Simulated Today

- The current detector is a baseline placeholder, not a trained brick-kiln model.
- Demo raw tiles are placeholder local files, not validated Sentinel imagery.
- Crop payloads only exist when a readable image tile and bbox allow an actual crop file to be written.
- The edge node runs locally, not on satellite hardware.
- Liquid/LFM integration is planned, not completed.

## Local Demo

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the ground-station dashboard:

```bash
streamlit run app.py
```

Open the displayed local URL, usually `http://localhost:8501`.

## Run Orbital Pass

Baseline mode keeps the demo stable and is explicitly simulated. It uses
sidecar metadata or filename hints, so it is useful for architecture and
bandwidth tests, not for real model claims:

```bash
python -m satellite_edge_node.orbital_pass \
  --raw-tiles data/raw_tiles \
  --transmission-queue transmission_queue \
  --detector baseline
```

YOLO mode is the real detector integration path. Put a locally trained
Ultralytics `.pt` brick-kiln detector at `models/brick_kiln_yolo.pt`.
Install the optional local inference package if needed:

```bash
pip install ultralytics
```

Then run:

```bash
python -m satellite_edge_node.orbital_pass \
  --raw-tiles data/raw_tiles \
  --transmission-queue transmission_queue \
  --detector yolo \
  --model-path models/brick_kiln_yolo.pt
```

If the weights or `ultralytics` package are unavailable, YOLO mode fails by
default. This prevents simulated detections from being mistaken for real AI
inference.

If you need the demo to continue while clearly marking the run as fallback
simulation, opt in explicitly:

```bash
python -m satellite_edge_node.orbital_pass \
  --raw-tiles data/raw_tiles \
  --transmission-queue transmission_queue \
  --detector yolo \
  --model-path models/brick_kiln_yolo.pt \
  --allow-baseline-fallback
```

Fallback telemetry sets `detector_mode=fallback`, `detector_is_real=false`,
`simulated=true`, `fallback_used=true`, and includes `fallback_reason`.

Then refresh the dashboard. The top metrics should show processed raw bytes, downlinked bytes, ignored tiles, received alerts, and bandwidth saved.

## Validate Manifests

Validate the sample dataset manifest:

```bash
python scripts/validate_manifest.py datasets/kilnwatch/manifests/sample_demo_manifest.jsonl
```

Run tests:

```bash
python -m unittest discover -s tests -p 'test*.py'
```

If `pytest` is installed, this repo also supports:

```bash
python -m pytest -q
```

## Model Status

Current status:

- YOLO integration code exists in `satellite_edge_node/yolo_detector.py`.
- The expected real detector weights path is `models/brick_kiln_yolo.pt`.
- This repo currently does not include confirmed trained brick-kiln weights.
- If `models/brick_kiln_yolo.pt` is missing, real detector mode is unavailable.
- Baseline mode remains available for architecture and bandwidth demos only.

Check readiness:

```bash
python scripts/check_model_ready.py
```

Machine-readable readiness:

```bash
python scripts/check_model_ready.py --json
```

The model training and evaluation path is documented in `docs/model_training.md`.

## How To Train

Train a small Ultralytics model on Kaggle, Colab, or local hardware after preparing a license-compatible YOLO dataset:

```bash
pip install ultralytics
yolo detect train \
  model=yolov8n.pt \
  data=/path/to/brick_kiln_data.yaml \
  imgsz=640 \
  epochs=50 \
  batch=16 \
  project=kilnwatch_runs \
  name=brick_kiln_yolov8n
```

For a slightly stronger run, use `yolov8s.pt`. Do not copy external datasets into this repo unless the license allows it.

## How To Place Weights

After training, copy the best checkpoint to:

```bash
mkdir -p models
cp kilnwatch_runs/brick_kiln_yolov8n/weights/best.pt models/brick_kiln_yolo.pt
```

Weights should not be committed unless size and license allow redistribution.

## How To Run Strict YOLO Mode

Strict mode fails instead of falling back to baseline:

```bash
python -m satellite_edge_node.orbital_pass \
  --raw-tiles data/raw_tiles \
  --transmission-queue transmission_queue \
  --detector yolo \
  --model-path models/brick_kiln_yolo.pt
```

If this command fails because weights or `ultralytics` are missing, real detection is not available yet.

## How To Run Evaluation

Sample baseline evaluation:

```bash
python scripts/evaluate_detector.py \
  --manifest datasets/kilnwatch/manifests/baseline_sample_eval_manifest.jsonl \
  --telemetry transmission_queue/telemetry.jsonl
```

Real YOLO evaluation after strict YOLO mode:

```bash
python scripts/evaluate_detector.py \
  --manifest datasets/kilnwatch/manifests/panipat_demo_manifest.jsonl \
  --telemetry transmission_queue/telemetry.jsonl \
  --output docs/latest_evaluation.json
```

Metrics produced:

- number of tiles,
- positives and negatives,
- detected positives,
- false positives,
- false negatives,
- average confidence,
- raw/downlinked/bandwidth-saved bytes,
- detector mode used,
- overclaim warning.

## What Counts As Real Proof

Real proof requires:

- real local weights at `models/brick_kiln_yolo.pt`,
- `ultralytics` installed,
- orbital pass run with `--detector yolo` and no fallback flag,
- telemetry with YOLO detector metadata and no fallback reason,
- non-sample manifest rows backed by real labeled imagery,
- evaluation output from `scripts/evaluate_detector.py`.

If any of those are missing, call the result baseline, simulated, or sample.

## Model Roadmap

Fastest practical MVP path:

1. Keep the baseline detector as an explicit simulation mode.
2. Train or obtain a license-compatible YOLO-style object detector for brick-kiln bounding boxes.
3. Place weights at `models/brick_kiln_yolo.pt` and run strict YOLO mode.
4. Emit detector truth metadata so the dashboard can distinguish real, simulated, and fallback runs.
5. Use Liquid/LFM later for risk reasoning, alert summarization, or vision-language review after detector candidate generation.

Do not claim Liquid fine-tuning or deployed model validation until the repo contains the files and evaluation evidence.

## Dataset Plan

Near-term dataset work:

- Use Panipat/Haryana/NCR coordinates for the personal demo story.
- Prefer Sentinel-style local image tiles and YOLO labels.
- Track every sample through `datasets/kilnwatch/manifests/*.jsonl`.
- Mark demo/sample rows clearly as sample, not ground truth.
- Use external datasets only when license and redistribution terms are clear.

Useful future candidates are documented in `docs/external_resources.md`.

## Evaluation Metrics

KilnWatch should be judged on two layers:

- Detection: precision, recall, mAP, false positives near non-kiln industrial sites, and geographic generalization.
- Space triage: raw bytes processed, bytes downlinked, bytes saved, compression ratio, ignored tiles, JSON-alert count, crop/full-review count, and inference latency.

The current demo proves the second layer on local telemetry. It does not yet prove robust detection accuracy.

## Limitations

- No real satellite deployment.
- No trained/validated YOLO model is wired yet.
- Current raw tile fixtures are placeholders.
- The dashboard proves payload reduction math, not environmental enforcement outcomes.
- Compliance risk scoring is still heuristic and needs validation.

## Future Work

- Add trained YOLO weights and validated threshold settings.
- Generate crop payloads from real Sentinel-style image tiles during review events.
- Replace placeholder tiles with local Sentinel-style samples.
- Calibrate thresholds using validated labels.
- Add Liquid/LFM risk reasoning once detector candidates are reliable.
- Package a reproducible demo run with fixed telemetry for judging.

## Credits And License Notes

This repo is a hackathon MVP by `dakshdoesdev`.

External brick-kiln datasets and papers should be treated as references unless their licenses allow use. Do not copy GPL/AGPL or unclear-license upstream code directly into this repo. Borrow concepts, cite sources, and write original integration code.

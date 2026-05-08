# Brick-Kiln YOLO Model Path

## Status

KilnWatch has a strict YOLO integration path. Real detection is unavailable until this file exists and loads with a brick-kiln class:

```text
models/brick_kiln_yolo.pt
```

Do not commit model weights unless the license and file size are acceptable. Keep large or restricted weights outside git and document how to place them locally.

## Data Requirements

Use only datasets you are allowed to use:

- Manually prepared Haryana, India tiles with your own labels.
- License-compatible public brick-kiln datasets.
- SentinelKilnDB or APAD-style resources only after checking license and redistribution constraints.

Do not copy unclear-license or GPL/AGPL code/data into this repo. Keep external downloads manual unless the user explicitly confirms the dataset and license.

## Train On Kaggle, Colab, Or Local

Use Ultralytics YOLO nano/small for the MVP:

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

For a slightly stronger model:

```bash
yolo detect train \
  model=yolov8s.pt \
  data=/path/to/brick_kiln_data.yaml \
  imgsz=640 \
  epochs=75 \
  batch=16 \
  project=kilnwatch_runs \
  name=brick_kiln_yolov8s
```

Expected training output:

```text
kilnwatch_runs/brick_kiln_yolov8n/weights/best.pt
```

Copy or symlink that file locally:

```bash
mkdir -p models
cp kilnwatch_runs/brick_kiln_yolov8n/weights/best.pt models/brick_kiln_yolo.pt
```

## Check Model Readiness

```bash
python scripts/check_model_ready.py
```

Expected missing-model output:

```text
real detector unavailable: weights not found at models/brick_kiln_yolo.pt
```

JSON form:

```bash
python scripts/check_model_ready.py --json
```

## Run Strict YOLO Mode

Strict mode fails if weights or `ultralytics` are missing:

```bash
python -m satellite_edge_node.orbital_pass \
  --raw-tiles data/final_demo_tiles \
  --transmission-queue transmission_queue \
  --detector yolo \
  --model-path models/brick_kiln_yolo.pt \
  --require-crops \
  --reset-queue
```

Fallback mode is acceptable for demo plumbing, but it is not real detection:

```bash
python -m satellite_edge_node.orbital_pass \
  --raw-tiles data/raw_tiles \
  --transmission-queue transmission_queue \
  --detector yolo \
  --model-path models/brick_kiln_yolo.pt \
  --allow-baseline-fallback
```

If fallback happens, telemetry records `detector_mode=fallback`, `detector_is_real=false`, `simulated=true`, `fallback_used=true`, and `fallback_reason`.

## Run Evaluation

Sample baseline evaluation:

```bash
python scripts/evaluate_detector.py \
  --manifest datasets/kilnwatch/manifests/baseline_sample_eval_manifest.jsonl \
  --telemetry transmission_queue/telemetry.jsonl
```

Real YOLO evaluation after strict mode:

```bash
python scripts/evaluate_detector.py \
  --manifest datasets/kilnwatch/manifests/haryana_demo_manifest.jsonl \
  --telemetry transmission_queue/telemetry.jsonl \
  --output docs/latest_evaluation.json
```

## What Counts As Real Proof

Real proof requires all of these:

- `models/brick_kiln_yolo.pt` exists locally.
- `ultralytics` is installed.
- `python scripts/check_model_ready.py --json` reports `kiln_class_available=true`.
- orbital pass was run with `--detector yolo` and no `--allow-baseline-fallback`.
- telemetry contains YOLO detector metadata, `detector_is_real=true`, and no fallback reason.
- every alert with a crop reference points to a non-empty file under `transmission_queue/crops/`.
- manifest rows are real labeled examples, not `sample_demo_not_ground_truth`.
- evaluation reports detection metrics and bandwidth metrics on those rows.

Anything else should be labeled simulated, baseline, or sample.

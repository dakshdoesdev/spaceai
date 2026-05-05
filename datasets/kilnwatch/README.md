# KilnWatch Dataset

KilnWatch is a tile-level dataset for brick kiln detection and compliance triage from locally saved Sentinel-2 image tiles. It is designed for a compact VLM prompt pipeline today and future fine-tuning later.

This MVP intentionally avoids kiln type classification. Each row answers whether a tile contains likely brick kiln evidence, a coarse kiln-count bucket, activity signal, settlement proximity, compliance risk, and label confidence.

## Folder Layout

```text
datasets/kilnwatch/
  images/
    train/       # locally saved labeled image tiles for training
    dev/         # labeled tiles for prompt/model tuning checks
    test/        # held-out labeled tiles for final eval
    unlabeled/   # tiles waiting for manual review
  labels/
    train.jsonl
    dev.jsonl
    test.jsonl
    seed_template.jsonl
  docs/
    dataset_schema.md
    labeling_guidelines.md
  scripts/
    validate_labels.py
```

## JSONL Row Shape

Each JSONL line is one tile annotation:

```json
{
  "tile_id": "kw_train_0001",
  "image_path": "images/train/kw_train_0001.png",
  "split": "train",
  "location_hint": "optional district/region or bbox id",
  "source": "Sentinel-2 local tile",
  "label": {
    "kiln_detected": true,
    "kiln_count_estimate": "1-3",
    "activity_signal": "active",
    "near_settlement": true,
    "compliance_risk": "high",
    "confidence": 0.82
  },
  "notes": "optional short labeling note"
}
```

Only `tile_id`, `image_path`, `split`, and `label` are required. Optional metadata is kept small so rows remain compatible with VLM prompting, supervised fine-tuning, and simple eval scripts.

## Suggested Split Plan

For 50-200 hand-labeled tiles:

- `train`: 70%, mixed positives and negatives.
- `dev`: 15%, used to tune prompts, thresholds, and label rules.
- `test`: 15%, held out until the pipeline is stable.

Keep negatives in every split. Include rural land, farms, settlements, roads, rivers, and industrial-looking areas without kilns. If tiles are geographically clustered, split by area where possible so neighboring near-duplicates do not leak across train/dev/test.

## Validate

Run:

```bash
python datasets/kilnwatch/scripts/validate_labels.py datasets/kilnwatch/labels/*.jsonl
```

Add `--check-images` once Agent 1 has saved the tile images:

```bash
python datasets/kilnwatch/scripts/validate_labels.py --check-images datasets/kilnwatch/labels/train.jsonl datasets/kilnwatch/labels/dev.jsonl datasets/kilnwatch/labels/test.jsonl
```

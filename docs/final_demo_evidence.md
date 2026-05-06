# Final Demo Evidence

Generated on 2026-05-06 with strict YOLO against real JPG fixtures in `data/final_demo_tiles/`.

## Command

```bash
python -m satellite_edge_node.orbital_pass \
  --raw-tiles data/final_demo_tiles \
  --transmission-queue transmission_queue \
  --detector yolo \
  --model-path models/brick_kiln_yolo.pt \
  --confidence-threshold 0.05 \
  --reset-queue
```

## Readiness

`python scripts/check_model_ready.py --json` reported:

| Field | Value |
| --- | --- |
| `weights_exist` | true |
| `ultralytics_available` | true |
| `ready_for_strict_yolo` | true |
| `status` | real detector available |

## Metrics

| Metric | Value |
| --- | ---: |
| Test images processed | 9 |
| Detector mode | YOLO |
| Detector is real? | true |
| Simulated? | false |
| Raw bytes processed | 711,843 |
| Transmitted bytes | 15,983 |
| Compression ratio | 44.54x |
| Bandwidth saved | 695,860 bytes |
| Detections | 5 |
| Crops generated | 5 |
| Label-positive images | 9 |
| Image-level true positives | 5 |
| Image-level false positives | 0 |
| Image-level false negatives | 4 |

## Crop Artifacts

Every non-null `crop_ref` in `transmission_queue/*.json` points to one of these non-empty files:

| Crop | Size |
| --- | ---: |
| `1117_jpg.rf.e581fd205529da567728b01a3566949a_crop.png` | 3,980 bytes |
| `1120_jpg.rf.0d3b75f8941d82aac47011a519bc7e65_crop.png` | 4,360 bytes |
| `A_103_jpg.rf.ae0ce5a735cd1271818c69491b65d4f3_crop.png` | 774 bytes |
| `A_84_jpg.rf.941c858b50d8cc84fefc1332a9baeb18_crop.png` | 691 bytes |
| `T_120_jpg.rf.da358af5d9623308ca663833beca7bf6_crop.png` | 937 bytes |

## Detection Rows

| Tile | Confidence | Risk | Crop |
| --- | ---: | --- | --- |
| `1117_jpg.rf.e581fd205529da567728b01a3566949a` | 0.0974 | medium | `transmission_queue/crops/1117_jpg.rf.e581fd205529da567728b01a3566949a_crop.png` |
| `1120_jpg.rf.0d3b75f8941d82aac47011a519bc7e65` | 0.0638 | medium | `transmission_queue/crops/1120_jpg.rf.0d3b75f8941d82aac47011a519bc7e65_crop.png` |
| `A_103_jpg.rf.ae0ce5a735cd1271818c69491b65d4f3` | 0.2455 | medium | `transmission_queue/crops/A_103_jpg.rf.ae0ce5a735cd1271818c69491b65d4f3_crop.png` |
| `A_84_jpg.rf.941c858b50d8cc84fefc1332a9baeb18` | 0.0518 | medium | `transmission_queue/crops/A_84_jpg.rf.941c858b50d8cc84fefc1332a9baeb18_crop.png` |
| `T_120_jpg.rf.da358af5d9623308ca663833beca7bf6` | 0.0621 | medium | `transmission_queue/crops/T_120_jpg.rf.da358af5d9623308ca663833beca7bf6_crop.png` |

## Caveats

- The final strict YOLO demo uses real JPG fixtures, not placeholder `.tile` files.
- The `0.05` confidence threshold is chosen for demo recall on this tiny validation slice and should be stated in the video.
- This is an image-level smoke evaluation, not a full object-level mAP report.

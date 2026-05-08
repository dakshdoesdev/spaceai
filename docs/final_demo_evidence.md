# Final Demo Evidence

Generated on 2026-05-08 with strict YOLO against readable JPG fixtures in `data/final_demo_tiles/`.

## Command

```bash
python -m satellite_edge_node.orbital_pass \
  --raw-tiles data/final_demo_tiles \
  --transmission-queue transmission_queue \
  --detector yolo \
  --model-path models/brick_kiln_yolo.pt \
  --confidence-threshold 0.25 \
  --reasoner disabled \
  --require-crops \
  --reset-queue
```

## Readiness

`python scripts/check_model_ready.py --json` reported:

| Field | Value |
| --- | --- |
| `weights_exist` | true |
| `ultralytics_available` | true |
| `model_loads` | true |
| `class_names` | `Brick-Kiln` |
| `kiln_class_available` | true |
| `ready_for_strict_yolo` | true |
| `model_sha256` | `0ff8c4a2de92e96de85f480eec1d097e1067de1d7ca431c6046b92b72d9be64f` |

## Metrics

| Metric | Value |
| --- | ---: |
| Images processed | 14 |
| Alert payload JSON files | 5 |
| Dropped tiles | 9 |
| Detector is real? | true |
| Simulated? | false |
| Fallback used? | false |
| Raw bytes processed | 1,108,441 |
| Transmitted bytes | 5,420 |
| Compression ratio | 204.51x |
| Bandwidth saved | 1,103,021 bytes |
| Bandwidth saved percent | 99.51% |
| Crop errors | 0 |

## Queue Contract

`transmission_queue/` contains only the 5 alert JSON payloads, 5 crop PNGs, and `telemetry.jsonl`.

Dropped tiles are represented in telemetry only. The ground station has no reason to read `data/final_demo_tiles/`.

## Crop Artifacts

Every alert `crop_ref` points to a non-empty file under `transmission_queue/crops/`.

| Crop | Size |
| --- | ---: |
| `A_103_jpg.rf.ae0ce5a735cd1271818c69491b65d4f3_crop.png` | 357 bytes |
| `A_84_jpg.rf.941c858b50d8cc84fefc1332a9baeb18_crop.png` | 460 bytes |
| `T_120_jpg.rf.da358af5d9623308ca663833beca7bf6_crop.png` | 346 bytes |
| `T_50_jpg.rf.8ccc5ad765fde45052e681621e8d2d8a_crop.png` | 272 bytes |
| `UP_744_jpg.rf.104b6416eacec2bb6ce618394ea76e69_crop.png` | 294 bytes |

## Detection Rows

| Tile | Confidence | Risk | JSON bytes | Crop bytes |
| --- | ---: | --- | ---: | ---: |
| `A_103_jpg.rf.ae0ce5a735cd1271818c69491b65d4f3` | 0.4084 | medium | 739 | 357 |
| `A_84_jpg.rf.941c858b50d8cc84fefc1332a9baeb18` | 0.4791 | medium | 736 | 460 |
| `T_120_jpg.rf.da358af5d9623308ca663833beca7bf6` | 0.5175 | medium | 740 | 346 |
| `T_50_jpg.rf.8ccc5ad765fde45052e681621e8d2d8a` | 0.4550 | medium | 735 | 272 |
| `UP_744_jpg.rf.104b6416eacec2bb6ce618394ea76e69` | 0.2668 | medium | 741 | 294 |

## Caveats

- The demo uses local real JPG fixtures, not placeholder `.tile` files.
- These fixtures are detector/crop proof artifacts; do not claim they are Haryana or Sentinel imagery without separate provenance.
- This is not a deployed satellite payload.
- This is not a full object-level mAP evaluation.

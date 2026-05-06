# KilnWatch Demo Data Pipeline

KilnWatch should demo the satellite-side bandwidth-aware architecture with local files, not a paid map API. The data pipeline converts a small coordinate CSV into local tile files, sidecar detector metadata, and a manifest JSONL that passes the existing validator.

## Modes

### Real Demo Mode: SimSat

Use this when you have real tile bytes from a local, license-compatible source such as SimSat/Sentinel-2.

```bash
python scripts/fetch_demo_tiles.py \
  --mode simsat \
  --coordinates-csv datasets/kilnwatch/coordinates/panipat_demo_coordinates.csv \
  --tile-dir data/raw_tiles \
  --manifest datasets/kilnwatch/manifests/panipat_demo_manifest.jsonl
```

SimSat must be running locally, defaulting to `http://localhost:9005`. The script does not use Mapbox, Google Maps Static API, Sentinel Hub, or paid keys. If SimSat is not reachable, it exits with a message telling you to start SimSat or rerun in placeholder mode.

Real mode only accepts readable `.png`, `.jpg`, `.jpeg`, or `.tif` outputs. If SimSat returns non-image bytes, the script fails instead of silently creating fake imagery.

### Real Demo Mode: Local Image Import

Use this when you manually downloaded real, license-compatible image tiles and named each file after `tile_id`.

```bash
python scripts/fetch_demo_tiles.py \
  --mode local-import \
  --coordinates-csv datasets/kilnwatch/coordinates/panipat_demo_coordinates.csv \
  --local-image-dir data/manual_tiles \
  --tile-dir data/raw_tiles \
  --manifest datasets/kilnwatch/manifests/panipat_demo_manifest.jsonl
```

Expected local files:

```text
data/manual_tiles/panipat_positive_replace_001.png
data/manual_tiles/panipat_refinery_negative_001.jpg
```

Supported extensions: `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`. The script validates readability before writing the manifest.

### Sample Placeholder Mode

Use this when real imagery is not ready yet:

```bash
python scripts/fetch_demo_tiles.py \
  --mode placeholder \
  --coordinates-csv datasets/kilnwatch/coordinates/panipat_demo_coordinates.csv \
  --tile-dir data/raw_tiles \
  --manifest datasets/kilnwatch/manifests/panipat_demo_manifest.jsonl
```

Placeholder mode writes tiny `.tile` files and `.meta.json` sidecars. These are architecture fixtures only and are marked `sample_demo_not_ground_truth`, `data_mode=placeholder`, `is_placeholder=true`, and `is_real_imagery=false` in the manifest.

## Coordinate CSV Format

Required columns:

```csv
tile_id,lat,lon,region_name,expected_label,source,notes
```

Allowed `expected_label` values:

- Positive: `positive`, `kiln`, `brick_kiln`, `yes`, `1`, `true`
- Negative: `negative`, `no_kiln`, `control`, `false_positive_control`, `0`, `false`

Template files:

- `datasets/kilnwatch/coordinates/panipat_demo_coordinates.csv`
- `datasets/kilnwatch/coordinates/apad_coordinates_template.csv`
- `datasets/kilnwatch/coordinates/negative_controls_panipat_template.csv`

If you run the script with a missing CSV path, it writes a small sample CSV at that path and exits so you can edit it deliberately.

## APAD / Panipat Path

If you have a local APAD-style coordinate CSV, convert or rename columns into the KilnWatch CSV shape:

```csv
tile_id,lat,lon,region_name,expected_label,source,notes
apad_panipat_0001,29.390900,76.963500,Panipat Haryana,positive,apad_local_csv,"Local APAD/manual coordinate; keep license/source notes."
```

Do not assume an APAD GitHub URL or notebook works. Do not run notebooks that depend on Google Static Maps or Google Earth Engine for this MVP. Use local CSV rows and a local imagery source.

## Negative Controls

Include hard negatives in every demo/eval batch:

- Panipat Refinery / industrial false positive.
- Agricultural fields.
- Greenhouses/polyhouses.
- Warehouses, construction, and bare soil.
- Settlement-like areas without visible kilns.

## How Many Tiles

- Minimum MVP: 10 positive + 5 negative.
- Decent demo: 20 positive + 10 negative.
- Strong demo: 50 positive + 25 negative.

For a hackathon demo, prioritize geographic diversity around Panipat/Haryana/NCR and hard negatives that look kiln-like.

## Validate

```bash
python scripts/validate_manifest.py datasets/kilnwatch/manifests/panipat_demo_manifest.jsonl
```

For final demo claims, require image readability:

```bash
python scripts/validate_manifest.py --check-images datasets/kilnwatch/manifests/panipat_demo_manifest.jsonl
```

This command is expected to fail for placeholder `.tile` manifests. It should pass only after SimSat or local-import mode has produced real readable images.

Then run the satellite-side pass:

```bash
python -m satellite_edge_node.orbital_pass \
  --raw-tiles data/raw_tiles \
  --transmission-queue transmission_queue \
  --reset-queue
```

`--reset-queue` refreshes only generated queue artifacts in the selected transmission queue: top-level payload JSON files, `telemetry.jsonl`, and the runner-owned `crops/` directory. It does not delete raw tile inputs, dataset files, source code, or docs.

## Final Strict YOLO Demo Run

For the final video/submission proof, do not use placeholder `.tile` files. Use the real JPG fixtures copied into `data/final_demo_tiles/`.

```bash
python -m satellite_edge_node.orbital_pass \
  --raw-tiles data/final_demo_tiles \
  --transmission-queue transmission_queue \
  --detector yolo \
  --model-path models/brick_kiln_yolo.pt \
  --confidence-threshold 0.05 \
  --reset-queue
```

Expected evidence from the current final queue:

| Metric | Value |
| --- | ---: |
| Test images processed | 9 |
| Detector mode | YOLO |
| Simulated? | false |
| Raw bytes processed | 711,843 |
| Transmitted bytes | 15,983 |
| Compression ratio | 44.54x |
| Bandwidth saved | 695,860 bytes |
| Detections | 5 |
| Crops generated | 5 |
| Image-level false positives | 0 |
| Image-level false negatives | 4 |

All non-null `crop_ref` values in `transmission_queue/*.json` must point to non-empty files under `transmission_queue/crops/`.

### Detector Honesty Note
- baseline mode is simulated
- strict YOLO requires `models/brick_kiln_yolo.pt` and `ultralytics`
- `--allow-baseline-fallback` is an explicit simulated fallback, not real detection.

The ground station should read only `transmission_queue/` and telemetry outputs, never the raw tile folder.

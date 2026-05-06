# External Brick-Kiln Resources

This file tracks external resources that can improve KilnWatch without making false claims about owned ground truth. Do not copy upstream code or data into this repo unless its license and download terms clearly allow it.

## Integration Rules

- No paid API dependency.
- No Mapbox, Google Static Maps, Sentinel Hub, OpenAI, Anthropic, or Gemini keys.
- Prefer metadata adapters that transform user-downloaded files into `datasets/kilnwatch/manifests/*.jsonl`.
- Keep demo/sample rows clearly marked as sample/demo, not ground truth.
- Record manual download steps and license limits before using any external data.

## Internal Manifest Format

Each JSONL row is one tile or coordinate-level record:

```json
{
  "tile_id": "sample_demo_panipat_001",
  "image_path": "datasets/kilnwatch/images/demo/sample_demo_panipat_001.png",
  "lat": 29.3909,
  "lon": 76.9635,
  "source": "sample_demo_not_ground_truth",
  "split": "demo",
  "label": "sample_positive",
  "kiln_detected": true,
  "bbox": [120, 90, 220, 180],
  "confidence": 0.5,
  "notes": "Sample/demo row only. Not ground truth."
}
```

Required fields: `tile_id`, `image_path`, `lat`, `lon`, `source`, `split`, `label`, `kiln_detected`, `notes`.

Optional fields: `bbox`, `confidence`.

Allowed `split` values: `train`, `dev`, `val`, `test`, `seed`, `unlabeled`, `demo`, `external`.

## Resource Review

### rishabh-mondal/kdd24_brick_kilns

- URL: https://github.com/rishabh-mondal/kdd24_brick_kilns
- What it is: KDD 2024 brick-kiln detection work with notebooks for downloading, preprocessing, SSL experiments, and prediction.
- Useful data shape: image tiles and labels from Bangladesh/Delhi/India experiments.
- License status: no repository license file found through GitHub API during inspection. Treat as reference-only until clarified.
- Paid/API issue: README points to Google Static API download notebooks, so do not run those in KilnWatch.
- Adapter stance: stub only. Accepts manually prepared CSV/JSONL rows with local tile paths and lat/lon if a license-compatible export is provided.

### APAD2024/brickkilnscidata

- URL: https://github.com/APAD2024/brickkilnscidata
- What it is: code and data accompanying the Scientific Data Pakistan IGP brick-kiln dataset.
- Useful data shape: CSV/shapefile rows for 11,277 identified kilns with `id`, `lat`, `lon`, `type`, `state`, proximity, production, and emissions columns.
- License status: no repository license file found through GitHub API during inspection. The related Zenodo dataset is the better integration target.
- Paid/API issue: high-resolution notebook requires Google Static Maps API; low-resolution notebook requires Google Earth Engine authentication. Do not wire either into KilnWatch MVP.
- Adapter stance: coordinate/label adapter for local CSV exports only; no upstream code copied.

### rishabh-mondal/SENTINELKILNDB_NeurIPS_2025

- URL: https://github.com/rishabh-mondal/SENTINELKILNDB_NeurIPS_2025
- Dataset page: https://huggingface.co/datasets/SustainabilityLabIITGN/SentinelKilnDB
- What it is: Sentinel-2 OBB brick-kiln benchmark for South Asia.
- Useful data shape: Sentinel-2 RGB tiles, DOTA / YOLO-OBB / YOLO-AA label files, train/val/test splits.
- License status: repository README lists dataset license as CC BY-NC-SA 4.0. This is non-commercial and share-alike; verify hackathon/publishing compatibility before bundling data.
- Adapter stance: best fit for KilnWatch model/detection validation because it has Sentinel-2 imagery and bounding boxes. Adapter should map tile image path + OBB labels to `bbox`, `kiln_detected`, `label`, and split fields.

### Esri ArcGIS Brick-Kiln Detection Sample

- URL/status: no single clearly licensed public code/data repository was identified during inspection. Esri object-detection samples often depend on ArcGIS tooling or credits.
- Useful data shape: potentially object-detection samples or notebooks if a specific licensed sample is later found.
- License/API issue: ArcGIS Online analysis can consume credits, and ArcGIS software/tooling is outside the no-paid-API MVP.
- Adapter stance: no adapter beyond a placeholder until a concrete license-compatible sample URL is provided.

### Space to Policy Brick-Kiln Project

- Paper: https://arxiv.org/abs/2412.04065
- What it is: scalable brick-kiln detection and automatic compliance monitoring with geospatial data over Indo-Gangetic Plain states.
- Useful data shape: detections, kiln type/classification, compliance fields if released.
- License status: paper located; no clean downloadable dataset/code license confirmed in this pass.
- Adapter stance: reference for compliance-field design only until code/data release terms are confirmed.

### Eye in the Sky Brick-Kiln Paper/Code

- Paper: https://arxiv.org/abs/2406.10723
- What it is: brick-kiln detection and compliance monitoring framework using satellite imagery.
- Useful data shape: detection/compliance methodology; possible precursor to Space to Policy.
- License status: paper located; code/data availability not confirmed in this pass.
- Adapter stance: reference-only until a licensed dataset/code URL is found.

### Pakistan IGP Brick Kiln Dataset on Zenodo

- URL: https://zenodo.org/records/14038648
- DOI: 10.5281/zenodo.14038648
- What it is: geospatial mapping of brick kilns in Pakistan's IGP region.
- Useful data shape: CSV, GeoJSON, and shapefile; WGS84 coordinates; `id`, `lat`, `lon`, `state`, `type`, proximity fields, and emissions estimates.
- License status: Zenodo marks it as an open dataset; verify the exact license in the Zenodo metadata before redistribution.
- Adapter stance: very useful for coordinate-grounded positive examples and compliance/risk notes, but it does not provide local Sentinel-2 tile images by itself.

### GEO-Bench / SustainBench Brick Kiln Dataset

- SustainBench URL: https://github.com/sustainlab-group/sustainbench
- GEO-Bench HF URL: https://huggingface.co/datasets/GEO-Optim/geo-bench
- What it is: benchmark datasets including brick-kiln classification tasks.
- Useful data shape: classification samples rather than object-detection boxes.
- License status: SustainBench code is MIT; README says raw data is CC-BY-SA 4.0. GEO-Bench is on Hugging Face; verify per-dataset terms before download/use.
- Adapter stance: useful for image-level `kiln_detected` labels and split mapping. Less useful than SentinelKilnDB for bbox-aware triage.

## Most Useful First Integration

SentinelKilnDB is the strongest match for KilnWatch because it uses Sentinel-2 imagery, provides train/val/test splits, and includes oriented bounding boxes. Use it only after accepting CC BY-NC-SA 4.0 constraints and downloading the dataset manually from the official hosting page.


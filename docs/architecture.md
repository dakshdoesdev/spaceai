# KilnWatch Architecture

## Core Boundary

KilnWatch separates satellite-side processing from ground-station display.

The ground station must not inspect raw tile folders. It should only read:

- `transmission_queue/*.json`
- `transmission_queue/crops/*`
- `transmission_queue/telemetry.jsonl`
- `telemetry_logs/*.jsonl` as sample or external telemetry logs

## Data Flow

```text
Raw local tiles
  data/raw_tiles/
        |
        v
Satellite edge node
  satellite_edge_node/orbital_pass.py
  satellite_edge_node/yolo_detector.py
  satellite_edge_node/baseline_detector.py
  satellite_edge_node/payloads.py
        |
        v
Downlinked artifacts
  transmission_queue/*.json for alerts
  transmission_queue/crops/*.png for alert evidence
  transmission_queue/telemetry.jsonl
        |
        v
Ground station
  app.py
  ground_station_ui/
```

## Satellite Edge Node

The edge node simulates onboard processing:

- discovers local tile files,
- runs the detector path,
- builds compact alert payloads,
- writes downlink telemetry for every processed tile,
- writes dropped tiles as telemetry-only records by default,
- avoids transmitting raw tiles when risk is not high.

Current detector status is explicit per run:

- strict YOLO when `models/brick_kiln_yolo.pt` loads with a brick-kiln class,
- baseline simulation when `--detector baseline` is used,
- simulated fallback only when `--allow-baseline-fallback` is used.

The expected real model path is:

```text
models/brick_kiln_yolo.pt
```

Use `python scripts/check_model_ready.py --json` before claiming real detector availability.

## Ground Station

The dashboard reads queue/log files and computes:

- tiles processed onboard,
- raw bytes processed,
- downlinked bytes,
- bytes saved,
- bandwidth saved percentage,
- compression ratio,
- ignored tiles,
- JSON alerts,
- crop/full-review alerts,
- average inference latency.

It also displays received alert payloads and a cumulative raw-vs-downlinked line chart.

## Triage Decisions

```text
IGNORE
  no alert or low confidence

JSON_ALERT_ONLY
  likely kiln but low/medium risk; transmit compact JSON

CROP_OR_REVIEW
  medium/high risk; transmit crop or review reference

FULL_DOWNLINK
  high confidence and high compliance risk; transmit full imagery/reference
```

## Liquid/LFM Extension

Liquid/LFM is best added after detector candidates exist:

- summarize risk evidence,
- rank alerts for human review,
- reason over crop metadata,
- produce compliance-friendly alert language.

This is future work until implementation and tests exist.

# Pitfalls Research: KilnWatch

**Date:** 2026-05-06

## Critical Pitfalls

### Fake Dashboard Risk

If the dashboard looks good but reads demo fixtures or simulated baseline output without clear labeling, judges may dismiss the project as theater.

Prevention:
- Show detector mode and simulation status prominently.
- Include a technical honesty panel.
- Make crop links resolve to real files.
- Run a visible command before the dashboard demo.

### Overclaiming Liquid Track

The Liquid Track expects LFM2-VL/LFM2.5-VL usage, with fine-tuning encouraged. If KilnWatch does not integrate Liquid models, submit under General Track.

Prevention:
- State "No fine-tuning" honestly.
- Frame Liquid LFM as future work unless implemented.

### Placeholder Imagery Confusion

`.tile` fixture blobs must not be called Sentinel-2 imagery.

Prevention:
- Separate real demo images from placeholder fixtures.
- Mark manifest rows with sample/placeholder metadata.

### Silent Fallback

YOLO setup failure must not quietly become "real detection."

Prevention:
- Strict YOLO fails loudly.
- Any fallback sets `fallback_used=true`, `detector_is_real=false`, and visible dashboard labels.

### Mixed Telemetry Runs

Append-only telemetry can mix detector modes and stale tile IDs.

Prevention:
- Add or use a queue reset/run command for the final demo.
- Prefer fresh queue artifacts for the recorded walkthrough.


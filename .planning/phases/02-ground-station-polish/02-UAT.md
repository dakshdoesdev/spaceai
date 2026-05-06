---
status: testing
phase: 02-ground-station-polish
source:
  - 02-01-SUMMARY.md
  - 02-02-SUMMARY.md
started: 2026-05-06T23:10:57+05:30
updated: 2026-05-06T23:10:57+05:30
---

## Current Test

number: 1
name: Proof Status First Screen
expected: |
  Open the Streamlit dashboard. The first visible proof section is `Proof Status`, and it shows detector honesty using labels such as `STRICT YOLO REAL`, `BASELINE SIMULATION`, `FALLBACK USED`, or `SAMPLE DATA`. It also shows Liquid reasoner state as `LIQUID LFM REAL`, `LIQUID MOCK`, or `LFM DISABLED`, plus raw truth fields like detector mode, simulated, fallback, and reasoner metadata when available.
awaiting: user response

## Tests

### 1. Proof Status First Screen
expected: Open the Streamlit dashboard. The first visible proof section is `Proof Status`, and it shows detector honesty using labels such as `STRICT YOLO REAL`, `BASELINE SIMULATION`, `FALLBACK USED`, or `SAMPLE DATA`. It also shows Liquid reasoner state as `LIQUID LFM REAL`, `LIQUID MOCK`, or `LFM DISABLED`, plus raw truth fields like detector mode, simulated, fallback, and reasoner metadata when available.
result: [pending]

### 2. Mission Metrics Proof
expected: The dashboard shows `Mission Metrics` near the top with tiles processed, detections, crops generated, raw bytes, transmitted bytes, bandwidth saved, review alerts, and compression ratio from queue-visible telemetry.
result: [pending]

### 3. Edge-To-Ground Boundary Explanation
expected: The dashboard clearly states that raw images are processed onboard, only JSON/crop artifacts are downlinked, and the ground station reads queue only.
result: [pending]

### 4. Crop Review Evidence
expected: The `Crop Review` section shows a real crop image only when a non-empty crop file exists under the transmission queue. If no safe queue crop exists, it says `no real crop available` and does not invent a preview from a raw tile.
result: [pending]

### 5. Alerts And Mission Replay
expected: The dashboard still shows alert rows and mission replay controls after the proof panels, and replay updates metrics/alerts from telemetry without reading raw onboard image folders.
result: [pending]

### 6. Queue-Only Boundary Protection
expected: Ground-station code and tests reject crop references under `data/raw_tiles`, `data/final_demo_tiles`, `datasets/roboflow`, and placeholder `.tile` fixtures. The production dashboard surfaces do not directly reference raw/source image folders.
result: [pending]

### 7. Optional Liquid Reasoner CLI
expected: `--reasoner disabled` produces no fake Liquid claim, `--reasoner liquid-mock` writes simulated advisory JSON marked `reasoner_is_real=false`, and `--reasoner liquid-local` fails loudly if local Liquid dependencies/model support are missing.
result: [pending]

## Summary

total: 7
passed: 0
issues: 0
pending: 7
skipped: 0
blocked: 0

## Gaps

[none yet]

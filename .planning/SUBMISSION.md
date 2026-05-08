# KilnWatch — Hackathon Submission Draft

> **For:** Liquid AI × DPhi Space *AI in Space* hackathon (May 2026)
> **Track:** Liquid (Liquid LFM2-VL is real and central in the pipeline)
> **Status:** Draft — paste verbatim or trim per form field caps.

---

## One-line pitch (≤120 chars)

KilnWatch: satellite-edge AI triage that reduces brick-kiln monitoring downlink by 99% and runs Liquid LFM2-VL onboard.

## Project name

KilnWatch

## Track

Liquid Track. Liquid LFM2-VL-450M runs on-device as the reasoning layer between detector and alert.

## Problem statement

Brick kilns are widespread, polluting, and hard to monitor manually across the Indo-Gangetic Plain. Satellite imagery can help — but raw imagery is too large to blindly downlink and inspect at scale. Most demos assume the imagery has already reached the ground; in space, that bandwidth has already been spent. The real lever is onboard.

## Solution overview

KilnWatch moves the first decision into orbit. The pipeline:

1. A strict YOLO detector runs onboard and proposes candidate kiln regions per tile.
2. **Liquid LFM2-VL-450M reasons over each crop** and produces structured alert metadata (visual summary, risk reasoning, human-review flag, compliance-risk band).
3. A 4-tier triage layer (`IGNORE / JSON_ALERT_ONLY / CROP_OR_REVIEW / FULL_DOWNLINK`) picks the cheapest useful transmission.
4. Only compact JSON alerts plus crop evidence cross the downlink boundary.
5. The ground station reads only the transmission queue — never raw tiles — and accounts for every byte.

On the included demo set (14 real overhead brick-kiln tiles), the pipeline preserves **99.1% of raw bytes** (116× compression) and produces 5 alerts, every one carrying real Liquid LFM2-VL reasoning.

## Why must this run in space (use of space-based compute)?

Because if the imagery is already on the ground, the bandwidth has already been spent. The contribution is the *triage* layer that runs **before** downlink, not the detector itself. With a bandwidth-constrained downlink (typical of LEO Earth-observation constellations), an onboard 4-tier triage that can drop most tiles, transmit compact JSON for likely candidates, transmit cropped evidence for medium-risk candidates, and transmit full imagery only for high-confidence high-risk candidates is the right architecture.

The Liquid LFM2-VL layer adds the cheapest possible "second opinion" before the alert leaves the satellite — turning a bbox into a structured, human-readable alert that an analyst on the ground can act on without round-tripping the full image.

## How does Liquid LFM2-VL fit?

LFM2-VL is **the onboard reasoning layer**, not a decoration on top of the detector. After YOLO produces a candidate bbox + crop, Liquid:

1. Looks at the crop image plus detection metadata.
2. Returns structured JSON: `visual_summary`, `risk_reasoning`, `compliance_risk` band, `human_review_needed`, `confidence_note`.
3. That JSON becomes the alert payload's `vlm_reasoning` field.

The model is the open `LiquidAI/LFM2.5-VL-450M` running locally via `transformers.AutoModelForImageTextToText`. **No fine-tuning** was performed — the base model's general visual reasoning is what produces the alert content. We do not claim Liquid was domain-fine-tuned on brick kilns; we use the base model honestly.

## DPhi SimSat / satellite imagery usage

**KilnWatch ingests both Roboflow optical fixtures and live DPhi SimSat Sentinel-2 tiles.** End-to-end integration with the official `DPhi-Space/SimSat` simulator (`docker compose up`) is verified — the historical Sentinel endpoint serves real Sentinel-2 RGB tiles for arbitrary IGP coordinates, and our existing `satellite_edge_node.orbital_pass` ingests them unchanged with full provenance metadata in the per-tile sidecars.

Two demo paths, both honest:

1. **Roboflow optical fixtures** (`data/final_demo_tiles/`) — proves the detector + Liquid layer fire end-to-end. **5/5 alerts with real `vlm_reasoning`, 99% bandwidth saved, 100×+ compression.**
2. **DPhi SimSat live Sentinel-2** (`data/simsat_live_tiles/`) — proves the pipeline ingests real space data. Five IGP coordinates pulled (Panipat, Kurukshetra, Aligarh, Ludhiana, Dhaka outskirts) at 2024-11-15. **Pipeline correctly drops all 5 — 100% bandwidth saved, 0 false positives** — because current YOLO weights are trained on optical morphology at ~0.3-1 m/pixel, not Sentinel-2 RGB at ~10 m/pixel. This is the **expected** finding the cookbook's `examples/satellite-vlm` recipe is designed to fix via VRSBench fine-tuning on `leap-finetune` + Modal H100s. Pipeline architecture, queue boundary, ground-station accounting are unchanged across both imagery sources.

We do not claim Haryana ground-truth provenance for the Roboflow fixtures, and we do not claim a fine-tuned detector on Sentinel-2 imagery — both honestly disclosed in the dashboard's imagery-provenance panel and `docs/technical_honesty.md`.

See `.planning/spikes/001-simsat-live-tile/README.md` for the full reproduction log (clone command, compose env, exact endpoint params, byte-exact tile fetches).

## Hardest part

Three things, ranked:

1. **Boundary enforcement.** Making sure the ground station genuinely reads only the transmission queue, never raw tiles or telemetry from other sources. The queue-only reader is enforced in `kilnwatch/ground_station.py:_safe_crop_path` (rejects paths outside the queue) plus boundary tests.
2. **Detector honesty under failure modes.** Strict YOLO must fail loudly when weights are missing, baseline must be labelled simulated, fallback must be visible in telemetry — and the dashboard must surface all of this so a judge cannot mistake simulated output for real detection. Multiple metadata fields propagate per detection (`detector_is_real`, `simulated`, `fallback_used`) and the dashboard's chip system reflects them.
3. **Liquid integration on a 4 GB-VRAM machine.** Running LFM2.5-VL-450M locally via Transformers without OOM on consumer hardware, then making it produce structured JSON reliably, then attaching it to every CROP_OR_REVIEW alert in the payload schema.

## What runs out of the box

```bash
pip install -r requirements.txt
pip install ultralytics transformers
python scripts/check_model_ready.py --json
python -m satellite_edge_node.orbital_pass --raw-tiles data/final_demo_tiles \
  --detector yolo --reasoner liquid-local --require-crops --reset-queue
streamlit run app.py
```

Total: 5 commands. The dashboard opens with bandwidth-saved hero metric, 5 alerts each with crop + Liquid reasoning, and a diagnostics expander for raw payload inspection.

## What's honest

- ✅ Strict YOLO real detector, no silent fallback.
- ✅ Real on-device Liquid LFM2-VL inference per detector candidate.
- ✅ Real bbox-to-crop artifacts.
- ✅ Queue-only ground station boundary.
- ✅ Real byte accounting from on-disk file sizes.

## What's not

- ❌ We do not claim real satellite deployment.
- ❌ We do not claim Liquid LFM2-VL fine-tuning on brick-kiln imagery.
- ❌ We do not claim Sentinel-2 or DPhi-API provenance for the demo tiles.
- ❌ We do not claim a validated brick-kiln detection accuracy on Sentinel-domain data.

## Repo

<https://github.com/dakshdoesdev/spaceai>

## Demo video

3-minute walkthrough at [video link]. See `docs/demo_script.md` for the verbatim script.

## References

- Brooks et al., "Scalable deep learning to identify brick kilns and aid regulatory capacity", *PNAS*, 2021.
- Mondal et al., "Space to Policy: Scalable Brick Kiln Detection and Automatic Compliance Monitoring with Geospatial Data", *ACM COMPASS*, 2024.
- Mondal et al., "SentinelKilnDB: A Large-Scale Dataset for Oriented Bounding Box Brick Kiln Detection", *NeurIPS*, 2025.
- Denby and Lucia, "Orbital Edge Computing: Nanosatellite Constellations as a New Class of Computer System", *ASPLOS*, 2020.

---

## Form-field cheat sheet

| Field | Pull from |
|---|---|
| Project name | "KilnWatch" |
| One-line pitch | First section above |
| Track | Liquid Track |
| Problem | Section above |
| Solution overview | Section above + 4-tier triage table |
| Space-compute rationale | "Why must this run in space" section |
| LFM2-VL usage | "How does Liquid LFM2-VL fit" section |
| DPhi imagery usage | "DPhi SimSat / satellite imagery usage" section (honest disclosure) |
| Hardest part | Three numbered items |
| Setup commands | "What runs out of the box" |
| Honest claims / not | Bottom two lists |

# KilnWatch — 3-Minute Demo Script (Liquid Track)

## 0:00 – 0:20  Hook

> "This is KilnWatch. **It moves the first decision into orbit.** Instead of downlinking every satellite image and detecting brick kilns on the ground, the satellite scans each tile, decides what is worth transmitting, and sends only the evidence. With our demo set, that is a 99% bandwidth reduction — and every alert that does come down carries Liquid LFM2-VL reasoning."

## 0:20 – 0:45  Problem

> "Brick kilns are widespread, polluting, hard to monitor. Satellites can help, but raw imagery is too large to blindly transmit and inspect. Most demos assume the imagery is already on the ground — but in space, the bandwidth has already been spent. The real lever is onboard."

## 0:45 – 1:30  Strict orbital pass + Liquid

Run on screen:

```bash
python scripts/check_model_ready.py --json
python -m satellite_edge_node.orbital_pass \
  --raw-tiles data/final_demo_tiles \
  --transmission-queue transmission_queue \
  --detector yolo \
  --reasoner liquid-local \
  --require-crops --reset-queue
```

Say:

> "Strict YOLO mode — if the weights or Ultralytics aren't there, the run fails loudly. No silent fallback. The detector runs across 14 tiles, finds 5 candidate brick kilns, and for each candidate **Liquid LFM2-VL-450M runs onboard** to produce a structured alert: visual summary, risk reasoning, whether human review is needed."

## 1:30 – 1:50  Transmission queue

Run:

```bash
find transmission_queue -maxdepth 2 -type f | sort
```

Say:

> "This is the entire downlink. Five JSON alerts, five crop PNGs, one telemetry stream. Total: under ten kilobytes. The ground station never opens the raw tile folder."

## 1:50 – 2:30  Dashboard

Run:

```bash
streamlit run app.py
```

Walk the screen:

> "Hero metric: 99.1% bandwidth saved, 116× compression. Detector chip: STRICT YOLO REAL. Reasoner chip: LIQUID LFM2-VL · LIVE. Imagery provenance is on screen — these are open-source brick-kiln tiles, not Sentinel or DPhi live, and we say that.
>
> Each alert card has the cropped evidence, the YOLO confidence, and Liquid's reasoning right there: what the model sees, why it does or doesn't look concerning, and whether a human should take a closer look. That's the Liquid layer doing useful work — turning a bbox into a structured human-readable alert."

## 2:30 – 2:50  Honest caveat

> "What we don't claim: real satellite deployment, fine-tuned Liquid weights, Sentinel-domain accuracy. The detector is the open-base YOLO trained on optical brick-kiln imagery; Liquid is the base 450M model. The next step is fine-tuning on DPhi SimSat Sentinel tiles — the architecture, queue boundary, and ground-station accounting do not change."

## 2:50 – 3:00  Close

> "KilnWatch proves the satellite-edge intelligence pattern: detect onboard, reason onboard with Liquid, downlink only the evidence, and make the ground station account for every byte."

---

## Cheat sheet — exact lines to memorize

- **Hero number:** "99.1% bandwidth saved. 116× compression. Five real alerts."
- **Why orbit:** "If you've downlinked the image, the bandwidth is already spent."
- **Liquid is doing what:** "LFM2-VL runs onboard, on each detector candidate, and produces structured alert reasoning."
- **What we won't fake:** "No fine-tune. No Sentinel claim. The architecture is the contribution."

## Pre-flight checklist (run 5 minutes before recording)

```bash
# 1. Pull anything other lanes pushed
git status -s

# 2. Reset the queue and run the full pipeline once so the dashboard opens with proof
python -m satellite_edge_node.orbital_pass \
  --raw-tiles data/final_demo_tiles --detector yolo \
  --reasoner liquid-local --require-crops --reset-queue

# 3. Confirm 5 alerts have real Liquid reasoning
python -c "
import json, glob
real = sum(1 for p in glob.glob('transmission_queue/*.json')
           for d in [__import__('json').load(open(p))]
           if d.get('vlm_reasoning',{}).get('reasoner_is_real'))
print(f'Real Liquid alerts: {real} / 5')
"

# 4. Boot the dashboard
streamlit run app.py
```

If the Liquid count is < 5, rerun step 2 once more — first runs of `transformers.AutoModelForImageTextToText` can miss the first 1–2 inferences while the model warms up.

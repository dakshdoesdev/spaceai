# KilnWatch 2-3 Minute Demo Script

## 0:00-0:20 Personal Hook

"I am showing KilnWatch, a hackathon project focused on brick-kiln compliance monitoring around Panipat, Haryana, and the Delhi NCR region. This is a real regional problem: kilns can contribute to pollution and compliance risk, but checking every location manually does not scale."

## 0:20-0:45 Problem

"Most satellite AI demos assume all imagery has already reached the ground. In space, that assumption is expensive. A satellite may observe many tiles, but downlink bandwidth is limited, so sending every raw tile wastes capacity."

## 0:45-1:10 Satellite-Side Triage

"KilnWatch simulates an onboard satellite edge node. It processes tiles locally, decides whether a kiln signal is actionable, and only downlinks what is needed: nothing, a compact JSON alert, a crop/review packet, or a full tile for high-risk cases."

## 1:10-1:30 Show Orbital Pass Command

Run:

```bash
python -m satellite_edge_node.orbital_pass \
  --raw-tiles data/raw_tiles \
  --transmission-queue transmission_queue
```

Say:

"This command simulates an orbital pass. The edge node reads local tile files, runs the current detector path, writes telemetry, and places only downlinked payloads into `transmission_queue/`."

## 1:30-1:45 Show Transmission Queue

Run:

```bash
ls -lh transmission_queue
sed -n '1,3p' transmission_queue/telemetry.jsonl
```

Say:

"The transmission queue is the ground-visible artifact. It contains compact JSON payloads and telemetry, not a blind dump of every raw satellite tile."

## 1:45-2:20 Show Dashboard

Run:

```bash
streamlit run app.py
```

Say:

"This is the ground station. The top metrics show how many tiles were processed onboard, how many raw bytes were considered in orbit, how many bytes were actually downlinked, and the percentage saved. The chart compares cumulative raw bytes against downlinked bytes, which is the core proof of the project."

## 2:20-2:40 Show Honesty Panel

"The dashboard also labels the current mode. If this is sample data or the baseline detector, it says so. I am not claiming this is deployed on a real satellite, and I am not claiming a fully validated model yet."

## 2:40-3:00 Final Impact

"The final direction is to replace the baseline detector with a YOLO-style brick-kiln detector and later add Liquid/LFM reasoning for risk review. The project contribution is the space architecture: detect and triage onboard, downlink only what matters, and prove the bandwidth savings at the ground station."


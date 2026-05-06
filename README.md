# KilnWatch

**One-line pitch:** KilnWatch simulates a satellite edge node that detects brick-kiln risk onboard and downlinks only the JSON alerts, crops, or full imagery that are worth the bandwidth.

KilnWatch was built for the Liquid AI x DPhi Space "AI in Space" hackathon. The important idea is not just "detect brick kilns." The differentiator is bandwidth-aware satellite-side triage: process imagery in orbit, decide what matters, and prove at the ground station how many bytes were avoided.

## Problem

Brick kilns across Panipat, Haryana, Delhi NCR, and the wider Indo-Gangetic Plain can create serious air-quality and compliance problems. Regulators and researchers need scalable monitoring, but manual inspection is slow and repeated satellite imagery can be expensive to move from orbit to ground.

For a space AI system, the constraint is not only detection accuracy. The satellite has limited compute, storage, and downlink bandwidth. Sending every raw tile is wasteful when many tiles contain no actionable kiln signal.

## Why Onboard Edge Triage

Ground-based batch pipelines usually assume imagery has already been downlinked. KilnWatch instead asks what the satellite should transmit in the first place.

The onboard node can choose:
- `IGNORE`: do not downlink a tile when no kiln or low-confidence signal is present.
- `JSON_ALERT_ONLY`: send a compact alert for likely low-risk detections.
- `CROP_OR_REVIEW`: send a small crop/reference for medium or review-worthy risk.
- `FULL_DOWNLINK`: send full imagery only for high-confidence, high-risk cases.

This matches the AI-in-space constraint: raw imagery is expensive, compact telemetry is cheap.

## Architecture

```text
data/raw_tiles/
  placeholder or future Sentinel-style local tiles
        |
        v
satellite_edge_node/
  YOLO detector for local real weights
  optional Liquid LFM crop-level reasoner
        |
        v
transmission_queue/
  compact JSON alerts
  drop records
  optional real crop files under crops/
  telemetry.jsonl
        |
        v
app.py or ground_station_ui/
  reads only downlinked payloads and telemetry
  shows bandwidth saved
```

---

## 🛠 Technical Honesty & Model Scope

**What KilnWatch demonstrates:**
KilnWatch demonstrates a complete Orbital Edge Architecture proof-of-concept. We successfully trained a YOLO triage engine that identifies brick kiln morphology. By simulating satellite-side inference—converting raw image tiles into compact JSON telemetry and targeted crops—KilnWatch achieves a simulated downlink bandwidth reduction of >99% while maintaining automated compliance alerts.

**Model vs. Mission Architecture Constraints:**
The core innovation of KilnWatch is the **bandwidth triage architecture** (JSON downlink vs. raw imagery). To validate the object detector's ability to recognize kiln morphology, our model (`brick_kiln_yolo.pt`) was trained on a high-resolution optical dataset (Roboflow, CC BY 4.0).
The Roboflow dataset serves as our **detector proof-of-concept**, while our Streamlit ground-station demonstrates the **telemetry and triage pipeline**. For a production orbital deployment, this specific model file would be swapped for weights trained natively on multi-spectral Sentinel-2 arrays (e.g., using the SentinelKilnDB framework). We do not claim zero-shot Sentinel-2 10m detection with these weights.

**YOLO vs. optional Liquid LFM reasoning:**
YOLO is the localization stage. It finds brick-kiln candidates and produces bounding boxes/crops. Liquid LFM is optional second-stage crop-level structured reasoning that can add advisory JSON (`visual_summary`, `risk_reasoning`, `compliance_risk`, `human_review_needed`, and model metadata) after YOLO or the explicit baseline detector has already produced a candidate.

Reasoner modes:
- `disabled` (default): no Liquid reasoning is run and no `vlm_reasoning` claim is added.
- `liquid-mock`: simulated Liquid-style advisory JSON for demo wiring only; it is marked `reasoner_is_real=false`.
- `liquid-local`: attempts to run `LiquidAI/LFM2.5-VL-450M` locally with compatible Transformers/Pillow/model access. Missing dependencies or model loading failures fail loudly and do not fall back to mock.

No Liquid LFM fine-tuning is claimed unless fine-tuning code, dataset evidence, and integration proof are actually added.

## 📊 Data Sources & Provenance

To ensure perfect open-source compliance and provenance transparency, the dataset used to train the underlying YOLO morphology engine is explicitly attributed:

*   **Dataset Name:** Brick Kiln Detection Dataset
*   **Version:** v13 (Updated August)
*   **Creator:** Avinash Mehta
*   **URL:** `https://universe.roboflow.com/avinash-mehta/brick-kiln-detection`
*   **License:** CC BY 4.0 (Creative Commons Attribution 4.0 International)
*   **Image Count:** 419 images (baseline)
*   **Classes:** 1 (`Brick-Kiln`)
*   **Annotation Format:** YOLOv8

## 🧪 Demo Data Plan & False Positive Testing

Our final demo uses a hybrid transmission queue to prove the model hasn't just memorized the training data and can effectively triage edge cases.

**Positive Kilns (15–20 instances):**
*   *Model Proof:* Extracted directly from the Roboflow test split to guarantee high-confidence hits demonstrating UI functionality.
*   *Geography Proof:* Manually sourced Panipat/Sonipat test crops demonstrating geographic generalization.

**Negative Controls (10–15 instances):**
To prove the model evaluates *morphology* (shape/shadow) and not just *spectral color* (brown pixels), the demo queue deliberately tests against the following categories:
1.  **Refinery/Industrial:** IOCL Panipat Refinery. Tests against circular storage tanks, cooling towers, and long smokestack shadows.
2.  **Agricultural Fields:** Karnal/Panipat fallow fields. Tests against the exact same ochre/brown spectral signature of barren, excavated earth.
3.  **Bare Soil/Construction:** Highway expansion/Sector 25 construction. Tests against disturbed earth without the Bull's Trench oval shape.
4.  **Settlement:** Dense housing in Purkhas/Panipat. Tests against clustered rectangular rooftops that mimic modern Zigzag kilns.
5.  **Warehouses:** Manesar logistics hubs. Tests against massive rectangular tin roofs matching the footprint of large kilns.
6.  **Greenhouse/Polyhouse:** Sonipat agricultural zones. Tests against long, continuous rectangular structures.

*Note: All items flowing through the Streamlit dashboard contain an explicit `source_provenance` tag labeling their origin.*

---

## Local Demo Instructions

Install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install ultralytics
```

Run the ground-station dashboard:
```bash
streamlit run app.py
```

Run the Strict YOLO Orbital Pass:
```bash
python -m satellite_edge_node.orbital_pass \
  --raw-tiles data/final_demo_tiles \
  --transmission-queue transmission_queue \
  --detector yolo \
  --model-path models/brick_kiln_yolo.pt \
  --reasoner disabled
```

Run Strict YOLO with simulated Liquid-style reasoning:
```bash
python -m satellite_edge_node.orbital_pass \
  --raw-tiles data/final_demo_tiles \
  --transmission-queue transmission_queue \
  --detector yolo \
  --model-path models/brick_kiln_yolo.pt \
  --reasoner liquid-mock
```

Run Strict YOLO with local Liquid LFM reasoning:
```bash
python -m satellite_edge_node.orbital_pass \
  --raw-tiles data/final_demo_tiles \
  --transmission-queue transmission_queue \
  --detector yolo \
  --model-path models/brick_kiln_yolo.pt \
  --reasoner liquid-local
```

---

## 📚 References & Citations

**Pollution & Compliance Context:**
1. **Guttikunda, S. K., et al. (2021).** *"Air quality, emissions, and source contributions in the Indo-Gangetic Plain."* (Establishes kilns as the 2nd largest industrial coal consumer, contributing 8–14% of regional PM2.5).
2. **Brooks, J., et al. (2021).** *"Scalable deep learning to identify brick kilns and aid regulatory capacity."* PNAS. (Proves the regulatory crisis: millions live within illegal proximity to kilns).

**Satellite Detection Viability:**
3. **Mondal, R., et al. (2024).** *"Space to Policy: Scalable Brick Kiln Detection and Automatic Compliance Monitoring with Geospatial Data."* ACM COMPASS. (Validates object detection for mapping >30,000 kilns in the IGP).
4. **Mondal, R., et al. (2025).** *"SentinelKilnDB: A Large-Scale Dataset for Oriented Bounding Box Brick Kiln Detection."* NeurIPS. (Validates that Sentinel-2's 10m resolution is sufficient to capture the 150m footprint of traditional kilns).

**The Downlink Bottleneck & Orbital Compute:**
5. **European Space Agency (ESA).** *"PhiSat-1 Mission Report (2020)."* (Pioneered Orbital Edge Computing using onboard chips to filter useless imagery before downlink).
6. **Denby, B., & Lucia, B. (2020).** *"Orbital Edge Computing: Nanosatellite Constellations as a New Class of Computer System."* ASPLOS. (Outlines the severe power/bandwidth constraints of CubeSats).
7. **Center for Security and Emerging Technology (CSET).** *"AI on the Edge of Space."* (Quantifies the bottleneck: processing objects onboard and sending metadata payloads reduces bandwidth usage by >90%).
8. **Gómez, A., & Meoni, G. (2023).** *"Tackling the Satellite Downlink Bottleneck with Federated Onboard Learning of Image Compression."* CVF. (Further academic proof that telemetry JSONs and smart crops are the required future of Earth Observation).

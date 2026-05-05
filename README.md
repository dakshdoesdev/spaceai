# SpaceAI - KilnWatch 🛰️🧱

**KilnWatch** is an on-board satellite imagery triage system designed to optimize bandwidth for environmental compliance monitoring. Specifically, it focuses on identifying and assessing brick kilns in Sentinel-2 imagery, making real-time decisions about which data is critical enough to downlink.

## 🌟 Overview

Satellite downlink bandwidth is a precious resource. KilnWatch implements a "Triage on the Edge" strategy:
1. **Detect:** Scans incoming satellite tiles for brick kilns.
2. **Assess:** Evaluates compliance risk (e.g., proximity to protected areas, operational status).
3. **Triage:** Decides whether to send the **Full Tile**, a **Targeted Crop**, or a **JSON Alert** based on bandwidth constraints and detection confidence.

## 🚀 Key Features

- **Bandwidth-Aware Downlink:** Intelligently saves >90% bandwidth by sending metadata-only alerts for low-risk detections.
- **Compliance Scoring:** Logic-based risk assessment for environmental monitoring.
- **Interactive Dashboard:** A Streamlit-powered interface to visualize triage decisions and bandwidth savings.
- **SimSat Integration:** Modular client for interfacing with simulated satellite data providers.

## 🧠 Triage Logic

KilnWatch uses a confidence/risk matrix to determine the `TriageDecision`:

| Confidence | Risk Score | Decision | Payload | Description |
| :--- | :--- | :--- | :--- | :--- |
| < 45% | Any | **IGNORE** | 0 MB | No kiln or low-confidence kiln signal. |
| > 85% | > 75% | **FULL DOWNLINK** | ~12 MB | High-confidence kiln with high compliance risk. |
| > 45% | > 45% | **CROP OR REVIEW** | ~1.2 MB | Kiln detected with medium/high risk; send crop. |
| > 45% | < 45% | **JSON ALERT ONLY** | ~4 KB | Kiln likely, but risk is low enough for metadata only. |

## 🛠️ Tech Stack

- **Language:** Python 3.x
- **Frontend:** Streamlit
- **Data:** Sentinel-2 Satellite Imagery (GeoJSON/SVG/JSONL)
- **Deployment:** Container-ready

## 📁 Project Structure

- `app.py`: Streamlit visualization dashboard.
- `kilnwatch/triage.py`: The core triage engine (Decision Logic).
- `kilnwatch/ingestion/`: Data acquisition and SimSat client implementation.
- `datasets/kilnwatch/`: Sample tiles and labels for development and testing.
- `config/regions/`: Target AOI (Area of Interest) configurations.

## 📄 Sample Prediction JSON

The system expects a JSON file in `datasets/kilnwatch/labels/` with the same stem as the image tile.

```json
{
  "schema_version": "kilnwatch.prediction.v0",
  "tile_id": "kilnwatch_demo_tile_001",
  "image_path": "datasets/kilnwatch/images/dev/kilnwatch_demo_tile_001.svg",
  "kiln_detected": true,
  "compliance_risk_score": 0.86,
  "detections": [
    {
      "class": "brick_kiln",
      "confidence": 0.91,
      "bbox_xyxy": [285, 198, 580, 388]
    }
  ],
  "risk_factors": [
    "elongated kiln-like oval structure",
    "dark plume signature downwind"
  ]
}
```

## 🚦 Getting Started

### 1. Installation

```bash
pip install -r requirements.txt
```

### 2. Run the Dashboard

Visualize how KilnWatch makes downlink decisions:

```bash
streamlit run app.py
```

### 3. Fetch New Data (Requires SimSat)

```bash
python scripts/smoke_fetch_panipat.py
```

---
*Developed for SpaceAI - Monitoring our planet from above.*

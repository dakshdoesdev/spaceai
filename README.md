# KilnWatch

**Satellite-edge intelligence that reduces brick-kiln monitoring bandwidth by deciding onboard what evidence is worth transmitting.**

Built for the Liquid AI × DPhi Space *AI in Space* hackathon (April–May 2026).

KilnWatch simulates a satellite-edge pipeline: a strict YOLO detector finds candidate brick kilns in raw tiles, **Liquid LFM2-VL** reasons over each crop, and only compact JSON alerts plus crop evidence are downlinked. The ground station receives ~99% less than the raw tile volume — and reads only what the satellite chose to transmit.

```
raw onboard imagery   →  YOLO (real, strict)  →  Liquid LFM2-VL  →  JSON + crop  →  ground station
   1.1 MB / 14 tiles                                                  9.5 KB total      (116× compression)
```

---

## 1. The problem

Brick kilns are widespread, polluting, and hard to monitor manually. Satellite imagery can help, but raw imagery is too large to blindly transmit and inspect at scale.

## 2. The old approach

Capture satellite image. Downlink everything. Run detection on the ground.

The bandwidth is already spent.

## 3. KilnWatch's approach

Move the **first decision** into orbit. The satellite scans each tile, detects possible kiln structures with a real YOLO model, asks Liquid LFM2-VL whether the candidate looks credible, and chooses the cheapest useful transmission:

| Decision | When | What is downlinked |
|---|---|---|
| `IGNORE` | no kiln signal | telemetry only — no payload |
| `JSON_ALERT_ONLY` | kiln likely, low risk | compact metadata JSON |
| `CROP_OR_REVIEW` | kiln + medium/high risk | JSON + the cropped evidence + Liquid's reasoning |
| `FULL_DOWNLINK` | high confidence + high risk | JSON + Liquid's reasoning + the full tile |

The ground station never reads raw tiles; it reads only the transmission queue.

## 4. Why it must run onboard

If the image is already downlinked, the bandwidth is already spent. Onboard AI reduces what *leaves* the satellite in the first place. With the included demo fixtures the pipeline preserves **99.1% of raw bytes** (116× compression) — and the alerts it does transmit carry Liquid VLM reasoning, not just a class label.

## 5. Where Liquid fits (Liquid Track)

LFM2-VL is the **lightweight visual reasoning layer** between the detector and the alert. The detector proposes candidate kiln regions; Liquid reasons over the crop and metadata to produce structured alert content per detection:

```json
"vlm_reasoning": {
  "visual_summary":      "...",      // what the model sees in the crop
  "risk_reasoning":      "...",      // why it does or doesn't look concerning
  "compliance_risk":     "low|medium|high",
  "human_review_needed": true,
  "confidence_note":     "...",
  "reasoner_is_real":    true,
  "model_name":          "LiquidAI/LFM2.5-VL-450M"
}
```

Liquid is not a decoration on top of YOLO; it is the reasoning step that turns a bbox into a structured alert. With Liquid disabled the system still works — but the alert is detector-only.

## 6. The proof

The ground station does not read raw images. It reads only `transmission_queue/*.json`, `transmission_queue/telemetry.jsonl`, and `transmission_queue/crops/*.png`. That lets us prove:

- bytes saved (raw vs downlinked)
- alert count and per-alert confidence
- crop evidence is present for every CROP_OR_REVIEW alert
- detector mode is real (`STRICT YOLO REAL`) or simulated (`BASELINE`/`FALLBACK`), never ambiguous
- Liquid reasoner mode is real (`LIQUID LFM2-VL · LIVE`) or disabled, never ambiguous

---

## Run the demo

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install ultralytics transformers      # YOLO + Liquid local

# Verify weights and dependencies are ready
python scripts/check_model_ready.py --json

# Orbital pass — produces transmission_queue/*.json + crops + telemetry
python -m satellite_edge_node.orbital_pass \
  --raw-tiles data/final_demo_tiles \
  --transmission-queue transmission_queue \
  --detector yolo \
  --reasoner liquid-local \
  --require-crops --reset-queue

# Ground station — reads only the queue
streamlit run app.py
```

Honest expectation: the orbital pass takes ~2–4 minutes the first time it loads `LiquidAI/LFM2.5-VL-450M` (~900 MB download then CPU inference). Subsequent runs reuse the cache.

### Optional: run on real DPhi SimSat Sentinel-2 imagery

```bash
# 1. Clone and start the official DPhi simulator
git clone https://github.com/DPhi-Space/SimSat ~/Work/tries/SimSat
cd ~/Work/tries/SimSat
MAPBOX_ACCESS_TOKEN=dummy_for_local_testing docker compose up -d --build

# 2. Pull a few IGP Sentinel-2 tiles via the historical endpoint
cd /path/to/SpaceAI
python - <<'PY'
import requests, json, time
from pathlib import Path
out = Path("data/simsat_live_tiles"); out.mkdir(parents=True, exist_ok=True)
for name, lat, lon in [
    ("haryana_panipat", 29.39, 76.97),
    ("haryana_kurukshetra", 29.97, 76.88),
    ("up_aligarh", 27.88, 78.07),
    ("punjab_ludhiana", 30.91, 75.85),
    ("bangladesh_dhaka_n", 23.95, 90.40),
]:
    r = requests.get("http://localhost:9005/data/image/sentinel",
                     params={"lat": lat, "lon": lon,
                             "timestamp": "2024-11-15T10:00:00Z",
                             "size_km": 5.0, "return_type": "png"},
                     timeout=30)
    r.raise_for_status()
    p = out / f"{name}_2024-11-15.png"; p.write_bytes(r.content)
    (out / f"{p.stem}.png.meta.json").write_text(json.dumps({
        "tile_id": p.stem, "source": "DPhi-Space SimSat",
        "endpoint": "/data/image/sentinel",
        "lat": lat, "lon": lon, "is_real_imagery": True,
        "imagery_provenance": "Sentinel-2 via DPhi SimSat",
    }, indent=2))
    print(f"{name}: {len(r.content)} bytes")
PY

# 3. Run the orbital pass on the SimSat tiles into a separate queue
python -m satellite_edge_node.orbital_pass \
  --raw-tiles data/simsat_live_tiles \
  --transmission-queue transmission_queue_simsat \
  --detector yolo --reasoner liquid-local \
  --require-crops --reset-queue
```

Expected outcome: 5 tiles processed, **0 detections, 100% bandwidth saved**. That's the honest finding — the architecture works on real DPhi imagery; current YOLO weights need Sentinel-domain fine-tuning to fire on 10 m/pixel data. See spike `.planning/spikes/001-simsat-live-tile/` for the full integration log.

The dashboard opens directly at the triage view: bandwidth saved as the hero metric, then the alerts the satellite chose to downlink — each card shows the crop, detector confidence, and Liquid's reasoning. A diagnostics expander at the bottom exposes raw payload/telemetry JSON for judge inspection.

## Imagery provenance — honest disclosure

KilnWatch supports **two imagery sources** end-to-end:

### A) Roboflow optical fixtures — `data/final_demo_tiles/`
Open-source brick-kiln imagery (Roboflow, Indo-Gangetic Plain morphology). Real overhead images of brick kilns at ~0.3-1 m/pixel that prove the satellite-edge pipeline end-to-end on the kind of structures the system is designed to detect. The detector + Liquid layer fire here: **5/5 alerts with real `vlm_reasoning`, ~99% bandwidth saved, ~100× compression**. Used by the primary demo.

These are **not** Sentinel-2 or DPhi SimSat live tiles. We do not claim Haryana ground-truth provenance for these specific images.

### B) DPhi SimSat live Sentinel-2 — `data/simsat_live_tiles/`
Real Sentinel-2 RGB tiles served by the official `DPhi-Space/SimSat` simulator running locally (`docker compose up`). Pipeline ingests these unchanged and emits proper telemetry, alert payloads, crops, and byte accounting. Five Indo-Gangetic Plain coordinates pulled (Panipat, Kurukshetra, Aligarh, Ludhiana, Dhaka outskirts) at `2024-11-15T10:00:00Z`. **Pipeline drops all 5 with `kiln_detected=false`, 100% bandwidth saved, 0 false positives.** Honest finding: current YOLO weights — trained on optical morphology at ~0.3-1 m/pixel — do not fire on Sentinel-2 RGB at ~10 m/pixel. Sentinel-domain fine-tuning is the documented next step (cookbook recipe: `Liquid4All/cookbook/examples/satellite-vlm` via `leap-finetune` + Modal H100). The triage architecture, queue boundary, and ground-station accounting do not change across imagery sources.

See `.planning/spikes/001-simsat-live-tile/README.md` for the full SimSat integration log and reproduction commands.

## Detector modes

- `--detector yolo` — strict real-detector mode. Requires `ultralytics`, `models/brick_kiln_yolo.pt`, and a class named like `Brick-Kiln`, `brick_kiln`, or `kiln`. Fails loudly if anything is missing — no silent fallback.
- `--detector baseline` — explicit simulation. Reads sidecar metadata or filename hints. Telemetry is marked `simulated=true`.
- `--allow-baseline-fallback` — explicit simulated fallback. Telemetry is marked `fallback_used=true` and the dashboard surfaces this prominently.

## Reasoner modes

- `--reasoner liquid-local` — `LiquidAI/LFM2.5-VL-450M` via `transformers.AutoModelForImageTextToText`. Real onboard reasoning. Used in the demo.
- `--reasoner liquid-mock` — explicit simulated reasoning. Telemetry marked `reasoner_is_real=false`.
- `--reasoner liquid-ollama` — Ollama-served LFM2 (currently broken in Ollama 0.17.5; use `liquid-local`).
- `--reasoner disabled` — YOLO-only, no Liquid layer. Alerts are detector-only.

## What is honest to claim

- Local satellite-edge triage architecture, end-to-end runnable.
- Strict YOLO detector path when readiness check passes.
- **Real on-device Liquid LFM2-VL reasoning** over each detector candidate (with `--reasoner liquid-local`).
- Real bbox-to-crop artifact generation for readable local image fixtures.
- Queue-only ground-station boundary.
- Real byte accounting from payload JSON, crop files, and telemetry.

## What we do not claim

- Real satellite deployment.
- Sentinel-2 or DPhi-API provenance for the included Roboflow demo tiles.
- Liquid LFM2-VL fine-tuning on brick-kiln imagery (the model is the open base; no fine-tune was performed).
- A trained, validated brick-kiln detection accuracy on Sentinel-domain data.
- Baseline or fallback telemetry as real detector evidence.

## Validate

```bash
python -m pytest -q
python scripts/check_model_ready.py --json
python scripts/validate_manifest.py datasets/kilnwatch/manifests/haryana_demo_manifest.jsonl
```

The placeholder Haryana manifest is intentionally not real ground truth and will fail image-readability validation with `--check-images`. That is correct.

## References

- Brooks et al., "Scalable deep learning to identify brick kilns and aid regulatory capacity", *PNAS*, 2021.
- Mondal et al., "Space to Policy: Scalable Brick Kiln Detection and Automatic Compliance Monitoring with Geospatial Data", *ACM COMPASS*, 2024.
- Mondal et al., "SentinelKilnDB: A Large-Scale Dataset for Oriented Bounding Box Brick Kiln Detection", *NeurIPS*, 2025.
- Denby and Lucia, "Orbital Edge Computing: Nanosatellite Constellations as a New Class of Computer System", *ASPLOS*, 2020.
- LiquidAI, *LFM2-VL technical reports*, 2025.

## Acknowledgements

Hackathon: Liquid AI × DPhi Space, *AI in Space*, April–May 2026.
Repository: <https://github.com/dakshdoesdev/spaceai>

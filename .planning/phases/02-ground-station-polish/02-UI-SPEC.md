---
phase: 2
slug: ground-station-polish
status: approved
shadcn_initialized: false
preset: streamlit-native
created: 2026-05-06
---

# Phase 2 — UI Design Contract

> Visual and interaction contract for Phase 2: Ground Station Polish. This contract locks the dashboard proof hierarchy, copy, crop evidence behavior, and honesty status display before planning.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none |
| Preset | streamlit-native |
| Component library | none |
| Icon library | none |
| Font | Streamlit default sans-serif |

**Design posture:** quiet operational ground-station dashboard. Prioritize proof, scanability, and technical honesty over decorative presentation. Do not introduce a marketing hero, decorative card-heavy layout, or broad visual redesign.

---

## First-Screen Information Architecture

The primary dashboard (`app.py`) MUST render the first screen in this order:

1. **Proof Status panel**
2. **Mission metrics**
3. **Edge-to-ground explanation**
4. **Crop review panel**
5. **Alert table and mission replay**
6. **Technical honesty panel**

The first viewport must make detector/reasoner truth visible without requiring source-code inspection or opening raw JSON.

---

## Proof Status Contract

The Proof Status panel MUST show explicit status labels using these exact concepts:

| Status Area | Required Labels |
|-------------|-----------------|
| Detector | `STRICT YOLO REAL`, `BASELINE SIMULATION`, `FALLBACK USED`, `SAMPLE DATA`, `DETECTOR METADATA UNKNOWN` |
| Liquid reasoner | `LIQUID LFM REAL`, `LIQUID MOCK`, `LFM DISABLED` |

The panel MUST expose raw truth fields when present:

- `detector_mode`
- `detector_is_real`
- `simulated`
- `fallback_used`
- `fallback_reason`
- `detector_version`
- model path/version if present in payload or telemetry
- confidence threshold if present in payload or telemetry
- `reasoner_mode`
- `reasoner_is_real`
- `model_name`

**Copy requirements:**

- If baseline or fallback is active, visible copy must say the detector output is simulated.
- If `liquid-mock` is active, visible copy must say Liquid reasoning is simulated.
- If `liquid-local` is active and `reasoner_is_real=true`, visible copy may say local Liquid LFM reasoning is real, but must not claim fine-tuning.
- If no `vlm_reasoning` exists, visible copy must say `LFM DISABLED`.

---

## Crop Review Contract

The crop review panel MUST render actual images only from safe downlinked crop artifacts.

Allowed image sources:

- Paths under the selected `transmission_queue/` tree.
- Paths under `transmission_queue/crops/`.
- Queue-visible crop paths referenced by payload/telemetry fields such as `crop_ref`, `crop_path`, or `payload_uri` when they resolve under the queue.

Forbidden image sources:

- `data/raw_tiles/`
- `data/final_demo_tiles/`
- `datasets/roboflow/`
- original Roboflow image folders
- placeholder `.tile` fixtures
- any path outside the queue/downlinked artifact boundary

UI behavior:

- If a safe crop file exists, show it with `st.image()` and a caption containing the tile id and source queue path.
- If a payload expects review but no safe crop file exists, show `no real crop available`.
- Never synthesize a crop preview from the raw tile or original source image.
- Never hide missing crop evidence behind an empty panel.

---

## Mission Metrics Contract

The first-screen metrics MUST include:

| Metric | Source |
|--------|--------|
| Tiles processed | telemetry event count |
| Detections | telemetry/payload `kiln_detected=true` or alert actions |
| Crops generated | safe crop refs with existing non-empty crop files |
| Raw bytes | `raw_bytes_processed` or `original_payload_bytes` |
| Transmitted bytes | `downlinked_bytes` or `transmitted_payload_bytes` |
| Bandwidth saved | existing byte accounting |
| Compression ratio | existing byte accounting |

Metric labels should be short and operational:

- `Tiles processed`
- `Detections`
- `Crops generated`
- `Raw bytes`
- `Transmitted bytes`
- `Bandwidth saved`
- `Compression ratio`

---

## Edge-To-Ground Explanation Contract

Add a compact explanation block near the top of the dashboard with this meaning:

- Raw images are processed onboard by the satellite edge node.
- Only JSON alerts, telemetry, and selected crop artifacts are downlinked.
- The ground station reads the downlinked queue only.

Required visible phrases:

- `processed onboard`
- `JSON/crop artifacts downlinked`
- `ground station reads queue only`

---

## Spacing Scale

Declared values (must be multiples of 4):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Inline status field gaps |
| sm | 8px | Badge padding and compact captions |
| md | 16px | Default spacing between controls and metric rows |
| lg | 24px | Section padding and column gaps |
| xl | 32px | Major proof section separation |
| 2xl | 48px | First-screen group separation when needed |
| 3xl | 64px | Avoid unless Streamlit default layout requires it |

Exceptions: Streamlit built-in component spacing may apply where custom CSS would add unnecessary risk.

---

## Typography

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body | Streamlit default / approx. 16px | 400 | 1.5 |
| Label | Streamlit caption / approx. 13px | 600 | 1.35 |
| Heading | Streamlit subheader / approx. 24px | 600 | 1.3 |
| Display | Streamlit title / approx. 36px | 700 | 1.2 |

Rules:

- Do not use oversized hero text.
- Keep panel headings concise: `Proof Status`, `Mission Metrics`, `Crop Review`, `Alerts`, `Mission Replay`, `Technical Honesty`.
- Literal honesty labels must be uppercase to improve scanability.

---

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | Streamlit default light/dark background | App background and base surfaces |
| Secondary (30%) | `#f8fafc` / Streamlit neutral surface | Proof and explanation panels when custom styling is needed |
| Accent (10%) | `#166534` | Real YOLO / real Liquid status only |
| Warning | `#92400e` | Sample data and simulated/mock status |
| Neutral | `#4b5563` | Disabled/unknown status |
| Destructive | `#991b1b` | Missing crop evidence or invalid boundary messages only |

Accent reserved for: real detector/reasoner status, not general buttons or chart decoration.

Avoid a one-hue dashboard. The palette must distinguish real (`#166534`), simulated/mock (`#92400e`), disabled/unknown (`#4b5563`), and missing evidence (`#991b1b`).

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Primary CTA | `Mission replay` |
| Secondary CTA | `Reset replay` |
| Empty state heading | `No transmission queue or telemetry logs found.` |
| Empty state body | `Run an orbital pass to create downlinked queue artifacts before opening the ground station.` |
| Missing crop evidence | `no real crop available` |
| Sample data warning | `SAMPLE DATA - replace transmission_queue/ and telemetry_logs/ with mission outputs.` |
| Boundary explanation | `Raw images are processed onboard; only JSON/crop artifacts are downlinked; ground station reads queue only.` |
| Error state | `No transmission queue or telemetry logs found. Run python -m satellite_edge_node.orbital_pass before refreshing the dashboard.` |
| Destructive confirmation | not applicable |

Copy rules:

- Do not claim deployed satellite operation.
- Do not claim Liquid LFM fine-tuning.
- Do not describe baseline/fallback/mock outputs as real model inference.
- Do not use "Sentinel" for placeholder or Roboflow-derived imagery unless provenance proves it.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none | not required |
| third-party registry | none | not allowed for this phase |

No new UI dependency, registry block, icon library, charting library, or CSS framework is approved for Phase 2. Use Streamlit, pandas, and local helpers already present in the repo.

---

## Accessibility And Responsiveness

- Status labels must be text, not color-only indicators.
- Any crop image must have a caption with the tile id and source queue path.
- Tables should use `width="stretch"` and hide index where appropriate.
- Metrics should wrap into multiple rows rather than squeezing long labels into one row.
- No text may overlap or require horizontal scrolling in the first-screen proof area.

---

## Verification Contract

Planner and executor MUST include verification that checks:

- `app.py` contains visible labels for `STRICT YOLO REAL`, `BASELINE SIMULATION`, `FALLBACK USED`, `SAMPLE DATA`, `LIQUID LFM REAL`, `LIQUID MOCK`, and `LFM DISABLED`.
- `app.py` or helper tests show `no real crop available` when crop evidence is missing.
- `kilnwatch/ground_station.py` rejects crop previews outside queue/downlinked artifact paths.
- `tests/test_ground_station.py` covers proof status, reasoner status, crop evidence, and metric helpers.
- `tests/test_ground_station_boundary.py` scans `app.py`, `kilnwatch/ground_station.py`, and `ground_station_ui/*.py` for forbidden raw-source path usage.
- `python -m unittest discover -s tests` passes.
- `python -m py_compile app.py kilnwatch/ground_station.py` passes.

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS

**Approval:** approved 2026-05-06

## UI-SPEC VERIFIED

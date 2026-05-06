# Phase 2: Ground Station Polish - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-06T19:06:55+05:30
**Phase:** 2-Ground Station Polish
**Areas discussed:** Detector honesty presentation, Crop/review evidence inspection, Dashboard proof hierarchy, Boundary validation focus

---

## Detector Honesty Presentation

| Option | Description | Selected |
|--------|-------------|----------|
| Make detector honesty the primary first-screen proof | Lead with strict YOLO vs baseline simulation vs fallback vs sample data, including raw metadata fields where available. | yes |
| Keep detector honesty as a secondary badge or technical panel | Less disruptive, but weaker judge-facing proof. | |
| Let metrics dominate first screen | Shows downlink value first, but risks hiding the honesty state. | |

**User's choice:** Detector honesty presentation is priority 1 for Phase 2.
**Notes:** Phase 1 fixed backend honesty. Phase 2 must make that honesty judge-visible. First screen should immediately prove whether the run is `STRICT YOLO REAL`, `BASELINE SIMULATION`, `FALLBACK USED`, or `SAMPLE DATA`.

---

## Crop/Review Evidence Inspection

| Option | Description | Selected |
|--------|-------------|----------|
| Show real crop image only from downlinked crop files | Strongest evidence path and respects queue-only boundary. | yes |
| Keep crop payloads as JSON references only | Safe but less judge-friendly. | |
| Attempt preview fallback from raw/source imagery | Not allowed because it violates the ground-station boundary. | |

**User's choice:** Crop/review evidence inspection is priority 2.
**Notes:** Show the real crop image if the crop file exists. If not, show `no real crop available`. Never invent a preview from raw tile data.

---

## Dashboard Proof Hierarchy

| Option | Description | Selected |
|--------|-------------|----------|
| Proof status -> metrics -> edge explanation -> crop review -> alert/replay -> honesty panel | Matches judge-facing proof order and keeps honesty visible immediately. | yes |
| Replay and alert table first | Current app shape is closer to this, but it hides the proof status. | |
| Metrics and chart first | Good for bandwidth story but weaker on detector honesty. | |

**User's choice:** Dashboard proof hierarchy is priority 3 after detector honesty and crop evidence.
**Notes:** Desired first-screen order: Proof Status panel, Mission metrics, Edge-to-ground explanation, Crop review panel, Alert table/replay, Technical honesty panel.

---

## Boundary Validation Focus

| Option | Description | Selected |
|--------|-------------|----------|
| Strengthen UI helpers and tests around allowed/forbidden paths | Locks queue-only behavior and prevents fake previews. | yes |
| UI polish only | Faster but does not prove the boundary. | |
| Tests only | Proves behavior but does not improve judge-facing clarity. | |

**User's choice:** Boundary validation focus is priority 4, after judge-visible proof.
**Notes:** Ground station may read only `transmission_queue/`, `telemetry_logs/`, and actual downlinked crop files. It must never read `data/raw_tiles/`, `data/final_demo_tiles/`, original Roboflow image folders, or placeholder `.tile` fixtures.

---

## the agent's Discretion

- Exact Streamlit layout and visual treatment are flexible if the first-screen hierarchy and explicit status text are preserved.
- Exact helper/function boundaries are flexible if business logic stays in `kilnwatch/ground_station.py` and rendering stays in `app.py`.

## Deferred Ideas

- Liquid LFM/LFM2.5-VL integration remains deferred unless implemented and proved before submission.
- Real detector training and production accuracy claims remain outside Phase 2.

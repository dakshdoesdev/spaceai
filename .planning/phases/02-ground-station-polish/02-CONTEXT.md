# Phase 2: Ground Station Polish - Context

**Gathered:** 2026-05-06T19:06:55+05:30
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 makes the primary Streamlit dashboard the judge-facing proof that KilnWatch is queue-only satellite-side triage. The dashboard must make detector honesty, downlinked crop evidence, mission metrics, and the satellite-to-ground boundary obvious from `transmission_queue/`, `telemetry_logs/`, and actual downlinked crop files only.

This phase does not add a new detector, train YOLO, integrate Liquid LFM, or read original raw imagery from the ground station.

</domain>

<decisions>
## Implementation Decisions

### Detector Honesty Presentation
- **D-01:** Detector honesty is the highest-priority Phase 2 concern because Phase 1 fixed backend honesty and Phase 2 must make that honesty judge-visible.
- **D-02:** The first screen must immediately prove which state applies: `STRICT YOLO REAL`, `BASELINE SIMULATION`, `FALLBACK USED`, or `SAMPLE DATA`.
- **D-03:** The dashboard must surface these detector fields when available: `detector_mode`, `detector_is_real`, `simulated`, `fallback_used`, model path/version, and confidence threshold.
- **D-04:** Baseline and fallback paths must be visually impossible to mistake for real detector output.

### Crop and Review Evidence
- **D-05:** Crop/review evidence is the second priority after detector honesty.
- **D-06:** The dashboard must show the real crop image when a downlinked crop file exists.
- **D-07:** If a crop payload exists but the crop file is missing or unreadable, the dashboard must show `no real crop available` or an equivalent explicit message.
- **D-08:** The dashboard must never invent a preview from raw tile data or original image folders.

### Dashboard Proof Hierarchy
- **D-09:** The desired first-screen hierarchy is:
  1. Proof Status panel.
  2. Mission metrics.
  3. Edge-to-ground explanation.
  4. Crop review panel.
  5. Alert table/replay.
  6. Technical honesty panel.
- **D-10:** The Proof Status panel must include: `STRICT YOLO REAL` / `BASELINE SIMULATION` / `FALLBACK USED` / `SAMPLE DATA`, `detector_mode`, `detector_is_real`, `simulated`, `fallback_used`, model path/version if available, and confidence threshold.
- **D-11:** Mission metrics must include: tiles processed, detections, crops generated, raw bytes, transmitted bytes, bandwidth saved, and compression ratio.
- **D-12:** The edge-to-ground explanation must state: raw images are processed onboard, only JSON/crop artifacts are downlinked, and the ground station reads the queue only.
- **D-13:** Alert table and replay are still useful, but they should sit after detector/crop/metric proof rather than dominating the first screen.

### Queue-Only Boundary Validation
- **D-14:** Ground station code may read only `transmission_queue/`, `telemetry_logs/`, and actual downlinked crop files referenced by queue payloads.
- **D-15:** Ground station code must never read `data/raw_tiles/`, `data/final_demo_tiles/`, original Roboflow image folders, or placeholder `.tile` fixtures.
- **D-16:** Boundary validation should cover UI-facing helpers and tests, not just visual wording.
- **D-17:** Phase 2 goal is to make the Streamlit dashboard the primary judge-facing proof that KilnWatch is queue-only satellite-side triage, not a fake dashboard.

### the agent's Discretion
- The exact Streamlit layout implementation is flexible as long as the first-screen hierarchy and boundary constraints above are met.
- The exact visual style of honesty badges is flexible, but status text must remain explicit and grep/test-verifiable where possible.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Scope and Requirements
- `.planning/ROADMAP.md` — Defines Phase 2 goal, dependency on Phase 1, success criteria, and planned work items `02-01` and `02-02`.
- `.planning/REQUIREMENTS.md` — Defines `DEMO-05`, `SPACE-02`, and `SPACE-03`, plus global honesty and submission constraints.
- `.planning/PROJECT.md` — Defines KilnWatch positioning, hackathon framing, core value, and out-of-scope claims.
- `.planning/STATE.md` — Records Phase 1 completion and current focus on Phase 2.

### Prior Phase Evidence
- `.planning/phases/01-strict-demo-chain/01-01-SUMMARY.md` — Prior implementation evidence for fresh demo queue/run isolation.
- `.planning/phases/01-strict-demo-chain/01-02-SUMMARY.md` — Prior implementation evidence for detector readiness and honesty metadata.
- `.planning/phases/01-strict-demo-chain/01-03-SUMMARY.md` — Prior implementation evidence for crop artifact generation and payload references.

### Ground Station Code
- `app.py` — Primary Streamlit dashboard to polish.
- `kilnwatch/ground_station.py` — Queue-visible telemetry loading, metrics, detector modes, alert rows, and safe review payload helpers.
- `ground_station_ui/app.py` — Secondary/simple queue dashboard; useful as a reference but not the primary judge-facing surface.
- `ground_station_ui/queue_reader.py` — Simple queue-only reader utilities.

### Boundary and Regression Tests
- `tests/test_ground_station.py` — Current ground-station metric, detector-mode, sample precedence, and review-payload tests.
- `tests/test_ground_station_boundary.py` — Current boundary test ensuring ground station UI modules do not import raw satellite modules or paths.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `kilnwatch.ground_station.load_ground_station_records()` already loads payloads and telemetry from ground-station-visible folders and filters sample records when real records exist.
- `kilnwatch.ground_station.calculate_metrics()` already computes raw bytes, downlinked bytes, savings, alert counts, compression ratio, and latency.
- `kilnwatch.ground_station.detector_modes()` already extracts detector mode strings from payload and telemetry metadata.
- `kilnwatch.ground_station.safe_review_payloads()` already restricts imagery references to `CROP_OR_REVIEW` and `FULL_DOWNLINK` decisions.
- `app.py` already has separable render functions for status badges, metrics, downlink chart, alert table, replay status, technical honesty, and review payload references.

### Established Patterns
- Keep business logic in `kilnwatch/ground_station.py`; keep Streamlit rendering in `app.py`.
- Ground-station logic reads file-backed queue and telemetry artifacts, not satellite raw input folders.
- Tests are Python `unittest`/pytest-compatible and should extend existing focused test files.
- Technical honesty is represented in payloads/telemetry through fields such as `detector_mode`, `detector_is_real`, `simulated`, `fallback_used`, and `fallback_reason`.

### Integration Points
- `app.py::main()` should be reorganized around the new first-screen hierarchy.
- `app.py::render_status_badges()` likely needs to become a richer Proof Status panel.
- `app.py::render_review_payloads()` likely needs to become or feed a Crop Review panel that attempts to show only downlinked crop files.
- `kilnwatch/ground_station.py` likely needs additional helpers for proof status, crop evidence counting, and safe crop path resolution.
- `tests/test_ground_station.py` and `tests/test_ground_station_boundary.py` should lock honesty extraction, crop evidence behavior, and forbidden raw-path access.

</code_context>

<specifics>
## Specific Ideas

- First-screen status labels should use the literal concepts `STRICT YOLO REAL`, `BASELINE SIMULATION`, `FALLBACK USED`, and `SAMPLE DATA`.
- Crop preview behavior must be evidence-based: show an image only if a downlinked crop file exists; otherwise show `no real crop available` or equivalent.
- Mission metrics should explicitly include detections and crops generated in addition to the existing byte accounting.
- The dashboard should state the satellite/ground flow in plain terms: raw images processed onboard, compact JSON/crops downlinked, ground station reads queue only.

</specifics>

<deferred>
## Deferred Ideas

- Liquid LFM/LFM2.5-VL integration remains v2 unless implemented and proved before submission.
- Real detector training, detector accuracy claims, and production enforcement evaluation remain outside Phase 2.
- Broad run-directory isolation and production data management remain outside Phase 2 unless already provided by Phase 1 artifacts.

</deferred>

---

*Phase: 2-Ground Station Polish*
*Context gathered: 2026-05-06T19:06:55+05:30*

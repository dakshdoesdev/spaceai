# KilnWatch

## What This Is

KilnWatch is a satellite-side brick kiln compliance triage demo for the Liquid AI x DPhi Space AI in Space hackathon. It simulates an onboard Earth-observation workflow where a satellite edge node inspects imagery, decides what is worth transmitting, and downlinks compact JSON alerts plus targeted crops instead of full raw tiles.

The current codebase is a strong system architecture MVP: satellite edge processing, detector routing, queue artifacts, telemetry, and a Streamlit ground station already exist. The final push is to make the demo polished, technically honest, and submission-ready, with at least one real end-to-end proof chain from real image to detector result to crop to JSON payload to dashboard.

## Core Value

Prove the satellite/ground boundary correctly: the satellite node decides what is worth transmitting, and the ground station only sees downlinked artifacts.

## Requirements

### Validated

- ✓ Satellite edge runner can process local tile inputs and write queue payloads — existing in `satellite_edge_node/orbital_pass.py`
- ✓ Detector routing supports baseline simulation and strict YOLO-style real detector mode — existing in `satellite_edge_node/detectors.py`, `satellite_edge_node/baseline_detector.py`, and `satellite_edge_node/yolo_detector.py`
- ✓ Payload builder can emit JSON alerts, telemetry, bandwidth accounting, and crop references — existing in `satellite_edge_node/payloads.py`
- ✓ Ground station dashboard reads queue-visible artifacts and visualizes alerts/metrics — existing in `app.py`, `kilnwatch/ground_station.py`, and `ground_station_ui/`
- ✓ SimSat/local ingestion and manifest validation scaffolding exists — existing in `kilnwatch/ingestion/`, `kilnwatch/datasets/`, and `scripts/`
- ✓ Test coverage exists for triage, ground-station boundary, manifest validation, detector paths, bandwidth, and fetch/demo utilities — existing in `tests/`
- ✓ Technical honesty documentation already identifies simulation vs real detector caveats — existing in `docs/technical_honesty.md`, `docs/model_training.md`, and related docs

### Active

- [ ] Produce one strict, honest end-to-end demo chain: real image -> detector/bbox -> actual crop file -> JSON payload -> dashboard display
- [ ] Make the public README and docs submission-ready for judges, with no overclaiming about Sentinel imagery, deployed satellite payloads, Liquid LFM usage, or trained detector accuracy
- [ ] Polish the Streamlit ground station as the primary demo surface, emphasizing queue-only visibility, alert triage, bandwidth saved, and detector honesty status
- [ ] Prepare hackathon submission answers: problem statement, solution overview, space-based compute rationale, DPhi SimSat endpoint usage, hardest part, one-line pitch, and demo script
- [ ] Decide and document General Track unless Liquid LFM integration or fine-tuning is actually implemented before submission
- [ ] Ensure fallback behavior is impossible to mistake for real detection: strict YOLO must fail loudly when model/dependencies are missing, and baseline mode must be labeled as simulated
- [ ] Ensure crop artifacts are real files when payloads claim a crop was downlinked
- [ ] Add or refresh practical validation evidence: tests, manifest checks, model readiness output, detector/evaluation output, and dashboard smoke proof
- [ ] Normalize demo artifacts so placeholder `.tile` files and sample telemetry cannot be mistaken for real Sentinel imagery or production mission data
- [ ] Coordinate multi-agent work across Codex/Gemini/tmux lanes without conflicting edits or duplicate claims

### Out of Scope

- Real deployed satellite payload — KilnWatch is a local simulation of a satellite-side triage architecture for the hackathon.
- Claiming completed Liquid LFM2-VL/LFM2.5-VL fine-tuning unless the repo actually contains the fine-tuning code, dataset card, and integration proof.
- Claiming production brick kiln enforcement accuracy without real labeled imagery, trained weights, and evaluation metrics.
- Building a generic VLM image-chat demo — the differentiator is bandwidth-aware downlink triage for a specific environmental compliance use case.
- Broad dataset automation across every possible brick-kiln dataset before submission — one honest real-image proof chain matters more than wide but unverifiable coverage.

## Context

The hackathon theme is Earth observation plus efficient AI near or onboard satellite systems. The official Liquid wildfire example establishes the expected architecture pattern: satellite imagery comes in, a compact model runs near/on the satellite, the model outputs structured JSON, and only the lightweight payload is downlinked. KilnWatch mirrors that pattern for brick kiln compliance monitoring across Panipat/Haryana/NCR instead of wildfire detection.

The likely competitor field includes wildfire tutorial remixes, maritime anomaly examples, generic satellite VLM apps, and dashboard-heavy projects. KilnWatch's strongest angle is not maximum detector accuracy; it is the grounded edge/ground architecture: process imagery locally, preserve the onboard boundary, and transmit only compact evidence that needs review.

Current workflow and tools:
- Repo: `https://github.com/dakshdoesdev/spaceai`
- Local directory: `/home/dux/Work/tries/SpaceAI`
- Runtime workflow: Codex CLI, Gemini Pro CLI, tmux, and GSD
- Working lanes: multiple Codex windows for implementation, Gemini for research, and review/test panes for critique and test validation
- GSD role: ask better questions, map the brownfield codebase, create requirements/roadmap, and organize final execution phases

Submission framing:
- Project name: KilnWatch
- Recommended track: General Track unless Liquid LFM integration/fine-tuning lands before submission
- One-line pitch: Satellite-side brick kiln triage that downlinks JSON alerts and crops instead of full raw imagery.
- Core story: real-world environmental compliance monitoring with satellite-side compute and bandwidth-aware downlink reduction
- Event details from the registration page: Hack #05 AI in Space, Liquid AI x DPhi Space, fully online, April 13 5:30 PM to May 9 5:30 AM GMT+5:30, Discord-based community, with submissions opened May 4.
- Judging criteria from the event page: use of satellite imagery from the DPhi API, innovation and problem-solution fit, technical implementation that runs without debugging, and an end-to-end demo walkthrough.
- Track framing from the event page: Liquid Track expects LFM2-VL/LFM2.5-VL usage with fine-tuning encouraged; General AI Track accepts any AI approach but prefers solutions designed around limited downlink, continuous streams, and onboard inference.
- Relevant SimSat endpoints from event updates: historical Sentinel `/data/image/sentinel`, historical Mapbox `/data/image/mapbox`, current Sentinel/Mapbox endpoints as provided by SimSat. Only claim endpoints that the repo actually uses.

## Constraints

- **Deadline**: Event materials show the hackathon ending around May 9, 2026 in local GMT+5:30 display, while the submission blast text contains a likely stale "May 9, 2025" date. Submit as early as possible and do not depend on last-hour fixes.
- **Submission honesty**: Do not imply the project uses Liquid LFM, Sentinel imagery, trained YOLO weights, or a deployed satellite payload unless the repo proves it.
- **Detector readiness**: Strict YOLO mode requires `models/brick_kiln_yolo.pt` and `ultralytics`; if absent, real detector claims are blocked.
- **Data proof**: Placeholder `.tile` blobs cannot be described as real Sentinel imagery; the final demo needs at least one real image/crop path or a clearly disclosed manual/simulated fixture.
- **Ground boundary**: The dashboard must read only `transmission_queue/` and telemetry/downlinked artifacts, not raw onboard inputs.
- **Time budget**: Prioritize the minimum real proof chain, README/demo polish, and submission answers over broad refactors.
- **Dependencies**: Avoid adding new dependencies unless they directly support final proof, demo polish, or validation.
- **Coordination**: Multiple Codex/Gemini lanes are active, so edits should stay scoped and commits should be intentional.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Position KilnWatch as satellite-side brick kiln compliance triage | Specific environmental compliance use case differentiates it from wildfire/maritime clones | — Pending |
| Lead with downlink triage rather than detector accuracy | The hackathon rewards efficient satellite-side compute patterns, and the current architecture is strongest there | — Pending |
| Recommend General Track unless Liquid LFM is actually integrated | Avoid overclaiming Liquid fine-tuning/model usage when current working path is YOLO-compatible CV plus simulation | — Pending |
| Treat baseline detector as simulation only | Filename/metadata-driven detections are useful for demo flow but not real model evidence | — Pending |
| Make one strict end-to-end proof chain the highest-impact next step | Real image -> detector -> crop -> JSON -> dashboard is more valuable than more architecture docs | — Pending |
| Use GSD to organize the final push | Brownfield map exists and can drive requirements, roadmap, and phase planning | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check -> still the right priority?
3. Audit Out of Scope -> reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-06 after initialization*

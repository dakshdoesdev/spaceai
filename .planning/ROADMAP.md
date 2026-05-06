# Roadmap: KilnWatch

## Overview

KilnWatch's final submission path is a four-phase sprint: first make the satellite-side proof chain honest and reproducible, then polish the dashboard around that proof, then clean the public repo and submission story, and finally run validation plus package the demo materials.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions

- [ ] **Phase 1: Strict Demo Chain** - Produce a fresh, honest edge-run proof with real crop artifacts and detector readiness checks.
- [ ] **Phase 2: Ground Station Polish** - Make the dashboard the primary judge-facing proof of queue-only downlink triage.
- [ ] **Phase 3: Public Story and Docs** - Make README/docs technically honest, compelling, and aligned with hackathon criteria.
- [ ] **Phase 4: Submission Verification** - Verify tests, manifests, demo script, form answers, repo cleanliness, and final risk.

## Phase Details

### Phase 1: Strict Demo Chain
**Goal**: A judge can run the satellite-side demo path and see fresh queue artifacts, detector status, triage output, and real crop files.
**Depends on**: Nothing
**Requirements**: DEMO-01, DEMO-02, DEMO-03, DEMO-04, HON-01, HON-02, VAL-03, VAL-04
**Success Criteria** (what must be TRUE):
  1. User can generate a fresh `transmission_queue/` demo run from a documented command.
  2. User can tell whether the run used strict YOLO or simulated baseline without reading source code.
  3. User can open a real crop file for any payload that claims a crop was downlinked.
  4. Strict YOLO failure is loud when weights/dependencies are missing unless explicit fallback is requested.
  5. Stale telemetry does not contaminate the final demo run.
**Plans**: 3 plans

Plans:
- [ ] 01-01-PLAN.md — Add/confirm fresh demo run workflow and queue reset/run isolation.
- [ ] 01-02-PLAN.md — Harden detector readiness, strict YOLO failure, and simulation/fallback metadata.
- [ ] 01-03-PLAN.md — Verify real crop artifact generation and payload references.

### Phase 2: Ground Station Polish
**Goal**: The Streamlit dashboard clearly demonstrates satellite-side triage, bandwidth savings, alerts, crops, and honesty state from queue artifacts only.
**Depends on**: Phase 1
**Requirements**: DEMO-05, SPACE-02, SPACE-03
**Success Criteria** (what must be TRUE):
  1. User can run the primary dashboard and immediately understand the satellite-to-ground flow.
  2. Dashboard shows raw bytes, downlinked bytes, bandwidth saved, alert counts, and detector honesty status.
  3. Dashboard reads only queue/telemetry/downlinked artifacts, not raw onboard inputs.
  4. Crop/review payloads are visible or linked in a way a judge can inspect.
**Plans**: 2 plans

Plans:
- [ ] 02-01: Polish dashboard information architecture and proof widgets.
- [ ] 02-02: Strengthen queue-only ground-station boundary validation.

### Phase 3: Public Story and Docs
**Goal**: The public repo tells the KilnWatch story cleanly and honestly for a hackathon judge.
**Depends on**: Phase 2
**Requirements**: HON-03, HON-04, HON-05, SPACE-01, SPACE-04, SUB-01
**Success Criteria** (what must be TRUE):
  1. README explains problem, solution, space-based compute rationale, setup, run commands, and limitations.
  2. Docs distinguish real imagery, placeholder fixtures, simulated baseline, strict YOLO, and future Liquid LFM work.
  3. Architecture flow maps satellite input -> onboard detection -> triage -> compact downlink -> ground review.
  4. General Track positioning is clear unless Liquid LFM integration is actually implemented.
**Plans**: 2 plans

Plans:
- [ ] 03-01: Rewrite README/submission docs around final judge-facing story.
- [ ] 03-02: Clean demo data language and technical honesty caveats.

### Phase 4: Submission Verification
**Goal**: The repo and submission materials are ready to submit without last-minute debugging.
**Depends on**: Phase 3
**Requirements**: SUB-02, SUB-03, SUB-04, SUB-05, VAL-01, VAL-02, VAL-05
**Success Criteria** (what must be TRUE):
  1. Test suite and validation commands pass or documented blockers are explicit.
  2. Submission answer draft covers every required form field.
  3. Demo script walks through command, queue artifacts, dashboard, and caveats.
  4. Repo status is understood and public-facing generated artifacts are intentional.
  5. Secret scan and final review find no private credentials or misleading claims.
**Plans**: 3 plans

Plans:
- [ ] 04-01: Run tests, manifest validation, model readiness, and secret checks.
- [ ] 04-02: Draft final Google Form answers and demo video script.
- [ ] 04-03: Final repo cleanup, public-readiness review, and submission checklist.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Strict Demo Chain | 0/3 | Not started | - |
| 2. Ground Station Polish | 0/2 | Not started | - |
| 3. Public Story and Docs | 0/2 | Not started | - |
| 4. Submission Verification | 0/3 | Not started | - |

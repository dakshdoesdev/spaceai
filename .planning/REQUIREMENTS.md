# Requirements: KilnWatch

**Defined:** 2026-05-06
**Core Value:** Prove the satellite/ground boundary correctly: the satellite node decides what is worth transmitting, and the ground station only sees downlinked artifacts.

## v1 Requirements

Requirements for the final AI in Space hackathon submission.

### Demo Proof

- [ ] **DEMO-01**: User can run one documented command sequence that creates a fresh transmission queue for the demo.
- [ ] **DEMO-02**: User can process at least one real raster image or explicitly disclosed fixture through the satellite edge node.
- [ ] **DEMO-03**: User can inspect a payload JSON containing detector metadata, triage action, byte accounting, and crop/full-downlink decision.
- [ ] **DEMO-04**: User can open an actual crop file when a payload claims a crop was downlinked.
- [ ] **DEMO-05**: User can view the resulting alert and bandwidth metrics in the Streamlit ground station.

### Honesty

- [ ] **HON-01**: Baseline detector output is visibly labeled as simulated in payloads, telemetry, docs, and dashboard.
- [ ] **HON-02**: Strict YOLO mode fails loudly when `ultralytics` or `models/brick_kiln_yolo.pt` is missing unless explicit fallback is requested.
- [ ] **HON-03**: Placeholder `.tile` files are not described as Sentinel imagery.
- [ ] **HON-04**: README and demo docs state that KilnWatch is a local simulation, not a deployed satellite payload.
- [ ] **HON-05**: Liquid LFM/LFM2.5-VL usage is described as future work unless implemented and proved in the repo.

### Space Compute

- [ ] **SPACE-01**: Documentation explains why onboard/near-satellite inference reduces downlink load.
- [ ] **SPACE-02**: Dashboard shows file-size-based raw bytes, downlinked bytes, and bandwidth saved.
- [ ] **SPACE-03**: Ground station reads only `transmission_queue/` and telemetry/downlinked artifacts, not raw onboard inputs.
- [ ] **SPACE-04**: Solution overview maps clearly to satellite input -> onboard detection -> triage -> compact downlink -> ground review.

### Submission

- [ ] **SUB-01**: README has a clear one-line pitch, problem statement, solution overview, architecture diagram/flow, setup, run commands, and limitations.
- [ ] **SUB-02**: Submission answer draft exists for every required Google Form field.
- [ ] **SUB-03**: Demo script exists and walks through command, queue artifacts, dashboard, and technical honesty caveats.
- [ ] **SUB-04**: Repo is public-facing clean: generated/sample artifacts are intentional, docs are current, and setup works from a clean environment.
- [ ] **SUB-05**: Track recommendation is documented as General Track unless Liquid LFM integration/fine-tuning is completed before submission.

### Validation

- [ ] **VAL-01**: Test suite passes for existing unit/regression tests.
- [ ] **VAL-02**: Manifest validation command passes for included demo/evaluation manifests.
- [ ] **VAL-03**: Model readiness command clearly reports whether real detector mode is available.
- [ ] **VAL-04**: Final demo queue is generated from a fresh run, not stale mixed telemetry.
- [ ] **VAL-05**: No submitted docs or generated code contain secrets or private credentials.

## v2 Requirements

Deferred beyond the current submission.

### Liquid Model Integration

- **LFM-01**: Integrate LFM2.5-VL-450M for structured visual/risk reasoning.
- **LFM-02**: Fine-tune or evaluate an LFM model on a documented brick-kiln/satellite dataset.
- **LFM-03**: Publish or link a Hugging Face dataset/model card if Liquid Track work is completed.

### Production Hardening

- **PROD-01**: Add run IDs and per-run output directories for telemetry isolation.
- **PROD-02**: Add CI for tests, manifest validation, dashboard smoke, and model readiness.
- **PROD-03**: Implement one license-checked real dataset adapter end to end.
- **PROD-04**: Add hardware-aware edge profiling for latency, memory, and power constraints.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Deployed satellite payload | Hackathon demo is local simulation and cannot claim real deployment. |
| Production enforcement accuracy | Requires real labeled imagery, trained detector weights, and robust evaluation beyond this sprint. |
| Liquid Track claim without implementation | The repo must not imply LFM fine-tuning or integration if it is not present. |
| Broad backend/platform rewrite | Current Python/Streamlit/file-queue stack is enough for final submission. |
| Generic image-chat VLM UI | Does not support the core downlink triage differentiator. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DEMO-01 | Phase 1 | Pending |
| DEMO-02 | Phase 1 | Pending |
| DEMO-03 | Phase 1 | Pending |
| DEMO-04 | Phase 1 | Pending |
| DEMO-05 | Phase 2 | Pending |
| HON-01 | Phase 1 | Pending |
| HON-02 | Phase 1 | Pending |
| HON-03 | Phase 3 | Pending |
| HON-04 | Phase 3 | Pending |
| HON-05 | Phase 3 | Pending |
| SPACE-01 | Phase 3 | Pending |
| SPACE-02 | Phase 2 | Pending |
| SPACE-03 | Phase 2 | Pending |
| SPACE-04 | Phase 3 | Pending |
| SUB-01 | Phase 3 | Pending |
| SUB-02 | Phase 4 | Pending |
| SUB-03 | Phase 4 | Pending |
| SUB-04 | Phase 4 | Pending |
| SUB-05 | Phase 4 | Pending |
| VAL-01 | Phase 4 | Pending |
| VAL-02 | Phase 4 | Pending |
| VAL-03 | Phase 1 | Pending |
| VAL-04 | Phase 1 | Pending |
| VAL-05 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0

---
*Requirements defined: 2026-05-06*
*Last updated: 2026-05-06 after initialization*

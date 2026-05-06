# Phase 1: Strict Demo Chain - Research

**Researched:** 2026-05-06
**Domain:** Python file-backed satellite-edge demo pipeline, detector readiness, payload/crop artifact integrity
**Confidence:** HIGH

## User Constraints

### Locked Phase Scope

- Phase 1 goal is: "A judge can run the satellite-side demo path and see fresh queue artifacts, detector status, triage output, and real crop files." [VERIFIED: .planning/ROADMAP.md]
- Phase 1 must address DEMO-01, DEMO-02, DEMO-03, DEMO-04, HON-01, HON-02, VAL-03, and VAL-04. [VERIFIED: .planning/ROADMAP.md] [VERIFIED: .planning/REQUIREMENTS.md]
- Keep the current Python, Streamlit, and file-queue architecture for the final sprint. [VERIFIED: .planning/STATE.md]
- Prioritize one strict end-to-end proof chain over broad refactors. [VERIFIED: .planning/STATE.md]
- Treat baseline detector output as simulation, not real detection. [VERIFIED: .planning/STATE.md]
- Strict YOLO mode requires `models/brick_kiln_yolo.pt` and `ultralytics`; if absent, real detector claims are blocked. [VERIFIED: .planning/PROJECT.md] [VERIFIED: scripts/check_model_ready.py]
- Placeholder `.tile` fixtures must not be described as real Sentinel imagery. [VERIFIED: .planning/PROJECT.md] [VERIFIED: .planning/research/SUMMARY.md]
- The dashboard and ground-station side must read only downlinked queue/telemetry artifacts, not raw onboard inputs. [VERIFIED: .planning/PROJECT.md] [VERIFIED: .planning/codebase/ARCHITECTURE.md]
- Avoid new dependencies unless they directly support final proof, demo polish, or validation. [VERIFIED: AGENTS.md] [VERIFIED: .planning/PROJECT.md]
- Do not make direct repo edits outside a GSD workflow unless explicitly asked; this file is a GSD research artifact requested by the phase workflow. [VERIFIED: AGENTS.md]

### Deferred Ideas (OUT OF SCOPE)

- Liquid LFM2.5-VL fine-tuning or integration is v2 unless implemented and proved before submission. [VERIFIED: .planning/STATE.md] [VERIFIED: .planning/REQUIREMENTS.md]
- Production run IDs, CI, dataset adapters, and hardware profiling are v2, except that Phase 1 may add a lightweight run-isolation or reset mechanism needed to avoid stale demo telemetry. [VERIFIED: .planning/STATE.md] [VERIFIED: .planning/REQUIREMENTS.md]
- Broad backend/platform rewrite is out of scope. [VERIFIED: .planning/REQUIREMENTS.md]

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEMO-01 | User can run one documented command sequence that creates a fresh transmission queue for the demo. [VERIFIED: .planning/REQUIREMENTS.md] | Add a CLI-visible fresh-run path: either `--reset-queue` for the selected output directory or a per-run output directory. Avoid using append-only `transmission_queue/telemetry.jsonl` as the final proof without reset/isolation. [VERIFIED: satellite_edge_node/orbital_pass.py] |
| DEMO-02 | User can process at least one real raster image or explicitly disclosed fixture through the satellite edge node. [VERIFIED: .planning/REQUIREMENTS.md] | Crop generation requires a Pillow-readable raster input when a payload claims a crop. Current `.tile` blobs are not readable images, so the plan needs a PNG/JPEG/TIFF fixture or a disclosed simulated raster fixture. [VERIFIED: satellite_edge_node/payloads.py] [VERIFIED: local file audit] |
| DEMO-03 | User can inspect a payload JSON containing detector metadata, triage action, byte accounting, and crop/full-downlink decision. [VERIFIED: .planning/REQUIREMENTS.md] | Existing payload JSON contains detector truth metadata and crop refs, while telemetry contains byte accounting and `action`; Phase 1 should either include enough byte/action fields in payload JSON or document the JSON+telemetry pair as the inspection unit. [VERIFIED: satellite_edge_node/payloads.py] |
| DEMO-04 | User can open an actual crop file when a payload claims a crop was downlinked. [VERIFIED: .planning/REQUIREMENTS.md] | Existing tests prove real PNG crop creation for readable image input and no crop claim for unreadable blobs; add/keep tests that every non-null `crop_ref` exists and has non-zero size. [VERIFIED: tests/test_satellite_edge_bandwidth.py] |
| HON-01 | Baseline detector output is visibly labeled as simulated in payloads, telemetry, docs, and dashboard. [VERIFIED: .planning/REQUIREMENTS.md] | Existing `DetectionResult` defaults set `detector_is_real=False` and `simulated=True`; planning should preserve those fields and add any missing CLI/user-facing status output. [VERIFIED: satellite_edge_node/baseline_detector.py] [VERIFIED: satellite_edge_node/payloads.py] |
| HON-02 | Strict YOLO mode fails loudly when `ultralytics` or `models/brick_kiln_yolo.pt` is missing unless explicit fallback is requested. [VERIFIED: .planning/REQUIREMENTS.md] | Existing `YoloDetector` raises `YoloModelUnavailable`, the CLI returns code `2`, and fallback only occurs with `--allow-baseline-fallback`; tests should cover CLI behavior as well as detector builder behavior. [VERIFIED: satellite_edge_node/yolo_detector.py] [VERIFIED: satellite_edge_node/orbital_pass.py] [VERIFIED: tests/test_yolo_detector.py] |
| VAL-03 | Model readiness command clearly reports whether real detector mode is available. [VERIFIED: .planning/REQUIREMENTS.md] | `scripts/check_model_ready.py --json` currently reports missing weights and missing `ultralytics`; Phase 1 should keep this as a demo preflight and maybe surface the command in the fresh-run workflow. [VERIFIED: scripts/check_model_ready.py] [VERIFIED: command output 2026-05-06] |
| VAL-04 | Final demo queue is generated from a fresh run, not stale mixed telemetry. [VERIFIED: .planning/REQUIREMENTS.md] | Current `simulate_orbital_pass()` opens telemetry in append mode and overwrites per-tile JSON files, so the plan must add reset/isolation and regression tests for duplicate/mixed runs. [VERIFIED: satellite_edge_node/orbital_pass.py] [VERIFIED: .planning/codebase/CONCERNS.md] |

</phase_requirements>

## Summary

Phase 1 is mostly a hardening and proof-chain phase, not a new architecture phase. The existing satellite edge runner, detector router, payload builder, model-readiness script, and crop-generation tests already cover most primitives, but the current default queue behavior can mix stale telemetry with newer payload JSON because telemetry is appended and payload files are overwritten. [VERIFIED: satellite_edge_node/orbital_pass.py] [VERIFIED: tests/test_satellite_edge_bandwidth.py]

The planner should prioritize a narrowly scoped fresh-run workflow: add explicit queue reset or output isolation, make the command sequence include model-readiness output, then run `satellite_edge_node.orbital_pass` over readable demo imagery that can produce real crop files. [VERIFIED: .planning/ROADMAP.md] [VERIFIED: satellite_edge_node/payloads.py] The safest near-term implementation is a `--reset-queue` option plus tests that delete only known generated queue artifacts in the selected queue directory, preserving the existing file-queue contract. [CITED: https://docs.python.org/3/library/shutil.html] [VERIFIED: .planning/codebase/ARCHITECTURE.md]

**Primary recommendation:** Implement Phase 1 as three executable slices: queue reset/isolation, detector-readiness/loud-failure proof, and crop-reference integrity tests. [VERIFIED: .planning/ROADMAP.md]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Fresh demo run / queue reset | Satellite Edge Layer | Downlink Boundary Layer | The edge runner owns writing queue artifacts; the downlink directory is the state boundary that must be reset or isolated before a judge run. [VERIFIED: satellite_edge_node/orbital_pass.py] [VERIFIED: .planning/codebase/ARCHITECTURE.md] |
| Strict detector readiness | Evaluation and Operations Layer | Satellite Edge Layer | `scripts/check_model_ready.py` is the preflight surface, while `YoloDetector` and CLI setup failures enforce runtime truth. [VERIFIED: scripts/check_model_ready.py] [VERIFIED: satellite_edge_node/yolo_detector.py] |
| Loud YOLO failure | Satellite Edge Layer | CLI boundary | `YoloModelUnavailable` originates in detector construction and `orbital_pass.main()` converts it into a clear message and exit code `2`. [VERIFIED: satellite_edge_node/yolo_detector.py] [VERIFIED: satellite_edge_node/orbital_pass.py] |
| Simulation/fallback metadata | Detector Layer | Payload/Telemetry Layer | Detector implementations set truth metadata; payload and telemetry serialization must preserve it for judge-visible artifacts. [VERIFIED: satellite_edge_node/baseline_detector.py] [VERIFIED: satellite_edge_node/detectors.py] [VERIFIED: satellite_edge_node/payloads.py] |
| Crop generation and references | Payload Builder | Input/Dataset Layer | `generate_crop_file()` owns crop creation, but it depends on a readable raster tile and valid bbox metadata. [VERIFIED: satellite_edge_node/payloads.py] [CITED: https://context7.com/python-pillow/pillow/llms.txt] |
| Stale telemetry avoidance | Downlink Boundary Layer | Evaluation Layer | Queue telemetry is append-only today, and evaluator joins by tile ID, so the downlink boundary must prevent or identify mixed runs before evaluation. [VERIFIED: satellite_edge_node/orbital_pass.py] [VERIFIED: scripts/evaluate_detector.py] |

## Standard Stack

### Core

| Library / Tool | Version | Purpose | Why Standard |
|----------------|---------|---------|--------------|
| Python | >=3.11 required; local shell is 3.14.4 | CLI runner, JSON/JSONL, pathlib filesystem operations, tests | Existing package requires Python >=3.11 and the codebase is synchronous Python. [VERIFIED: pyproject.toml] [VERIFIED: `python --version`] |
| Pillow | >=10 required; latest and locally installed is 12.2.0 | Read image tiles and save crop PNGs | Existing crop generation and image validation use Pillow; Pillow documents `Image.open()`, `Image.crop()`, and `Image.save()` for this exact operation. [VERIFIED: requirements.txt] [VERIFIED: pip index] [CITED: https://context7.com/python-pillow/pillow/llms.txt] |
| pytest | latest registry version 9.0.3; missing locally | Run existing `tests/` suite from `pyproject.toml` | `pyproject.toml` configures pytest discovery and `.planning/codebase/TESTING.md` identifies it as the primary runner. [VERIFIED: pyproject.toml] [VERIFIED: pip index] [VERIFIED: local import check] |
| Ultralytics | optional; latest registry version 8.4.46; missing locally | Strict YOLO inference when local weights exist | Existing `YoloDetector` imports `ultralytics.YOLO` only in strict mode, and Ultralytics docs show loading custom weights plus reading boxes/conf/classes from results. [VERIFIED: satellite_edge_node/yolo_detector.py] [VERIFIED: pip index] [CITED: https://github.com/ultralytics/ultralytics/blob/main/docs/en/tasks/detect.md] |

### Supporting

| Library / Tool | Version | Purpose | When to Use |
|----------------|---------|---------|-------------|
| `shutil` | Python standard library | Remove a selected output queue tree for reset workflows | Use for a scoped `--reset-queue` implementation if the queue directory should be deleted and recreated. [CITED: https://docs.python.org/3/library/shutil.html] |
| `pathlib` | Python standard library | Path-safe traversal, file existence checks, and output paths | Continue current repo convention of `Path` objects for filesystem code. [VERIFIED: AGENTS.md] [CITED: https://docs.python.org/3/library/pathlib.html] |
| `tempfile.TemporaryDirectory` | Python standard library | Test isolated raw/queue directories | Existing tests use temporary directories, and Python docs support it as a context manager with cleanup. [VERIFIED: tests/test_satellite_edge_bandwidth.py] [CITED: https://docs.python.org/3/library/tempfile.html] |
| Streamlit | >=1.35 required; latest registry version 1.57.0; missing locally | Ground station display in later phases | Phase 1 should avoid Streamlit edits unless needed for metadata visibility handoff into Phase 2. [VERIFIED: requirements.txt] [VERIFIED: pip index] |
| pandas | >=2.2 required; latest registry version 3.0.2; missing locally | Dashboard tables/charts in later phases | Phase 1 validation can focus on file artifacts and tests, not dashboard rendering. [VERIFIED: requirements.txt] [VERIFIED: pip index] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `--reset-queue` | Per-run directories under `transmission_queue/runs/<run_id>/` | Per-run directories are cleaner long-term but listed as v2 production hardening; `--reset-queue` is faster and sufficient for Phase 1 freshness. [VERIFIED: .planning/REQUIREMENTS.md] [ASSUMED] |
| Strict YOLO only | Baseline simulation with explicit labels | Strict YOLO is required for real detector claims, but baseline remains useful when disclosed as simulation and can still prove the file-queue architecture. [VERIFIED: .planning/PROJECT.md] [VERIFIED: satellite_edge_node/baseline_detector.py] |
| New image/crop library | Pillow | Pillow is already in requirements and current code; adding another image library violates the dependency constraint without improving Phase 1. [VERIFIED: requirements.txt] [VERIFIED: .planning/PROJECT.md] |

**Installation:**

```bash
python -m pip install -r requirements.txt
python -m pip install pytest
# Optional strict YOLO only:
python -m pip install ultralytics
```

**Version verification:**

```bash
pip index versions Pillow
pip index versions pytest
pip index versions ultralytics
pip index versions streamlit
pip index versions pandas
```

## Architecture Patterns

### System Architecture Diagram

```text
Judge / CLI
  |
  | 1. preflight: python scripts/check_model_ready.py --json
  v
Detector readiness status
  |
  | 2. fresh run command with --reset-queue or isolated queue path
  v
satellite_edge_node.orbital_pass
  |
  +--> discover readable raw/demo raster tiles
  |
  +--> detector router
  |      |
  |      +--> strict yolo: require weights + ultralytics, fail loudly if missing
  |      |
  |      +--> baseline/fallback: allowed only when explicitly simulated
  |
  +--> payload builder
         |
         +--> if alert + bbox + readable raster: create crops/<tile>_crop.png
         |
         +--> write <tile>.json payload with detector truth metadata
         |
         +--> write fresh telemetry.jsonl with byte accounting and crop status
  |
  v
transmission_queue/
  |
  +--> judge inspects JSON payload, telemetry, and crop file
```

### Recommended Project Structure

```text
satellite_edge_node/
├── orbital_pass.py      # add CLI reset/isolation and keep detector failure behavior
├── payloads.py          # keep crop file and payload reference integrity
├── detectors.py         # preserve explicit fallback metadata
└── yolo_detector.py     # strict local YOLO setup and result normalization
scripts/
└── check_model_ready.py # model preflight for judge command sequence
tests/
├── test_satellite_edge_bandwidth.py # add fresh queue and crop-ref assertions
├── test_yolo_detector.py            # keep strict/fallback behavior tests
└── test_model_readiness_eval.py     # keep readiness JSON tests
```

### Pattern 1: Scoped Fresh Queue Reset

**What:** Add an explicit CLI option that removes only generated artifacts under the selected queue directory before a run, then recreates the directory and writes a new telemetry file. [VERIFIED: satellite_edge_node/orbital_pass.py] [CITED: https://docs.python.org/3/library/shutil.html]

**When to use:** Use it for DEMO-01 and VAL-04 when the final judge command targets `transmission_queue/` or another demo queue path. [VERIFIED: .planning/REQUIREMENTS.md]

**Example:**

```python
# Source: Python shutil docs and existing Path-based repo style
if reset_queue and transmission_queue.exists():
    shutil.rmtree(transmission_queue)
transmission_queue.mkdir(parents=True, exist_ok=True)
```

### Pattern 2: Strict Detector Preflight + Runtime Enforcement

**What:** Treat `scripts/check_model_ready.py --json` as the preflight and `--detector yolo` as the runtime enforcement path; a missing model or package must produce non-zero readiness and non-zero strict-run status. [VERIFIED: scripts/check_model_ready.py] [VERIFIED: satellite_edge_node/orbital_pass.py]

**When to use:** Use before any run that claims real detector behavior. [VERIFIED: .planning/PROJECT.md]

**Example:**

```bash
python scripts/check_model_ready.py --json
python -m satellite_edge_node.orbital_pass --detector yolo --reset-queue
```

### Pattern 3: Crop Claims Must Be File-Backed

**What:** Keep the current invariant: `crop_ref` is non-null only when `generate_crop_file()` saved a file, and telemetry records `crop_error` when no crop can be produced. [VERIFIED: satellite_edge_node/payloads.py] [VERIFIED: tests/test_satellite_edge_bandwidth.py]

**When to use:** Use for DEMO-04 and all alert payloads that have a bbox. [VERIFIED: .planning/REQUIREMENTS.md]

**Example:**

```python
# Source: Pillow Image.crop docs and existing generate_crop_file() pattern
with Image.open(tile_path) as image:
    crop_box = _crop_box_from_bbox(detection.bbox, image.size)
    image.crop(crop_box).save(crop_path, format="PNG")
```

### Anti-Patterns to Avoid

- **Appending final-demo telemetry:** Appending to `telemetry.jsonl` makes mixed detector modes and duplicate tile IDs likely. Use reset/isolation for the final demo. [VERIFIED: satellite_edge_node/orbital_pass.py] [VERIFIED: .planning/codebase/CONCERNS.md]
- **Deleting broad repo data:** A reset option must target only the selected queue directory, not `data/`, `datasets/`, or source fixtures. [VERIFIED: .planning/PROJECT.md]
- **Silent fallback:** Do not catch `YoloModelUnavailable` and continue as baseline unless `--allow-baseline-fallback` is explicitly set. [VERIFIED: satellite_edge_node/detectors.py] [VERIFIED: satellite_edge_node/orbital_pass.py]
- **Crop references to missing files:** Never emit non-null `crop_ref` if the crop was not saved. [VERIFIED: satellite_edge_node/payloads.py]
- **Using unreadable `.tile` blobs for crop proof:** Current `.tile` files are root-owned placeholder blobs and not reliable raster proof. [VERIFIED: local file audit] [VERIFIED: .planning/codebase/CONCERNS.md]
- **Moving business logic into Streamlit:** Keep Phase 1 logic in satellite/payload/scripts modules so it remains testable without Streamlit. [VERIFIED: .planning/codebase/ARCHITECTURE.md]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Image crop extraction | Custom byte slicing or ad hoc PNG writing | Pillow `Image.open()`, `Image.crop()`, `Image.save()` | Image formats and bounding boxes are already handled through Pillow APIs and current code. [CITED: https://context7.com/python-pillow/pillow/llms.txt] [VERIFIED: satellite_edge_node/payloads.py] |
| YOLO result parsing from scratch | New detector output schema | Existing `normalize_yolo_results()` over Ultralytics `result.boxes.xyxy`, `conf`, and `cls` | Ultralytics exposes those fields, and current tests already normalize fake result objects. [CITED: https://github.com/ultralytics/ultralytics/blob/main/docs/en/tasks/detect.md] [VERIFIED: tests/test_yolo_detector.py] |
| Freshness tracking through manual instructions only | "Tell judges to delete files first" | CLI reset/isolation plus tests | VAL-04 requires the final demo queue to be generated fresh, and current append behavior is fragile. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: satellite_edge_node/orbital_pass.py] |
| Detector readiness probe | Importing YOLO in shell snippets only | `scripts/check_model_ready.py --json` | Existing script reports weights/package status and returns non-zero when unavailable. [VERIFIED: scripts/check_model_ready.py] |

**Key insight:** The difficult part is not creating new artifacts; it is preventing plausible stale or simulated artifacts from being mistaken for the fresh strict demo proof. [VERIFIED: .planning/research/SUMMARY.md] [VERIFIED: .planning/codebase/CONCERNS.md]

## Common Pitfalls

### Pitfall 1: Mixed Telemetry from Repeated Runs

**What goes wrong:** `telemetry.jsonl` contains rows from old and new runs while payload JSON files reflect only the latest write for each tile ID. [VERIFIED: satellite_edge_node/orbital_pass.py]

**Why it happens:** The runner opens telemetry in append mode and writes payload files by deterministic `tile_id`. [VERIFIED: satellite_edge_node/orbital_pass.py]

**How to avoid:** Add `--reset-queue` or run-isolated output and test that telemetry line count equals the current discovered tiles after reset. [VERIFIED: .planning/ROADMAP.md]

**Warning signs:** Duplicate `tile_id` rows in telemetry, mixed `requested_detector_mode`, or payload file count not matching current telemetry semantics. [VERIFIED: .planning/codebase/CONCERNS.md]

### Pitfall 2: Simulated Baseline Looks Real

**What goes wrong:** Baseline sidecar/filename detections create plausible alerts even though no visual model inference occurred. [VERIFIED: satellite_edge_node/baseline_detector.py]

**Why it happens:** Baseline detector intentionally reads sidecar metadata or filename hints to exercise architecture before real detector setup. [VERIFIED: satellite_edge_node/baseline_detector.py]

**How to avoid:** Preserve `detector_mode`, `detector_is_real`, `simulated`, `fallback_used`, and `fallback_reason` in payloads, telemetry, CLI output, docs, and dashboard handoff. [VERIFIED: satellite_edge_node/payloads.py] [VERIFIED: .planning/REQUIREMENTS.md]

**Warning signs:** Demo output says "detected" without also saying baseline/simulated or fallback. [VERIFIED: .planning/research/SUMMARY.md]

### Pitfall 3: Crop Payloads Without Real Crop Files

**What goes wrong:** A payload claims `crop_ref`, but the referenced file is missing or zero bytes. [VERIFIED: DEMO-04 in .planning/REQUIREMENTS.md]

**Why it happens:** Crop generation depends on readable image input, bbox shape, and Pillow availability. [VERIFIED: satellite_edge_node/payloads.py]

**How to avoid:** Use PNG/JPEG/TIFF fixtures for crop proof, and assert every non-null `crop_ref` exists and has non-zero size. [VERIFIED: tests/test_satellite_edge_bandwidth.py]

**Warning signs:** `crop_error` is non-null, `crop_payload_bytes` is `0`, or input file has `.tile` extension with non-image bytes. [VERIFIED: satellite_edge_node/payloads.py] [VERIFIED: local file audit]

### Pitfall 4: Real YOLO Claim Without Readiness Proof

**What goes wrong:** Evaluation or docs claim real YOLO even though weights or `ultralytics` are missing. [VERIFIED: .planning/codebase/CONCERNS.md]

**Why it happens:** The evaluator can classify telemetry metadata as real YOLO without checking local model readiness or image readability. [VERIFIED: scripts/evaluate_detector.py] [VERIFIED: .planning/codebase/CONCERNS.md]

**How to avoid:** Pair any real-detector claim with `check_model_ready.py --json` and a strict `--detector yolo` run with no fallback. [VERIFIED: scripts/check_model_ready.py] [VERIFIED: satellite_edge_node/orbital_pass.py]

**Warning signs:** `ready_for_strict_yolo=false`, missing weights, missing `ultralytics`, or run command includes `--allow-baseline-fallback`. [VERIFIED: scripts/check_model_ready.py] [VERIFIED: command output 2026-05-06]

### Pitfall 5: Root-Owned Generated Artifacts Block Reset

**What goes wrong:** Normal user execution may fail to reset or overwrite committed/generated artifacts owned by `root`. [VERIFIED: local file audit] [VERIFIED: .planning/codebase/CONCERNS.md]

**Why it happens:** Current `data/raw_tiles/`, `models/.gitkeep`, and `transmission_queue/` files include `root:root` ownership in the local checkout. [VERIFIED: local file audit]

**How to avoid:** Prefer temp/output queue paths in tests; for the final repo demo command, planner should account for ownership normalization or generate into a user-writable fresh queue path. [VERIFIED: tests/test_satellite_edge_bandwidth.py] [ASSUMED]

**Warning signs:** `PermissionError` during queue reset or payload write. [ASSUMED]

## Code Examples

Verified patterns from official and local sources:

### CLI Strict Failure Boundary

```python
# Source: satellite_edge_node/orbital_pass.py
try:
    records = simulate_orbital_pass(..., detector_mode=args.detector)
except YoloDetectorError as exc:
    print(f"Detector setup failed: {exc}")
    return 2
```

### Fallback Truth Metadata

```python
# Source: satellite_edge_node/detectors.py
return replace(
    detection,
    detector_mode="fallback",
    detector_is_real=False,
    simulated=True,
    fallback_used=True,
    fallback_reason=self.reason,
)
```

### Crop Generation

```python
# Source: Pillow docs and satellite_edge_node/payloads.py
with Image.open(tile_path) as image:
    crop_box = _crop_box_from_bbox(detection.bbox, image.size)
    image.crop(crop_box).save(crop_path, format="PNG")
```

### Model Readiness JSON

```python
# Source: scripts/check_model_ready.py
{
    "weights_exist": weights_exist,
    "ultralytics_available": ultralytics_available,
    "ready_for_strict_yolo": ready,
    "status": "real detector available" if ready else "real detector unavailable",
    "missing": missing,
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Generic placeholder architecture demo | Strict, honest proof chain with fresh queue, detector status, crop file, payload JSON, and dashboard handoff | Phase 1 planning on 2026-05-06 | Planner should turn existing primitives into a reproducible judge command sequence. [VERIFIED: .planning/ROADMAP.md] |
| Silent or ambiguous detector fallback | Strict YOLO failure unless explicit fallback is requested | Already implemented before Phase 1 | Planner should preserve and test this behavior at CLI level. [VERIFIED: satellite_edge_node/detectors.py] [VERIFIED: satellite_edge_node/orbital_pass.py] |
| Placeholder `.tile` demo flow | Readable raster or explicitly disclosed fixture for crop proof | Required by Phase 1 | Planner must include a real PNG/JPEG/TIFF crop fixture path or a disclosed simulated raster fixture. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: satellite_edge_node/payloads.py] |

**Deprecated/outdated:**

- Treating committed `transmission_queue/` as final proof is outdated for Phase 1 because VAL-04 requires a fresh generated queue. [VERIFIED: .planning/REQUIREMENTS.md]
- Treating `.tile` placeholders as real imagery is explicitly disallowed. [VERIFIED: .planning/PROJECT.md] [VERIFIED: .planning/research/SUMMARY.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `--reset-queue` is the fastest acceptable implementation compared with full per-run directories. | Standard Stack / Architecture Patterns | If the user wants production-style run directories in Phase 1, a reset-only plan may underdeliver traceability. |
| A2 | Ownership normalization can be handled by generating into a user-writable queue path if root-owned committed artifacts cannot be changed. | Common Pitfalls | If final docs must use exactly `transmission_queue/`, planner may need an ownership or cleanup task. |
| A3 | `PermissionError` is the likely failure mode for root-owned queue reset. | Common Pitfalls | If the actual failure differs, tests may need broader filesystem error assertions. |

## Open Questions

1. **Should Phase 1 use reset-in-place or per-run output directories?**
   - What we know: ROADMAP plan 01-01 names "queue reset/run isolation", and production run IDs are deferred to v2. [VERIFIED: .planning/ROADMAP.md] [VERIFIED: .planning/REQUIREMENTS.md]
   - What's unclear: Whether judges should always inspect `transmission_queue/` or a generated path such as `transmission_queue/demo_run/`. [ASSUMED]
   - Recommendation: Use `--reset-queue` for the selected queue path now; optionally allow `--transmission-queue transmission_queue/demo_run` without adding a run registry. [ASSUMED]

2. **What readable raster should be the canonical crop-proof input?**
   - What we know: Current committed `data/raw_tiles/*.tile` files are placeholder blobs and root-owned; crop proof requires readable raster input. [VERIFIED: local file audit] [VERIFIED: satellite_edge_node/payloads.py]
   - What's unclear: Whether a license-checked real image is already available outside the scanned files. [ASSUMED]
   - Recommendation: Use or add one small disclosed PNG fixture with sidecar bbox for Phase 1 if no real licensed image is ready. [ASSUMED]

3. **Should payload JSON duplicate byte accounting from telemetry?**
   - What we know: DEMO-03 asks for payload JSON containing detector metadata, triage action, byte accounting, and crop/full-downlink decision; current byte accounting is primarily telemetry-side. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: satellite_edge_node/payloads.py]
   - What's unclear: Whether "payload JSON" can mean payload plus telemetry record in judge workflow. [ASSUMED]
   - Recommendation: Add minimal byte/action fields to alert payload JSON or generate a small run summary JSON so DEMO-03 is satisfied without requiring source-code knowledge. [ASSUMED]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | All Phase 1 commands | yes | 3.14.4 local | Project requires >=3.11. [VERIFIED: `python --version`] [VERIFIED: pyproject.toml] |
| Pillow | Crop generation and image validation | yes | 12.2.0 local | None for real crop proof; without Pillow, crops report an error. [VERIFIED: local import check] [VERIFIED: satellite_edge_node/payloads.py] |
| pytest | Automated test suite | no | registry latest 9.0.3 | Install `pytest`; stdlib `unittest` can be a fallback for many tests. [VERIFIED: `python -m pytest --version`] [VERIFIED: .planning/codebase/TESTING.md] |
| ultralytics | Strict YOLO real detector mode | no | registry latest 8.4.46 | Baseline simulation with explicit labels only; no real detector claim. [VERIFIED: local import check] [VERIFIED: pip index] |
| YOLO weights | Strict YOLO real detector mode | no | `models/brick_kiln_yolo.pt` missing | Baseline simulation with explicit labels only; no real detector claim. [VERIFIED: scripts/check_model_ready.py --json] |
| Streamlit | Dashboard handoff in later phase | no | registry latest 1.57.0 | Phase 1 can validate artifacts without dashboard runtime. [VERIFIED: local import check] [VERIFIED: requirements.txt] |
| pandas | Dashboard handoff in later phase | no | registry latest 3.0.2 | Phase 1 can validate artifacts without dashboard runtime. [VERIFIED: local import check] [VERIFIED: requirements.txt] |

**Missing dependencies with no fallback:**

- Real strict YOLO proof is blocked until both `ultralytics` and `models/brick_kiln_yolo.pt` are available. [VERIFIED: scripts/check_model_ready.py --json]
- `pytest` is missing locally, so the normal test command cannot run until installed. [VERIFIED: `python -m pytest --version`]

**Missing dependencies with fallback:**

- Streamlit and pandas are missing locally, but Phase 1 can still verify queue artifacts, detector readiness, and crops without launching the dashboard. [VERIFIED: local import check]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | Current workflows are local CLI/demo flows with no authentication boundary. [VERIFIED: .planning/codebase/ARCHITECTURE.md] |
| V3 Session Management | no | No server-side user sessions exist in Phase 1. [VERIFIED: .planning/codebase/ARCHITECTURE.md] |
| V4 Access Control | yes | Keep reset/delete operations scoped to the selected queue directory and do not expose them through a remote service. [VERIFIED: .planning/codebase/CONCERNS.md] |
| V5 Input Validation | yes | Validate detector mode choices, model paths, bbox shape, and readable image inputs through existing argparse and payload checks. [VERIFIED: satellite_edge_node/orbital_pass.py] [VERIFIED: satellite_edge_node/payloads.py] |
| V6 Cryptography | no | Phase 1 has no cryptographic protocol or secret handling. [VERIFIED: .planning/codebase/ARCHITECTURE.md] |

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Over-broad queue deletion | Tampering | Limit reset to the CLI-provided queue path; avoid deleting `data/`, `datasets/`, or parent directories. [VERIFIED: .planning/codebase/CONCERNS.md] |
| Path leakage in shareable telemetry | Information Disclosure | Prefer relative paths in public-facing payloads/telemetry or document that local paths are demo artifacts. [VERIFIED: .planning/codebase/CONCERNS.md] |
| Misleading detector metadata | Spoofing | Preserve `detector_is_real`, `simulated`, `fallback_used`, and `fallback_reason` across detector, payload, telemetry, and UI surfaces. [VERIFIED: satellite_edge_node/payloads.py] |

## Sources

### Primary (HIGH confidence)

- `.planning/PROJECT.md` - project constraints, honesty boundaries, detector readiness, ground-station boundary.
- `.planning/STATE.md` - current phase, decisions, blockers.
- `.planning/ROADMAP.md` - Phase 1 goal, requirements, success criteria, and plans.
- `.planning/REQUIREMENTS.md` - DEMO/HON/VAL requirement definitions and v2 deferrals.
- `.planning/research/SUMMARY.md` - submission strategy and watch-outs.
- `.planning/codebase/ARCHITECTURE.md` - layer ownership, data flow, anti-patterns.
- `.planning/codebase/CONCERNS.md` - stale telemetry, root-owned files, detector/evaluator fragility.
- `.planning/codebase/TESTING.md` - test framework and commands.
- `AGENTS.md` - project constraints, dependency policy, GSD workflow enforcement.
- `satellite_edge_node/orbital_pass.py` - queue write/append behavior and CLI detector handling.
- `satellite_edge_node/payloads.py` - crop generation, payload fields, telemetry fields.
- `satellite_edge_node/detectors.py` - strict/fallback detector routing.
- `satellite_edge_node/yolo_detector.py` - YOLO readiness and result normalization.
- `satellite_edge_node/baseline_detector.py` - simulated baseline semantics.
- `scripts/check_model_ready.py` - model readiness command.
- `tests/test_satellite_edge_bandwidth.py`, `tests/test_yolo_detector.py`, `tests/test_model_readiness_eval.py` - existing regression patterns.
- Context7 `/python-pillow/pillow` - Pillow crop/open/save APIs.
- Context7 `/ultralytics/ultralytics` - YOLO model loading and result boxes API.
- Python docs - `shutil`, `pathlib`, and `tempfile` filesystem APIs.
- `pip index versions` - current registry versions for Streamlit, pandas, Pillow, pytest, and ultralytics.

### Secondary (MEDIUM confidence)

- Local command probes on 2026-05-06 - Python version, installed/missing packages, local model-readiness output, local file ownership.

### Tertiary (LOW confidence)

- None.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - versions checked through pip index and local imports; architecture constrained by existing repo files.
- Architecture: HIGH - phase maps directly onto existing modules and planning artifacts.
- Pitfalls: HIGH - main risks are explicitly documented in `.planning/codebase/CONCERNS.md` and visible in source.
- External docs: HIGH - Pillow and Ultralytics APIs verified through Context7/official source docs; Python filesystem APIs verified through official docs.

**Research date:** 2026-05-06
**Valid until:** 2026-05-13 for dependency versions; architecture findings valid until Phase 1 implementation changes land.

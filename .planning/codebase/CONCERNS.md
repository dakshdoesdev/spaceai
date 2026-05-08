# Codebase Concerns

**Analysis Date:** 2026-05-09

Concerns are ordered by severity, then by area. Each entry carries severity (BLOCKER / HIGH / MEDIUM / LOW), area (correctness / honesty / dependency / dx / docs / performance / security), file evidence, status (open / mitigated / wontfix), and a recommended next action.

## Severity Index

| # | Severity | Area | Title | Status |
|---|----------|------|-------|--------|
| H1 | HIGH | honesty | No detection-quality evaluation rigor | open |
| H2 | HIGH | honesty | Demo provenance is Roboflow imagery, not Sentinel-2 / SimSat / Haryana | mitigated |
| H3 | HIGH | correctness | Evaluator silently overwrites duplicate `tile_id` rows | open |
| M1 | MEDIUM | performance | Liquid local inference is slow on CPU (~3 min / 14 tiles) | open |
| M2 | MEDIUM | honesty | No fine-tuning performed on Liquid base model | open |
| M3 | CLOSED | correctness | Four-tier triage now drives the transmit gate (was: metadata only) | resolved |
| M4 | MEDIUM | dx | Large uncommitted churn (~98 changes) on a single working tree | open |
| M5 | MEDIUM | docs | `liquid-ollama` documented as a CLI flag but no code path exists | open |
| M6 | MEDIUM | correctness | `_from_filename` assigns `compliance_risk="high"` to non-kiln tiles | open |
| M7 | MEDIUM | dx | `pyproject.toml` declares no runtime deps; installed CLI is broken | open |
| L1 | LOW | dependency | Ollama LFM2 GGUF load bug blocks `liquid-ollama` deployment path | mitigated |
| L2 | LOW | dx | `models/liquid/` is dormant (~390 MB committed-on-disk) | open |
| L3 | LOW–MEDIUM | dependency | No lockfile; optional deps unpinned; `requirements.txt` floors only | open |
| L4 | LOW | dx | `--write-drop-payloads` is legacy/debug, can pollute queue | open |

---

## HIGH

### H1 — No model evaluation rigor

- **Severity:** HIGH (honesty)
- **Files:** `scripts/evaluate_detector.py`, `tests/` (66 tests, none score detection accuracy on labelled imagery), `docs/final_demo_evidence.md`, `docs/technical_honesty.md`
- **Description:** The repo has 66 unit tests but no held-out detection accuracy evaluation, no precision/recall, no F1 against labelled imagery. `scripts/evaluate_detector.py` does compute `precision`, `recall`, `accuracy`, and `roc_auc` via sklearn (lines 70–90), but only when telemetry is matched against a manifest by `tile_id` — and it does not require image readability, model presence, or strict-run provenance to classify a result as `real_yolo` (lines 49–50). `docs/latest_evaluation.json` is referenced by `docs/technical_honesty.md:13` but does not exist in the tree. The 116×/168× compression numbers reported in `README.md` and `app.py` are byte accounting, not detection quality.
- **Status:** open. README is honest about the gap (`README.md:135`: "no validated brick-kiln detection accuracy on Sentinel-domain data"), so this is honesty-disclosed, but the gap itself is real.
- **Next action:** Build a held-out labelled set under `datasets/kilnwatch/labels/`, run strict YOLO against it via `scripts/evaluate_detector.py`, persist the result to `docs/latest_evaluation.json`. Gate any future "production" claim surface (README hero, dashboard) on the existence of that file.

### H2 — Demo provenance is Roboflow brick-kiln imagery, not Sentinel-2 / SimSat / Haryana ground-truth

- **Severity:** HIGH (honesty)
- **Files:** `data/final_demo_tiles/*.jpg` (14 Roboflow brick-kiln tiles, untracked), `README.md:100-106`, `docs/technical_honesty.md` ("Unsafe Claims" section), `app.py` (imagery-provenance panel), `data/raw_tiles/haryana_*.tile` (placeholder bytes)
- **Description:** The 14 demo tiles in `data/final_demo_tiles/` are open-source Roboflow brick-kiln imagery (filenames such as `Bangladesh_143_jpg.rf.*.jpg`, `UP_226_jpg.rf.*.jpg`, `T_50_jpg.rf.*.jpg`). They are real overhead images of brick kilns but are not Sentinel-2 or DPhi SimSat tiles, and have no Haryana ground-truth. The risk is that judges or future contributors silently treat these as Sentinel-derived. The `data/raw_tiles/haryana_*.tile` files are placeholder bytes with `.meta.json` sidecars, not real imagery.
- **Status:** mitigated. Disclosed explicitly in `README.md:100-106`, `docs/technical_honesty.md` ("Do not claim Roboflow/demo fixture images are Haryana or Sentinel imagery"), and the dashboard imagery-provenance panel.
- **Next action:** Keep the disclosures; do not regress them. When swapping in DPhi SimSat / Sentinel-2 imagery, retire the Roboflow path or move it under `data/demo/` with a README marker so it cannot be confused with operational ingestion.

### H3 — Evaluator silently overwrites duplicate `tile_id` rows in telemetry

- **Severity:** HIGH (correctness)
- **Files:** `scripts/evaluate_detector.py:25` (`telemetry_by_tile = {str(row.get("tile_id")): row for row in telemetry_rows if row.get("tile_id")}`), `transmission_queue/telemetry.jsonl`, `satellite_edge_node/orbital_pass.py:64` (telemetry opened in append mode unless `--reset-queue`)
- **Description:** The evaluator joins manifest rows to telemetry by `tile_id` using a plain dict comprehension. Repeated runs append to `telemetry.jsonl` (only `--reset-queue` truncates), and the evaluator silently keeps only the last row per `tile_id`. There is no run-ID, timestamp, or detector-mode filter on the join. A baseline run followed by a YOLO run will be evaluated as YOLO; a YOLO run followed by a debug baseline run will be evaluated as baseline. No test covers mixed-run telemetry.
- **Status:** open.
- **Next action:** Write each run under `transmission_queue/runs/<run_id>/` (already named in `docs/technical_honesty.md` "Future Integrations"), add `run_id` + `timestamp_utc` to telemetry rows, require an explicit `--run-id` selector in the evaluator, and reject duplicate `tile_id` rows otherwise.

---

## MEDIUM

### M1 — Liquid local inference is slow on CPU

- **Severity:** MEDIUM (performance)
- **Files:** `satellite_edge_node/liquid_vlm_reasoner.py:85-184` (`LiquidLocalReasoner`), `README.md:96` ("the orbital pass takes ~2–4 minutes the first time it loads `LiquidAI/LFM2.5-VL-450M`")
- **Description:** `LiquidLocalReasoner` runs `LiquidAI/LFM2.5-VL-450M` via `transformers.AutoModelForImageTextToText` with `do_sample=False`, `max_new_tokens=256`. The only device handling is `if hasattr(self.model, "device"): inputs = inputs.to(self.model.device)` (line 168). There is no explicit `.to("cuda")` or device-map argument; on a CPU box, an orbital pass over 14 tiles takes ~2–4 minutes (README's own honesty note, plus the prompt's "~3 min per orbital pass on 14 tiles"). Acceptable for the demo, blocks rapid iteration and any larger batch.
- **Status:** open.
- **Next action:** Add a `--device {auto,cpu,cuda}` flag to `--reasoner liquid-local`, default `auto`, route via Transformers' `device_map`/`torch_dtype`. Add a `--reasoner-batch-size` parameter and stream tile detections to the reasoner in batches.

### M2 — No fine-tuning performed on Liquid base model

- **Severity:** MEDIUM (honesty)
- **Files:** `satellite_edge_node/liquid_vlm_reasoner.py:13` (`MODEL_NAME = "LiquidAI/LFM2.5-VL-450M"`), `README.md:134`, `docs/technical_honesty.md` ("Unsafe Claims" + "Future Integrations")
- **Description:** Base `LiquidAI/LFM2.5-VL-450M` is used as-is. The reasoning prompt template (`liquid_vlm_reasoner.py:122-148`) explicitly references the Liquid cookbook satellite-vlm pattern and VRSBench format, but no fine-tuning has been run. The cookbook recipe is named in comments as the documented next step. Reasoning text is generic.
- **Status:** open. Clearly disclosed (`README.md:134`: "Liquid LFM2-VL fine-tuning on brick-kiln imagery (the model is the open base; no fine-tune was performed)").
- **Next action:** Run the Liquid cookbook satellite-vlm fine-tune against the same labelled set produced for H1; ship the fine-tuned weights as a separate model id and gate `--reasoner liquid-local` on which checkpoint is loaded so telemetry can record `model_name="LiquidAI/LFM2.5-VL-450M-kilnwatch-ft"` only when applicable.

### M3 — Four-tier triage as the actual transmit gate (RESOLVED 2026-05-09)

- **Severity:** was MEDIUM — now CLOSED
- **Files:** `satellite_edge_node/payloads.py` (`transmission_action_for`, `should_transmit_triage`, `crop_required_for`, `full_tile_required_for`, `copy_full_tile`, `FullTileArtifact`), `satellite_edge_node/orbital_pass.py` (main loop dispatches by tier)
- **Description:** the four-tier `TriageDecision` is now the runtime transmit gate. `IGNORE` drops with telemetry only; `JSON_ALERT_ONLY` writes a metadata-only payload (no `crop_ref`); `CROP_OR_REVIEW` writes JSON + crop; `FULL_DOWNLINK` additionally copies the source tile to `transmission_queue/full_tiles/<tile_id>_full.<ext>` with `full_tile_ref` recorded in the payload. `--require-crops` enforces a real crop only on the two tiers that need one. The legacy `should_transmit_alert(detection)` boolean is preserved for back-compat callers but is no longer the runtime gate.
- **Verification:** three new tier-specific tests lock the behavior:
  - `test_full_downlink_tier_copies_full_tile_into_queue` — high-conf high-risk fixture → `TRANSMIT_FULL_TILE`, raw tile bytes copied into `full_tiles/`, sizes match.
  - `test_json_only_tier_writes_payload_without_crop` — kiln + low risk → `TRANSMIT_JSON_ONLY`, no `crop_ref`, no crop file generated.
  - `test_ignore_tier_drops_tile_with_no_payload` — low-confidence non-kiln → telemetry only, no JSON payload on disk.
- **Status:** closed. 69/69 tests pass with the new gate. End-to-end on demo tiles: 14 → 9 IGNORE + 5 CROP_OR_REVIEW, 165× compression, no FULL_DOWNLINK fired (under YOLO-only with confidence ≤ 0.85).

### M4 — Large uncommitted churn on a single working tree

- **Severity:** MEDIUM (dx)
- **Files:** working tree (`git status --short` reports 98 entries: 22 deletions, 24 modifications, 52 untracked including the `panipat → haryana` rename, `docs/youtube_script.md`, `data/final_demo_tiles/`, `transmission_queue.backup_2026-05-09/`, `tmp_brick_kiln/`, `models/liquid/`, refactored payloads/telemetry, new `kilnwatch/datasets/adapters/apad_igp.py`, new `scripts/process_apad.py`, new `scripts/smoke_fetch_haryana.py`)
- **Description:** No stashes, no in-flight branch. Last commit (`4a8f19b "Make dashboard sections actually navigable"`) is well behind the current state. High lost-work risk: a rebase, branch switch, or accidental `git checkout .` would destroy tens of files of work. Two of the untracked directories are sizeable (`tmp_brick_kiln/` 38 MB, `models/liquid/` 390 MB) and `transmission_queue.backup_2026-05-09/` is a parallel queue tree that exists only on disk.
- **Status:** open.
- **Next action:** Stage and commit in three logical chunks: (a) the panipat → haryana rename + region config + manifests, (b) payloads/telemetry + triage refactor + tests, (c) docs (`youtube_script.md`, updated `technical_honesty.md`, `submission_checklist.md`). Decide on `tmp_brick_kiln/`, `transmission_queue.backup_2026-05-09/`, `models/liquid/`, and `Brick Kiln Detection.v1-dataset_aug.yolov8/` separately — likely `.gitignore` rather than commit. Avoid committing `models/liquid/` GGUF blobs.

### M5 — `liquid-ollama` documented as a CLI flag but no code path exists

- **Severity:** MEDIUM (docs drift, correctness-affecting)
- **Files:** `README.md:118` (`--reasoner liquid-ollama` listed with "currently broken in Ollama 0.17.5; use `liquid-local`"), `docs/technical_honesty.md:45` (`liquid-ollama` reasoner backend "path exists in code; broken on Ollama 0.17.5"), `satellite_edge_node/orbital_pass.py:174` (only accepts `("disabled", "liquid-mock", "liquid-local")`), `satellite_edge_node/liquid_vlm_reasoner.py:187-195` (`build_reasoner` raises `ValueError` for any other mode)
- **Description:** Both docs claim a `--reasoner liquid-ollama` flag exists; argparse will reject it with `SystemExit(2)` at `orbital_pass.py:174` because `choices=("disabled","liquid-mock","liquid-local")`, and `build_reasoner` would also raise. There is no `LiquidOllamaReasoner` class anywhere (`grep -rn "LiquidOllamaReasoner\|liquid-ollama" --include="*.py"` returns nothing). A user copy-pasting the documented command will hit "argument --reasoner: invalid choice".
- **Status:** open.
- **Next action:** Either (a) remove `liquid-ollama` from `README.md:118` and `docs/technical_honesty.md:45` and replace with a forward-looking "future" bullet, or (b) re-add the class behind a flag once Ollama upstream fixes LFM2 (see L1) and document the upstream constraint precisely. Pick (a) for now.

### M6 — Baseline `_from_filename` assigns `compliance_risk="high"` to non-kiln tiles

- **Severity:** MEDIUM (correctness)
- **Files:** `satellite_edge_node/baseline_detector.py:86-100` (`_from_filename`), `transmission_queue/telemetry.jsonl`, `data/raw_tiles/haryana_settlement_negative_001.tile` (untracked but present)
- **Description:** `_from_filename` sets `high_risk = any(token in name for token in ("high", "settlement", "active"))` and then `risk = "high"` when `high_risk` is true — independent of `kiln_detected`. So `haryana_settlement_negative_001.tile` produces a record with `kiln_detected=False`, `compliance_risk="high"`, and `action="DROP_RAW_TILE"` (because `should_transmit_alert` requires `kiln_detected`), but the high-risk band still appears in telemetry, the dashboard, and the triage label. This was flagged in the prior CONCERNS.md and is still unfixed.
- **Status:** open.
- **Next action:** Compute `risk` only after `kiln_detected` is true: e.g. `risk = "high" if kiln_detected and high_risk else ("medium" if kiln_detected else "low")`. Add a regression test in `tests/test_satellite_edge_bandwidth.py` covering `settlement_negative_*.tile`.

### M7 — `pyproject.toml` declares no runtime dependencies; installed CLI is broken

- **Severity:** MEDIUM (dx / dependency)
- **Files:** `pyproject.toml` (lines: `dependencies = []`, plus two `[project.scripts]` entries `kilnwatch-fetch-haryana = "kilnwatch.ingestion.cli:main"` and `kilnwatch-orbital-pass = "satellite_edge_node.orbital_pass:main"`), `requirements.txt` (only `streamlit>=1.35`, `pandas>=2.2`, `Pillow>=10`)
- **Description:** A clean `pip install .` installs the package and creates the two console scripts, but pulls in zero runtime dependencies. `kilnwatch-orbital-pass` imports Pillow indirectly (crops), Ultralytics (in `--detector yolo`), and Transformers (in `--reasoner liquid-local`) — none of which are declared. Users following any pip-only install path get a CLI that fails on import or first invocation. `requirements.txt` floors only and does not constrain Ultralytics, Transformers, or Torch versions.
- **Status:** open.
- **Next action:** Move `streamlit`, `pandas`, `Pillow` into `pyproject.toml`'s `dependencies`. Add `[project.optional-dependencies]` groups: `yolo = ["ultralytics>=8.x,<9"]`, `liquid = ["transformers>=4.x", "torch>=2.x"]`, `eval = ["scikit-learn>=1.x"]`. Generate a `uv.lock` or `requirements-lock.txt` for reproducible installs.

---

## LOW

### L1 — Ollama LFM2 GGUF load bug (upstream) blocks `liquid-ollama` deployment path

- **Severity:** LOW (dependency / external)
- **Files:** `models/liquid/LFM2.5-VL-450M-Q4_0.gguf`, `models/liquid/mmproj-LFM2.5-VL-450m-F16.gguf`, `models/liquid/Modelfile`
- **Description:** Ollama 0.17.5 fails to load `LiquidAI/LFM2.5-VL-450M` GGUFs (Q4_0 and Q8_0, official files) with `missing tensor 'output_norm'`. KilnWatch's response: removed `--reasoner liquid-ollama` from the CLI choices and removed `LiquidOllamaReasoner` class (verified — see M5 evidence). The `models/liquid/` GGUF + mmproj + Modelfile files are now inert; nothing in the Python code references them.
- **Status:** mitigated (workaround: `--reasoner liquid-local` via Transformers).
- **Next action:** Track upstream Ollama LFM2 support. When fixed, re-add a `LiquidOllamaReasoner` class behind `--reasoner liquid-ollama`, point it at the local Ollama daemon, and remove the docs caveat in M5.

### L2 — `models/liquid/` is dormant and large

- **Severity:** LOW (dx / storage)
- **Files:** `models/liquid/LFM2.5-VL-450M-Q4_0.gguf` (~219 MB), `models/liquid/mmproj-LFM2.5-VL-450m-F16.gguf` (~189 MB), `models/liquid/Modelfile` (72 bytes)
- **Description:** The directory totals ~390 MB on disk, all untracked. Modelfile content is `FROM ./LFM2.5-VL-450M-Q4_0.gguf` then `ADAPTER ./mmproj-LFM2.5-VL-450m-F16.gguf` — the `ADAPTER` directive in Ollama means LoRA adapter, not multimodal projector, so the Modelfile was always semantically wrong even before the Ollama bug in L1. No Python code references these files (`grep -rn "models/liquid\|LFM2.5-VL-450M-Q4_0\|mmproj-LFM2"` returns zero hits in `.py` or `.md`). Cleanup was previously blocked because the prompt said file deletion was denied as out-of-scope local destruction.
- **Status:** open (storage-only cost; not in git).
- **Next action:** Add `models/liquid/` to `.gitignore` (already protected by global `*.pt` rule but GGUFs are not pt). Either delete the directory locally with explicit user confirmation, or fold it into a documented `models/inert/` quarantine. If kept, fix the Modelfile to use `--mmproj` syntax / a multimodal-aware Modelfile so the directory is at least self-documenting.

### L3 — No lockfile; optional deps unpinned

- **Severity:** LOW–MEDIUM (dependency)
- **Files:** `requirements.txt` (`streamlit>=1.35`, `pandas>=2.2`, `Pillow>=10` — floors only), `pyproject.toml` (`dependencies = []`)
- **Description:** No `uv.lock`, no `pip-tools` `requirements-lock.txt`, no `poetry.lock`. Optional deps (`ultralytics`, `transformers`, `torch`, `scikit-learn`) are only mentioned in README install instructions, never pinned. Reproducibility risk: any future Streamlit, Ultralytics, or Transformers release that breaks the API surface used here will silently break the dashboard or detector. Folds into M7.
- **Status:** open.
- **Next action:** See M7. Pin tested versions and ship a lockfile.

### L4 — `--write-drop-payloads` CLI flag is legacy/debug, can pollute queue

- **Severity:** LOW (dx)
- **Files:** `satellite_edge_node/orbital_pass.py:46,86,196-199,213` (`--write-drop-payloads`, help text "Legacy/debug mode: write JSON files for dropped tiles instead of telemetry-only drops")
- **Description:** When `--write-drop-payloads` is passed, the orbital-pass loop writes a JSON payload for every tile, including `DROP_RAW_TILE` actions (`orbital_pass.py:86: if should_transmit_alert(detection) or write_drop_payloads`). The dashboard's bandwidth-saved math counts these JSONs as `transmitted_payload_bytes`, which inflates downlink totals and compresses the saved-bytes ratio. There is no UI marker that a run was made with this flag.
- **Status:** open.
- **Next action:** Either (a) remove the flag entirely once nothing depends on it, or (b) tag drop-payload JSON files (e.g. write to `transmission_queue/dropped/` or set `event="dropped"` in the payload — already done at `payloads.py:108-117`) and exclude them from byte accounting and the alerts table in `app.py`.

---

## Concerns Reviewed and Out of Scope

- **MCP / Figma instructions in the inbound prompt** — not part of the codebase; ignored.
- **Pre-existing CONCERNS.md (2026-05-06)** — replaced by this analysis. Several items there (overlapping ground-station readers, telemetry append accumulation, dataset adapter placeholders, Streamlit `unsafe_allow_html`, baseline `compliance_risk` filename bug, evaluator `tile_id` join) were re-verified; the still-open ones are folded into M3, M6, H3, M5 above. Items resolved or no longer applicable (e.g. `transmission_queue.backup_2026-05-09/` exists; ground-station boundary now centralized through `kilnwatch.ground_station._safe_crop_path` per `docs/technical_honesty.md:38`) were dropped to keep the surface actionable.

---

*Concerns audit: 2026-05-09*

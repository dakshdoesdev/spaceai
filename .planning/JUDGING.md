# KilnWatch — Hackathon Judging Strategy

**Authored:** 2026-05-09 (dux strategic brief, transcribed).
**Source:** Direct dux directive following judging-criteria analysis.

## Hero Sentence (memorize)

> **KilnWatch is a satellite-edge intelligence system that reduces brick-kiln monitoring bandwidth by deciding onboard what evidence is worth transmitting.**

NOT "we built a brick kiln detector." NOT "another satellite VLM app." Satellite-edge **triage** is the product.

## Track Decision

**Liquid Track** — Liquid LFM2.5-VL-450M is verified real (`reasoner_is_real: true` across 5/14 demo tiles, 2026-05-09 run). Liquid must feel central, not decorative.

**Liquid framing for submission:**
> YOLO proposes candidate kiln regions. LFM2-VL reasons over each crop and metadata to decide whether it is actually kiln-like, whether it needs human review, and what alert metadata to attach. Liquid is the onboard reasoning layer that turns visual detections into compact structured intelligence.

NOT: "Liquid optionally explains crop." Liquid IS the reasoning/compression layer.

## Five Judging Criteria — How We Score Now

| Criterion | Current state | What we must do |
|---|---|---|
| **Use of DPhi satellite imagery** | ~~MEDIUM/HIGH RISK~~ → **GAP CLOSED** as of spike 001 (2026-05-09). The pipeline now ingests real DPhi-served Sentinel-2 tiles end-to-end. Demo path supports both Roboflow optical (where detector + Liquid fire) and DPhi SimSat Sentinel (where the system honestly reports 0 detections, 100% bandwidth saved, "fine-tune is next"). | Keep both paths visible in the demo and the dashboard imagery-provenance panel; the SimSat path is the *honest* DPhi-imagery answer to the rubric. |
| **Innovation & problem-solution fit** | STRONG — onboard triage > ground triage is exactly the rubric's preference for limited-downlink, large-volume, temporal-continuity workloads. | Lead with: "If the image is downlinked, the bandwidth is already spent. Onboard AI reduces what leaves the satellite in the first place." |
| **Technical implementation (must run without debugging)** | RISK — judges must clone, install, and run with zero broken paths. | One-command demo. Sample queue committed so dashboard opens with proof immediately. No "train first" or "download model manually" friction. |
| **Fine-tuning** | WEAK — no documented fine-tune. | Do **not** fake it. Position: "We focused on a runnable satellite-edge system and structured downlink proof. Fine-tuning is the next stage once enough DPhi/Sentinel-domain kiln labels are available." |
| **Demo & communication** | WIN-CONDITION — sounds like a mission, not a code walkthrough. | 3-min video script: problem → old approach → KilnWatch approach → why orbit → Liquid layer → proof. |

## Final Project Story (use this exact structure)

### 1. Problem
> Brick kilns are widespread, polluting, and hard to monitor manually. Satellite imagery can help, but raw imagery is too large to blindly transmit and inspect at scale.

### 2. Old approach
> Capture satellite image, downlink everything, run detection on the ground.

### 3. Our approach
> KilnWatch moves the first decision into orbit. The satellite scans each tile, detects possible kiln structures, and chooses the cheapest useful transmission: ignore, JSON alert, crop evidence, or full image.

### 4. Why it must run onboard
> If the image is already downlinked, the bandwidth is already spent. Onboard AI reduces what leaves the satellite in the first place.

### 5. Where Liquid fits
> LFM2-VL is the lightweight visual reasoning layer. The detector proposes candidate kiln regions; Liquid reasons over the crop and context, producing structured alert metadata for the ground station.

### 6. Proof
> The ground station does not read raw images. It reads only the simulated downlink queue. That lets us prove bytes saved, alert count, crop evidence, detector mode, and Liquid reasoning per alert.

## What to Salvage From Repo

KEEP: satellite edge node, transmission queue, telemetry JSONL, ground station dashboard, strict YOLO detector, crop evidence, byte accounting, **Liquid reasoning layer (now central, not decorative)**.

## What to Stop Saying

- ❌ "We solved brick kiln detection." → ✅ "We solved the satellite downlink triage layer for brick-kiln monitoring."
- ❌ "Liquid is optional." → ✅ "Liquid is the onboard reasoning layer for turning visual detections into compact structured intelligence."
- ❌ "This is production-ready." → ✅ "This is a runnable proof-of-concept with honest constraints and a clear production path."

## Discriminating Constraints

1. **Repo MUST run for a judge with zero patience** — no "install ultralytics first" discovery, no missing weights, no broken paths. Pre-built sample queue commits this guarantee.
2. **DPhi imagery MUST be visible** — judging rubric: "Satellite images from the DPhi API are the core data source." If invisible, points lost.
3. **Liquid MUST feel central in Liquid Track** — every detected alert in the dashboard shows the LFM2-VL reasoning. Not a footnote.
4. **No fake fine-tuning claims** — honest wins.

## Cookbook Alignment (Liquid4All/cookbook · 2026-05-09)

The official Liquid satellite-VLM cookbook example for THIS hackathon is at
`Liquid4All/cookbook/examples/satellite-vlm/`. Key facts we now align with:

- **Same model:** `LiquidAI/LFM2.5-VL-450M` is the cookbook's reference model. ✓
- **Pretraining task suite:** VRSBench (NeurIPS 2024) with three tasks — VQA (123K), grounding (52K, JSON bbox format), captioning (29K). The model is **already trained** on JSON bbox detection in normalized 0-1 coordinates and on satellite-VQA-style answers.
- **Pretrained grounding format** (use this exact shape if asking the model to detect):
  ```
  Inspect the image and detect the {target}.
  Provide result as a valid JSON: [{"label": str, "bbox": [x1,y1,x2,y2]}, ...].
  Coordinates must be normalized to 0-1.
  ```
- **Structured-generation pattern** (cookbook `car-maker-identification` example):
  ```python
  outlines.from_transformers(model, processor)
  prompt = Chat([{"role": "system", ...}, {"role": "user", "content": [image, text]}])
  outlines_model(prompt, PydanticOutputType, max_new_tokens=64)
  ```
  Uses `outlines` for **decode-time JSON schema enforcement**. We do not use `outlines` (deadline risk), but we mirror the system+user message structure and deterministic decoding (`do_sample=False`).
- **Production fine-tune path:** `leap-finetune` framework on Modal H100s ($30 free credit) via `vrsbench_multitask_modal.yaml`. Documented in our README as the next step — not attempted before deadline (would risk a botched submission).

### Changes applied 2026-05-09 from cookbook study

- `satellite_edge_node/liquid_vlm_reasoner.py`: split prompt into system + user roles, named brick-kiln visual features the model should look for (kiln ovens, chimneys, fired-clay color, firing lots, spoil heaps), passed detector confidence/signals as context, locked `do_sample=False` for JSON reliability and deterministic demo output. Aligns with cookbook patterns without adding `outlines` dependency.
- README + JUDGING reference VRSBench as the production training corpus and `leap-finetune` + Modal as the production fine-tuning path.

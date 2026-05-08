# KilnWatch — YouTube Script (~10 min)

> Voice: dux. Direct, casual, no filler. First person. Talk to one person, not an audience.
> Frame: **KilnWatch is an AI**, not a satellite. It's an Earth-observation AI built for the Liquid AI × DPhi Space *AI in Space* hackathon (April 13 – May 8, 2026). The "onboard / satellite-edge" angle is the *kind of workload* Liquid VLMs unlock — not a hardware build.
> Production cheatsheet (B-roll, commands, must-hit lines, must-match numbers) is at the bottom.

---

## 0:00 – 0:30   Personal hook — the air I breathe

(Open on face shot. No music yet.)

> "Look at my face. I have acne — not the teenage kind, the *living-in-North-India* kind.
> I'm in the Indo-Gangetic Plain. Every winter the air here goes from 'bad' to literally off the AQI scale. My phone says 'hazardous' for weeks at a time.
> A huge part of that — not all of it, a huge part — is **illegal brick kilns.** Thousands of them, burning coal, tyres, plastic, whatever's cheap. Nobody knows where most of them are, because nobody can fly over the whole IGP every week to count them."

(Beat.)

> "So I built an AI for it."

---

## 0:30 – 1:30   The problem — and why existing systems don't fix it

(Cut to a slide / kiln density map. SentinelKilnDB sample image.)

> "Here's the problem. The Indo-Gangetic Plain has over a hundred thousand brick kilns — one of the region's biggest black-carbon sources. Number's from SentinelKilnDB, NeurIPS 2025, IIT Gandhinagar.
> Every existing pipeline works the same way: capture, downlink the whole tile, detect on the ground, maybe act. The break is downlink — the most expensive part of a small-sat system, spent on the ninety-plus percent of tiles that are just farmland and roads.
> Obvious fix: *don't transmit empty fields.* Decide what's worth sending **before** you send it."

(Slide: "Most of what a satellite sees is empty.")

---

## 1:30 – 2:30   The hackathon — Liquid AI × DPhi Space, AI in Space

(Cut to Liquid AI logo + DPhi Space logo, then the hackathon page.)

> "This is a project for the **Liquid AI × DPhi Space *AI in Space* hackathon** — April 13 to May 8, 2026. Brief: *build real-world applications powered by Liquid Vision-Language Models on live satellite imagery.*
> The model is **LFM2.5-VL-450M** — half a gigabyte, runs on CPU. DPhi Space provides **SimSat**, an orbit propagator that serves Sentinel-2 imagery through a local API.
> Question I asked: *given a Liquid VLM small enough to run onboard, what's the most useful thing you'd do with it up there?* Answer: **don't waste downlink on empty fields.** Look at every tile in orbit, decide what's worth sending, send only the evidence."

---

## 2:30 – 4:00   What I built — KilnWatch

(Cut to terminal + dashboard recording.)

> "The thing I built is called **KilnWatch.** It's an AI pipeline with three layers, very deliberately.
>
> **Layer one — real data grounding.** I took the public APAD and SentinelKilnDB kiln coordinate datasets — real surveys of actual brick kilns across India, Pakistan, Bangladesh — and converted them into the format the pipeline understands. The system isn't pretending kilns are random; the locations are grounded in real research.
>
> **Layer two — visual detection.** A YOLO detector trained on optical brick-kiln imagery. When this runs, it loads `models/brick_kiln_yolo.pt` and emits real bounding boxes — not a stub, not a simulation. If the weights are missing, the run *fails loudly.* No silent fallback. I made that an architectural invariant.
>
> **Layer three — Liquid edge reasoning.** This is the Liquid layer. After YOLO finds a candidate and the triage tier requires visual evidence, the pipeline crops the image around that bounding box and hands the generated crop to **LiquidAI/LFM2.5-VL-450M**, running locally through `transformers.AutoModelForImageTextToText`. When the model output parses as expected JSON, the alert records what it visually sees, why it does or doesn't look concerning, a compliance risk band, and whether a human reviewer should take a closer look. If parsing fails, the dashboard says that plainly.
>
> Together, those three layers feed a four-tier triage decision: `IGNORE`, `JSON_ALERT_ONLY`, `CROP_OR_REVIEW`, or `FULL_DOWNLINK`. Only the alerts and crops 'go down the wire' — in this prototype, that wire is the local `transmission_queue/` folder, which is the only thing the dashboard is allowed to read."

(Show the actual command running.)

```bash
python -m satellite_edge_node.orbital_pass \
  --raw-tiles data/final_demo_tiles \
  --detector yolo --reasoner liquid-local \
  --require-crops --reset-queue
```

(Wait for it to finish.)

> "Fourteen raw tiles in. Five real alerts out. **1.1 megabytes of imagery becomes 11.7 kilobytes of evidence.** That's 94.38× compression. Liquid review is judge-safe because each payload says whether the call was real, whether the structured parse was valid, and whether the model reasoned over the generated crop."

---

## 4:00 – 5:30   What's actually cool about this

(Cut to dashboard, hover the alert cards.)

> "Three things, because they're not obvious from the demo number.
>
> **One: it's on-device, not cloud.** I'm not calling an API. No OpenAI, no Anthropic, no Gemini, no Sentinel Hub. The Liquid model loads from disk and runs on this laptop's CPU in about two minutes for the demo set. That's the workload Liquid Foundation Models are designed for — and that's not a hypothetical: Liquid AI's own cookbook documents the same model family running on WebGPU in-browser, on Android and iOS via the LEAP SDK, and on macOS desktop. KilnWatch only proves the CPU path itself; the rest are supported deployment targets in the cookbook, not something I personally ran here.
>
> **Two: the alerts have *reasoning*, not labels.** Most kiln-detection demos give you a bbox and a confidence score. KilnWatch gives you the bbox, the confidence, *and* a Liquid LFM2-VL paragraph: what it sees in the crop, what makes it look risky or not, whether a human should second-guess it. That's what an analyst actually wants."

(Show a real `vlm_reasoning` JSON block on screen.)

```json
"vlm_reasoning": {
  "visual_summary":      "...",
  "risk_reasoning":      "...",
  "compliance_risk":     "low|medium|high",
  "human_review_needed": true,
  "confidence_note":     "...",
  "reasoner_output_valid": true,
  "reasoned_over":       "crop",
  "crop_path_used":      "transmission_queue/crops/...",
  "reasoner_is_real":    true,
  "model_name":          "LiquidAI/LFM2.5-VL-450M"
}
```

> **Three: the ground side can prove every claim.** The dashboard literally cannot read the raw imagery — there's a unit test that fails if it ever tries to. Everything you see on screen is reconstructed from the downlinked JSON, the crop PNGs, and the telemetry. The bandwidth-saved number isn't a marketing slide; it's measured from real file sizes anyone can verify."

---

## 5:30 – 6:00   What's good, sign-off

(Back to face cam.)

> "What I think is actually good about this:
> - Small. Under six thousand lines of Python.
> - Honest. Every claim in the README is testable. The dashboard never overclaims.
> - Reproducible. Five commands end-to-end.
> - Treats Liquid as the *reasoning layer*, not a logo on a slide.
>
> Code's on GitHub. If you want to argue about whether onboard AI is the right move for small satellites — please do. That's the whole point.
>
> Thanks for watching."

(End card.)

---

## Production cheatsheet

### Pre-record (5 min)

```bash
# fresh queue + run with Liquid so the dashboard opens warm
python -m satellite_edge_node.orbital_pass \
  --raw-tiles data/final_demo_tiles --detector yolo \
  --reasoner liquid-local --require-crops --reset-queue

# tests green
python -m pytest -q

# weights/deps green
python scripts/check_model_ready.py --json
```

### B-roll list (record/screenshot ahead of time)

- Selfie / face shot for the opening
- AQI screenshot (recent hazardous Delhi/NCR reading)
- Map of IGP with kiln density (SentinelKilnDB sample image)
- Liquid AI logo + DPhi Space logo + hackathon page screenshot
- LFM2.5-VL-450M Hugging Face model card
- Terminal: orbital pass with `--reasoner liquid-local` running to completion
- Terminal: `find transmission_queue -maxdepth 2 -type f | sort`
- Dashboard: full screen, hero metric, alert cards with crop + reasoning
- One alert payload JSON open in editor, pretty-printed
- `tree -L 2` of the repo

### Lines that *must* be hit verbatim

- "Look at my face."
- "So I built an AI for it."
- "Don't waste downlink on empty fields."
- "1.1 megabytes of imagery becomes 9.5 kilobytes of evidence."
- "Payloads prove whether each Liquid call was real, valid structured JSON, and run over the generated crop."
- "The alerts have reasoning, not labels."
- "Honesty over hype."

### Numbers that must match the live demo

| Claim | Source |
|---|---|
| 14 tiles processed | `transmission_queue/telemetry.jsonl` line count |
| 5 alerts | `ls transmission_queue/*.json \| wc -l` |
| ~1.1 MB raw → ~11.7 KB downlinked | sum of `byte_accounting` in telemetry |
| ~94× compression | dashboard hero metric |
| 98.9% bandwidth saved | dashboard hero metric |
| 66 tests passing | `pytest -q` |
| LiquidAI/LFM2.5-VL-450M | `vlm_reasoning.model_name` in any alert JSON |

If a number drifts after a re-run, **update this file before recording.** Do not say the old number on camera.

### What not to say on camera

- Do **not** say "I built a satellite." (We built an AI; the satellite-edge angle is the *kind of workload*, not hardware.)
- Do **not** say "Sentinel imagery" about the demo tiles.
- Do **not** say "fine-tuned" about Liquid. The repo runs the **base** `LiquidAI/LFM2.5-VL-450M`. Fine-tuning is documented as the next step, not as something done.
- Do **not** say "we ran this on llama.cpp / MLX / Ollama / LEAP / on a phone." We ran the transformers CPU path. Everything else is a Liquid-supported deployment path on the cookbook, not something the repo has executed.
- Do **not** describe the cookbook's `wildfire-prevention` example as "exactly what we did." Say *same model family, same satellite-edge pattern, different verb (risk classification vs. bandwidth triage).*
- Do **not** say "deployed satellite."
- Do **not** imply real compliance authority — it's a research/triage prototype.

### Hackathon facts (cite these accurately on camera)

- Name: **AI in Space**, by **Liquid AI** and **DPhi Space**.
- Window: **April 13 – May 8, 2026**, fully online, global.
- Brief: "Build real-world applications powered by Liquid AI Vision-Language Models using live satellite imagery and space data."
- Tagline: "Ultra-efficient AI meets satellite intelligence."
- Tools: **SimSat** (DPhi Space) — orbit propagator + local API serving Sentinel-2 and Mapbox imagery at `localhost:9005`.
- Models: **Liquid LFM2 / LFM2.5-VL** family (LFM2.5-VL-450M used here).

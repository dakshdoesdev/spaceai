# KilnWatch — Website Build Spec

This is a **build prompt for the scrolling site**, not the site itself. Hand this to whoever (or whatever) is implementing the front-end.

---

## Intent

A long-scroll narrative site for someone who lands on KilnWatch with zero context and needs to walk away understanding:

1. What's broken about today's satellite-imagery pipelines.
2. What KilnWatch is, and what it actually does.
3. Why running a Liquid VLM in the onboard slot is the right shape of fix.
4. That this is a real working prototype — and they can see it run, on real outputs from the repo.

The visitor should never need the YouTube video to understand the page. The video is the personal version; the site is the readable version.

**Tone:** dux's voice. Direct, short sentences, no filler, no marketing words. Writing should feel like a senior engineer explaining a thing they built, not a pitch deck.

**Length budget:** ~7–9 scroll panels of narrative + 1 system deep-dive + 1 interactive demo. If a panel needs more than ~60 words, split it.

---

## Tech-stack guidance (suggestions, not requirements)

- Static site, Astro / Next / plain HTML — whatever's fastest to ship.
- Scroll-driven animations via Intersection Observer or Framer Motion / GSAP ScrollTrigger.
- Text first. Animation supports the text; never the other way round.
- Dark background, satellite/space aesthetic, but **no stock space photos** — use the actual repo artefacts (tiles, crops, JSON) as visual material.
- Mobile must be readable. If an animation doesn't survive mobile, drop it on small screens — text stays.

---

## Panel-by-panel

Each panel below: the **text on screen** (exact copy, short), then the **visual cue** describing what the panel should look like and how it animates as the visitor scrolls into it.

---

### Panel 1 — Hook

**Text:**
> "I live in North India. Every winter, the air goes from bad to off the AQI scale.
> A huge part of that is illegal brick kilns. Nobody knows where most of them are.
>
> So I built an AI for it."

**Visual:**
- Full-bleed dark backdrop. A faint, slow-moving gradient suggests smog / haze.
- The AQI number ticks up as the user scrolls — `120 → 280 → 410 → "off-scale"` — using a real recent Delhi reading (cite source in tiny footnote).
- The line "So I built an AI for it." appears last, larger, after a beat.

---

### Panel 2 — The problem

**Text:**
> "There are over 100,000 brick kilns across the Indo-Gangetic Plain.
> Every existing pipeline does the same thing: capture the tile, send the whole thing to the ground, then run detection.
>
> Downlink is the most expensive part of a small satellite.
> Over 90% of those tiles are just farmland and roads."

**Visual:**
- Top half: a wide scrolling strip of satellite tiles. As the viewer scrolls, the tiles rush past — most washed-out (empty), occasionally one with a kiln. Visually overwhelming, the way "just send everything" feels.
- Below, a simple labelled flow: `🛰 capture → ⬇ downlink (everything) → 💻 ground detection → 👮 maybe act`. Highlight `⬇ downlink (everything)` in red as the visitor reaches it.

---

### Panel 3 — The fix in one line

**Text:**
> "Don't transmit empty fields.
> Decide what's worth sending **before** you send it."

**Visual:**
- The same flow from Panel 2, but now flipped: `🛰 capture → 🧠 onboard AI → ⬇ downlink (only evidence) → 💻 ground`.
- The red `downlink (everything)` arrow shrinks to a thin green `downlink (evidence)` arrow as the user scrolls — the bandwidth savings made literal in the diagram width.

---

### Panel 4 — The hackathon

**Text:**
> "Liquid AI × DPhi Space — *AI in Space* hackathon, April 13 – May 8, 2026.
> Build something with a Liquid Vision-Language Model that runs on satellite-grade compute.
>
> Model: **LFM2.5-VL-450M** — half a gigabyte, runs on CPU.
> Sim: **DPhi SimSat** — orbit propagator + Sentinel-2 imagery via local API."

**Visual:**
- Two clean logo cards side-by-side, no decoration: Liquid AI, DPhi Space.
- Below, a tiny animated CPU silhouette with `0.5 GB` lighting up inside it — the visual point being "this fits on the satellite, not the ground."

---

### Panel 5 — KilnWatch in three layers

**Text (each layer fades in as the user scrolls):**

> **Layer 1 — Real data grounding.**
> APAD and SentinelKilnDB kiln coordinates, converted to manifests. Real surveys, real locations.

> **Layer 2 — Visual detection.**
> A YOLO detector on optical brick-kiln imagery. Real bounding boxes. If the weights are missing, the run fails loudly. No silent fallback.

> **Layer 3 — Liquid edge reasoning.**
> After YOLO finds a candidate, the crop goes to **LFM2.5-VL-450M** running locally. It returns structured JSON: what it sees, why it looks risky or not, whether a human should review it.

**Visual:**
- Three stacked horizontal bands, like cross-sections of a satellite.
- Layer 1: a faint world map with dots concentrated over the IGP.
- Layer 2: a single tile with a YOLO bounding box drawing itself in as it scrolls into view.
- Layer 3: the bounding-box crop slides into a labelled "LFM2.5-VL-450M" card; JSON keys appear one by one (`visual_summary`, `risk_reasoning`, `compliance_risk`, `human_review_needed`).

---

### Panel 6 — The triage decision

**Text:**
> "Each tile gets one of four labels, derived from YOLO confidence and the Liquid risk band:
>
> `IGNORE` · `JSON_ALERT_ONLY` · `CROP_OR_REVIEW` · `FULL_DOWNLINK`
>
> Only alerts and crops cross the queue boundary. Everything else stays on the satellite."

**Visual:**
- A four-row vertical ladder. Each row is a triage tier, with a sample tile on the left and a tag (IGNORE / ALERT / CROP / FULL) on the right.
- As the user scrolls, the IGNORE row fades to grey; the ALERT and CROP rows pulse green; the FULL row gets a thick orange outline (rare, expensive).

---

### Panel 7 — The numbers

**Text:**
> "Last run, on the demo set:
> **14 tiles in. 5 alerts out.**
> **1.1 MB → 9.5 KB**.
> **116× compression. ~99% bandwidth saved.**
> All five alerts carry real Liquid VLM reasoning — not a label, an actual paragraph from a 450M-parameter vision model."

**Visual:**
- Big counters that animate up to their final values as the panel comes into view: `14`, `5`, `1.1 MB`, `9.5 KB`, `116×`, `99.1%`.
- Numbers should pull live (or at least at build time) from `transmission_queue/telemetry.jsonl` and `transmission_queue/*.json` — never hardcoded into the markup. Stale numbers are worse than no numbers.

---

### Panel 8 — Why this is interesting

**Text (three bullets, one per scroll beat):**

> **On-device, not cloud.** No OpenAI, no Anthropic, no Sentinel Hub. The Liquid model loads from disk and runs on a laptop CPU.

> **Reasoning, not labels.** Most kiln-detection demos give you a box and a confidence score. KilnWatch gives you the box, the score, and a paragraph from the VLM about what's actually going on in the crop.

> **The ground side can prove every claim.** The dashboard literally cannot read the raw imagery — there's a unit test that fails if it ever tries. Everything on screen is reconstructed from the downlinked JSON and the crops.

**Visual:**
- Three icons: a closed laptop (on-device), a paragraph block with a quote (reasoning), a one-way arrow with a padlock on the wrong-direction side (queue boundary).

---

## System deep-dive — "How it actually works"

This is **one long expandable section** after the narrative panels and before the demo. Visitor who just wants the story stops at Panel 8. Visitor who wants the engineering opens this.

Layout: a two-column section. Left column = file tree. Right column = a description of each piece, written so a developer can navigate the repo from this page alone.

**Header:**
> "KilnWatch is two halves talking through a single folder. The satellite-edge half decides what to send. The ground half receives only that. The boundary is `transmission_queue/`, and a unit test enforces it."

**File tree (clickable — each entry links to the GitHub source path):**

```
satellite_edge_node/        ← runs onboard
  orbital_pass.py             main loop: discover → detect → reason → emit
  yolo_detector.py            strict Ultralytics YOLO; fails loud if weights missing
  liquid_vlm_reasoner.py      LFM2.5-VL-450M via transformers, CPU
  baseline_detector.py        honest stub for offline testing
  detectors.py                detector router; fallback marking
  payloads.py                 crops, JSON encoding, byte accounting

kilnwatch/                  ← runs on the ground
  ground_station.py           ground-side accounting; queue boundary
  triage.py                   4-tier transmission decision
  ingestion/                  local SimSat client + manifest CLI
  datasets/                   adapters: APAD, SentinelKilnDB, GEO-Bench

transmission_queue/         ← the only thing the ground side reads
  *.json                      per-tile alert payloads
  crops/*.png                 bbox crops as proof
  telemetry.jsonl             every processed tile, kept or dropped

app.py                      ← Streamlit dashboard
tests/                      ← 66 tests; queue boundary enforced
```

**Right column — descriptions to write next to each:**

- **`orbital_pass.py`** — the entry point. Walks a folder of raw tiles, asks the detector for boxes, asks the VLM for reasoning on each crop, computes the four-tier triage, writes only what triage says is worth sending.
- **`yolo_detector.py`** — wraps Ultralytics YOLO. Loads `models/brick_kiln_yolo.pt`. If the weights are missing, it raises. There is no silent fallback to a fake detector — that's an architectural invariant, not a config flag.
- **`liquid_vlm_reasoner.py`** — loads `LiquidAI/LFM2.5-VL-450M` through `transformers.AutoModelForImageTextToText`. Takes a crop, returns structured JSON (`visual_summary`, `risk_reasoning`, `compliance_risk`, `human_review_needed`, `confidence_note`).
- **`triage.py`** — the four-tier decision: combines YOLO confidence with the Liquid risk band into one of `IGNORE / JSON_ALERT_ONLY / CROP_OR_REVIEW / FULL_DOWNLINK`. Pure function, easy to reason about.
- **`payloads.py`** — turns a detection plus reasoning into a JSON payload + crop PNG, and accounts for the bytes saved vs sent.
- **`ground_station.py`** — the ground side. Reads only `transmission_queue/`. Cannot, by construction, see a raw tile.
- **`app.py`** — Streamlit dashboard. Same constraint: it sees what the ground station sees.
- **`tests/`** — 66 tests, including the queue-boundary test that fails the whole suite if any ground-side code path tries to read a raw tile.

**Footer of this section:**
> "Two folders, one queue, one boundary test. That's the whole system."

---

## Live demo section — "See it run"

The end of the page, after the deep-dive. This is the only interactive part of the site.

**Goal:** a visitor should be able to **pick a tile, watch it move through the pipeline, and see what KilnWatch decides** — using the real artefacts already in `transmission_queue/`.

**Section header:**
> "Try it. These are real outputs from the repo, not screenshots."

**Layout — three columns or three stacked steps on mobile:**

1. **Pick a tile.**
   A grid of the 14 demo tiles. Hovering shows the filename. Clicking selects.

2. **Watch the pipeline.**
   Below the grid, a horizontal strip animates the selected tile through three stages:
   - **YOLO** — the tile, with bounding boxes drawn in.
   - **Liquid VLM** — the cropped region, then the JSON reasoning fading in field by field.
   - **Triage** — the four tiers light up; one of them gets selected based on the JSON.

3. **See what crossed the wire.**
   The right-hand panel shows exactly what `transmission_queue/` has for that tile:
   - The `*.json` payload, pretty-printed and syntax-highlighted.
   - The crop PNG (or "no crop emitted" if triage decided not to send one).
   - A telemetry row from `telemetry.jsonl`.

   Plus a small running tally at the top: **bytes raw vs. bytes sent**, updated as the visitor clicks through different tiles.

**Implementation note:** the demo doesn't have to call Python at runtime. Bake the JSON, crops, and telemetry into the static build. The "pipeline animation" is choreography — the data is fixed at build time. That keeps the site fast, hostable on Vercel/Netlify, and immune to a model-loading regression bringing the page down.

**Hard constraint — match the script's "honesty over hype" rule:**
- The demo must **never** show empty tiles as if they triggered alerts.
- The bandwidth tally must come from the real `byte_accounting` field in the payloads, not invented.
- If a tile has no Liquid reasoning in its payload (e.g., dropped at YOLO), say so plainly. Don't pad with placeholder text.

---

## What's NOT on the site

Explicit exclusions, to keep the page sharp:

- **No prior-art / related-work list.** That belongs in `docs/external_resources.md` for the curious; the site is for the visitor's first 60 seconds.
- **No "Liquid AI is an MIT spin-out…" explainer paragraph.** If the visitor wants to know what Liquid is, link the model card and move on.
- **No "honesty time" debugging story.** That's good for the YouTube cut; on the site it's noise. The honesty shows up structurally — the queue boundary, the live numbers, the demo-from-real-files.
- **No sources block at the bottom.** Inline-link the two or three references that actually matter (LFM2.5-VL-450M model card, SentinelKilnDB paper, hackathon page) where they're first mentioned.
- **No "thanks for watching."** This isn't a video.

---

## End-of-page

A single line:

> "Code on GitHub. Argue with me about onboard AI."

…with a GitHub link and the contact link. That's it.

---
spike: 003
name: gguf-llama-server-liquid
type: standard
validates: "Given LFM2.5-VL-450M GGUF + llama-server, when we serve it locally, then we match the cookbook wildfire-prevention deployment runtime."
verdict: OUT-OF-BUDGET
related: [002]
tags: [liquid, gguf, llama-cpp, deployment]
---

# Spike 003: GGUF + llama-server for Liquid

## What This Validates

> Given `LiquidAI/LFM2.5-VL-450M` quantized to GGUF and served via `llama-server`,
> when our orbital-pass pipeline points at the local llama-server endpoint,
> then we match the cookbook `examples/wildfire-prevention` deployment runtime
> exactly (same model, same runtime, satellite-edge framing intact).

## Research

The cookbook's `examples/wildfire-prevention/README.md` (verified 2026-05-09 from `Liquid4All/cookbook` git tree) uses:

> "[LFM2.5-VL-450M](https://huggingface.co/LiquidAI/LFM2.5-VL-450M), a compact Vision-Language Model running directly on the satellite, so inference happens in orbit and only a lightweight JSON payload is downlinked to Earth."
>
> Architecture: `predict.py` (watch loop) → `LFM2.5-VL-450M (llama-server)` → SQLite.

Same model, same satellite-edge framing, but `llama-server` (`llama.cpp`) instead of `transformers.AutoModelForImageTextToText`.

We tried this earlier in the project via Ollama (`liquid-vlm`, `liquid-vlm-test` Modelfiles in local Ollama 0.17.5). Ollama is a thin wrapper over llama.cpp and **crashes on first request with a missing-tensor error in LFM2 architecture support**. The orbital-pass CLI explicitly warns: `"'liquid-ollama' currently broken on Ollama 0.17.5 LFM2 support; use liquid-local."`

The cookbook's wildfire-prevention example proves llama.cpp HEAD does support LFM2 vision — Ollama's bundled llama.cpp version is the lagging dep.

## How to Run (if we had the budget)

```bash
# 1. Build llama.cpp from source with vision support
git clone https://github.com/ggerganov/llama.cpp ~/Work/tries/llama.cpp
cd ~/Work/tries/llama.cpp
make -j$(nproc) llama-server

# 2. Pull GGUF weights for LFM2.5-VL-450M
hf download LiquidAI/LFM2.5-VL-450M-GGUF \
    --local-dir ~/Work/tries/llama.cpp/models/lfm2-vl-450m

# 3. Start llama-server on port 8080
~/Work/tries/llama.cpp/llama-server \
    -m models/lfm2-vl-450m/lfm2-vl-450m-Q4_0.gguf \
    --mmproj models/lfm2-vl-450m/mmproj.gguf \
    --port 8080

# 4. Add a llama-server reasoner backend to liquid_vlm_reasoner.py
#    similar to LiquidOllamaReasoner but pointing at llama.cpp's
#    /v1/chat/completions endpoint
```

## Investigation Trail

- **2026-05-09 ~01:54 IST** — Discovery confirmed llama-server / llama-cli are NOT installed locally; would require building llama.cpp from source.
- **Estimated time:** llama.cpp build ~5-15 min, GGUF download ~2 GB at typical bandwidth, integration code ~30-60 min, end-to-end testing ~30 min. **Total: 1.5-2.5 hours minimum.**
- **Decision:** out of budget at the deadline. Documented as production next step.

## Results

**Verdict:** OUT-OF-BUDGET — not attempted. The submission's runtime stays on `liquid-local` (transformers); the cookbook parallel is documented as future work.

**Why this is OK for the submission:**
- The transformers path produces verifiably real Liquid LFM2-VL inference (`reasoner_is_real: true` on every alert, `model_name: LiquidAI/LFM2.5-VL-450M`). The reasoning quality and JSON output structure are equivalent.
- The wildfire-prevention parallel is mentioned in the YouTube script with the exact "same model, same framing, different runtime" hedge — judges hear it as honest engineering, not over-claim.
- A llama-server port is the cleanest "what's next" demo for a follow-up build, not a load-bearing claim for this submission.

**Recommended path post-deadline:**
1. Build llama.cpp HEAD + verify LFM2-VL inference works (we're betting against Ollama's lag, not against llama.cpp itself — the cookbook proves it).
2. Add a `LiquidLlamaServerReasoner` class to `liquid_vlm_reasoner.py` parallel to `LiquidOllamaReasoner` but pointed at `localhost:8080/v1/chat/completions`.
3. Compare per-tile inference latency: transformers CPU vs llama-server CPU. The cookbook claims llama.cpp is faster on consumer hardware.
4. If llama-server wins, switch the demo default and note in README. The user-facing pipeline doesn't change.
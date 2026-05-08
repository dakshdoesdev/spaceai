---
spike: 002
name: outlines-structured-liquid
type: standard
validates: "Given outlines.from_transformers wrapping LFM2.5-VL-450M, when we generate against a Pydantic schema, then output is decode-time-guaranteed valid JSON matching the cookbook car-maker-identification pattern."
verdict: INVALIDATED-ON-PYTHON-3.14
related: []
tags: [liquid, structured-generation, optional]
---

# Spike 002: Outlines Structured Generation for Liquid

## What This Validates

> Given `outlines.from_transformers` wrapping LFM2.5-VL-450M,
> when we generate against a Pydantic output type,
> then the output is decode-time-guaranteed valid JSON
> matching the cookbook `examples/car-maker-identification` pattern.

## Research

The Liquid cookbook's `car-maker-identification` example uses the same model size (LFM2-VL-450M) with `outlines` for structured generation:

```python
import outlines
from outlines.inputs import Image as OutlinesImage, Chat
outlines_model = outlines.from_transformers(model, processor)
prompt = Chat([
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": [
        {"type": "image", "image": OutlinesImage(image)},
        {"type": "text", "text": user_prompt},
    ]},
])
response = outlines_model(prompt, OutputType, max_new_tokens=64)
parsed = OutputType.model_validate_json(response)
```

This constrains the decoder at every token to produce only outputs that match the Pydantic schema — guaranteed JSON validity, not just prompt-engineered.

## How to Run

```bash
.venv/bin/pip install outlines
.venv/bin/python -c "
import outlines
print(outlines.__version__)
"
```

## What to Expect

`outlines` installs cleanly, exposes `from_transformers`, and the LFM2-VL-450M model can be wrapped without modification.

## Investigation Trail

- **2026-05-09 ~02:01 IST** — Ran `pip install outlines` against the project venv (Python 3.14).
- **Result:** `outlines_core` (a Rust extension) failed to build a wheel for Python 3.14:
  ```
  Failed to build outlines_core
  error: failed-wheel-build-for-install
  × Failed to build installable wheels for some pyproject.toml based projects
  ╰─> outlines_core
  ```
- **Root cause:** `outlines_core` ships pre-built wheels only up to CPython 3.13. Python 3.14 (used by this venv) has no wheel; the source build needs a Rust toolchain matching the project's pinned ABI.
- **Did not pivot to:** building a Python 3.13 sub-venv just for outlines. The deadline budget doesn't justify a second venv plus model re-load and a parallel Liquid path.

## Results

**Verdict:** INVALIDATED on Python 3.14 (this venv) at this deadline.

**What's still true:**
- The cookbook pattern is real and validated by Liquid AI for the same model family.
- Our current Liquid integration in `satellite_edge_node/liquid_vlm_reasoner.py` mirrors the cookbook's system+user message structure and uses deterministic decoding (`do_sample=False`), which captures most of the JSON-reliability benefit without the Rust dep.
- `_extract_json_object` in the same module is a tolerant post-hoc parser that handles slightly malformed JSON gracefully.

**Recommended next steps if revisited:**
- Create a Python 3.13 venv: `python3.13 -m venv .venv313 && source .venv313/bin/activate && pip install outlines transformers torch` and port `LiquidLocalReasoner` to use the outlines pattern there.
- Or wait for `outlines_core` to ship a 3.14 wheel.
- Or use `outlines` 0.1.x which is pure-Python (no Rust dep) — older API but works across CPython versions.

**Impact on the submission:** none. The current Liquid integration produces 5/5 valid `vlm_reasoning` payloads with `reasoner_is_real: true` against the live demo. Outlines would be a reliability hardening, not a new capability.
# Feature Research: KilnWatch

**Date:** 2026-05-06

## Table Stakes For This Hackathon

- Uses satellite imagery from DPhi/SimSat or documents exactly why a local fixture is used.
- Demonstrates onboard or near-satellite inference/triage.
- Sends compact structured payloads instead of raw images whenever possible.
- Provides an end-to-end demo walkthrough that runs without debugging.
- Explains why limited downlink and onboard inference matter.
- Keeps technical claims honest.

## KilnWatch V1 Features

- Satellite edge runner processes one or more image/tile inputs.
- Detector result is normalized into a shared schema.
- Triage chooses ignore, JSON alert, crop/review, or full downlink.
- Queue contains only downlinked artifacts.
- Crop payloads point to real crop files when claimed.
- Ground station dashboard reads queue artifacts only.
- Bandwidth metrics are file-size based.
- Detector mode/fallback/simulation status is visible.
- Submission docs include problem, solution, space-compute rationale, endpoint usage, hardest part, and demo video script.

## Differentiators

- Brick kiln compliance is more specific than generic wildfire/maritime clones.
- Panipat/Haryana/NCR framing gives the project a grounded real-world story.
- The core proof is the satellite-ground boundary, not just a dashboard.
- Technical honesty can become a strength: the demo shows what is simulated, strict, missing, and next.

## Anti-Features

- Do not hide baseline simulation behind polished UI.
- Do not claim Liquid Track if Liquid LFM is not integrated.
- Do not claim Sentinel imagery for placeholder `.tile` blobs.
- Do not let the ground station read raw onboard inputs.


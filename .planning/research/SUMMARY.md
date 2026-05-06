# Research Summary: KilnWatch

**Date:** 2026-05-06

## Key Finding

KilnWatch should be optimized as a polished General Track hackathon submission proving satellite-side downlink triage. The strongest submission story is not "best brick kiln detector"; it is "the satellite decides what is worth transmitting, and Earth only receives compact evidence."

## Stack

Keep the current Python/Streamlit/file-queue architecture. Harden the existing system instead of adding a new backend.

## Table Stakes

- DPhi/SimSat satellite imagery usage or precise disclosure of local fixtures.
- Edge/onboard inference or simulation boundary.
- Compact JSON/crop downlink.
- Dashboard that runs without debugging.
- End-to-end demo walkthrough.
- Honest limitation statements.

## Watch Out For

- Do not overclaim Liquid LFM fine-tuning.
- Do not call placeholder `.tile` files Sentinel imagery.
- Do not let baseline simulation masquerade as real detection.
- Do not allow crop payloads without actual crop files.
- Do not let the ground station read raw onboard files.

## Recommendation

Submit under General Track unless Liquid LFM integration lands with proof. Prioritize one strict demo run: real image -> detector/bbox -> actual crop -> JSON payload -> dashboard.


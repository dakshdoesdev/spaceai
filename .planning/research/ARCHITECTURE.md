# Architecture Research: KilnWatch

**Date:** 2026-05-06

## Target Architecture

KilnWatch should present a clean satellite-side triage architecture:

1. SimSat/local imagery enters the satellite edge node.
2. Detector runs in strict real mode or explicit simulated baseline mode.
3. Triage converts detections into downlink decisions.
4. Payload builder writes compact queue artifacts.
5. Ground station reads only the queue and telemetry.
6. Dashboard proves alerts, crops, byte savings, and detector honesty.

## Required Boundary

The ground station must not inspect `data/raw_tiles/`, `data/raw/`, or onboard image inputs. Its source of truth is `transmission_queue/` and telemetry/downlinked artifact paths.

## Build Order

1. Lock final demo path and queue reset/run behavior.
2. Make one real crop chain work.
3. Harden detector honesty/fallback behavior.
4. Polish dashboard proof surfaces.
5. Validate with tests and docs.
6. Prepare submission text and demo script.

## Architecture Risks

- Stale telemetry append mode can mix old and new runs.
- Multiple queue readers can drift.
- Placeholder data can look operational.
- Missing YOLO weights can make a demo silently simulated unless clearly guarded.

## Evidence

- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/CONCERNS.md`
- Liquid wildfire example architecture pattern


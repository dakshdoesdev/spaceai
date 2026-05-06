# KilnWatch Submission Checklist

## Demo Readiness

- [ ] Run the orbital-pass simulation from local placeholder or real local tiles.
- [ ] Confirm `transmission_queue/telemetry.jsonl` exists.
- [ ] Confirm `transmission_queue/*.json` contains downlinked payloads.
- [ ] Run `streamlit run app.py`.
- [ ] Confirm the dashboard shows tiles processed, raw bytes, downlinked bytes, saved percentage, ignored tiles, JSON alerts, and review alerts.
- [ ] Confirm the dashboard displays `SAMPLE DATA` or `BASELINE SIMULATION` when appropriate.
- [ ] Confirm the dashboard does not read from raw tile folders.

## Technical Honesty

- [ ] State that the current detector is baseline/placeholder unless YOLO metadata is present.
- [ ] State that raw demo tiles are placeholders unless replaced with real local imagery.
- [ ] State that the edge node is a local simulation, not satellite hardware.
- [ ] State that Liquid/LFM integration is future work unless implemented.
- [ ] Avoid claiming validated model accuracy without evaluation files.

## Validation

- [ ] Run `python -m unittest discover -s tests -p 'test*.py'`.
- [ ] Run `python scripts/validate_manifest.py datasets/kilnwatch/manifests/sample_demo_manifest.jsonl`.
- [ ] Run `python scripts/check_model_ready.py` and record whether real YOLO is available.
- [ ] Run `python scripts/evaluate_detector.py --manifest datasets/kilnwatch/manifests/baseline_sample_eval_manifest.jsonl --telemetry transmission_queue/telemetry.jsonl` for sample evaluation.
- [ ] Capture dashboard screenshot or video segment showing bandwidth saved.

## Submission Materials

- [ ] README is judge-readable.
- [ ] Demo script is ready.
- [ ] Architecture doc is present.
- [ ] Technical honesty doc is present.
- [ ] License notes do not overclaim rights to external datasets/code.

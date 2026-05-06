from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from kilnwatch.ground_station import (
    calculate_metrics,
    cumulative_series,
    display_decision,
    event_downlinked_bytes,
    format_bytes,
    load_ground_station_records,
    mission_proof_counts,
    proof_status_summary,
    received_alert_rows,
    resolve_crop_evidence,
)


st.set_page_config(page_title="KilnWatch Ground Station", layout="wide")

DETECTOR_PROOF_LABELS = (
    "STRICT YOLO REAL",
    "BASELINE SIMULATION",
    "FALLBACK USED",
    "SAMPLE DATA",
)
REASONER_PROOF_LABELS = (
    "LIQUID LFM REAL",
    "LIQUID MOCK",
    "LFM DISABLED",
)


def main() -> None:
    st.title("KilnWatch Ground Station")
    st.caption("Satellite-side brick kiln triage telemetry and downlink proof")

    payloads, telemetry_events, sample_data = load_ground_station_records()
    if not payloads and not telemetry_events:
        st.error("No transmission queue or telemetry logs found.")
        st.stop()

    if sample_data:
        st.warning("SAMPLE DATA - replace transmission_queue/ and telemetry_logs/ with mission outputs.")

    render_proof_status(payloads, telemetry_events, sample_data)

    replay_events = mission_replay_controls(telemetry_events)
    metrics = calculate_metrics(replay_events)
    counts = mission_proof_counts(payloads, replay_events)

    render_mission_metrics(metrics, counts)
    render_edge_to_ground_explanation()
    render_crop_review(payloads, replay_events)
    render_downlink_chart(replay_events)

    left, right = st.columns([1.25, 0.75], gap="large")
    with left:
        render_alert_table(payloads, replay_events)
    with right:
        render_replay_status(replay_events, telemetry_events)
        render_technical_honesty()


def mission_replay_controls(events: list[dict]) -> list[dict]:
    if "replay_index" not in st.session_state:
        st.session_state.replay_index = len(events)

    controls = st.columns([0.18, 0.18, 0.64])
    if controls[0].button("Mission replay", width="stretch"):
        if st.session_state.replay_index >= len(events):
            st.session_state.replay_index = 1 if events else 0
        else:
            st.session_state.replay_index += 1
    if controls[1].button("Reset replay", width="stretch"):
        st.session_state.replay_index = 0

    replay_index = min(st.session_state.replay_index, len(events))
    controls[2].progress((replay_index / len(events)) if events else 0.0)
    controls[2].caption(f"Replay position: {replay_index}/{len(events)} telemetry events received")
    return events[:replay_index]


def render_mission_metrics(metrics, counts) -> None:
    st.subheader("Mission Metrics")
    top = st.columns(4)
    top[0].metric("Tiles processed onboard", metrics.tiles_processed)
    top[1].metric("Detections", counts.detections)
    top[2].metric("Crops generated", counts.crops_generated)
    top[3].metric("Raw bytes", format_bytes(metrics.raw_bytes_processed))

    bottom = st.columns(4)
    bottom[0].metric("Transmitted bytes", format_bytes(metrics.downlinked_bytes))
    bottom[1].metric("Bandwidth saved", f"{metrics.bandwidth_saved_percent:.1f}%")
    bottom[2].metric("Review alerts", metrics.crop_or_full_review_alerts)
    bottom[3].metric("Compression ratio", _ratio_label(metrics.compression_ratio))

    st.caption(f"JSON alerts: {metrics.json_alerts} | Tiles ignored: {metrics.ignored_tiles}")
    st.caption(f"Average inference latency: {metrics.average_latency_ms:.2f} ms")


def render_proof_status(payloads: list[dict], events: list[dict], sample_data: bool) -> None:
    st.subheader("Proof Status")
    status = proof_status_summary(payloads, events, sample_data)
    detector_col, reasoner_col = st.columns(2)
    detector_col.metric("Detector", status.detector_label)
    reasoner_col.metric("Liquid reasoner", status.reasoner_label)
    if status.notes:
        st.warning(" | ".join(status.notes))
    if status.truth_fields:
        st.json(status.truth_fields, expanded=False)


def render_edge_to_ground_explanation() -> None:
    st.info(
        "Raw images are processed onboard; only JSON/crop artifacts downlinked; "
        "ground station reads queue only."
    )


def render_crop_review(payloads: list[dict], events: list[dict]) -> None:
    st.subheader("Crop Review")
    evidence_rows = resolve_crop_evidence(payloads, events)
    if not evidence_rows:
        st.caption("no real crop available")
        return
    for evidence in evidence_rows:
        if evidence.available and evidence.path is not None:
            st.image(
                str(evidence.path),
                caption=f"tile_id={evidence.tile_id} | queue path={evidence.path}",
                width="stretch",
            )
        else:
            st.warning(f"{evidence.tile_id}: no real crop available")


def render_downlink_chart(events: list[dict]) -> None:
    st.subheader("Cumulative Downlink Proof")
    series = cumulative_series(events)
    if not series:
        st.info("Replay has not received telemetry yet.")
        return
    chart_df = pd.DataFrame(series).set_index("event")
    st.line_chart(chart_df[["Raw bytes processed in orbit", "Bytes downlinked"]], height=280)
    latest = series[-1]
    st.caption(
        "Ground station receives telemetry showing cumulative raw bytes processed on-board "
        f"({format_bytes(latest['Raw bytes processed in orbit'])}) versus actual downlink "
        f"({format_bytes(latest['Bytes downlinked'])})."
    )


def render_alert_table(payloads: list[dict], events: list[dict]) -> None:
    st.subheader("Alerts")
    rows = received_alert_rows(payloads, events)
    if not rows:
        st.info("No alert payloads received at this replay position.")
        return
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def render_replay_status(replay_events: list[dict], all_events: list[dict]) -> None:
    st.subheader("Mission Replay")
    if not replay_events:
        st.info("Press Mission replay to receive the next telemetry event.")
        return
    latest = replay_events[-1]
    st.markdown(f"**Latest tile:** `{latest.get('tile_id', 'unknown')}`")
    st.markdown(f"**Decision:** `{display_decision(latest) or 'unknown'}`")
    st.markdown(f"**Downlinked:** {format_bytes(event_downlinked_bytes(latest))}")
    st.caption(f"Event {len(replay_events)} of {len(all_events)}")


def render_technical_honesty() -> None:
    st.subheader("Technical Honesty")
    rows = [
        ("Real architecture", "edge pass writes queue payloads and telemetry; ground station reads only downlinked artifacts"),
        ("Simulated parts", "local orbital pass, placeholder raw tiles, baseline detector unless YOLO metadata is present"),
        ("Missing final integrations", "real Sentinel tiles, trained/validated YOLO weights, crop generation, threshold calibration"),
        ("Liquid LFM", "optional crop-level structured reasoning; LFM DISABLED, LIQUID MOCK, and LIQUID LFM REAL are shown from payload metadata"),
        ("What is proven", "payload reduction math and ground-station boundary"),
        ("What is not proven yet", "real orbital deployment or fully validated model performance"),
    ]
    for label, value in rows:
        st.markdown(f"**{label}:** {value}")


def _ratio_label(value: float) -> str:
    if math.isinf(value):
        return "infinite"
    return f"{value:.1f}x"


if __name__ == "__main__":
    main()

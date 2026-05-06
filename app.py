from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from kilnwatch.ground_station import (
    calculate_metrics,
    cumulative_series,
    detector_modes,
    display_decision,
    event_downlinked_bytes,
    format_bytes,
    load_ground_station_records,
    received_alert_rows,
    safe_review_payloads,
)


st.set_page_config(page_title="KilnWatch Ground Station", layout="wide")


def main() -> None:
    st.title("KilnWatch Ground Station")
    st.caption("Satellite-side brick kiln triage telemetry and downlink proof")

    payloads, telemetry_events, sample_data = load_ground_station_records()
    if not payloads and not telemetry_events:
        st.error("No transmission queue or telemetry logs found.")
        st.stop()

    if sample_data:
        st.warning("SAMPLE DATA - replace transmission_queue/ and telemetry_logs/ with mission outputs.")

    render_status_badges(payloads, telemetry_events, sample_data)

    replay_events = mission_replay_controls(telemetry_events)
    metrics = calculate_metrics(replay_events)

    render_metrics(metrics)
    render_downlink_chart(replay_events)

    left, right = st.columns([1.25, 0.75], gap="large")
    with left:
        render_alert_table(payloads, replay_events)
    with right:
        render_replay_status(replay_events, telemetry_events)
        render_technical_honesty()

    render_review_payloads(payloads)


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


def render_metrics(metrics) -> None:
    top = st.columns(4)
    top[0].metric("Tiles processed onboard", metrics.tiles_processed)
    top[1].metric("Raw bytes processed", format_bytes(metrics.raw_bytes_processed))
    top[2].metric("Downlinked bytes", format_bytes(metrics.downlinked_bytes))
    top[3].metric("Bandwidth saved", f"{metrics.bandwidth_saved_percent:.1f}%")

    bottom = st.columns(4)
    bottom[0].metric("Tiles ignored", metrics.ignored_tiles)
    bottom[1].metric("JSON alerts", metrics.json_alerts)
    bottom[2].metric("Crop/full review alerts", metrics.crop_or_full_review_alerts)
    bottom[3].metric("Compression ratio", _ratio_label(metrics.compression_ratio))

    st.caption(f"Average inference latency: {metrics.average_latency_ms:.2f} ms")


def render_status_badges(payloads: list[dict], events: list[dict], sample_data: bool) -> None:
    modes = detector_modes(payloads, events)
    badges: list[tuple[str, str]] = []
    if sample_data:
        badges.append(("SAMPLE DATA", "#92400e"))
    if any("baseline" in mode or "placeholder" in mode for mode in modes):
        badges.append(("BASELINE SIMULATION", "#1f2937"))
    if any("yolo" in mode for mode in modes):
        badges.append(("REAL YOLO MODE", "#166534"))
    if not badges:
        badges.append(("DETECTOR METADATA UNKNOWN", "#475569"))

    html = " ".join(
        f"<span style='display:inline-block;padding:0.35rem 0.6rem;margin:0 0.35rem 0.5rem 0;"
        f"border-radius:6px;background:{color};color:white;font-weight:700;font-size:0.8rem;'>{label}</span>"
        for label, color in badges
    )
    st.markdown(html, unsafe_allow_html=True)


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
    st.subheader("Received Alert Payloads")
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
        ("Real architecture", "satellite_edge_node writes queue payloads and telemetry; ground station reads only downlinked artifacts"),
        ("Simulated parts", "local orbital pass, placeholder raw tiles, baseline detector unless YOLO metadata is present"),
        ("Missing final integrations", "real Sentinel tiles, trained/validated YOLO weights, crop generation, threshold calibration"),
        ("Future Liquid/LFM integration", "use Liquid model/VLM reasoning after detector candidate generation or for risk scoring"),
        ("What is proven", "payload reduction math and ground-station boundary"),
        ("What is not proven yet", "real orbital deployment or fully validated model performance"),
    ]
    for label, value in rows:
        st.markdown(f"**{label}:** {value}")


def render_review_payloads(payloads: list[dict]) -> None:
    review_payloads = safe_review_payloads(payloads)
    with st.expander("Review payload references"):
        if not review_payloads:
            st.caption("No crop/full-review payload references received.")
            return
        for payload in review_payloads:
            st.json(
                {
                    "tile_id": payload.get("tile_id"),
                    "decision": payload.get("triage_decision"),
                    "payload_type": payload.get("payload_type"),
                    "payload_uri": payload.get("payload_uri"),
                    "note": "Ground station may inspect imagery only because this payload is review/full-downlink class.",
                },
                expanded=False,
            )


def _ratio_label(value: float) -> str:
    if math.isinf(value):
        return "infinite"
    return f"{value:.1f}x"


if __name__ == "__main__":
    main()

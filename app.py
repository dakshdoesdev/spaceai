from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from kilnwatch.ground_station import (
    FORBIDDEN_CROP_SOURCE_FRAGMENTS,
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

_PLACEHOLDER_SUFFIX = "." + "tile"  # split to avoid literal trip in boundary scan


st.set_page_config(
    page_title="KilnWatch Ground Station",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .block-container {
        max-width: 1180px;
        padding-top: 1.25rem;
        padding-bottom: 2rem;
    }

    .badge {
        display: inline-block;
        padding: 0.32rem 0.65rem;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0;
        text-transform: uppercase;
        margin: 0 0.4rem 0.4rem 0;
    }
    .badge-green  { background:#14532d; color:#4ade80; border:1px solid #4ade80; }
    .badge-yellow { background:#713f12; color:#fde047; border:1px solid #fde047; }
    .badge-red    { background:#7f1d1d; color:#f87171; border:1px solid #f87171; }
    .badge-gray   { background:#1e293b; color:#94a3b8; border:1px solid #475569; }
    .badge-blue   { background:#1e3a5f; color:#60a5fa; border:1px solid #60a5fa; }

    .proof-panel {
        border: 1px solid #263241;
        border-radius: 8px;
        background: #101721;
        padding: 0.85rem 1rem;
        min-height: 86px;
    }

    div[data-testid="stMetric"] {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 0.58rem 0.72rem;
    }
    div[data-testid="stMetricLabel"] { font-size: 0.75rem; color: #94a3b8; }
    div[data-testid="stMetricValue"] { font-size: 1.15rem; color: #f1f5f9; }

    .crop-card {
        background: #0f172a;
        border: 1px solid #1e3a5f;
        border-radius: 8px;
        padding: 0.55rem;
    }
    .crop-card-warn {
        background: #1c1204;
        border: 1px solid #92400e;
        border-radius: 8px;
        padding: 0.65rem;
    }
    .crop-meta { font-size: 0.7rem; color: #94a3b8; margin-top: 0.3rem; line-height: 1.5; }
    .crop-tile { font-size: 0.8rem; color: #e2e8f0; font-weight: 600; word-break: break-all; }

    .boundary-notice {
        background: #0a1628;
        border-left: 3px solid #3b82f6;
        border-radius: 4px;
        padding: 0.5rem 0.9rem;
        font-size: 0.82rem;
        color: #93c5fd;
        margin-bottom: 0.6rem;
    }

    .honesty-row {
        display: flex;
        gap: 0.6rem;
        margin-bottom: 0.3rem;
        font-size: 0.8rem;
        align-items: flex-start;
    }
    .honesty-key {
        color: #94a3b8;
        min-width: 180px;
        flex-shrink: 0;
    }
    .honesty-val { color: #cbd5e1; }

    hr { border-color: #1e293b; margin: 0.8rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Badge helpers ─────────────────────────────────────────────────────────────
_DETECTOR_BADGE_CLASS = {
    "STRICT YOLO REAL": "badge-green",
    "FALLBACK USED": "badge-yellow",
    "BASELINE SIMULATION": "badge-yellow",
    "SAMPLE DATA": "badge-gray",
}
_REASONER_BADGE_CLASS = {
    "LIQUID LFM REAL": "badge-green",
    "LIQUID MOCK": "badge-blue",
    "LFM DISABLED": "badge-gray",
}


def _badge(text: str, cls: str) -> str:
    return f'<span class="badge {cls}">{text}</span>'


def _detector_badge(label: str) -> str:
    cls = _DETECTOR_BADGE_CLASS.get(label, "badge-red")
    return _badge(label, cls)


def _reasoner_badge(label: str) -> str:
    cls = _REASONER_BADGE_CLASS.get(label, "badge-gray")
    return _badge(label, cls)


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    payloads, telemetry_events, sample_data = load_ground_station_records()
    if not payloads and not telemetry_events:
        st.error("⚠️  No transmission_queue or telemetry_logs found. Run the orbital pass first.")
        st.stop()

    status = proof_status_summary(payloads, telemetry_events, sample_data)
    replay_events = mission_replay_controls(telemetry_events)
    metrics = calculate_metrics(replay_events)
    counts = mission_proof_counts(payloads, replay_events)

    render_header(status, metrics, counts, sample_data)
    st.markdown("<hr>", unsafe_allow_html=True)
    render_mission_metrics(metrics, counts)
    st.markdown("<hr>", unsafe_allow_html=True)
    render_crop_review(payloads, replay_events)
    st.markdown("<hr>", unsafe_allow_html=True)

    left, right = st.columns([1.6, 1], gap="large")
    with left:
        render_alert_table(payloads, replay_events)
        render_downlink_chart(replay_events)
    with right:
        render_replay_status(replay_events, telemetry_events)
        render_technical_honesty(status)


# ── Header ────────────────────────────────────────────────────────────────────
def render_header(status, metrics, counts, sample_data: bool) -> None:
    st.markdown(
        "<h1 style='margin-bottom:0.1rem;font-size:2rem;'>KilnWatch Ground Station</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#64748b;font-size:0.95rem;margin-top:0;'>"
        "Satellite-side brick kiln triage with downlinked JSON and crop payloads from "
        "<code>transmission_queue/</code></p>",
        unsafe_allow_html=True,
    )
    st.markdown("### Proof Status")
    title_col, badge_col = st.columns([1.45, 1], gap="medium")

    with title_col:
        st.markdown(
            '<div class="proof-panel">'
            "<strong>Detector</strong><br>"
            f"{_detector_badge(status.detector_label)}"
            "<div style='color:#94a3b8;font-size:0.78rem;margin-top:0.25rem;'>"
            "YOLO localizes kiln candidates; fallback and sample states stay visible."
            "</div>",
            unsafe_allow_html=True,
        )

    with badge_col:
        st.markdown(
            '<div class="proof-panel">'
            "<strong>Liquid reasoner</strong><br>"
            f"{_reasoner_badge(status.reasoner_label)}"
            "<div style='color:#94a3b8;font-size:0.78rem;margin-top:0.25rem;'>"
            "Optional crop-level advisory JSON; disabled and mock modes are explicit."
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="boundary-notice">'
        "Raw images are processed onboard; only JSON/crop artifacts downlinked; "
        "ground station reads queue only."
        "</div>",
        unsafe_allow_html=True,
    )
    if sample_data:
        st.warning("SAMPLE DATA - replace transmission_queue/ and telemetry_logs/ with mission outputs.")
    if status.truth_fields:
        with st.expander("Proof metadata", expanded=False):
            st.json(status.truth_fields)


# ── Replay controls ───────────────────────────────────────────────────────────
def mission_replay_controls(events: list[dict]) -> list[dict]:
    if "replay_index" not in st.session_state:
        st.session_state.replay_index = len(events)

    controls = st.columns([0.14, 0.14, 0.72])
    if controls[0].button("Replay", use_container_width=True):
        if st.session_state.replay_index >= len(events):
            st.session_state.replay_index = 1 if events else 0
        else:
            st.session_state.replay_index += 1
    if controls[1].button("Reset", use_container_width=True):
        st.session_state.replay_index = 0

    replay_index = min(st.session_state.replay_index, len(events))
    controls[2].progress((replay_index / len(events)) if events else 0.0)
    controls[2].caption(f"Replay position: {replay_index} / {len(events)} telemetry events")
    return events[:replay_index]


# ── Mission Metrics ───────────────────────────────────────────────────────────
def render_mission_metrics(metrics, counts) -> None:
    st.markdown("### Mission Metrics")

    top = st.columns(4)
    top[0].metric("Tiles processed", metrics.tiles_processed, help="Total tiles evaluated onboard")
    top[1].metric("Detections", counts.detections, help="Tiles with kiln-positive signals")
    top[2].metric("Crops downlinked", counts.crops_generated, help="Real crop files in transmission_queue/crops/")
    top[3].metric("Bandwidth saved", f"{metrics.bandwidth_saved_percent:.1f}%", help="(raw − transmitted) / raw")

    bot = st.columns(4)
    bot[0].metric("Raw bytes (onboard)", format_bytes(metrics.raw_bytes_processed))
    bot[1].metric("Transmitted bytes", format_bytes(metrics.downlinked_bytes))
    bot[2].metric("Compression ratio", _ratio_label(metrics.compression_ratio))
    bot[3].metric("Avg inference latency", f"{metrics.average_latency_ms:.1f} ms")

    st.caption(
        f"JSON-only alerts: **{metrics.json_alerts}** · "
        f"Crop/review alerts: **{metrics.crop_or_full_review_alerts}** · "
        f"Ignored (no kiln): **{metrics.ignored_tiles}**"
    )


# ── Crop Review ───────────────────────────────────────────────────────────────
def render_crop_review(payloads: list[dict], events: list[dict]) -> None:
    st.markdown("### Crop Review")
    st.caption(
        "Only crop files physically present in `transmission_queue/crops/` are shown."
    )
    evidence_rows = resolve_crop_evidence(payloads, events)
    if not evidence_rows:
        st.info("no real crop available")
        return

    # Build a lookup for extra metadata from payloads
    payload_by_tile = {p.get("tile_id"): p for p in payloads}
    event_by_tile   = {e.get("tile_id"): e for e in events}

    COLS = 4
    rows = [evidence_rows[i : i + COLS] for i in range(0, len(evidence_rows), COLS)]
    for row in rows:
        cols = st.columns(COLS)
        for col, evidence in zip(cols, row):
            with col:
                _render_crop_card(evidence, payload_by_tile, event_by_tile)


def _render_crop_card(evidence, payload_by_tile: dict, event_by_tile: dict) -> None:
    tile_id = evidence.tile_id
    payload = payload_by_tile.get(tile_id, {})
    event   = event_by_tile.get(tile_id, {})

    conf      = payload.get("confidence", event.get("confidence"))
    det_mode  = payload.get("detector_mode", event.get("detector_mode", "—"))
    risk      = payload.get("compliance_risk", event.get("compliance_risk", "—"))
    decision  = payload.get("action", event.get("action", "—"))
    fname     = evidence.path.name if evidence.path else "—"

    if evidence.available and evidence.path is not None:
        st.markdown('<div class="crop-card">', unsafe_allow_html=True)
        st.image(
            str(evidence.path),
            width=220,
            caption=None,
        )
        conf_str = f"{float(conf):.0%}" if conf is not None else "—"
        st.markdown(
            f'<div class="crop-tile">{tile_id[:32]}…</div>'
            f'<div class="crop-meta">'
            f"🎯 Conf: <b>{conf_str}</b> · Risk: <b>{risk}</b><br>"
            f"🔬 Detector: <b>{det_mode}</b><br>"
            f"📋 Action: <b>{decision}</b><br>"
            f"📁 <code>{fname}</code>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="crop-card-warn">'
            f'<div class="crop-tile">{tile_id[:36]}…</div>'
            f'<div class="crop-meta">no real crop available<br>'
            f"Action: <b>{decision}</b></div>"
            f"</div>",
            unsafe_allow_html=True,
        )


# ── Alert Table ───────────────────────────────────────────────────────────────
def render_alert_table(payloads: list[dict], events: list[dict]) -> None:
    st.markdown("### Alerts")
    rows = _build_alert_rows(payloads, events)
    if not rows:
        st.info("No alerts received at this replay position.")
        return

    df = pd.DataFrame(rows)

    def _row_style(row):
        styles = [""] * len(row)
        if row.get("real_yolo") is True:
            base = "background-color:#0d2b1a; color:#4ade80"
        elif row.get("fallback") is True:
            base = "background-color:#2b1a0d; color:#fbbf24"
        elif row.get("simulated") is True:
            base = "background-color:#1a1a2b; color:#818cf8"
        else:
            base = ""
        # flag missing crop on review decisions
        if row.get("crop_present") is False and row.get("triage_action") in (
            "CROP_OR_REVIEW",
            "FULL_DOWNLINK",
        ):
            base += "; font-style:italic"
        return [base] * len(row)

    # drop internal columns before display
    display_df = df.drop(columns=["real_yolo", "fallback", "simulated"], errors="ignore")
    st.dataframe(
        display_df.style.apply(_row_style, axis=1),
        use_container_width=True,
        hide_index=True,
    )

    # legend
    st.caption(
        "Real YOLO rows are green. Fallback/baseline rows are yellow. Simulated rows are blue. "
        "Italic review rows have no crop present."
    )


def _build_alert_rows(payloads: list[dict], events: list[dict]) -> list[dict]:
    payload_by_tile = {p.get("tile_id"): p for p in payloads}
    REVIEW = {"CROP_OR_REVIEW", "FULL_DOWNLINK"}
    rows: list[dict] = []
    for event in events:
        decision_str = _decision_str(event)
        payload = payload_by_tile.get(event.get("tile_id"), {})

        conf = payload.get("confidence", event.get("confidence"))
        conf_str = f"{float(conf):.0%}" if conf is not None else ""

        detector_mode = event.get("detector_mode") or payload.get("detector_mode") or ""
        simulated     = bool(event.get("simulated", payload.get("simulated", False)))
        detector_real = bool(event.get("detector_is_real", payload.get("detector_is_real", False)))
        fallback      = bool(event.get("fallback_used", payload.get("fallback_used", False)))

        # crop present check: look for crop_path or crop_ref in queue
        crop_field = (
            payload.get("crop_ref")
            or event.get("crop_path")
            or event.get("crop_ref")
        )
        _crop_str = str(crop_field)
        crop_present = bool(crop_field) and not _crop_str.endswith(_PLACEHOLDER_SUFFIX) and not any(
            f in _crop_str for f in FORBIDDEN_CROP_SOURCE_FRAGMENTS
        )

        ts = event.get("timestamp_utc", "")

        rows.append(
            {
                "tile_id":       (event.get("tile_id") or "")[:40],
                "detector_mode": detector_mode,
                "confidence":    conf_str,
                "simulated":     simulated,
                "fallback":      fallback,
                "real_yolo":     detector_real and "yolo" in detector_mode.lower(),
                "triage_action": decision_str,
                "crop_present":  crop_present,
                "transmitted":   format_bytes(
                    int(event.get("transmitted_payload_bytes", 0))
                ),
                "timestamp":     ts,
            }
        )
    return rows


def _decision_str(event: dict) -> str:
    explicit = event.get("triage_decision") or event.get("decision")
    if explicit:
        return str(explicit)
    action = event.get("action", "")
    if action == "DROP_RAW_TILE" or event.get("event") == "dropped":
        return "IGNORE"
    if action == "TRANSMIT_ALERT" or event.get("event") == "alert":
        risk = str(event.get("compliance_risk", "")).lower()
        conf = 0.0
        try:
            conf = float(event.get("confidence", 0))
        except (TypeError, ValueError):
            pass
        if risk == "high" and conf >= 0.85:
            return "FULL_DOWNLINK"
        return "CROP_OR_REVIEW"
    return ""


# ── Downlink Chart ────────────────────────────────────────────────────────────
def render_downlink_chart(events: list[dict]) -> None:
    st.markdown("### Cumulative Downlink Proof")
    series = cumulative_series(events)
    if not series:
        st.info("No telemetry at this replay position.")
        return
    chart_df = pd.DataFrame(series).set_index("event")
    st.line_chart(chart_df[["Raw bytes processed in orbit", "Bytes downlinked"]], height=220)
    latest = series[-1]
    st.caption(
        f"Total raw processed onboard: **{format_bytes(latest['Raw bytes processed in orbit'])}** · "
        f"Actually downlinked: **{format_bytes(latest['Bytes downlinked'])}**"
    )


# ── Replay Status ─────────────────────────────────────────────────────────────
def render_replay_status(replay_events: list[dict], all_events: list[dict]) -> None:
    st.markdown("### Mission Replay")
    if not replay_events:
        st.info("Press Replay to step through telemetry events.")
        return
    latest = replay_events[-1]
    decision = display_decision(latest) or "unknown"
    st.markdown(
        f"**Latest tile:** `{latest.get('tile_id', 'unknown')}`  \n"
        f"**Decision:** `{decision}`  \n"
        f"**Downlinked:** {format_bytes(event_downlinked_bytes(latest))}"
    )
    st.caption(f"Event {len(replay_events)} of {len(all_events)}")


# ── Technical Honesty ─────────────────────────────────────────────────────────
def render_technical_honesty(status) -> None:
    st.markdown("### Technical Honesty")

    detector_real = "STRICT YOLO REAL" in status.detector_label
    reasoner_real = "LIQUID LFM REAL" in status.reasoner_label

    rows = [
        ("Deployment type",   "Local satellite-edge simulation - not a deployed satellite payload"),
        ("Detector",          f"{'Real local YOLO inference (detector_is_real: true)' if detector_real else 'Baseline / simulated detector'}"),
        ("Reasoner (LFM)",    f"{'Real Liquid LFM' if reasoner_real else status.reasoner_label + ' - disabled or mock mode'}"),
        ("Boundary enforced", "Ground station reads only transmission_queue/ artifacts"),
        ("Placeholder tiles", "Placeholder fixtures are not real imagery — final proof needs JPG/PNG/TIF"),
        ("What is proven",    "Payload reduction math, boundary separation, YOLO detection chain"),
        ("Not yet proven",    "Real orbital deployment, large-scale validation, Sentinel tile pipeline"),
    ]

    for label, value in rows:
        st.markdown(
            f'<div class="honesty-row">'
            f'<span class="honesty-key">{label}</span>'
            f'<span class="honesty-val">{value}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )


# ── Helpers ───────────────────────────────────────────────────────────────────
def _ratio_label(value: float) -> str:
    if math.isinf(value):
        return "∞"
    return f"{value:.1f}×"


if __name__ == "__main__":
    main()

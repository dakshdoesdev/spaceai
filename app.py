from __future__ import annotations

import json
import math
from html import escape
from pathlib import Path
from typing import Any
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
    resolve_crop_evidence,
)


st.set_page_config(
    page_title="KilnWatch Mission Control",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def main() -> None:
    _inject_mission_control_css()
    _render_ops_rail()
    _render_top_bar()

    payloads, telemetry_events, sample_data = load_ground_station_records()
    if not payloads and not telemetry_events:
        st.error("No transmission_queue or telemetry_logs found. Run the orbital pass first.")
        st.stop()

    _ensure_replay_index(telemetry_events)
    replay_events = _current_replay_events(telemetry_events)
    status = proof_status_summary(payloads, telemetry_events, sample_data)
    metrics = calculate_metrics(replay_events)
    counts = mission_proof_counts(payloads, replay_events)
    evidence = resolve_crop_evidence(payloads, replay_events)

    st.markdown('<main class="kw-main">', unsafe_allow_html=True)
    _render_header()
    _render_proof_status(status, sample_data, evidence)
    _render_mission_metrics(metrics, counts)
    _render_transparency_panel(status)
    replay_events = _render_replay_controls(telemetry_events)
    _render_lower_console(payloads, replay_events, evidence)
    st.markdown("</main>", unsafe_allow_html=True)


def _inject_mission_control_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --kw-bg: #141313;
            --kw-panel: #1c1b1b;
            --kw-panel-2: #201f1f;
            --kw-panel-3: #353434;
            --kw-text: #e5e2e1;
            --kw-muted: #c4c7c8;
            --kw-border: #444748;
            --kw-outline: #8e9192;
            --kw-good: #fdfdfc;
            --kw-stream: #c1c7d1;
            --kw-warn: #ffba43;
            --kw-error: #ffb4ab;
        }

        .stApp {
            background: var(--kw-bg);
            color: var(--kw-text);
            font-family: ui-sans-serif, system-ui, sans-serif;
        }

        .block-container {
            max-width: none;
            padding: 80px 24px 24px 280px;
            margin-left: 0;
        }

        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        header[data-testid="stHeader"] {
            display: none;
        }

        .kw-side {
            position: fixed;
            inset: 0 auto 0 0;
            width: 256px;
            background: var(--kw-panel);
            border-right: 1px solid var(--kw-border);
            z-index: 20;
            padding: 24px 16px;
            display: flex;
            flex-direction: column;
        }

        .kw-side-title {
            font-size: 18px;
            font-weight: 700;
        }

        .kw-side-status {
            margin-top: 4px;
            font-family: monospace;
            font-size: 13px;
            color: var(--kw-muted);
            position: relative;
            cursor: default;
        }

        .kw-side-status:hover .kw-flyout,
        .kw-nav-item:hover .kw-flyout,
        .kw-tab:hover .kw-flyout {
            display: block;
        }

        .kw-nav {
            margin-top: 36px;
            display: grid;
            gap: 4px;
        }

        .kw-nav-item {
            position: relative;
            height: 40px;
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 0 12px;
            border-left: 2px solid transparent;
            color: var(--kw-muted);
            font-size: 11px;
            font-weight: 700;
        }

        .kw-nav-item.active {
            background: #414750;
            color: var(--kw-text);
            border-left-color: var(--kw-good);
        }

        .kw-nav-item.active::after {
            content: "";
            position: absolute;
            left: 48px;
            right: 12px;
            bottom: 5px;
            height: 2px;
            background: var(--kw-good);
        }

        .kw-nav-symbol {
            width: 22px;
            font-family: monospace;
            text-align: center;
            font-size: 18px;
        }

        .kw-side-footer {
            margin-top: auto;
            border: 1px solid var(--kw-outline);
            height: 42px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--kw-text);
            font-size: 11px;
            font-weight: 700;
        }

        .kw-top {
            position: fixed;
            top: 0;
            left: 256px;
            right: 0;
            z-index: 10;
            height: 56px;
            background: #0e0e0e;
            border-bottom: 1px solid var(--kw-border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 24px;
        }

        .kw-build {
            font-family: monospace;
            font-size: 24px;
            letter-spacing: -0.02em;
            color: var(--kw-good);
        }

        .kw-tabs {
            display: flex;
            gap: 28px;
            font-size: 11px;
            font-weight: 700;
            color: var(--kw-muted);
        }

        .kw-tab {
            position: relative;
            height: 56px;
            display: flex;
            align-items: center;
        }

        .kw-tab.active {
            color: var(--kw-text);
            border-bottom: 2px solid var(--kw-text);
        }

        .kw-flyout {
            display: none;
            position: absolute;
            left: calc(100% + 14px);
            top: 0;
            width: 260px;
            background: #0e0e0e;
            border: 1px solid var(--kw-outline);
            color: var(--kw-text);
            z-index: 40;
            padding: 10px;
            font-family: monospace;
            font-size: 12px;
            line-height: 1.45;
        }

        .kw-flyout-title {
            color: var(--kw-good);
            font-weight: 700;
            margin-bottom: 6px;
        }

        .kw-flyout-row {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            border-top: 1px solid var(--kw-border);
            padding-top: 6px;
            margin-top: 6px;
            color: var(--kw-muted);
        }

        .kw-tab .kw-flyout {
            left: auto;
            right: 0;
            top: 52px;
        }

        .kw-main {
            display: block;
            padding: 0;
        }

        .kw-title {
            padding: 0 0 24px;
            border-bottom: 1px solid var(--kw-border);
            margin-bottom: 24px;
        }

        .kw-title h1 {
            margin: 0 0 8px;
            font-family: monospace;
            font-size: 24px;
            line-height: 32px;
            font-weight: 500;
            color: var(--kw-text);
        }

        .kw-title p {
            margin: 0;
            font-family: monospace;
            font-size: 13px;
            color: var(--kw-muted);
        }

        .kw-section-label {
            margin: 18px 0 8px;
            color: var(--kw-text);
            font-size: 11px;
            font-weight: 700;
        }

        .kw-strip,
        .kw-metrics {
            display: grid;
            gap: 6px;
        }

        .kw-strip {
            grid-template-columns: repeat(5, max-content);
            overflow-x: auto;
            padding-bottom: 2px;
        }

        .kw-chip {
            border: 1px solid var(--kw-outline);
            background: var(--kw-panel);
            color: var(--kw-text);
            padding: 7px 9px;
            font-size: 11px;
            font-weight: 700;
            white-space: nowrap;
        }

        .kw-pip {
            display: inline-block;
            width: 8px;
            height: 8px;
            margin-right: 6px;
            background: var(--kw-good);
        }

        .kw-pip.muted { background: var(--kw-border); }
        .kw-pip.warn { background: var(--kw-warn); }

        .kw-metrics {
            grid-template-columns: repeat(6, minmax(0, 1fr));
            margin-top: 10px;
        }

        .kw-metric {
            min-height: 96px;
            border: 1px solid var(--kw-border);
            background: var(--kw-panel);
            padding: 12px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .kw-metric-label {
            color: var(--kw-muted);
            font-size: 11px;
            font-weight: 700;
        }

        .kw-metric-value {
            font-family: monospace;
            font-size: 24px;
            color: var(--kw-good);
        }

        .kw-panel {
            border: 1px solid var(--kw-border);
            background: var(--kw-panel);
        }

        .kw-panel-head {
            background: var(--kw-panel-3);
            border-bottom: 1px solid var(--kw-border);
            padding: 10px 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 11px;
            font-weight: 700;
        }

        .kw-panel-body {
            padding: 12px;
        }

        .kw-transparency {
            margin-top: 20px;
            border: 1px solid var(--kw-outline);
            background: var(--kw-panel-2);
            padding: 12px;
            font-family: monospace;
            font-size: 13px;
            color: var(--kw-muted);
        }

        .kw-transparency strong {
            color: var(--kw-text);
        }

        .kw-lower {
            display: grid;
            grid-template-columns: minmax(0, 2fr) minmax(320px, 1fr);
            gap: 24px;
            margin-top: 20px;
        }

        .kw-evidence-note {
            font-family: monospace;
            color: var(--kw-muted);
            text-align: center;
            font-size: 13px;
            line-height: 1.6;
        }

        .kw-json pre {
            margin: 0;
            padding: 12px;
            min-height: 220px;
            overflow: auto;
            background: #0e0e0e;
            color: var(--kw-text);
            border: 0;
            font-family: monospace;
            font-size: 12px;
            line-height: 1.5;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--kw-border);
        }

        .kw-table {
            width: 100%;
            border-collapse: collapse;
            font-family: monospace;
            font-size: 13px;
        }

        .kw-table th {
            color: var(--kw-muted);
            background: var(--kw-panel-2);
            border-bottom: 1px solid var(--kw-border);
            font-size: 11px;
            font-weight: 700;
            padding: 9px 10px;
            text-align: left;
        }

        .kw-table td {
            border-bottom: 1px solid var(--kw-border);
            padding: 9px 10px;
            color: var(--kw-text);
            white-space: nowrap;
        }

        .kw-table td.muted {
            color: var(--kw-muted);
        }

        .kw-table td.good {
            color: var(--kw-good);
        }

        div[data-testid="stButton"] button {
            border-radius: 0;
            border: 1px solid var(--kw-outline);
            background: transparent;
            color: var(--kw-text);
            font-size: 11px;
            font-weight: 700;
        }

        div[data-testid="stButton"] button:hover {
            border-color: var(--kw-good);
            color: var(--kw-good);
        }

        @media (max-width: 920px) {
            .kw-side { display: none; }
            .kw-top { left: 0; }
            .block-container { padding: 76px 16px 16px; }
            .kw-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .kw-lower { grid-template-columns: 1fr; }
            .kw-build { font-size: 18px; }
            .kw-tabs { display: none; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_ops_rail() -> None:
    st.markdown(
        """
        <aside class="kw-side">
          <div>
            <div class="kw-side-title">SAT-01 / BUS / OPS</div>
            <div class="kw-side-status">STATUS: NOMINAL
              <div class="kw-flyout">
                <div class="kw-flyout-title">Satellite Bus</div>
                <div>Current orbit pass is loaded from downlinked telemetry.</div>
                <div class="kw-flyout-row"><span>Boundary</span><span>queue-only</span></div>
                <div class="kw-flyout-row"><span>Detector</span><span>YOLO strict</span></div>
              </div>
            </div>
          </div>
          <nav class="kw-nav">
            <div class="kw-nav-item"><span class="kw-nav-symbol">01</span><span>SENSOR</span>
              <div class="kw-flyout">
                <div class="kw-flyout-title">Sensor</div>
                <div>Raw tile intake is satellite-side only.</div>
                <div class="kw-flyout-row"><span>Ground access</span><span>blocked</span></div>
                <div class="kw-flyout-row"><span>Visible here</span><span>telemetry</span></div>
              </div>
            </div>
            <div class="kw-nav-item"><span class="kw-nav-symbol">02</span><span>NETWORK</span>
              <div class="kw-flyout">
                <div class="kw-flyout-title">Network</div>
                <div>Downlink path carries JSON payloads and crop files only.</div>
                <div class="kw-flyout-row"><span>Queue</span><span>transmission_queue/</span></div>
                <div class="kw-flyout-row"><span>Raw bytes</span><span>not sent</span></div>
              </div>
            </div>
            <div class="kw-nav-item"><span class="kw-nav-symbol">03</span><span>PAYLOAD</span>
              <div class="kw-flyout">
                <div class="kw-flyout-title">Payload</div>
                <div>Each alert links detector metadata, triage action, and crop evidence.</div>
                <div class="kw-flyout-row"><span>Format</span><span>JSON + PNG</span></div>
                <div class="kw-flyout-row"><span>Preview</span><span>real crop only</span></div>
              </div>
            </div>
            <div class="kw-nav-item active"><span class="kw-nav-symbol">04</span><span>TRIAGE</span>
              <div class="kw-flyout">
                <div class="kw-flyout-title">Triage</div>
                <div>Active judge view: proof status, mission metrics, alerts, crop review.</div>
                <div class="kw-flyout-row"><span>Detector</span><span>honest mode</span></div>
                <div class="kw-flyout-row"><span>LFM</span><span>optional</span></div>
              </div>
            </div>
            <div class="kw-nav-item"><span class="kw-nav-symbol">05</span><span>SYSTEM</span>
              <div class="kw-flyout">
                <div class="kw-flyout-title">System</div>
                <div>Technical honesty state comes from payload and telemetry metadata.</div>
                <div class="kw-flyout-row"><span>Fallbacks</span><span>visible</span></div>
                <div class="kw-flyout-row"><span>Samples</span><span>flagged</span></div>
              </div>
            </div>
          </nav>
          <div class="kw-side-footer">REPLAY_MODE</div>
        </aside>
        """,
        unsafe_allow_html=True,
    )


def _render_top_bar() -> None:
    st.markdown(
        """
        <header class="kw-top">
          <div class="kw-build">ORBITAL_TRIAGE_v4.1</div>
          <div class="kw-tabs">
            <div class="kw-tab">LIVE
              <div class="kw-flyout">
                <div class="kw-flyout-title">Live</div>
                <div>Shows the current replay frame from queue telemetry.</div>
                <div class="kw-flyout-row"><span>State</span><span>local demo</span></div>
              </div>
            </div>
            <div class="kw-tab">ARCHIVE
              <div class="kw-flyout">
                <div class="kw-flyout-title">Archive</div>
                <div>Past alert payloads remain visible from transmission_queue.</div>
                <div class="kw-flyout-row"><span>Source</span><span>JSON files</span></div>
              </div>
            </div>
            <div class="kw-tab active">TELEMETRY
              <div class="kw-flyout">
                <div class="kw-flyout-title">Telemetry</div>
                <div>Active view for byte accounting and detector honesty fields.</div>
                <div class="kw-flyout-row"><span>Replay</span><span>enabled</span></div>
              </div>
            </div>
            <div class="kw-tab">DIAGNOSTICS
              <div class="kw-flyout">
                <div class="kw-flyout-title">Diagnostics</div>
                <div>Boundary proof and missing crop states are exposed in-panel.</div>
                <div class="kw-flyout-row"><span>Raw tiles</span><span>not read</span></div>
              </div>
            </div>
          </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def _render_header() -> None:
    st.markdown(
        """
        <section class="kw-title">
          <h1>KilnWatch</h1>
          <p>Satellite-side brick kiln triage with queue-only downlink.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_proof_status(status: Any, sample_data: bool, evidence: list[Any]) -> None:
    crop_state = "CROP: PRESENT" if any(item.available for item in evidence) else "CROP: QUEUE ONLY"
    fallback_used = bool(status.truth_fields.get("fallback_used"))
    fallback_state = "FALLBACK: USED" if fallback_used else "FALLBACK: NOT USED"
    detector_pip = "warn" if status.detector_label in {"BASELINE SIMULATION", "FALLBACK USED"} else ""
    reasoner_pip = "muted" if status.reasoner_label == "LFM DISABLED" else ""
    sample_chip = (
        '<div class="kw-chip"><span class="kw-pip warn"></span>[SAMPLE DATA]</div>'
        if sample_data
        else ""
    )
    st.markdown(
        f"""
        <div class="kw-section-label">Proof Status</div>
        <section class="kw-strip">
          <div class="kw-chip"><span class="kw-pip {detector_pip}"></span>[{status.detector_label}]</div>
          <div class="kw-chip"><span class="kw-pip {reasoner_pip}"></span>[{status.reasoner_label}]</div>
          <div class="kw-chip"><span class="kw-pip muted"></span>[{fallback_state}]</div>
          <div class="kw-chip"><span class="kw-pip"></span>[{crop_state}]</div>
          {sample_chip}
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_mission_metrics(metrics: Any, counts: Any) -> None:
    data_volume = f"RAW {format_bytes(metrics.raw_bytes_processed)} / DL {format_bytes(metrics.downlinked_bytes)}"
    tiles = _format_int(metrics.tiles_processed)
    detections = _format_int(counts.detections)
    crops = _format_int(counts.crops_generated)
    saved = f"{metrics.bandwidth_saved_percent:.1f}%"
    ratio = _ratio_label(metrics.compression_ratio)
    st.markdown(
        f"""
        <div class="kw-section-label">Mission Metrics</div>
        <section class="kw-metrics">
          <div class="kw-metric"><span class="kw-metric-label">Tiles Processed</span><span class="kw-metric-value">{tiles}</span></div>
          <div class="kw-metric"><span class="kw-metric-label">Detections</span><span class="kw-metric-value">{detections}</span></div>
          <div class="kw-metric"><span class="kw-metric-label">Crops Downlinked</span><span class="kw-metric-value">{crops}</span></div>
          <div class="kw-metric"><span class="kw-metric-label">Bandwidth Saved</span><span class="kw-metric-value">{saved}</span></div>
          <div class="kw-metric"><span class="kw-metric-label">Compression Ratio</span><span class="kw-metric-value">{ratio}</span></div>
          <div class="kw-metric"><span class="kw-metric-label">Data Volume</span><span class="kw-metric-value" style="font-size:13px">{data_volume}</span></div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_transparency_panel(status: Any) -> None:
    st.markdown(
        f"""
        <section class="kw-transparency">
          <strong>Engineering Transparency:</strong>
          Raw images are processed onboard; only JSON/crop artifacts downlinked;
          ground station reads queue only. Detector state is <strong>{status.detector_label}</strong>.
          Liquid reasoner state is <strong>{status.reasoner_label}</strong>.
          Crop quality reflects source resolution and saved crop dimensions.
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_replay_controls(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    st.markdown('<div class="kw-section-label">Mission Replay</div>', unsafe_allow_html=True)
    controls = st.columns([0.12, 0.12, 0.76])
    if controls[0].button("Replay", use_container_width=True):
        if st.session_state.replay_index >= len(events):
            st.session_state.replay_index = 1 if events else 0
        else:
            st.session_state.replay_index += 1
    if controls[1].button("Reset", use_container_width=True):
        st.session_state.replay_index = 0
    replay_index = min(st.session_state.replay_index, len(events))
    progress = (replay_index / len(events)) if events else 0.0
    controls[2].markdown(
        f"""
        <div style="border:1px solid var(--kw-border);height:36px;padding:7px 9px;font-family:monospace;font-size:12px;color:var(--kw-muted);">
          <div style="height:4px;background:#0e0e0e;border:1px solid var(--kw-border);margin-bottom:5px;">
            <div style="height:100%;width:{progress * 100:.1f}%;background:var(--kw-good);"></div>
          </div>
          Replay position: {replay_index} / {len(events)} telemetry events
        </div>
        """,
        unsafe_allow_html=True,
    )
    return events[:replay_index]


def _render_lower_console(
    payloads: list[dict[str, Any]],
    events: list[dict[str, Any]],
    evidence: list[Any],
) -> None:
    left, right = st.columns([1.9, 0.9], gap="large")
    with left:
        _render_downlink_queue(payloads, events, evidence)
        _render_downlink_chart(events)
    with right:
        _render_evidence_payload(payloads, events, evidence)
        _render_raw_telemetry(events)


def _render_downlink_queue(
    payloads: list[dict[str, Any]],
    events: list[dict[str, Any]],
    evidence: list[Any],
) -> None:
    st.markdown('<div class="kw-section-label">Alerts</div>', unsafe_allow_html=True)
    rows = _build_queue_rows(payloads, events, evidence)
    if not rows:
        st.info("No alerts received at this replay position.")
        return
    st.markdown(_queue_table_html(rows), unsafe_allow_html=True)


def _queue_table_html(rows: list[dict[str, Any]]) -> str:
    columns = ["ID", "MODE", "TYPE", "CONF", "TRIAGE", "CROP", "RAW / DL"]
    header = "".join(f"<th>{escape(column)}</th>" for column in columns)
    body_rows = []
    for row in rows:
        cells = []
        for column in columns:
            value = str(row.get(column, ""))
            css_class = ""
            if column in {"MODE", "RAW / DL"}:
                css_class = ' class="muted"'
            if column in {"TYPE", "CROP"} and value in {"REAL", "PRESENT"}:
                css_class = ' class="good"'
            cells.append(f"<td{css_class}>{escape(value)}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")
    return (
        '<section class="kw-panel">'
        '<div class="kw-panel-head"><span>Downlink Queue</span></div>'
        '<div class="kw-panel-body" style="padding:0;overflow:auto;max-height:360px;">'
        f'<table class="kw-table"><thead><tr>{header}</tr></thead>'
        f"<tbody>{''.join(body_rows)}</tbody></table>"
        "</div></section>"
    )


def _render_evidence_payload(
    payloads: list[dict[str, Any]],
    events: list[dict[str, Any]],
    evidence: list[Any],
) -> None:
    st.markdown('<div class="kw-section-label">Crop Review</div>', unsafe_allow_html=True)
    selected = _selected_evidence(evidence)
    st.markdown('<section class="kw-panel"><div class="kw-panel-head"><span>Evidence Payload</span></div><div class="kw-panel-body">', unsafe_allow_html=True)
    if selected is None:
        st.markdown('<div class="kw-evidence-note">no real crop available</div>', unsafe_allow_html=True)
    elif selected.available and selected.path is not None:
        width, height = _image_size(selected.path)
        display_width = _crop_display_width(width)
        st.image(str(selected.path), width=display_width)
        size = f"{width}x{height}px" if width and height else "size unknown"
        st.markdown(
            f"""
            <div class="kw-evidence-note">
              Native Scale ({size})<br>
              Source: {selected.path.name}<br>
              Tile: {selected.tile_id}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="kw-evidence-note">{selected.tile_id}<br>no real crop available</div>',
            unsafe_allow_html=True,
        )
    st.markdown("</div></section>", unsafe_allow_html=True)


def _render_raw_telemetry(events: list[dict[str, Any]]) -> None:
    latest = events[-1] if events else {}
    st.markdown('<div class="kw-section-label">Raw Telemetry</div>', unsafe_allow_html=True)
    st.markdown(
        '<section class="kw-panel kw-json"><div class="kw-panel-head"><span>Telemetry JSON</span></div>',
        unsafe_allow_html=True,
    )
    st.code(json.dumps(latest, indent=2, sort_keys=True), language="json")
    st.markdown("</section>", unsafe_allow_html=True)


def _render_downlink_chart(events: list[dict[str, Any]]) -> None:
    st.markdown('<div class="kw-section-label">Cumulative Downlink Proof</div>', unsafe_allow_html=True)
    series = cumulative_series(events)
    if not series:
        st.info("No telemetry at this replay position.")
        return
    st.markdown(_downlink_proof_html(series), unsafe_allow_html=True)


def _downlink_proof_html(series: list[dict[str, Any]]) -> str:
    latest = series[-1]
    raw_total = _safe_int(latest.get("Raw bytes processed in orbit"))
    downlinked_total = _safe_int(latest.get("Bytes downlinked"))
    rows = []
    for point in series[-8:]:
        event = str(point.get("event", ""))
        raw_bytes = _safe_int(point.get("Raw bytes processed in orbit"))
        downlinked_bytes = _safe_int(point.get("Bytes downlinked"))
        saved = max(raw_bytes - downlinked_bytes, 0)
        rows.append(
            "<tr>"
            f"<td>{escape(event)}</td>"
            f'<td class="muted">{escape(format_bytes(raw_bytes))}</td>'
            f'<td class="muted">{escape(format_bytes(downlinked_bytes))}</td>'
            f"<td>{escape(format_bytes(saved))}</td>"
            "<td>"
            '<div style="height:6px;background:#0e0e0e;border:1px solid var(--kw-border);">'
            f'<div style="height:100%;width:{_percent(raw_bytes, raw_total):.2f}%;background:var(--kw-muted);"></div>'
            "</div>"
            '<div style="height:6px;background:#0e0e0e;border:1px solid var(--kw-border);margin-top:4px;">'
            f'<div style="height:100%;width:{_percent(downlinked_bytes, raw_total):.2f}%;background:var(--kw-good);"></div>'
            "</div>"
            "</td>"
            "</tr>"
        )
    return (
        '<section class="kw-panel">'
        '<div class="kw-panel-head"><span>Raw vs Downlinked Bytes</span></div>'
        '<div class="kw-panel-body" style="padding:0;overflow:auto;">'
        '<table class="kw-table"><thead><tr>'
        "<th>Event</th><th>Raw</th><th>Downlinked</th><th>Saved</th><th>Proof</th>"
        f"</tr></thead><tbody>{''.join(rows)}</tbody></table>"
        "</div></section>"
        f'<div class="kw-evidence-note" style="text-align:left;margin-top:8px;">'
        f"Latest cumulative: raw {escape(format_bytes(raw_total))} / "
        f"downlinked {escape(format_bytes(downlinked_total))}</div>"
    )


def _build_queue_rows(
    payloads: list[dict[str, Any]],
    events: list[dict[str, Any]],
    evidence: list[Any],
) -> list[dict[str, Any]]:
    payload_by_tile = {payload.get("tile_id"): payload for payload in payloads}
    crop_tiles = {item.tile_id for item in evidence if item.available}
    rows: list[dict[str, Any]] = []
    for event in events:
        decision = display_decision(event)
        if decision == "IGNORE":
            continue
        tile_id = str(event.get("tile_id") or "")
        payload = payload_by_tile.get(tile_id, {})
        confidence = payload.get("confidence", event.get("confidence"))
        rows.append(
            {
                "ID": tile_id[:36],
                "MODE": event.get("detector_mode") or payload.get("detector_mode") or "",
                "TYPE": "REAL" if event.get("detector_is_real") else "SIM",
                "CONF": _confidence_label(confidence),
                "TRIAGE": decision or event.get("action", ""),
                "CROP": "PRESENT" if tile_id in crop_tiles else "NONE",
                "RAW / DL": f"{format_bytes(_raw_bytes(event))} / {format_bytes(event_downlinked_bytes(event))}",
            }
        )
    return rows


def _selected_evidence(evidence: list[Any]) -> Any | None:
    for item in evidence:
        if item.available:
            return item
    return evidence[0] if evidence else None


def _ensure_replay_index(events: list[dict[str, Any]]) -> None:
    if "replay_index" not in st.session_state:
        st.session_state.replay_index = len(events)


def _current_replay_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    replay_index = min(st.session_state.replay_index, len(events))
    return events[:replay_index]


def _image_size(path: Path) -> tuple[int | None, int | None]:
    try:
        from PIL import Image

        with Image.open(path) as image:
            return image.size
    except (ImportError, OSError):
        return None, None


def _crop_display_width(width: int | None) -> int:
    if width is None:
        return 96
    return max(64, min(width, 128))


def _ratio_label(value: float) -> str:
    if math.isinf(value):
        return "inf"
    return f"{value:.1f}:1"


def _format_int(value: int) -> str:
    return f"{value:,}"


def _confidence_label(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return ""
    return f"{numeric:.2f}" if numeric <= 1 else f"{numeric:.0f}"


def _raw_bytes(event: dict[str, Any]) -> int:
    try:
        return int(event.get("raw_bytes_processed", event.get("original_payload_bytes", 0)))
    except (TypeError, ValueError):
        return 0


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _percent(value: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return max(0.0, min((value / total) * 100, 100.0))


if __name__ == "__main__":
    main()

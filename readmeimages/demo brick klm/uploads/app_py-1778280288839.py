"""KilnWatch ground-station mission replay dashboard.

The dashboard is the judge-facing demo. It reads only downlinked queue
artifacts and telemetry, then proves what happened at the satellite boundary.
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from kilnwatch.ground_station import (
    TELEMETRY_LOG_DIR,
    TRANSMISSION_QUEUE_DIR,
    calculate_metrics,
    format_bytes,
    gate_counts,
    load_ground_station_records,
    mission_proof_counts,
    proof_status_summary,
    queue_artifact_summary,
    reasoner_statuses,
    tile_replay_rows,
)


ACCENT = "#e47a3c"
TEXT = "#f4ede1"
QUEUE_DIR = TRANSMISSION_QUEUE_DIR


st.set_page_config(
    page_title="KilnWatch - Mission Replay GS-01",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_data(show_spinner=False)
def _cached_records(queue_dir: str, telemetry_dir: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    return load_ground_station_records(Path(queue_dir), Path(telemetry_dir))


def main() -> None:
    _inject_css()
    payloads, telemetry, sample_data = _cached_records(str(QUEUE_DIR), str(TELEMETRY_LOG_DIR))
    if not payloads and not telemetry:
        _render_empty_state()
        return

    metrics = calculate_metrics(telemetry)
    counts = mission_proof_counts(payloads, telemetry, QUEUE_DIR)
    gates = gate_counts(payloads, telemetry)
    status = proof_status_summary(payloads, telemetry, sample_data)
    statuses = reasoner_statuses(payloads, telemetry)
    artifacts = queue_artifact_summary(QUEUE_DIR)
    rows = tile_replay_rows(payloads, telemetry, QUEUE_DIR)

    _render_header(status, statuses, sample_data)
    _render_status_panel(status, statuses, artifacts)
    _render_metrics(metrics, counts)
    _render_gate_panel(gates)
    selected = _render_tile_replay(rows)
    _render_alert_detail(selected)
    _render_queue_panel(artifacts)
    _render_run_panel()
    _render_honesty_panel(status, statuses, sample_data)
    _render_diagnostics(payloads, telemetry, status)


def _inject_css() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --kw-bg: #0c0d0c;
            --kw-panel: #151615;
            --kw-panel-2: #1b1b19;
            --kw-text: {TEXT};
            --kw-muted: #a79b8c;
            --kw-border: #51483d;
            --kw-border-soft: #342e28;
            --kw-accent: {ACCENT};
            --kw-good: #9ec27f;
            --kw-warn: #e2ae5c;
            --kw-bad: #d26455;
        }}
        .stApp {{
            background:
                radial-gradient(circle at 12% -10%, rgba(228,122,60,.16), transparent 28rem),
                linear-gradient(180deg, #10100f 0%, #080909 100%);
            color: var(--kw-text);
        }}
        .block-container {{
            max-width: 1320px;
            padding: 28px 34px 56px;
        }}
        [data-testid="stToolbar"], [data-testid="stDecoration"],
        [data-testid="stStatusWidget"], header[data-testid="stHeader"] {{
            display: none;
        }}
        .kw-shell {{
            border: 1px solid var(--kw-border-soft);
            background: rgba(20, 20, 18, .88);
            box-shadow: 0 20px 70px rgba(0,0,0,.35);
        }}
        .kw-header {{
            padding: 28px 30px 22px;
            border-bottom: 1px solid var(--kw-border-soft);
        }}
        .kw-kicker {{
            color: var(--kw-accent);
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 12px;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 8px;
        }}
        .kw-title {{
            color: var(--kw-text);
            font-family: Georgia, "Times New Roman", serif;
            font-size: clamp(42px, 7vw, 82px);
            line-height: .95;
            font-weight: 500;
            letter-spacing: 0;
            margin: 0;
        }}
        .kw-title .accent {{ color: var(--kw-accent); }}
        .kw-subtitle {{
            max-width: 720px;
            color: var(--kw-muted);
            font-size: 18px;
            line-height: 1.55;
            margin: 14px 0 20px;
        }}
        .kw-chip-row {{ display: flex; flex-wrap: wrap; gap: 8px; }}
        .kw-chip {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 7px 10px;
            border: 1px solid var(--kw-border);
            color: var(--kw-text);
            background: rgba(255,255,255,.025);
            border-radius: 999px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: .9px;
            text-transform: uppercase;
        }}
        .kw-chip::before {{
            content: "";
            width: 7px;
            height: 7px;
            border-radius: 99px;
            background: currentColor;
        }}
        .kw-chip.good {{ color: var(--kw-good); border-color: rgba(158,194,127,.55); }}
        .kw-chip.warn {{ color: var(--kw-warn); border-color: rgba(226,174,92,.6); }}
        .kw-chip.bad {{ color: var(--kw-bad); border-color: rgba(210,100,85,.6); }}
        .kw-chip.accent {{ color: var(--kw-accent); border-color: rgba(228,122,60,.65); }}
        .kw-section-title {{
            margin: 34px 0 12px;
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 16px;
        }}
        .kw-section-title h2 {{
            margin: 0;
            color: var(--kw-text);
            font-size: 13px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            letter-spacing: 2px;
            text-transform: uppercase;
        }}
        .kw-section-title span {{
            color: var(--kw-muted);
            font-size: 12px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        }}
        .kw-grid {{
            display: grid;
            gap: 12px;
        }}
        .kw-grid.metrics {{ grid-template-columns: repeat(5, minmax(0, 1fr)); }}
        .kw-grid.status {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
        .kw-grid.gates {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
        .kw-card {{
            border: 1px solid var(--kw-border-soft);
            background: linear-gradient(180deg, rgba(255,255,255,.035), rgba(255,255,255,.015));
            padding: 16px;
            min-height: 104px;
        }}
        .kw-card .label {{
            color: var(--kw-muted);
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 11px;
            letter-spacing: 1.4px;
            text-transform: uppercase;
        }}
        .kw-card .value {{
            color: var(--kw-text);
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 26px;
            line-height: 1.1;
            margin-top: 10px;
            overflow-wrap: anywhere;
        }}
        .kw-card .value.accent {{ color: var(--kw-accent); }}
        .kw-card .value.good {{ color: var(--kw-good); }}
        .kw-card .value.warn {{ color: var(--kw-warn); }}
        .kw-card .note {{
            color: var(--kw-muted);
            font-size: 12px;
            line-height: 1.45;
            margin-top: 8px;
        }}
        .kw-gate {{
            border-top: 2px solid var(--kw-accent);
            min-height: 138px;
        }}
        .kw-gate .count {{
            color: var(--kw-accent);
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 38px;
            margin-top: 10px;
        }}
        .kw-detail {{
            border: 1px solid var(--kw-border-soft);
            background: rgba(16,16,15,.9);
            padding: 18px;
        }}
        .kw-detail-title {{
            display: flex;
            flex-wrap: wrap;
            align-items: baseline;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 14px;
        }}
        .kw-detail-title strong {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            color: var(--kw-text);
            font-size: 16px;
        }}
        .kw-muted {{
            color: var(--kw-muted);
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 12px;
        }}
        .kw-path-list {{
            border: 1px solid var(--kw-border-soft);
            background: #0b0c0b;
            padding: 14px;
            color: var(--kw-text);
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 13px;
            line-height: 1.7;
            white-space: pre-wrap;
            overflow-wrap: anywhere;
        }}
        .kw-callout {{
            border-left: 3px solid var(--kw-accent);
            background: rgba(228,122,60,.08);
            padding: 13px 15px;
            color: var(--kw-text);
            line-height: 1.55;
        }}
        .kw-callout strong {{ color: var(--kw-accent); }}
        .kw-warning {{
            border-left-color: var(--kw-warn);
            background: rgba(226,174,92,.08);
        }}
        pre, code, [data-testid="stCodeBlock"] {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace !important;
        }}
        .stDataFrame {{
            border: 1px solid var(--kw-border-soft);
        }}
        @media (max-width: 980px) {{
            .kw-grid.metrics, .kw-grid.status, .kw-grid.gates {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
        }}
        @media (max-width: 620px) {{
            .block-container {{ padding: 18px 14px 40px; }}
            .kw-grid.metrics, .kw-grid.status, .kw-grid.gates {{
                grid-template-columns: 1fr;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_header(status: Any, statuses: set[str], sample_data: bool) -> None:
    chips = [
        _chip(status.detector_label, "good" if status.detector_label == "STRICT YOLO REAL" else "warn"),
        _chip(_liquid_chip_label(statuses), _liquid_chip_class(statuses)),
        _chip("QUEUE-ONLY GROUND STATION", "accent"),
        _chip("FOUR-TIER TRIAGE", "accent"),
        _chip("LOCAL SIMULATION", "warn"),
        _chip("NOT SENTINEL-VALIDATED", "warn"),
    ]
    if sample_data:
        chips.append(_chip("SAMPLE DATA", "warn"))
    st.markdown(
        f"""
        <section class="kw-shell kw-header">
          <div class="kw-kicker">Ground Station Console</div>
          <h1 class="kw-title"><span class="accent">Mission Replay</span> · GS-01</h1>
          <p class="kw-subtitle">Fourteen tiles entered the satellite node. Only evidence crossed the downlink.</p>
          <div class="kw-chip-row">{''.join(chips)}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_status_panel(status: Any, statuses: set[str], artifacts: Any) -> None:
    truth = status.truth_fields
    reasoning = truth.get("vlm_reasoning") if isinstance(truth.get("vlm_reasoning"), dict) else {}
    cards = [
        ("detector_mode", _fmt_truth(truth.get("detector_mode")), ""),
        ("detector_is_real", _fmt_truth(truth.get("detector_is_real")), ""),
        ("simulated", _fmt_truth(truth.get("simulated")), ""),
        ("fallback_used", _fmt_truth(truth.get("fallback_used", False)), ""),
        ("reasoner_mode", _fmt_truth(reasoning.get("reasoner_mode", "disabled")), ""),
        ("reasoner_is_real", _fmt_truth(reasoning.get("reasoner_is_real")), ""),
        ("reasoner_output_valid", _fmt_truth(reasoning.get("reasoner_output_valid")), ""),
        ("model_name", _fmt_truth(reasoning.get("model_name")), ""),
        ("reasoned_over", _fmt_truth(reasoning.get("reasoned_over", "none")), ""),
        ("crop_path_used", _fmt_truth(reasoning.get("crop_path_used")), ""),
        ("queue_path", artifacts.queue_dir, ""),
        ("payload_files", str(len(artifacts.payload_files)), "JSON alerts in queue"),
    ]
    st.markdown(
        """
        <div class="kw-section-title">
          <h2>Proof Status</h2>
          <span>driven by payload and telemetry metadata</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<section class="kw-grid status">'
        + "".join(_metric_card(label, value, note) for label, value, note in cards)
        + "</section>",
        unsafe_allow_html=True,
    )
    if "liquid-real-invalid" in statuses:
        st.markdown(
            """
            <div class="kw-callout kw-warning" style="margin-top:12px;">
              <strong>Liquid call succeeded; structured parse failed.</strong>
              The dashboard does not call this structured reasoning.
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_metrics(metrics: Any, counts: Any) -> None:
    saved_pct = f"{metrics.bandwidth_saved_percent:.1f}%"
    ratio = "inf" if metrics.compression_ratio == float("inf") else f"{metrics.compression_ratio:.2f}x"
    cards = [
        ("Tiles processed", f"{metrics.tiles_processed:,}", "telemetry events"),
        ("Alerts downlinked", f"{counts.detections:,}", "unique non-ignore tiles"),
        ("Ignored tiles", f"{counts.ignored_tiles:,}", "telemetry only"),
        ("Raw bytes processed", format_bytes(metrics.raw_bytes_processed), "onboard file sizes"),
        ("Transmitted bytes", format_bytes(metrics.downlinked_bytes), "queue artifacts only"),
        ("Bandwidth saved", saved_pct, format_bytes(metrics.bytes_saved), "accent"),
        ("Compression ratio", ratio, "raw / transmitted", "accent"),
        ("Crops generated", f"{counts.crops_generated:,}", "real files in queue"),
        ("Full tiles", f"{counts.full_tiles_generated:,}/{counts.full_downlinks:,}", "written / requested"),
    ]
    st.markdown(
        """
        <div class="kw-section-title">
          <h2>Mission Metrics</h2>
          <span>no payload plus telemetry double-counting</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<section class="kw-grid metrics">'
        + "".join(
            _metric_card(card[0], card[1], card[2], card[3] if len(card) > 3 else "")
            for card in cards
        )
        + "</section>",
        unsafe_allow_html=True,
    )


def _render_gate_panel(gates: dict[str, int]) -> None:
    gate_specs = [
        ("IGNORE", "telemetry only"),
        ("JSON_ALERT_ONLY", "JSON payload only"),
        ("CROP_OR_REVIEW", "JSON + crop PNG"),
        ("FULL_DOWNLINK", "JSON + crop + full tile"),
    ]
    st.markdown(
        """
        <div class="kw-section-title">
          <h2>Four-Tier Gate</h2>
          <span>YOLO and triage decide the downlink tier</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    html = ['<section class="kw-grid gates">']
    for name, note in gate_specs:
        html.append(
            f"""
            <div class="kw-card kw-gate">
              <div class="label">{escape(name)}</div>
              <div class="count">{gates.get(name, 0)}</div>
              <div class="note">{escape(note)}</div>
            </div>
            """
        )
    html.append("</section>")
    st.markdown("".join(html), unsafe_allow_html=True)


def _render_tile_replay(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    st.markdown(
        """
        <div class="kw-section-title">
          <h2>Tile Replay Table</h2>
          <span>select a row to inspect crop, JSON, and byte accounting</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not rows:
        st.info("No tile telemetry is available in the transmission queue.")
        return None

    df = pd.DataFrame(
        [
            {
                "tile_id": row["tile_id"],
                "triage_decision": row["triage_decision"],
                "transmission_action": row["transmission_action"],
                "confidence": round(float(row["confidence"]), 4),
                "compliance_risk": row["compliance_risk"],
                "detector_mode": row["detector_mode"],
                "reasoner status": row["reasoner_status"],
                "reasoner_output_valid": row["reasoner_output_valid"],
                "raw bytes": row["raw_bytes"],
                "transmitted bytes": row["transmitted_bytes"],
                "crop_written": row["crop_written"],
                "full_tile_written": row["full_tile_written"],
            }
            for row in rows
        ]
    )
    event = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )
    selected_indices = getattr(getattr(event, "selection", None), "rows", []) or []
    selected_index = selected_indices[0] if selected_indices else _first_alert_index(rows)
    return rows[selected_index]


def _render_alert_detail(row: dict[str, Any] | None) -> None:
    st.markdown(
        """
        <div class="kw-section-title">
          <h2>Alert Detail Panel</h2>
          <span>queue evidence for the selected tile</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if row is None:
        return

    st.markdown(
        f"""
        <section class="kw-detail">
          <div class="kw-detail-title">
            <strong>{escape(row['tile_id'])}</strong>
            <span class="kw-muted">{escape(row['triage_decision'])} / {escape(row['transmission_action'])}</span>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    left, right = st.columns([0.85, 1.15], gap="large")
    with left:
        _render_crop_evidence(row)
        st.markdown("**Detector evidence**")
        st.json(
            {
                "bbox": row.get("bbox"),
                "confidence": row.get("confidence"),
                "compliance_risk": row.get("compliance_risk"),
                "detector_mode": row.get("detector_mode"),
                "detector_is_real": row.get("detector_is_real"),
            }
        )
    with right:
        _render_reasoner_evidence(row)
        st.markdown("**Byte accounting**")
        st.json(
            {
                "raw_bytes": row.get("raw_bytes"),
                "transmitted_bytes": row.get("transmitted_bytes"),
                "saved_bytes": max(0, int(row.get("raw_bytes") or 0) - int(row.get("transmitted_bytes") or 0)),
                "crop_written": row.get("crop_written"),
                "full_tile_written": row.get("full_tile_written"),
            }
        )
        st.markdown("**Raw JSON payload**")
        payload = row.get("payload") or {}
        if payload:
            st.json({key: value for key, value in payload.items() if not key.startswith("_")})
        else:
            st.info("No JSON payload crossed the boundary for this tile.")


def _render_crop_evidence(row: dict[str, Any]) -> None:
    st.markdown("**Crop evidence**")
    crop_path = Path(row["crop_path"]) if row.get("crop_path") else None
    if crop_path and crop_path.is_file():
        width, height = _image_dimensions(crop_path)
        if width and height:
            st.caption(f"{crop_path} / {width}x{height}px / {format_bytes(crop_path.stat().st_size)}")
            st.image(str(crop_path), width=max(1, width))
        else:
            st.caption(f"{crop_path} / {format_bytes(crop_path.stat().st_size)}")
            st.image(str(crop_path))
    elif row.get("crop_path"):
        st.warning("Crop reference exists, but the crop file is missing from the queue.")
        st.code(str(row.get("crop_path")))
    else:
        st.info("No crop crossed the boundary for this tile.")


def _render_reasoner_evidence(row: dict[str, Any]) -> None:
    payload = row.get("payload") or {}
    telemetry = row.get("telemetry") or {}
    reasoning = payload.get("vlm_reasoning") or telemetry.get("vlm_reasoning") or {}
    st.markdown("**Liquid review status**")
    if not isinstance(reasoning, dict) or not reasoning:
        st.info("LFM disabled for this pass. Alert metadata is detector-only.")
        return
    if reasoning.get("reasoner_is_real") is True and reasoning.get("reasoner_output_valid") is False:
        st.warning("Liquid call succeeded; structured parse failed.")
    elif reasoning.get("reasoner_is_real") is True and reasoning.get("reasoner_output_valid") is True:
        st.success("Liquid emitted valid structured crop reasoning.")
    elif reasoning.get("reasoner_mode") == "liquid-mock":
        st.warning("Liquid mock output. This is labelled simulated and is not real model inference.")
    else:
        st.info(row["reasoner_status"])
    st.json(
        {
            "reasoner_mode": reasoning.get("reasoner_mode"),
            "model_name": reasoning.get("model_name"),
            "reasoner_is_real": reasoning.get("reasoner_is_real"),
            "reasoner_output_valid": reasoning.get("reasoner_output_valid"),
            "reasoned_over": reasoning.get("reasoned_over"),
            "crop_path_used": reasoning.get("crop_path_used"),
            "raw_output_excerpt": reasoning.get("raw_output_excerpt"),
            "visual_summary": reasoning.get("visual_summary"),
            "risk_reasoning": reasoning.get("risk_reasoning"),
        }
    )


def _render_queue_panel(artifacts: Any) -> None:
    st.markdown(
        """
        <div class="kw-section-title">
          <h2>Transmission Queue</h2>
          <span>the only boundary the ground station can see</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    tree = _queue_tree_text(artifacts)
    st.markdown(f'<div class="kw-path-list">{escape(tree)}</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="kw-callout" style="margin-top:12px;">
          <strong>The ground station reads only these artifacts.</strong>
          Raw tiles stay outside the boundary.
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_run_panel() -> None:
    st.markdown(
        """
        <div class="kw-section-title">
          <h2>Run Locally</h2>
          <span>commands used for the judge demo</span>
        </div>
        <div class="kw-callout">
          <strong>Detector readiness</strong>
        </div>
        ```bash
        python scripts/check_model_ready.py --json
        ```

        <div class="kw-callout">
          <strong>Full local Liquid review path</strong>
        </div>
        ```bash
        python -m satellite_edge_node.orbital_pass \\
          --raw-tiles data/final_demo_tiles \\
          --transmission-queue transmission_queue \\
          --detector yolo \\
          --reasoner liquid-local \\
          --require-crops \\
          --reset-queue

        streamlit run app.py
        ```

        <div class="kw-callout kw-warning">
          <strong>Reliable YOLO-only fallback</strong> - use this when local Liquid dependencies or model cache are unavailable.
        </div>
        ```bash
        python -m satellite_edge_node.orbital_pass \\
          --raw-tiles data/final_demo_tiles \\
          --transmission-queue transmission_queue \\
          --detector yolo \\
          --reasoner disabled \\
          --require-crops \\
          --reset-queue
        ```
        """,
        unsafe_allow_html=True,
    )


def _render_honesty_panel(status: Any, statuses: set[str], sample_data: bool) -> None:
    liquid_line = "Liquid annotates/reviews evidence and does not decide the gate."
    if "liquid-real-invalid" in statuses:
        liquid_line = "Liquid ran, but structured parsing failed; the dashboard says that directly."
    elif "disabled" in statuses:
        liquid_line = "Liquid is disabled for the current queue; the dashboard does not pretend otherwise."
    elif "liquid-mock" in statuses:
        liquid_line = "Liquid mock mode is labelled simulated and is not real model inference."
    st.markdown(
        f"""
        <div class="kw-section-title">
          <h2>Technical Honesty</h2>
          <span>what this demo is and is not</span>
        </div>
        <div class="kw-path-list">local satellite-edge simulation, not deployed satellite hardware
demo imagery is optical fixture imagery, not Sentinel/Haryana proof unless explicitly stated
YOLO drives the four-tier downlink gate
{escape(liquid_line)}
ground station reads only queue artifacts
bandwidth savings come from actual byte accounting
detector status: {escape(status.detector_label)}
sample data active: {sample_data}</div>
        """,
        unsafe_allow_html=True,
    )


def _render_diagnostics(payloads: list[dict[str, Any]], telemetry: list[dict[str, Any]], status: Any) -> None:
    with st.expander("Diagnostics - payloads, telemetry, and proof metadata", expanded=False):
        st.markdown(
            "Boundary check: this dashboard reads `transmission_queue/*.json`, "
            "`transmission_queue/telemetry.jsonl`, queue crop files, queue full-tile files, "
            "and optional telemetry logs. It does not inspect onboard raw image folders."
        )
        st.markdown("**Proof metadata**")
        st.json(status.truth_fields)
        st.markdown("**Payload files**")
        st.json([{k: v for k, v in payload.items() if not k.startswith("_")} for payload in payloads])
        st.markdown("**Telemetry events**")
        st.json([{k: v for k, v in event.items() if not k.startswith("_")} for event in telemetry])


def _render_empty_state() -> None:
    st.markdown(
        """
        <section class="kw-shell kw-header">
          <div class="kw-kicker">Ground Station Console</div>
          <h1 class="kw-title"><span class="accent">Mission Replay</span> · GS-01</h1>
          <p class="kw-subtitle">No transmission queue artifacts found. Run the orbital pass first.</p>
        </section>

        ```bash
        python -m satellite_edge_node.orbital_pass \\
          --raw-tiles data/final_demo_tiles \\
          --transmission-queue transmission_queue \\
          --detector yolo \\
          --reasoner liquid-local \\
          --require-crops \\
          --reset-queue

        streamlit run app.py
        ```
        """,
        unsafe_allow_html=True,
    )


def _metric_card(label: str, value: str, note: str, value_class: str = "") -> str:
    cls = f" {value_class}" if value_class else ""
    return (
        f'<div class="kw-card">'
        f'<div class="label">{escape(str(label))}</div>'
        f'<div class="value{cls}">{escape(str(value))}</div>'
        f'<div class="note">{escape(str(note))}</div>'
        "</div>"
    )


def _chip(label: str, cls: str = "") -> str:
    return f'<span class="kw-chip {escape(cls)}">{escape(label)}</span>'


def _liquid_chip_label(statuses: set[str]) -> str:
    if "liquid-real-invalid" in statuses:
        return "LIQUID CALLED · STRUCTURED PARSE FAILED"
    if "liquid-real-unverified" in statuses:
        return "LIQUID LOCAL REVIEW UNVERIFIED"
    if "liquid-real" in statuses:
        return "LIQUID LOCAL REVIEW"
    if "liquid-mock" in statuses:
        return "LIQUID MOCK REVIEW"
    return "LFM DISABLED"


def _liquid_chip_class(statuses: set[str]) -> str:
    if "liquid-real-invalid" in statuses or "liquid-real-unverified" in statuses or "liquid-mock" in statuses:
        return "warn"
    if "liquid-real" in statuses:
        return "good"
    return ""


def _fmt_truth(value: Any) -> str:
    if value is None:
        return "none"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list | tuple | set):
        return ", ".join(_fmt_truth(item) for item in value)
    return str(value)


def _first_alert_index(rows: list[dict[str, Any]]) -> int:
    for index, row in enumerate(rows):
        if row["triage_decision"] != "IGNORE":
            return index
    return 0


def _image_dimensions(path: Path) -> tuple[int | None, int | None]:
    try:
        from PIL import Image

        with Image.open(path) as image:
            return image.size
    except Exception:
        return None, None


def _queue_tree_text(artifacts: Any) -> str:
    lines = [f"{artifacts.queue_dir}/"]
    if artifacts.payload_files:
        for name in artifacts.payload_files:
            lines.append(f"  {name}")
    else:
        lines.append("  (no alert JSON payloads)")
    if artifacts.crop_files:
        lines.append("  crops/")
        for name in artifacts.crop_files:
            lines.append(f"    {name}")
    else:
        lines.append("  crops/ (empty)")
    if artifacts.full_tile_files:
        lines.append("  full_tiles/")
        for name in artifacts.full_tile_files:
            lines.append(f"    {name}")
    else:
        lines.append("  full_tiles/ (empty unless FULL_DOWNLINK)")
    if artifacts.telemetry_files:
        for name in artifacts.telemetry_files:
            lines.append(f"  {name}")
    else:
        lines.append("  telemetry.jsonl (missing)")
    return "\n".join(lines)


if __name__ == "__main__":
    main()

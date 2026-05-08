"""KilnWatch ground station — single-page mission dashboard.

The judge sees one screen: bandwidth saved up top, then the alerts the
satellite chose to downlink, each with its Liquid VLM reasoning and crop
evidence. Imagery provenance and detector honesty are visible, never hidden.
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any

import streamlit as st

from kilnwatch.ground_station import (
    calculate_metrics,
    cumulative_series,
    display_decision,
    format_bytes,
    load_ground_station_records,
    mission_proof_counts,
    proof_status_summary,
    reasoner_statuses,
    resolve_crop_evidence,
)


st.set_page_config(
    page_title="KilnWatch — Satellite-Edge Triage",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def main() -> None:
    _inject_css()
    payloads, telemetry, sample = load_ground_station_records()
    if not payloads and not telemetry:
        _render_empty_state()
        return

    metrics = calculate_metrics(telemetry)
    counts = mission_proof_counts(payloads, telemetry)
    status = proof_status_summary(payloads, telemetry, sample)
    evidence = resolve_crop_evidence(payloads, telemetry)
    statuses = reasoner_statuses(payloads, telemetry)

    _render_header(status, sample, statuses)
    _render_hero_strip(metrics, counts)
    _render_honesty_panel(status, sample, statuses)
    _render_imagery_provenance()
    _render_alerts(payloads, telemetry, evidence)
    _render_downlink_chart(telemetry, metrics)
    _render_diagnostics(payloads, telemetry, status)


# ────────────────────────────────────────────────────────────
# Styling
# ────────────────────────────────────────────────────────────


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --kw-bg: #071013;
            --kw-panel: #10191d;
            --kw-panel-2: #142127;
            --kw-panel-3: #1f2d33;
            --kw-text: #e6edf0;
            --kw-muted: #90a0a7;
            --kw-border: #2f3f46;
            --kw-outline: #51646c;
            --kw-good: #34a853;
            --kw-stream: #4b9cd3;
            --kw-warn: #d79b2b;
            --kw-error: #d94f45;
            --kw-liquid: #6b8cff;
        }
        .stApp { background: var(--kw-bg); color: var(--kw-text); font-family: ui-sans-serif, system-ui, sans-serif; }
        .block-container { max-width: 1200px; padding: 24px 32px 48px; margin: 0 auto; }
        [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], header[data-testid="stHeader"] { display: none; }

        .kw-title { display: flex; align-items: baseline; justify-content: space-between; padding: 0 0 16px; border-bottom: 1px solid var(--kw-border); margin-bottom: 28px; gap: 24px; flex-wrap: wrap; }
        .kw-title h1 { margin: 0; font-family: monospace; font-size: 28px; line-height: 1.1; font-weight: 600; color: var(--kw-text); letter-spacing: 0.5px; }
        .kw-title .kw-tag { color: var(--kw-muted); font-family: monospace; font-size: 13px; }
        .kw-title .kw-status { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }

        .kw-chip { display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--kw-outline); background: var(--kw-panel); color: var(--kw-text); padding: 6px 10px; font-size: 11px; font-weight: 700; white-space: nowrap; border-radius: 999px; letter-spacing: 0.5px; }
        .kw-chip.good { border-color: var(--kw-good); color: var(--kw-good); }
        .kw-chip.warn { border-color: var(--kw-warn); color: var(--kw-warn); }
        .kw-chip.muted { color: var(--kw-muted); }
        .kw-chip.liquid { border-color: var(--kw-liquid); color: var(--kw-liquid); }
        .kw-chip .pip { width: 7px; height: 7px; border-radius: 50%; background: currentColor; opacity: 0.85; }

        .kw-hero { display: grid; grid-template-columns: 1.6fr 1fr 1fr 1fr; gap: 12px; margin-bottom: 24px; }
        .kw-hero-cell { border: 1px solid var(--kw-border); background: var(--kw-panel); padding: 18px 20px; border-radius: 8px; display: flex; flex-direction: column; justify-content: space-between; min-height: 130px; }
        .kw-hero-cell .label { color: var(--kw-muted); font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; }
        .kw-hero-cell .value { font-family: monospace; color: var(--kw-good); }
        .kw-hero-cell.primary .value { font-size: 56px; line-height: 1.1; font-weight: 600; }
        .kw-hero-cell.primary .sub { color: var(--kw-muted); font-family: monospace; font-size: 12px; margin-top: 4px; }
        .kw-hero-cell .value.small { font-size: 28px; }

        .kw-section { margin: 32px 0 12px; display: flex; align-items: baseline; justify-content: space-between; }
        .kw-section h2 { margin: 0; font-size: 13px; font-weight: 700; color: var(--kw-text); letter-spacing: 1.5px; text-transform: uppercase; }
        .kw-section .meta { color: var(--kw-muted); font-family: monospace; font-size: 11px; }

        .kw-honesty { border: 1px solid var(--kw-border); background: var(--kw-panel-2); padding: 16px 18px; border-radius: 8px; font-family: monospace; font-size: 13px; color: var(--kw-text); display: flex; flex-direction: column; gap: 12px; }
        .kw-honesty .row { display: flex; flex-wrap: wrap; gap: 18px; }
        .kw-honesty .item { display: flex; flex-direction: column; gap: 4px; min-width: 160px; }
        .kw-honesty .item .k { color: var(--kw-muted); font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; }
        .kw-honesty .item .v { color: var(--kw-text); font-size: 14px; }
        .kw-honesty .item .v.good { color: var(--kw-good); }
        .kw-honesty .item .v.warn { color: var(--kw-warn); }
        .kw-honesty .item .v.liquid { color: var(--kw-liquid); }

        .kw-provenance { border: 1px dashed var(--kw-outline); background: var(--kw-panel); padding: 12px 16px; border-radius: 8px; font-family: monospace; font-size: 12px; color: var(--kw-muted); line-height: 1.55; }
        .kw-provenance strong { color: var(--kw-text); }

        .kw-alert { border: 1px solid var(--kw-border); background: var(--kw-panel); padding: 16px 18px; border-radius: 8px; margin-bottom: 12px; display: grid; grid-template-columns: 96px 1fr; gap: 16px; align-items: start; }
        .kw-alert.high { border-left: 3px solid var(--kw-error); }
        .kw-alert.medium { border-left: 3px solid var(--kw-warn); }
        .kw-alert.low { border-left: 3px solid var(--kw-stream); }
        .kw-alert .crop { width: 96px; aspect-ratio: 1; border: 1px solid var(--kw-outline); background: #091114; display: flex; align-items: center; justify-content: center; overflow: hidden; }
        .kw-alert .crop img { width: 100%; height: 100%; object-fit: cover; image-rendering: pixelated; }
        .kw-alert .crop.empty { color: var(--kw-muted); font-family: monospace; font-size: 10px; text-align: center; padding: 6px; }
        .kw-alert .body { display: flex; flex-direction: column; gap: 8px; }
        .kw-alert .head { display: flex; gap: 12px; align-items: baseline; flex-wrap: wrap; }
        .kw-alert .tile-id { font-family: monospace; font-size: 13px; color: var(--kw-text); font-weight: 700; }
        .kw-alert .meta { color: var(--kw-muted); font-family: monospace; font-size: 11px; }
        .kw-alert .meta strong { color: var(--kw-text); }
        .kw-alert .reason-block { background: var(--kw-panel-2); border: 1px solid var(--kw-border); padding: 10px 12px; border-radius: 6px; font-family: monospace; font-size: 12px; color: var(--kw-text); line-height: 1.55; }
        .kw-alert .reason-block .label { color: var(--kw-liquid); font-size: 10px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 4px; }
        .kw-alert .reason-block.no-liquid { border-style: dashed; color: var(--kw-muted); }
        .kw-alert .reason-block.no-liquid .label { color: var(--kw-muted); }
        .kw-alert .triage-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
        .kw-alert .triage-row .arrow { color: var(--kw-muted); font-family: monospace; }

        .kw-chart { border: 1px solid var(--kw-border); background: var(--kw-panel); padding: 18px; border-radius: 8px; font-family: monospace; font-size: 12px; color: var(--kw-text); }
        .kw-chart-row { display: grid; grid-template-columns: 60px 1fr 1fr 100px; gap: 12px; padding: 6px 0; border-top: 1px solid var(--kw-border); }
        .kw-chart-row:first-child { border-top: 0; color: var(--kw-muted); font-size: 11px; font-weight: 700; letter-spacing: 1px; }
        .kw-chart-row .bar { height: 8px; background: #091114; border: 1px solid var(--kw-border); position: relative; align-self: center; }
        .kw-chart-row .bar > div { height: 100%; }
        .kw-chart-row .bar.raw > div { background: var(--kw-muted); }
        .kw-chart-row .bar.dl > div { background: var(--kw-good); }

        .kw-empty { padding: 80px 24px; text-align: center; color: var(--kw-muted); font-family: monospace; }
        .kw-empty h2 { color: var(--kw-text); font-family: monospace; font-size: 18px; margin: 0 0 12px; }
        .kw-empty code { background: var(--kw-panel); padding: 6px 10px; border-radius: 4px; color: var(--kw-good); display: inline-block; margin: 4px 0; }

        @media (max-width: 900px) {
            .kw-hero { grid-template-columns: 1fr 1fr; }
            .kw-alert { grid-template-columns: 64px 1fr; }
            .kw-alert .crop { width: 64px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ────────────────────────────────────────────────────────────
# Sections
# ────────────────────────────────────────────────────────────


def _render_header(status: Any, sample: bool, statuses: set) -> None:
    detector_chip = _detector_chip(status, sample)
    liquid_chip = _liquid_chip(statuses)
    boundary_chip = '<span class="kw-chip muted"><span class="pip"></span>QUEUE-ONLY</span>'
    sample_chip = '<span class="kw-chip warn"><span class="pip"></span>SAMPLE DATA</span>' if sample else ""
    st.markdown(
        f"""
        <header class="kw-title">
          <div>
            <h1>KilnWatch</h1>
            <div class="kw-tag">Satellite-edge AI triage / Indo-Gangetic Plain brick-kiln monitoring / GS-01</div>
          </div>
          <div class="kw-status">
            {detector_chip}
            {liquid_chip}
            {boundary_chip}
            {sample_chip}
          </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def _render_hero_strip(metrics: Any, counts: Any) -> None:
    saved_pct = f"{metrics.bandwidth_saved_percent:.1f}%"
    raw = format_bytes(metrics.raw_bytes_processed)
    dl = format_bytes(metrics.downlinked_bytes)
    saved = format_bytes(metrics.bytes_saved)
    ratio = (
        "∞"
        if metrics.compression_ratio == float("inf")
        else f"{metrics.compression_ratio:.0f}×"
    )
    st.markdown(
        f"""
        <section class="kw-hero">
          <div class="kw-hero-cell primary">
            <div class="label">Bandwidth saved</div>
            <div class="value">{saved_pct}</div>
            <div class="sub">raw {raw} → downlinked {dl} ({saved} not transmitted)</div>
          </div>
          <div class="kw-hero-cell">
            <div class="label">Tiles processed</div>
            <div class="value small">{metrics.tiles_processed:,}</div>
            <div class="sub">onboard, before downlink</div>
          </div>
          <div class="kw-hero-cell">
            <div class="label">Alerts downlinked</div>
            <div class="value small">{counts.detections:,}</div>
            <div class="sub">{counts.crops_generated} with crop evidence</div>
          </div>
          <div class="kw-hero-cell">
            <div class="label">Compression ratio</div>
            <div class="value small">{ratio}</div>
            <div class="sub">raw / transmitted</div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_honesty_panel(status: Any, sample: bool, statuses: set) -> None:
    detector_class = "good" if status.detector_label == "STRICT YOLO REAL" else "warn"
    liquid_label, liquid_class = _liquid_label_and_class(statuses)
    fallback_used = bool(status.truth_fields.get("fallback_used"))
    fallback_class = "warn" if fallback_used else "good"
    sample_label = "ACTIVE" if sample else "DISABLED"
    sample_class = "warn" if sample else "muted"

    detector_version = status.truth_fields.get("detector_version", "—")
    if isinstance(detector_version, list):
        detector_version = ", ".join(str(x) for x in detector_version)

    reasoner_truth = status.truth_fields.get("vlm_reasoning", {}) or {}
    reasoner_model = reasoner_truth.get("model_name", "—") if isinstance(reasoner_truth, dict) else "—"

    st.markdown(
        f"""
        <section class="kw-honesty">
          <div class="row">
            <div class="item">
              <span class="k">Detector</span>
              <span class="v {detector_class}">{escape(status.detector_label)}</span>
              <span class="k" style="font-size:10px;">{escape(str(detector_version))}</span>
            </div>
            <div class="item">
              <span class="k">Onboard reasoner</span>
              <span class="v {liquid_class}">{escape(liquid_label)}</span>
              <span class="k" style="font-size:10px;">{escape(str(reasoner_model))}</span>
            </div>
            <div class="item">
              <span class="k">Fallback used</span>
              <span class="v {fallback_class}">{'YES' if fallback_used else 'NO'}</span>
              <span class="k" style="font-size:10px;">strict failure mode is loud</span>
            </div>
            <div class="item">
              <span class="k">Sample fixtures</span>
              <span class="v {sample_class}">{sample_label}</span>
              <span class="k" style="font-size:10px;">queue/telemetry visibility only</span>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_imagery_provenance() -> None:
    st.markdown(
        """
        <section class="kw-section">
          <h2>Imagery provenance</h2>
          <span class="meta">honest disclosure</span>
        </section>
        <section class="kw-provenance">
          <strong>Source:</strong> Open-source brick-kiln imagery (Roboflow optical tiles, Indo-Gangetic Plain morphology). These are real overhead images of brick kilns used to wire and prove the satellite-edge pipeline end-to-end.
          <br><br>
          <strong>Not:</strong> The included demo tiles are <em>not</em> Sentinel-2 or DPhi SimSat live imagery. They are not labelled as Haryana-provenance ground truth.
          <br><br>
          <strong>Production path:</strong> Replace the tile source with the DPhi SimSat <code>/data/image/sentinel</code> endpoint and fine-tune YOLO + Liquid LFM2-VL on Sentinel-domain kiln labels. The triage architecture, queue boundary, and ground-station accounting do not change.
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_alerts(
    payloads: list[dict[str, Any]],
    telemetry: list[dict[str, Any]],
    evidence: list[Any],
) -> None:
    alerts = _build_alerts(payloads, telemetry, evidence)
    st.markdown(
        f"""
        <section class="kw-section">
          <h2>Downlinked alerts</h2>
          <span class="meta">{len(alerts)} alert{'s' if len(alerts) != 1 else ''} • Liquid LFM2-VL onboard reasoning</span>
        </section>
        """,
        unsafe_allow_html=True,
    )
    if not alerts:
        st.markdown(
            """
            <div class="kw-provenance" style="text-align:center;">
              The satellite chose <strong>not to transmit</strong> any tile in this pass.
              Bandwidth was preserved; nothing met the kiln-detection threshold.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return
    for alert in alerts:
        _render_alert_card(alert)


def _build_alerts(
    payloads: list[dict[str, Any]],
    telemetry: list[dict[str, Any]],
    evidence: list[Any],
) -> list[dict[str, Any]]:
    crop_by_tile = {item.tile_id: item for item in evidence}
    payload_by_tile = {p.get("tile_id"): p for p in payloads}
    alerts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in (payloads, telemetry):
        for item in source:
            tile_id = str(item.get("tile_id") or "")
            if not tile_id or tile_id in seen:
                continue
            decision = display_decision(item)
            if decision == "IGNORE":
                continue
            seen.add(tile_id)
            payload = payload_by_tile.get(tile_id, {})
            tel_event = next((t for t in telemetry if t.get("tile_id") == tile_id), {})
            vlm = (
                payload.get("vlm_reasoning")
                or tel_event.get("vlm_reasoning")
                or {}
            )
            alerts.append(
                {
                    "tile_id": tile_id,
                    "decision": decision,
                    "confidence": payload.get("confidence", tel_event.get("confidence", 0.0)),
                    "compliance_risk": payload.get(
                        "compliance_risk", tel_event.get("compliance_risk", "low")
                    ),
                    "detector_mode": payload.get(
                        "detector_mode", tel_event.get("detector_mode", "")
                    ),
                    "raw_bytes": int(
                        tel_event.get("original_payload_bytes")
                        or payload.get("byte_accounting", {}).get("original_payload_bytes")
                        or 0
                    ),
                    "transmitted_bytes": int(
                        tel_event.get("transmitted_payload_bytes")
                        or payload.get("byte_accounting", {}).get("transmitted_payload_bytes")
                        or 0
                    ),
                    "vlm": vlm if isinstance(vlm, dict) else {},
                    "crop": crop_by_tile.get(tile_id),
                }
            )
    return alerts


def _render_alert_card(alert: dict[str, Any]) -> None:
    risk = str(alert.get("compliance_risk", "low")).lower()
    risk_class = risk if risk in {"low", "medium", "high"} else "low"
    conf = _confidence_pct(alert.get("confidence"))
    raw = format_bytes(alert.get("raw_bytes", 0))
    tx = format_bytes(alert.get("transmitted_bytes", 0))
    decision = alert.get("decision", "")
    crop_html = _crop_img_html(alert.get("crop"))
    vlm = alert.get("vlm") or {}
    reason_html = _reasoning_block_html(vlm)
    detector_mode = alert.get("detector_mode", "yolo").upper()

    # Safer to render vlm-derived strings via st.markdown HTML escape since they come from a model
    visual = escape(str(vlm.get("visual_summary") or "")).strip()
    risk_reasoning = escape(str(vlm.get("risk_reasoning") or "")).strip()
    review = vlm.get("human_review_needed")
    review_chip = ""
    if isinstance(review, bool):
        cls = "warn" if review else "good"
        review_chip = f'<span class="kw-chip {cls}" style="margin-left:8px;"><span class="pip"></span>{"REVIEW NEEDED" if review else "AUTO-OK"}</span>'

    st.markdown(
        f"""
        <article class="kw-alert {risk_class}">
          {crop_html}
          <div class="body">
            <div class="head">
              <span class="tile-id">{escape(alert['tile_id'][:48])}</span>
              <span class="meta">conf <strong>{conf}</strong></span>
              <span class="meta">risk <strong>{escape(risk)}</strong></span>
              <span class="meta">det <strong>{escape(detector_mode)}</strong></span>
              <span class="meta">raw <strong>{escape(raw)}</strong> → tx <strong>{escape(tx)}</strong></span>
              {review_chip}
            </div>
            {reason_html}
            <div class="triage-row">
              <span class="meta">triage</span>
              <span class="arrow">→</span>
              <span class="kw-chip {'good' if decision in {'CROP_OR_REVIEW','FULL_DOWNLINK'} else 'muted'}">{escape(decision)}</span>
            </div>
          </div>
        </article>
        """,
        unsafe_allow_html=True,
    )


def _crop_img_html(crop: Any) -> str:
    if crop is None or not getattr(crop, "available", False) or crop.path is None:
        return '<div class="crop empty">no crop<br>available</div>'
    try:
        import base64

        data = crop.path.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        suffix = crop.path.suffix.lstrip(".") or "png"
        return f'<div class="crop"><img src="data:image/{suffix};base64,{b64}" alt="crop {crop.tile_id}"/></div>'
    except OSError:
        return '<div class="crop empty">read error</div>'


def _reasoning_block_html(vlm: dict[str, Any]) -> str:
    if not vlm:
        return (
            '<div class="reason-block no-liquid">'
            '<div class="label">Onboard reasoner</div>'
            'Liquid LFM disabled for this pass — alert metadata is detector-only.'
            "</div>"
        )
    is_real = bool(vlm.get("reasoner_is_real"))
    label_suffix = "LIQUID LFM2-VL · LIVE" if is_real else "LIQUID · MOCK"
    visual = escape(str(vlm.get("visual_summary") or "")).strip() or "—"
    risk_text = escape(str(vlm.get("risk_reasoning") or "")).strip() or "—"
    confidence_note = escape(str(vlm.get("confidence_note") or "")).strip()
    confidence_html = (
        f'<div style="color: var(--kw-muted); margin-top: 6px; font-size: 11px;">{confidence_note}</div>'
        if confidence_note
        else ""
    )
    return (
        f'<div class="reason-block">'
        f'<div class="label">{label_suffix}</div>'
        f'<div><strong>Visual:</strong> {visual}</div>'
        f'<div style="margin-top:4px;"><strong>Risk:</strong> {risk_text}</div>'
        f"{confidence_html}"
        "</div>"
    )


def _render_downlink_chart(telemetry: list[dict[str, Any]], metrics: Any) -> None:
    series = cumulative_series(telemetry)
    if not series:
        return
    st.markdown(
        f"""
        <section class="kw-section">
          <h2>Cumulative downlink</h2>
          <span class="meta">raw onboard ({format_bytes(metrics.raw_bytes_processed)}) vs downlinked ({format_bytes(metrics.downlinked_bytes)})</span>
        </section>
        """,
        unsafe_allow_html=True,
    )
    raw_total = max(1, series[-1].get("Raw bytes processed in orbit", 1))
    rows_html = ['<div class="kw-chart-row"><span>Tile</span><span>Raw cumulative</span><span>Downlinked cumulative</span><span>Saved</span></div>']
    for point in series:
        raw = int(point.get("Raw bytes processed in orbit", 0))
        dl = int(point.get("Bytes downlinked", 0))
        saved = max(0, raw - dl)
        raw_pct = max(0.0, min(100.0, (raw / raw_total) * 100))
        dl_pct = max(0.0, min(100.0, (dl / raw_total) * 100))
        tile_id = str(point.get("tile_id", ""))[:14]
        rows_html.append(
            f'<div class="kw-chart-row">'
            f'<span class="meta">{escape(tile_id)}</span>'
            f'<span class="bar raw"><div style="width:{raw_pct:.1f}%"></div></span>'
            f'<span class="bar dl"><div style="width:{dl_pct:.1f}%"></div></span>'
            f'<span class="meta">{escape(format_bytes(saved))}</span>'
            "</div>"
        )
    st.markdown(
        f'<section class="kw-chart">{"".join(rows_html)}</section>',
        unsafe_allow_html=True,
    )


def _render_diagnostics(
    payloads: list[dict[str, Any]],
    telemetry: list[dict[str, Any]],
    status: Any,
) -> None:
    with st.expander("Diagnostics — raw payload + telemetry (for judge inspection)", expanded=False):
        st.markdown(
            "**Boundary check:** the dashboard reads only `transmission_queue/*.json`, "
            "`transmission_queue/telemetry.jsonl`, and crop files inside `transmission_queue/crops/`. "
            "Raw onboard tile folders are never opened here.",
            unsafe_allow_html=False,
        )
        st.markdown("---")
        st.markdown("**Truth metadata** (single source for honesty chips above):")
        st.json(status.truth_fields)
        st.markdown("---")
        if payloads:
            tile_ids = [p.get("tile_id", "?") for p in payloads]
            chosen = st.selectbox("Inspect a payload JSON", tile_ids, index=0)
            for p in payloads:
                if p.get("tile_id") == chosen:
                    st.json({k: v for k, v in p.items() if not k.startswith("_")})
                    break
        st.markdown("---")
        st.markdown(f"**Telemetry stream** ({len(telemetry)} events)")
        if telemetry:
            st.code(
                "\n".join(json.dumps(e, sort_keys=True)[:400] + ("…" if len(json.dumps(e)) > 400 else "") for e in telemetry[-12:]),
                language="json",
            )


def _render_empty_state() -> None:
    st.markdown(
        """
        <div class="kw-empty">
          <h2>No transmission queue artifacts found</h2>
          <p>The ground station only displays what the satellite chose to downlink. Run the orbital pass first:</p>
          <code>python -m satellite_edge_node.orbital_pass \\<br>
          &nbsp;&nbsp;--raw-tiles data/final_demo_tiles \\<br>
          &nbsp;&nbsp;--detector yolo --reasoner liquid-local \\<br>
          &nbsp;&nbsp;--require-crops --reset-queue</code>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────


def _detector_chip(status: Any, sample: bool) -> str:
    label = status.detector_label
    if sample:
        return '<span class="kw-chip warn"><span class="pip"></span>SAMPLE FIXTURES</span>'
    if label == "STRICT YOLO REAL":
        return '<span class="kw-chip good"><span class="pip"></span>STRICT YOLO</span>'
    if label == "FALLBACK USED":
        return '<span class="kw-chip warn"><span class="pip"></span>FALLBACK</span>'
    if label == "BASELINE SIMULATION":
        return '<span class="kw-chip warn"><span class="pip"></span>BASELINE SIM</span>'
    if label == "MIXED DETECTOR METADATA":
        return '<span class="kw-chip warn"><span class="pip"></span>MIXED MODES</span>'
    return f'<span class="kw-chip muted"><span class="pip"></span>{escape(label)}</span>'


def _liquid_chip(statuses: set) -> str:
    if "liquid-real" in statuses:
        return '<span class="kw-chip liquid"><span class="pip"></span>LFM2-VL · LIVE</span>'
    if "liquid-mock" in statuses:
        return '<span class="kw-chip warn"><span class="pip"></span>LIQUID · MOCK</span>'
    return '<span class="kw-chip muted"><span class="pip"></span>LFM DISABLED</span>'


def _liquid_label_and_class(statuses: set) -> tuple[str, str]:
    if "liquid-real" in statuses:
        return "LIQUID LFM2-VL · LIVE", "liquid"
    if "liquid-mock" in statuses:
        return "LIQUID · MOCK", "warn"
    return "DISABLED", "muted"


def _confidence_pct(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "—"
    if numeric <= 1:
        return f"{numeric * 100:.0f}%"
    return f"{numeric:.0f}%"


if __name__ == "__main__":
    main()

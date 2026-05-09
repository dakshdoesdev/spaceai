"""KilnWatch ground-station mission replay dashboard.

Judge-facing demo. Reads only downlinked queue artifacts and telemetry, then
proves what actually crossed the satellite boundary. Every number, every chip,
every Liquid status comes from real `transmission_queue/` files.
"""

from __future__ import annotations

import json
import re
import textwrap
from html import escape
from pathlib import Path
from typing import Any

import streamlit as st


_BLANK_LINE_RE = re.compile(r"^\s+$", re.MULTILINE)


def _html(markup: str) -> None:
    """Render raw HTML through Streamlit without tripping CommonMark's
    indented-code-block rules by stripping all leading whitespace per line."""
    dedented = textwrap.dedent(markup)
    # Join into a single string with no line-start whitespace
    cleaned = "".join(line.strip() for line in dedented.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)

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


QUEUE_DIR = TRANSMISSION_QUEUE_DIR


st.set_page_config(
    page_title="KilnWatch · Mission Replay GS-01",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_data(show_spinner=False)
def _cached_records(queue_dir: str, telemetry_dir: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    return load_ground_station_records(Path(queue_dir), Path(telemetry_dir))


def main() -> None:
    _inject_css()
    _render_topbar()

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

    _render_hero(status, statuses, sample_data)
    _render_proof_status(status, statuses, artifacts)
    _render_mission_metrics(metrics, counts)
    _render_gate_panel(gates)
    selected_row = _render_tile_replay(rows)
    _render_alert_detail(selected_row)
    _render_queue_panel(artifacts)
    _render_run_panel()
    _render_honesty_panel(status, statuses, sample_data)
    _render_diagnostics(payloads, telemetry, status)
    _render_footer()


def _inject_css() -> None:
    _html(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
        :root {
            --bg:#0c0d0c;
            --bg-2:#0a0b0a;
            --panel:#141513;
            --panel-2:#1b1c19;
            --panel-3:#0f100e;
            --text:#f4ede1;
            --muted:#a79b8c;
            --dim:#7a7164;
            --border:#34302a;
            --border-soft:#221f1b;
            --border-strong:#4a4238;
            --accent:#e47a3c;
            --accent-soft:rgba(228,122,60,.16);
            --accent-line:rgba(228,122,60,.45);
            --good:#9ec27f;
            --warn:#e2ae5c;
            --bad:#d26455;
            --mono:"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            --serif:"Instrument Serif", "Iowan Old Style", Georgia, "Times New Roman", serif;
        }
        html, body, .stApp {
            font-family: var(--mono);
            color: var(--text);
        }
        .stApp {
            background:
              radial-gradient(1200px 600px at 8% -8%, rgba(228,122,60,.10), transparent 60%),
              radial-gradient(900px 500px at 100% 0%, rgba(228,122,60,.05), transparent 60%),
              linear-gradient(180deg,#10100f 0%, #070807 100%) !important;
        }
        ::selection { background: var(--accent); color:#0c0d0c; }
        [data-testid="stToolbar"], [data-testid="stDecoration"],
        [data-testid="stStatusWidget"], header[data-testid="stHeader"],
        footer { display: none !important; }
        .block-container { max-width: 1400px; padding: 18px 32px 64px; }

        /* Topbar */
        .kw-topbar {
            display:flex; align-items:center; justify-content:space-between; gap:16px;
            padding:10px 14px; border:1px solid var(--border-soft);
            background:rgba(20,20,18,.6);
            font-family:var(--mono); font-size:11px; letter-spacing:1.6px; text-transform:uppercase;
            color:var(--muted);
        }
        .kw-topbar .left { display:flex; align-items:center; gap:14px; }
        .kw-topbar .dot { width:7px; height:7px; border-radius:99px; background:var(--accent); box-shadow:0 0 12px var(--accent); animation: kwpulse 1.4s ease-in-out infinite; }
        .kw-topbar .right { display:flex; align-items:center; gap:18px; }
        .kw-topbar .right span { display:inline-flex; align-items:center; gap:8px; }
        .kw-topbar .right b { color: var(--text); font-weight:500; }
        @keyframes kwpulse { 0%,100% { opacity:.55 } 50% { opacity:1 } }

        /* Hero */
        .kw-hero {
            margin-top:10px;
            border:1px solid var(--border-soft);
            background:linear-gradient(180deg, rgba(20,20,18,.92), rgba(14,15,13,.92));
            padding:34px 36px 30px;
            position:relative; overflow:hidden;
        }
        .kw-hero::before {
            content:""; position:absolute; inset:0; pointer-events:none;
            background:
              linear-gradient(transparent 95%, rgba(228,122,60,.07) 96%) 0 0/100% 28px,
              linear-gradient(90deg, transparent 95%, rgba(228,122,60,.04) 96%) 0 0/28px 100%;
            mask-image:linear-gradient(180deg, rgba(0,0,0,.7), transparent 70%);
        }
        .kw-kicker {
            color:var(--accent); font-family:var(--mono); font-size:11px;
            letter-spacing:2.4px; text-transform:uppercase; margin-bottom:14px;
            display:inline-flex; align-items:center; gap:10px;
        }
        .kw-kicker::before { content:""; width:18px; height:1px; background:var(--accent); }
        .kw-title {
            margin:0; font-family:var(--serif); font-weight:400;
            font-size:clamp(48px,7vw,96px); line-height:.95; letter-spacing:-.01em;
            color:var(--text);
        }
        .kw-title .accent { color:var(--accent); font-style:italic; }
        .kw-subtitle {
            max-width:760px; color:var(--muted); font-family:var(--mono);
            font-size:14px; line-height:1.6; margin:18px 0 0;
        }
        .kw-chip-row { display:flex; flex-wrap:wrap; gap:8px; margin-top:24px; }
        .kw-chip {
            display:inline-flex; align-items:center; gap:8px;
            padding:7px 11px; border:1px solid var(--border);
            background:rgba(255,255,255,.02); color:var(--text);
            font-family:var(--mono); font-size:10.5px; font-weight:600;
            letter-spacing:1.2px; text-transform:uppercase; border-radius:999px;
        }
        .kw-chip::before { content:""; width:6px; height:6px; border-radius:99px; background:currentColor; }
        .kw-chip.good { color:var(--good); border-color:rgba(158,194,127,.45); }
        .kw-chip.warn { color:var(--warn); border-color:rgba(226,174,92,.5); }
        .kw-chip.bad  { color:var(--bad);  border-color:rgba(210,100,85,.5); }
        .kw-chip.accent { color:var(--accent); border-color:var(--accent-line); }

        /* Section heading */
        .kw-section { margin-top:34px; }
        .kw-sec-head {
            display:flex; align-items:baseline; justify-content:space-between; gap:18px;
            border-bottom:1px solid var(--border-soft); padding-bottom:10px; margin-bottom:16px;
        }
        .kw-sec-head h2 {
            margin:0; font-family:var(--mono); font-size:11px;
            letter-spacing:2.4px; text-transform:uppercase; color:var(--text); font-weight:600;
            display:flex; align-items:center; gap:10px;
        }
        .kw-sec-head h2::before {
            content:""; width:6px; height:6px; background:var(--accent); display:inline-block;
        }
        .kw-sec-head .meta { color:var(--dim); font-family:var(--mono); font-size:10.5px; letter-spacing:1.4px; text-transform:uppercase; }

        /* Card grids */
        .kw-grid { display:grid; gap:1px; background:var(--border-soft); border:1px solid var(--border-soft); }
        .kw-grid.cols-5 { grid-template-columns:repeat(5,minmax(0,1fr)); }
        .kw-grid.cols-4 { grid-template-columns:repeat(4,minmax(0,1fr)); }
        .kw-grid.cols-3 { grid-template-columns:repeat(3,minmax(0,1fr)); }
        .kw-grid.cols-2 { grid-template-columns:repeat(2,minmax(0,1fr)); }
        .kw-card {
            background:var(--panel); padding:18px 18px 20px; min-height:108px;
            display:flex; flex-direction:column; justify-content:space-between; gap:12px;
        }
        .kw-card .label { font-family:var(--mono); font-size:10px; letter-spacing:1.6px; text-transform:uppercase; color:var(--muted); }
        .kw-card .value { font-family:var(--mono); font-size:24px; font-weight:600; color:var(--text); line-height:1.05; overflow-wrap:anywhere; }
        .kw-card .value.accent { color:var(--accent); }
        .kw-card .value.good   { color:var(--good); }
        .kw-card .value.warn   { color:var(--warn); }
        .kw-card .value.bad    { color:var(--bad); }
        .kw-card .value.serif  { font-family:var(--serif); font-weight:400; font-size:42px; letter-spacing:-.01em; }
        .kw-card .value.small  { font-size:14px; }
        .kw-card .note { font-family:var(--mono); font-size:10.5px; color:var(--dim); letter-spacing:.6px; line-height:1.5; }

        /* Hero metrics */
        .kw-metrics-hero {
            display:grid; grid-template-columns:1.4fr 1fr 1fr 1fr; gap:1px;
            background:var(--border-soft); border:1px solid var(--border-soft);
        }
        .kw-metrics-hero .kw-card { min-height:148px; }
        .kw-metrics-hero .kw-card.feature {
            background:linear-gradient(135deg, rgba(228,122,60,.12), rgba(228,122,60,.02) 60%), var(--panel);
            border-left:2px solid var(--accent);
        }
        .kw-metrics-hero .kw-card.feature .value { color:var(--accent); font-family:var(--serif); font-size:64px; font-weight:400; letter-spacing:-.02em; }
        .kw-metrics-hero .kw-card.feature .sub { font-family:var(--mono); font-size:11px; color:var(--muted); letter-spacing:1.4px; text-transform:uppercase; margin-top:6px; }

        /* Gate cards */
        .kw-gate-card { position:relative; border-top:2px solid transparent; }
        .kw-gate-card.ignore { border-top-color:#5a5147; }
        .kw-gate-card.json   { border-top-color:#9ec27f; }
        .kw-gate-card.crop   { border-top-color:var(--accent); }
        .kw-gate-card.full   { border-top-color:#d26455; }
        .kw-gate-card .count { font-family:var(--serif); font-size:48px; line-height:1; font-weight:400; color:var(--text); }
        .kw-gate-card.ignore .count { color:#8a7f70; }
        .kw-gate-card.json   .count { color:var(--good); }
        .kw-gate-card.crop   .count { color:var(--accent); }
        .kw-gate-card.full   .count { color:var(--bad); }
        .kw-gate-card .gate-name { font-family:var(--mono); font-size:11px; letter-spacing:1.6px; text-transform:uppercase; color:var(--text); font-weight:600; }
        .kw-gate-card .gate-flow { font-family:var(--mono); font-size:10px; color:var(--dim); letter-spacing:.6px; line-height:1.5; display:flex; align-items:center; gap:6px; flex-wrap:wrap; }
        .kw-gate-card .arrow { color:var(--accent); }

        /* Tile replay */
        .kw-tile-table { padding:0; display:flex; flex-direction:column; min-height:0; border:1px solid var(--border-soft); background:var(--panel); }
        .kw-tile-table-head {
            display:grid; grid-template-columns:90px 100px 1fr 80px 90px;
            padding:12px 16px; border-bottom:1px solid var(--border-soft);
            font-family:var(--mono); font-size:10px; letter-spacing:1.4px;
            text-transform:uppercase; color:var(--dim);
        }
        .kw-tile-row {
            display:grid; grid-template-columns:90px 100px 1fr 80px 90px;
            padding:14px 16px; border-bottom:1px solid var(--border-soft);
            align-items:center;
            font-family:var(--mono); font-size:12px; color:var(--text);
        }
        .kw-tile-row.selected {
            background:linear-gradient(90deg, rgba(228,122,60,.16), rgba(228,122,60,.02));
            border-left:2px solid var(--accent); padding-left:14px;
        }
        .kw-tile-row .tid { font-weight:600; color:var(--text); }
        .kw-tile-row .gate-tag {
            font-size:10px; letter-spacing:1.2px; text-transform:uppercase; font-weight:600;
            padding:3px 7px; border:1px solid var(--border); display:inline-block; width:fit-content;
        }
        .kw-tile-row .gate-tag.ignore { color:var(--dim); border-color:var(--border); }
        .kw-tile-row .gate-tag.json { color:var(--good); border-color:rgba(158,194,127,.4); }
        .kw-tile-row .gate-tag.crop { color:var(--accent); border-color:var(--accent-line); }
        .kw-tile-row .gate-tag.full { color:var(--bad); border-color:rgba(210,100,85,.45); }
        .kw-tile-row .conf { color:var(--text); font-variant-numeric:tabular-nums; }
        .kw-tile-row .conf.low { color:var(--dim); }
        .kw-tile-row .bytes { color:var(--muted); text-align:right; font-variant-numeric:tabular-nums; }
        .kw-conf-bar { height:3px; background:rgba(255,255,255,.06); margin-top:5px; position:relative; }
        .kw-conf-bar > i { position:absolute; left:0; top:0; bottom:0; background:var(--accent); display:block; }

        /* Alert detail */
        .kw-detail-head {
            display:flex; align-items:flex-start; justify-content:space-between; gap:14px; flex-wrap:wrap;
            margin-bottom:18px;
        }
        .kw-detail-head .id {
            font-family:var(--serif); font-size:34px; line-height:1; color:var(--text); font-weight:400; letter-spacing:-.01em;
        }
        .kw-detail-head .id .accent { color:var(--accent); font-style:italic; }
        .kw-detail-head .gate-tag {
            font-family:var(--mono); font-size:10.5px; letter-spacing:1.4px; text-transform:uppercase;
            padding:6px 10px; border:1px solid var(--accent-line); color:var(--accent);
        }

        .kw-liquid-card {
            border:1px solid var(--border-soft); background:var(--panel-3); padding:16px;
            margin-top:16px;
        }
        .kw-liquid-card .head { display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; }
        .kw-liquid-card h4 {
            margin:0; font-family:var(--mono); font-size:10.5px; letter-spacing:1.6px;
            text-transform:uppercase; color:var(--text); font-weight:600;
        }
        .kw-liquid-card .verdict {
            font-family:var(--mono); font-size:9.5px; letter-spacing:1.4px; text-transform:uppercase;
            padding:4px 8px; border:1px solid rgba(158,194,127,.4); color:var(--good);
        }
        .kw-liquid-card .verdict.warn { color:var(--warn); border-color:rgba(226,174,92,.4); }
        .kw-liquid-card .verdict.bad  { color:var(--bad);  border-color:rgba(210,100,85,.4); }
        .kw-liquid-card .summary {
            font-family:var(--mono); font-size:12px; line-height:1.6; color:var(--text);
            border-left:2px solid var(--accent); padding:6px 0 6px 12px; margin:8px 0 12px;
        }
        .kw-liquid-card .reasoning {
            font-family:var(--mono); font-size:11.5px; line-height:1.6; color:var(--muted); margin:0 0 12px;
        }
        .kw-liquid-card pre.raw {
            margin:0; padding:10px 12px; background:#000; border:1px solid var(--border-soft);
            font-family:var(--mono); font-size:11px; color:var(--accent);
            white-space:pre-wrap; overflow-wrap:anywhere; line-height:1.55;
        }

        .kw-kv {
            border:1px solid var(--border-soft); background:var(--panel-3); padding:14px;
        }
        .kw-kv h4 {
            margin:0 0 10px; font-family:var(--mono); font-size:10px; letter-spacing:1.6px;
            text-transform:uppercase; color:var(--muted); font-weight:600;
        }
        .kw-kv .row {
            display:flex; justify-content:space-between; gap:10px; padding:5px 0;
            font-family:var(--mono); font-size:11.5px; border-bottom:1px dashed var(--border-soft);
        }
        .kw-kv .row:last-child { border-bottom:0; }
        .kw-kv .row .k { color:var(--dim); }
        .kw-kv .row .v { color:var(--text); text-align:right; overflow-wrap:anywhere; }
        .kw-kv .row .v.accent { color:var(--accent); }
        .kw-kv .row .v.good   { color:var(--good); }
        .kw-kv .row .v.warn   { color:var(--warn); }
        .kw-kv .row .v.bad    { color:var(--bad); }

        .kw-json-viewer {
            border:1px solid var(--border-soft); background:#08090a; padding:0;
            font-family:var(--mono); font-size:11.5px; line-height:1.6;
            max-height:380px; overflow:auto; margin-top:10px;
        }
        .kw-json-viewer pre { margin:0; padding:14px 16px; color:var(--text); white-space:pre; }
        .kw-json-viewer .k  { color:var(--accent); }
        .kw-json-viewer .s  { color:#a8c98a; }
        .kw-json-viewer .n  { color:#e2c47a; }
        .kw-json-viewer .b  { color:#c98ac9; }
        .kw-json-viewer .nl { color:var(--dim); }

        /* Tree */
        .kw-tree {
            font-family:var(--mono); font-size:12px; line-height:1.85; color:var(--text);
            background:#08090a; border:1px solid var(--border-soft); padding:14px 16px;
            white-space:pre; overflow:auto;
        }
        .kw-tree .dir { color:var(--accent); }
        .kw-tree .file { color:var(--text); }
        .kw-tree .dim { color:var(--dim); }
        .kw-tree .new { color:var(--good); }

        .kw-callout {
            border-left:2px solid var(--accent); background:var(--accent-soft);
            padding:14px 16px; font-family:var(--mono); font-size:12px; line-height:1.65; color:var(--text);
            margin-top:14px;
        }
        .kw-callout strong { color:var(--accent); font-weight:600; }
        .kw-callout.warn { border-left-color:var(--warn); background:rgba(226,174,92,.08); }
        .kw-callout.warn strong { color:var(--warn); }

        /* Run locally */
        .kw-cmd-card {
            border:1px solid var(--border-soft); background:var(--panel-3); padding:0;
            display:flex; flex-direction:column;
        }
        .kw-cmd-card .cmd-head {
            padding:12px 16px; border-bottom:1px solid var(--border-soft);
            display:flex; align-items:center; justify-content:space-between; gap:10px;
        }
        .kw-cmd-card .cmd-head h4 {
            margin:0; font-family:var(--mono); font-size:10.5px; letter-spacing:1.6px;
            text-transform:uppercase; color:var(--text); font-weight:600;
        }
        .kw-cmd-card .badge {
            font-family:var(--mono); font-size:9.5px; letter-spacing:1.2px;
            text-transform:uppercase; padding:3px 7px; border:1px solid var(--accent-line);
            color:var(--accent);
        }
        .kw-cmd-card .badge.warn { color:var(--warn); border-color:rgba(226,174,92,.4); }
        .kw-cmd-card pre {
            margin:0; padding:14px 16px; background:#08090a;
            font-family:var(--mono); font-size:11.5px; line-height:1.7; color:var(--text);
            white-space:pre; overflow:auto;
        }
        .kw-cmd-card pre .c { color:var(--dim); }
        .kw-cmd-card pre .a { color:var(--accent); }

        /* Honesty */
        .kw-honesty {
            border:1px solid var(--border-soft); background:var(--panel); padding:22px 24px;
            display:grid; grid-template-columns:1fr 1fr; gap:24px;
        }
        .kw-honesty h3 {
            margin:0 0 12px; font-family:var(--mono); font-size:10.5px; letter-spacing:1.6px;
            text-transform:uppercase; color:var(--text); font-weight:600;
            display:flex; align-items:center; gap:10px;
        }
        .kw-honesty h3 .dot { width:6px; height:6px; background:var(--accent); }
        .kw-honesty ul { margin:0; padding:0; list-style:none; }
        .kw-honesty li {
            font-family:var(--mono); font-size:12px; line-height:1.65; color:var(--muted);
            padding:6px 0 6px 18px; position:relative;
        }
        .kw-honesty li::before {
            content:""; position:absolute; left:0; top:14px; width:8px; height:1px; background:var(--accent);
        }
        .kw-honesty li b { color:var(--text); font-weight:500; }

        .kw-foot {
            margin-top:40px; border-top:1px solid var(--border-soft); padding-top:18px;
            display:flex; justify-content:space-between; gap:20px; flex-wrap:wrap;
            font-family:var(--mono); font-size:10.5px; letter-spacing:1.4px; text-transform:uppercase; color:var(--dim);
        }
        .kw-foot .accent { color:var(--accent); }

        /* Streamlit overrides */
        [data-testid="stImage"] img {
            border:1px solid var(--border-soft);
            background:#000;
        }
        .stCodeBlock, pre, code {
            font-family: var(--mono) !important;
        }
        .stDataFrame { border:1px solid var(--border-soft); }
        .stButton > button {
            border:1px solid var(--accent);
            background:linear-gradient(180deg, var(--accent) 0%, #c9682f 100%);
            color:#10100f; font-family:var(--mono); font-weight:700;
            font-size:13px; letter-spacing:1.6px; text-transform:uppercase;
            border-radius:0; box-shadow:0 8px 30px rgba(228,122,60,.28), inset 0 1px 0 rgba(255,255,255,.18);
        }
        .stButton > button:hover { transform:translateY(-1px); }

        @media (max-width:1100px) {
            .kw-grid.cols-5 { grid-template-columns:repeat(3,1fr); }
            .kw-grid.cols-4 { grid-template-columns:repeat(2,1fr); }
            .kw-metrics-hero { grid-template-columns:1fr 1fr; }
            .kw-honesty { grid-template-columns:1fr; }
        }
        @media (max-width:640px) {
            .block-container { padding:18px 14px 40px; }
            .kw-grid.cols-5, .kw-grid.cols-4, .kw-grid.cols-3 { grid-template-columns:1fr; }
        }
        </style>

        <script>
        (function() {
          function pad(n){return String(n).padStart(2,"0")}
          function tick() {
            var clk = window.parent.document.getElementById('kw-clock') || document.getElementById('kw-clock');
            if (!clk) return;
            var d = new Date();
            clk.textContent = pad(d.getUTCHours())+":"+pad(d.getUTCMinutes())+":"+pad(d.getUTCSeconds());
          }
          setInterval(tick, 1000); tick();
        })();
        </script>
        """
    )


def _render_topbar() -> None:
    pass_id = "0×" + format(abs(hash("KILNWATCH-GS-01")) & 0xFFFF, "04X")
    _html(
        f"""
        <div class="kw-topbar">
          <div class="left">
            <span class="dot"></span>
            <span>KILNWATCH · GS-01</span>
            <span style="color:var(--dim)">|</span>
            <span>Liquid AI × DPhi · AI in Space</span>
          </div>
          <div class="right">
            <a href="https://dakshdoesdev.github.io/spaceai/" target="_blank" style="text-decoration:none;">
              <span class="kw-chip accent" style="cursor:pointer;">📖 View Project Story</span>
            </a>
            <span style="color:var(--dim)">|</span>
            <span>Pass <b>{pass_id}</b></span>
            <span>UTC <b id="kw-clock">--:--:--</b></span>
            <span>Build <b>v1.0.0</b></span>
          </div>
        </div>
        """
    )


def _render_hero(status: Any, statuses: set[str], sample_data: bool) -> None:
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
    _html(
        f"""
        <header class="kw-hero">
          <div class="kw-kicker">Ground Station Console — Mission Replay</div>
          <h1 class="kw-title">Detect <span class="accent">before</span> downlink.<br/>Reason <span class="accent">before</span> review.</h1>
          <p class="kw-subtitle">
            Fourteen overhead tiles entered the satellite-edge node. Strict YOLO localized kiln candidates,
            Liquid LFM2-VL reviewed each crop with structured reasoning, and the four-tier triage gate
            decided what crossed the downlink. The ground station only sees what was actually transmitted.
          </p>
          <div class="kw-chip-row">{''.join(chips)}</div>
        </header>
        """
    )

    cols = st.columns([1, 1, 4])
    with cols[0]:
        if st.button("↻ RELOAD QUEUE", key="reload_queue"):
            st.cache_data.clear()
            st.rerun()
    with cols[1]:
        _html(
            f"<div style='padding:14px 0; color:var(--muted); font-size:10.5px; letter-spacing:1.4px; text-transform:uppercase'>Queue loaded · {len(statuses)} reasoner state(s)</div>"
        )


def _render_proof_status(status: Any, statuses: set[str], artifacts: Any) -> None:
    truth = status.truth_fields
    reasoning = truth.get("vlm_reasoning") if isinstance(truth.get("vlm_reasoning"), dict) else {}
    detector_real = bool(truth.get("detector_is_real"))
    reasoner_real = bool(reasoning.get("reasoner_is_real"))
    reasoner_valid = reasoning.get("reasoner_output_valid")

    cards = [
        ("detector_mode", _fmt_truth(truth.get("detector_mode")), "strict YOLO, no fallback", ""),
        ("detector_is_real", _fmt_truth(truth.get("detector_is_real")), "real model weights", "good" if detector_real else "warn"),
        ("simulated", _fmt_truth(truth.get("simulated", False)), "no synthetic detections", ""),
        ("fallback_used", _fmt_truth(truth.get("fallback_used", False)), "strict path active", ""),
        ("reasoner_mode", _fmt_truth(reasoning.get("reasoner_mode", "disabled")), "Liquid LFM2-VL local", "accent"),
        ("reasoner_is_real", _fmt_truth(reasoning.get("reasoner_is_real")), "real model invocation", "good" if reasoner_real else "warn"),
        ("reasoner_output_valid", _fmt_truth(reasoner_valid), "structured JSON parsed", "good" if reasoner_valid is True else ("warn" if reasoner_valid is False else "")),
        ("reasoned_over", _fmt_truth(reasoning.get("reasoned_over", "none")), "crop only, not raw tile", "accent"),
        ("model_name", _fmt_truth(reasoning.get("model_name", "—")), "local checkpoint", "small"),
        ("queue_path", artifacts.queue_dir + "/", "ground-station boundary", "small"),
        ("payload_files", str(len(artifacts.payload_files)), "JSON alerts in queue", ""),
        ("telemetry", "present" if artifacts.telemetry_files else "missing", "telemetry.jsonl status", "good" if artifacts.telemetry_files else "warn"),
    ]
    _section_head("Proof Status", "driven by payload + telemetry metadata")
    _html(
        '<div class="kw-grid cols-4">'
        + "".join(_metric_card(label, value, note, cls) for label, value, note, cls in cards)
        + "</div>"
    )
    if "liquid-real-invalid" in statuses:
        _html(
            """
            <div class="kw-callout warn" style="margin-top:14px;">
              <strong>Liquid call succeeded; structured parse failed for one or more tiles.</strong>
              The dashboard does not call this structured reasoning. Raw model output is shown as evidence below.
            </div>
            """
        )


def _render_mission_metrics(metrics: Any, counts: Any) -> None:
    saved_pct = f"{metrics.bandwidth_saved_percent:.1f}%"
    ratio = "inf" if metrics.compression_ratio == float("inf") else f"{metrics.compression_ratio:.2f}×"
    _section_head("Mission Metrics", "no payload + telemetry double-counting")

    _html(
        f"""
        <div class="kw-metrics-hero">
          <div class="kw-card feature">
            <div class="label">Bandwidth saved</div>
            <div>
              <div class="value">{escape(saved_pct)}</div>
              <div class="sub">{escape(format_bytes(metrics.bytes_saved))} saved</div>
            </div>
            <div class="note">raw bytes processed minus transmitted bytes</div>
          </div>
          <div class="kw-card">
            <div class="label">Compression ratio</div>
            <div class="value accent">{escape(ratio)}</div>
            <div class="note">raw / transmitted</div>
          </div>
          <div class="kw-card">
            <div class="label">Tiles processed</div>
            <div class="value serif">{metrics.tiles_processed:,}</div>
            <div class="note">telemetry events</div>
          </div>
          <div class="kw-card">
            <div class="label">Alerts downlinked</div>
            <div class="value serif">{counts.detections:,}</div>
            <div class="note">unique non-IGNORE tiles</div>
          </div>
        </div>
        """
    )

    secondary = [
        ("Ignored tiles", f"{counts.ignored_tiles:,}", "telemetry only", ""),
        ("Raw bytes processed", format_bytes(metrics.raw_bytes_processed), "onboard file sizes", ""),
        ("Transmitted bytes", format_bytes(metrics.downlinked_bytes), "queue artifacts only", ""),
        ("Crops generated", f"{counts.crops_generated:,}", "real PNG files", ""),
        ("Full tiles written", f"{counts.full_tiles_generated:,}/{counts.full_downlinks:,}", "written / requested", ""),
    ]
    _html(
        '<div class="kw-grid cols-5" style="margin-top:14px">'
        + "".join(_metric_card(label, value, note, cls) for label, value, note, cls in secondary)
        + "</div>"
    )


def _render_gate_panel(gates: dict[str, int]) -> None:
    _section_head("Four-Tier Triage Gate", "YOLO + triage logic decide the downlink tier")
    specs = [
        ("ignore", "IGNORE", "tile", "dropped onboard", "telemetry only — no payload, no crop"),
        ("json", "JSON_ALERT_ONLY", "bbox", "JSON", "alert metadata, no pixel evidence"),
        ("crop", "CROP_OR_REVIEW", "JSON", "crop PNG", "evidence crop crosses the boundary"),
        ("full", "FULL_DOWNLINK", "JSON + crop", "full tile", "compliance review escalation"),
    ]
    html = ['<div class="kw-grid cols-4">']
    for cls, name, lhs, rhs, note in specs:
        count = gates.get(name, 0)
        if "+" in lhs:
            flow_html = f'{escape(lhs)} <span class="arrow">+</span> {escape(rhs)}'
        else:
            flow_html = f'{escape(lhs)} <span class="arrow">→</span> {escape(rhs)}'
        html.append(
            f"""
            <div class="kw-card kw-gate-card {cls}">
              <div>
                <div class="gate-name">{escape(name)}</div>
                <div class="gate-flow">{flow_html}</div>
              </div>
              <div class="count">{count}</div>
              <div class="note">{escape(note)}</div>
            </div>
            """
        )
    html.append("</div>")
    _html("".join(html))


def _render_tile_replay(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    _section_head("Tile Replay · Alert Detail", "select a tile to inspect crop, JSON, byte accounting")
    if not rows:
        st.info("No tile telemetry is available in the transmission queue.")
        return None

    sorted_rows = sorted(
        rows,
        key=lambda r: (0 if r["triage_decision"] != "IGNORE" else 1, -float(r.get("confidence") or 0)),
    )

    default_id = next((r["tile_id"] for r in sorted_rows if r["triage_decision"] != "IGNORE"), sorted_rows[0]["tile_id"])
    if "kw_selected_tile" not in st.session_state or st.session_state["kw_selected_tile"] not in {r["tile_id"] for r in sorted_rows}:
        st.session_state["kw_selected_tile"] = default_id

    options = [r["tile_id"] for r in sorted_rows]
    labels = {
        r["tile_id"]: f"{r['tile_id']}  ·  {r['triage_decision']}  ·  conf={float(r.get('confidence') or 0):.4f}"
        for r in sorted_rows
    }
    st.selectbox(
        "Inspect tile",
        options,
        index=options.index(st.session_state["kw_selected_tile"]),
        format_func=lambda tid: labels.get(tid, tid),
        key="kw_selected_tile",
        label_visibility="collapsed",
    )
    selected_id = st.session_state["kw_selected_tile"]

    table_html = [
        '<div class="kw-tile-table">',
        '<div class="kw-tile-table-head">',
        '<span>Tile</span><span>Gate</span><span>Confidence</span><span>Crop</span><span style="text-align:right">Tx bytes</span>',
        '</div>',
    ]
    for r in sorted_rows:
        decision = r["triage_decision"]
        cls = (
            "ignore" if decision == "IGNORE"
            else "json" if decision == "JSON_ALERT_ONLY"
            else "full" if decision == "FULL_DOWNLINK"
            else "crop"
        )
        short = (
            "IGNORE" if decision == "IGNORE"
            else "JSON" if decision == "JSON_ALERT_ONLY"
            else "FULL" if decision == "FULL_DOWNLINK"
            else "CROP"
        )
        is_alert = decision != "IGNORE"
        conf = float(r.get("confidence") or 0)
        conf_pct = max(0, min(100, conf * 100))
        crop_label = "yes" if r.get("crop_written") else "—"
        bytes_label = format_bytes(r.get("transmitted_bytes") or 0)
        selected_cls = " selected" if r["tile_id"] == selected_id else ""
        table_html.append(
            f"""
            <div class="kw-tile-row{selected_cls}">
              <span class="tid">{escape(r['tile_id'])}</span>
              <span><span class="gate-tag {cls}">{short}</span></span>
              <span>
                <span class="conf {'low' if not is_alert else ''}">{conf:.4f}</span>
                <span class="kw-conf-bar"><i style="width:{conf_pct:.1f}%"></i></span>
              </span>
              <span class="conf {'low' if not r.get('crop_written') else ''}">{crop_label}</span>
              <span class="bytes">{bytes_label}</span>
            </div>
            """
        )
    table_html.append("</div>")
    _html("".join(table_html))

    return next((r for r in sorted_rows if r["tile_id"] == selected_id), sorted_rows[0])


def _render_alert_detail(row: dict[str, Any] | None) -> None:
    if row is None:
        return

    decision = row["triage_decision"]
    action = row.get("transmission_action", "")
    _html(
        f"""
        <div class="kw-detail-head" style="margin-top:24px">
          <div class="id">Tile <span class="accent">{escape(row['tile_id'])}</span></div>
          <div class="gate-tag">{escape(decision)} · {escape(action)}</div>
        </div>
        """
    )

    left, right = st.columns([1.05, 1], gap="large")
    with left:
        _render_crop_evidence(row)
        _render_liquid_card(row)
    with right:
        _render_kv_panels(row)
        _render_json_payload(row)


def _render_crop_evidence(row: dict[str, Any]) -> None:
    _html(
        '<h4 style="margin:0 0 10px;font-family:var(--mono);font-size:10px;letter-spacing:1.6px;text-transform:uppercase;color:var(--muted);font-weight:600">Crop evidence</h4>'
    )
    crop_path = Path(row["crop_path"]) if row.get("crop_path") else None
    if crop_path and crop_path.is_file():
        width, height = _image_dimensions(crop_path)
        size_label = format_bytes(crop_path.stat().st_size)
        meta = f"{crop_path}  ·  {width}×{height}px  ·  {size_label}" if width else f"{crop_path}  ·  {size_label}"
        st.caption(meta)
        st.image(str(crop_path), use_container_width=True)
    elif row.get("crop_path"):
        _html(
            '<div class="kw-callout warn"><strong>Crop reference present, file missing.</strong> The queue does not contain the bytes that were promised.</div>'
        )
        st.code(str(row.get("crop_path")))
    else:
        _html(
            '<div class="kw-callout warn"><strong>No crop transmitted.</strong> Tile was IGNORED onboard. No pixel evidence crossed the boundary.</div>'
        )


def _render_liquid_card(row: dict[str, Any]) -> None:
    payload = row.get("payload") or {}
    telemetry = row.get("telemetry") or {}
    reasoning = payload.get("vlm_reasoning") or telemetry.get("vlm_reasoning") or {}

    if not isinstance(reasoning, dict) or not reasoning:
        _html(
            """
            <div class="kw-liquid-card">
              <div class="head">
                <h4>Liquid LFM2-VL · Crop Review</h4>
                <span class="verdict warn">NOT INVOKED</span>
              </div>
              <div class="reasoning">LFM not invoked for this tile (gate did not require evidence review). Liquid only reasons over crops that crossed the boundary.</div>
            </div>
            """
        )
        return

    is_real = bool(reasoning.get("reasoner_is_real"))
    valid = reasoning.get("reasoner_output_valid")
    if is_real and valid is True:
        verdict = "VALID · STRUCTURED"
        verdict_cls = ""
    elif is_real and valid is False:
        verdict = "PARSE FAILED"
        verdict_cls = "bad"
    elif is_real:
        verdict = "UNVERIFIED"
        verdict_cls = "warn"
    elif str(reasoning.get("reasoner_mode") or "").lower() == "liquid-mock":
        verdict = "MOCK"
        verdict_cls = "warn"
    else:
        verdict = "DISABLED"
        verdict_cls = "warn"

    summary = reasoning.get("visual_summary") or "—"
    risk = reasoning.get("risk_reasoning") or "—"
    raw_excerpt = reasoning.get("raw_output_excerpt") or "—"
    model_name = reasoning.get("model_name") or "—"

    _html(
        f"""
        <div class="kw-liquid-card">
          <div class="head">
            <h4>Liquid LFM2-VL · Crop Review · {escape(str(model_name))}</h4>
            <span class="verdict {verdict_cls}">{escape(verdict)}</span>
          </div>
          <div class="summary">{escape(str(summary))}</div>
          <div class="reasoning">{escape(str(risk))}</div>
          <pre class="raw">{escape(str(raw_excerpt))}</pre>
        </div>
        """
    )


def _render_kv_panels(row: dict[str, Any]) -> None:
    bbox = row.get("bbox")
    bbox_label = f"[{', '.join(str(x) for x in bbox)}]" if isinstance(bbox, list) else "—"
    conf = float(row.get("confidence") or 0)
    saved = max(0, int(row.get("raw_bytes") or 0) - int(row.get("transmitted_bytes") or 0))
    detector_real = row.get("detector_is_real")
    crop_written = bool(row.get("crop_written"))
    full_written = bool(row.get("full_tile_written"))

    _html(
        f"""
        <div class="kw-kv">
          <h4>Detector evidence (YOLO)</h4>
          <div class="row"><span class="k">bbox</span><span class="v">{escape(bbox_label)}</span></div>
          <div class="row"><span class="k">confidence</span><span class="v accent">{conf:.4f}</span></div>
          <div class="row"><span class="k">compliance_risk</span><span class="v">{escape(str(row.get('compliance_risk') or '—'))}</span></div>
          <div class="row"><span class="k">detector_mode</span><span class="v">{escape(str(row.get('detector_mode') or '—'))}</span></div>
          <div class="row"><span class="k">detector_is_real</span><span class="v {'good' if detector_real else 'warn'}">{_fmt_truth(detector_real)}</span></div>
        </div>
        <div class="kw-kv" style="margin-top:14px">
          <h4>Byte accounting</h4>
          <div class="row"><span class="k">raw_bytes</span><span class="v">{format_bytes(int(row.get('raw_bytes') or 0))}</span></div>
          <div class="row"><span class="k">transmitted_bytes</span><span class="v">{format_bytes(int(row.get('transmitted_bytes') or 0))}</span></div>
          <div class="row"><span class="k">saved_bytes</span><span class="v accent">{format_bytes(saved)}</span></div>
          <div class="row"><span class="k">crop_written</span><span class="v {'good' if crop_written else 'warn'}">{_fmt_truth(crop_written)}</span></div>
          <div class="row"><span class="k">full_tile_written</span><span class="v {'good' if full_written else 'warn'}">{_fmt_truth(full_written)}</span></div>
        </div>
        """
    )


def _render_json_payload(row: dict[str, Any]) -> None:
    payload = row.get("payload") or {}
    if not payload:
        _html(
            """
            <h4 style="margin:14px 0 10px;font-family:var(--mono);font-size:10px;letter-spacing:1.6px;text-transform:uppercase;color:var(--muted);font-weight:600">Raw JSON payload (transmitted)</h4>
            <div class="kw-json-viewer"><pre>// IGNORE tile — no payload crossed the boundary.\n// Telemetry-only event recorded in transmission_queue/telemetry.jsonl</pre></div>
            """
        )
        return
    clean = {k: v for k, v in payload.items() if not k.startswith("_")}
    highlighted = _json_highlight(clean)
    _html(
        f"""
        <h4 style="margin:14px 0 10px;font-family:var(--mono);font-size:10px;letter-spacing:1.6px;text-transform:uppercase;color:var(--muted);font-weight:600">Raw JSON payload (transmitted)</h4>
        <div class="kw-json-viewer"><pre>{highlighted}</pre></div>
        """
    )


def _render_queue_panel(artifacts: Any) -> None:
    _section_head("Transmission Queue", "the only boundary the ground station can see")
    tree_html = _queue_tree_html(artifacts)
    _html(
        f"""
        <div class="kw-grid cols-2" style="background:transparent;border:0">
          <div style="background:var(--panel);padding:18px;border:1px solid var(--border-soft)">
            <h4 style="margin:0 0 10px;font-family:var(--mono);font-size:10px;letter-spacing:1.6px;text-transform:uppercase;color:var(--muted);font-weight:600">{escape(artifacts.queue_dir)}/</h4>
            <div class="kw-tree">{tree_html}</div>
          </div>
          <div style="background:var(--panel);padding:18px;border:1px solid var(--border-soft)">
            <div class="kw-callout">
              <strong>The ground station reads only these artifacts.</strong>
              Raw tiles never cross the satellite boundary. Bandwidth savings come from real byte
              accounting against onboard tile sizes.
            </div>
            <div class="kw-callout warn">
              <strong>Liquid annotates the evidence.</strong> YOLO + the four-tier triage decide the
              gate. LFM2-VL reasons over the crop after detection — never the raw tile.
            </div>
            <div class="kw-callout">
              <strong>Pipeline:</strong> raw tile → YOLO bbox → real crop → Liquid structured JSON →
              four-tier gate → downlink → queue → this dashboard.
            </div>
          </div>
        </div>
        """
    )


def _render_run_panel() -> None:
    _section_head("Run Locally", "commands used to regenerate this queue")
    _html(
        """
        <div class="kw-grid cols-2" style="background:transparent;border:0;gap:14px">
          <div class="kw-cmd-card">
            <div class="cmd-head"><h4>1 · Detector readiness</h4></div>
<pre><span class="c"># Verify strict YOLO weights and Liquid LFM2-VL cache</span>
python scripts/check_model_ready.py <span class="a">--json</span></pre>
          </div>
          <div class="kw-cmd-card">
            <div class="cmd-head"><h4>2 · Strict YOLO + Liquid local</h4><span class="badge">recommended</span></div>
<pre><span class="c"># Full local pipeline: YOLO detects, Liquid reviews crops</span>
python -m satellite_edge_node.orbital_pass \\
  <span class="a">--raw-tiles</span> data/final_demo_tiles \\
  <span class="a">--transmission-queue</span> transmission_queue \\
  <span class="a">--detector</span> yolo \\
  <span class="a">--reasoner</span> liquid-local \\
  <span class="a">--require-crops</span> \\
  <span class="a">--reset-queue</span>

streamlit run app.py</pre>
          </div>
          <div class="kw-cmd-card">
            <div class="cmd-head"><h4>3 · YOLO-only fallback</h4><span class="badge warn">no Liquid</span></div>
<pre><span class="c"># Use when local Liquid dependencies / model cache are unavailable</span>
python -m satellite_edge_node.orbital_pass \\
  <span class="a">--raw-tiles</span> data/final_demo_tiles \\
  <span class="a">--transmission-queue</span> transmission_queue \\
  <span class="a">--detector</span> yolo \\
  <span class="a">--reasoner</span> disabled \\
  <span class="a">--require-crops</span> \\
  <span class="a">--reset-queue</span></pre>
          </div>
          <div class="kw-cmd-card">
            <div class="cmd-head"><h4>4 · Verify Liquid proof chain</h4></div>
<pre><span class="c"># Confirm structured Liquid JSON crossed the boundary</span>
jq -s '{
  payloads: length,
  liquid_real:        map(select(.vlm_reasoning.reasoner_is_real == true)) | length,
  liquid_valid:       map(select(.vlm_reasoning.reasoner_output_valid == true)) | length,
  reasoned_over_crop: map(select(.vlm_reasoning.reasoned_over == "crop")) | length
}' transmission_queue/*.json</pre>
          </div>
        </div>
        """
    )


def _render_honesty_panel(status: Any, statuses: set[str], sample_data: bool) -> None:
    if "liquid-real-invalid" in statuses:
        liquid_line = "<b>Liquid ran on the GPU</b> for every alert; structured JSON parsed for some tiles, failed for others. Both states are surfaced honestly."
    elif "liquid-real" in statuses and "liquid-real-invalid" not in statuses:
        liquid_line = "<b>Liquid ran on the GPU</b> and emitted valid structured JSON over real crop pixels. Reasoning is shown verbatim."
    elif "disabled" in statuses:
        liquid_line = "<b>Liquid is disabled</b> for the current queue. The dashboard does not pretend otherwise."
    elif "liquid-mock" in statuses:
        liquid_line = "<b>Liquid mock mode</b> is labelled simulated; this is not real model inference."
    else:
        liquid_line = "<b>Liquid call status</b> is unverified for this queue."

    _section_head("Technical Honesty", "what this demo is and is not")
    _html(
        f"""
        <div class="kw-honesty">
          <div>
            <h3><span class="dot"></span>What is real</h3>
            <ul>
              <li><b>Strict YOLO</b> runs on CPU/GPU with real weights — detector_is_real=true, no fallback path active.</li>
              <li>{liquid_line}</li>
              <li>Crops are <b>real PNG files</b> generated from detector bounding boxes against the source tiles.</li>
              <li>Bandwidth savings come from <b>actual byte accounting</b> against onboard tile sizes — not estimates.</li>
              <li>The ground station reads only <b>queue artifacts</b>: <code>*.json</code>, <code>crops/*.png</code>, <code>full_tiles/*.png</code>, <code>telemetry.jsonl</code>.</li>
            </ul>
          </div>
          <div>
            <h3><span class="dot"></span>What is simulated</h3>
            <ul>
              <li>This is a <b>local satellite-edge simulation</b>, not deployed satellite hardware.</li>
              <li>Demo imagery is <b>optical fixture imagery</b>, not Sentinel/Haryana ground-truth proof.</li>
              <li>YOLO drives the <b>four-tier downlink gate</b>; Liquid annotates evidence and never decides the gate.</li>
              <li>Detector status: <b>{escape(status.detector_label)}</b> · sample data active: <b>{str(sample_data).lower()}</b>.</li>
              <li>Latency is wall-clock on local hardware, not orbit-realistic.</li>
            </ul>
          </div>
        </div>
        """
    )


def _render_diagnostics(payloads: list[dict[str, Any]], telemetry: list[dict[str, Any]], status: Any) -> None:
    with st.expander("Diagnostics — payloads, telemetry, and proof metadata", expanded=False):
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


def _render_footer() -> None:
    _html(
        """
        <div class="kw-foot">
          <span>KILNWATCH · GROUND STATION GS-01 · MISSION REPLAY</span>
          <span>DETECT BEFORE DOWNLINK <span class="accent">·</span> REASON BEFORE REVIEW <span class="accent">·</span> SEND EVIDENCE INSTEAD OF EMPTY FIELDS</span>
        </div>
        """
    )


def _render_empty_state() -> None:
    _html(
        """
        <header class="kw-hero">
          <div class="kw-kicker">Ground Station Console — Mission Replay</div>
          <h1 class="kw-title">No <span class="accent">queue</span> loaded.</h1>
          <p class="kw-subtitle">
            Run the orbital pass below to populate <code>transmission_queue/</code>, then refresh this page.
          </p>
        </header>

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
        """
    )


# ---- helpers ----


def _section_head(title: str, meta: str) -> None:
    _html(
        f"""
        <div class="kw-section">
          <div class="kw-sec-head">
            <h2>{escape(title)}</h2>
            <span class="meta">{escape(meta)}</span>
          </div>
        </div>
        """
    )


def _metric_card(label: str, value: str, note: str, value_class: str = "") -> str:
    cls = f" {escape(value_class)}" if value_class else ""
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
    if "liquid-real" in statuses and "liquid-real-invalid" in statuses:
        return "LIQUID LFM2-VL · MIXED · STRUCTURED + PARSE FAILED"
    if "liquid-real-invalid" in statuses:
        return "LIQUID LFM2-VL · CALLED · STRUCTURED PARSE FAILED"
    if "liquid-real-unverified" in statuses:
        return "LIQUID LFM2-VL · UNVERIFIED"
    if "liquid-real" in statuses:
        return "LIQUID LFM2-VL · STRUCTURED · REASONED OVER CROP"
    if "liquid-mock" in statuses:
        return "LIQUID MOCK REVIEW"
    return "LFM DISABLED"


def _liquid_chip_class(statuses: set[str]) -> str:
    if "liquid-real" in statuses and "liquid-real-invalid" not in statuses:
        return "good"
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


def _image_dimensions(path: Path) -> tuple[int | None, int | None]:
    try:
        from PIL import Image

        with Image.open(path) as image:
            return image.size
    except Exception:
        return None, None


def _queue_tree_html(artifacts: Any) -> str:
    lines: list[str] = []
    lines.append(f'<span class="dir">{escape(artifacts.queue_dir)}/</span>')
    if artifacts.payload_files:
        for name in artifacts.payload_files:
            lines.append(f'  <span class="file">{escape(name)}</span>  <span class="dim"># JSON alert</span>')
    else:
        lines.append('  <span class="dim">(no alert JSON payloads)</span>')
    lines.append('  <span class="dir">crops/</span>')
    if artifacts.crop_files:
        for name in artifacts.crop_files:
            lines.append(f'    <span class="file">{escape(name)}</span>  <span class="dim"># bbox crop · evidence</span>')
    else:
        lines.append('    <span class="dim">(empty)</span>')
    lines.append('  <span class="dir">full_tiles/</span>')
    if artifacts.full_tile_files:
        for name in artifacts.full_tile_files:
            lines.append(f'    <span class="new">{escape(name)}</span>  <span class="dim"># FULL_DOWNLINK escalation</span>')
    else:
        lines.append('    <span class="dim">(empty unless FULL_DOWNLINK)</span>')
    if artifacts.telemetry_files:
        for name in artifacts.telemetry_files:
            lines.append(f'  <span class="file">{escape(name)}</span>  <span class="dim"># every tile · including IGNORE</span>')
    else:
        lines.append('  <span class="dim">telemetry.jsonl (missing)</span>')
    return "\n".join(lines)


def _json_highlight(obj: Any) -> str:
    raw = json.dumps(obj, indent=2, default=str)
    safe = escape(raw)
    import re

    def repl(match: "re.Match[str]") -> str:
        token = match.group(0)
        if token.startswith('&quot;'):
            if token.endswith(':'):
                return f'<span class="k">{token}</span>'
            return f'<span class="s">{token}</span>'
        if token in ("true", "false"):
            return f'<span class="b">{token}</span>'
        if token == "null":
            return f'<span class="nl">{token}</span>'
        return f'<span class="n">{token}</span>'

    pattern = re.compile(
        r'(&quot;(?:\\&quot;|[^&])*?&quot;\s*:?)|(\btrue\b|\bfalse\b|\bnull\b)|(-?\d+(?:\.\d+)?(?:[eE][+\-]?\d+)?)'
    )
    return pattern.sub(repl, safe)


if __name__ == "__main__":
    main()

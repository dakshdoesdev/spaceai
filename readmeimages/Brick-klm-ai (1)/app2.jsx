// KilnWatch v2 — components 5-9 (built, bandwidth, proof, pass, liquid)
const { useState: uS, useEffect: uE, useRef: uR } = React;

// ─── WHAT I BUILT (3 layers) ───────────────────────────
function Built() {
  return (
    <section className="section ink-2" id="built" data-bg="ink" data-screen-label="05 Built">
      <div className="section-inner">
        <div className="eyebrow">04 / What I built</div>
        <h2 className="h-display">
          KilnWatch is an <span className="it">AI pipeline</span> with<br/>
          <span className="accent">three deliberate layers.</span>
        </h2>
        <p className="lede">
          Real-data grounding. Visual detection. Liquid edge reasoning. Each layer is testable on its own; together they make the four-tier triage decision: <em>IGNORE / JSON_ALERT / CROP_OR_REVIEW / FULL_DOWNLINK.</em>
        </p>

        <div className="layers">
          <div className="layer">
            <div className="num">Layer 01</div>
            <h3>Real-data <em>grounding</em></h3>
            <p className="desc">APAD and SentinelKilnDB kiln coordinate datasets — actual surveys of real kilns across India, Pakistan, Bangladesh — adapted to the pipeline format. The system isn't pretending kilns are random; locations come from real research.</p>
            <div className="tag"><span className="pip"></span>11,277 kilns · APAD2024 · NeurIPS 2025</div>
          </div>
          <div className="layer">
            <div className="num">Layer 02</div>
            <h3>YOLO <em>detection</em></h3>
            <p className="desc">Loads <code>models/brick_kiln_yolo.pt</code> and emits real bounding boxes. If weights are missing, the run <em>fails loudly</em>. No silent fallback. Architectural invariant — there's a unit test that fails if the dashboard ever reads a raw tile path.</p>
            <div className="tag"><span className="pip"></span>Ultralytics YOLOv8 · strict mode</div>
          </div>
          <div className="layer liquid">
            <div className="num">Layer 03</div>
            <h3>Liquid <em>review</em></h3>
            <p className="desc">After YOLO finds a candidate, the pipeline crops around the bbox and hands the crop to <strong>LiquidAI/LFM2.5-VL-450M</strong>, running locally through <code>transformers.AutoModelForImageTextToText</code>. Liquid annotates evidence after the gate; the payload records whether structured JSON parsing succeeded.</p>
            <div className="tag"><span className="pip"></span>LFM2.5-VL-450M · CPU · ~20s per crop</div>
          </div>
        </div>

        <div className="demo-result">
          <div className="cmd">
<span className="prompt">$</span> python -m satellite_edge_node.orbital_pass \{"\n"}
{"  "}<span className="flag">--raw-tiles</span> <span className="arg">data/final_demo_tiles</span> \{"\n"}
{"  "}<span className="flag">--detector</span> <span className="arg">yolo</span> \{"\n"}
{"  "}<span className="flag">--reasoner</span> <span className="arg">liquid-local</span> \{"\n"}
{"  "}<span className="flag">--require-crops --reset-queue</span>
          </div>
          <div className="out">
            <h2>{fmtBytes(TOTALS.rawTotal)} <span className="arrow">→</span> {fmtBytes(TOTALS.txTotal)}</h2>
            <p>14 raw tiles in. 5 real alerts out. {Math.round(TOTALS.ratio)}× compression. Liquid runs over crop evidence when enabled, and every payload carries validity metadata instead of pretending parse failures are structured reasoning.</p>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── BANDWIDTH ─────────────────────────────────────────
function Bandwidth() {
  const ref = uR(null);
  const [vis, setVis] = uS(false);
  uE(() => {
    const obs = new IntersectionObserver(([e]) => e.isIntersecting && setVis(true), { threshold: 0.3 });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, []);
  const txPct = (TOTALS.txTotal / TOTALS.rawTotal) * 100;
  return (
    <section className="section ink" id="bandwidth" data-bg="ink" data-screen-label="06 Bandwidth">
      <div className="section-inner">
        <div className="eyebrow">05 / The bandwidth math</div>
        <h2 className="h-display">
          The win <span className="it">isn't in</span> the model.<br/>
          It's in the <span className="accent underline">bytes you don't send.</span>
        </h2>
        <p className="lede">
          On the demo pass, KilnWatch processed 14 tiles onboard. If the satellite had downlinked everything raw it would have spent {fmtBytes(TOTALS.rawTotal)}. Instead it transmitted only JSON alerts and ~11×10 px crop evidence — {fmtBytes(TOTALS.txTotal)}.
        </p>

        <div ref={ref} className="bw">
          <div className="bw-side before">
            <div className="label">If we downlinked raw</div>
            <div className="val">{(TOTALS.rawTotal / 1024).toFixed(0)}<span className="u">KB</span></div>
            <div className="desc">14 raw 640×640 JPEGs at ~75 KB each. Every tile travels the bandwidth budget — <strong>regardless of whether it contains a kiln.</strong></div>
            <div className="bw-bar"><div style={{ width: vis ? "100%" : "0%" }}></div></div>
          </div>
          <div className="bw-side after">
            <div className="label">What KilnWatch downlinks</div>
            <div className="val">{(TOTALS.txTotal / 1024).toFixed(1)}<span className="u">KB</span></div>
            <div className="desc">5 JSON payloads + 5 crop PNGs. Dropped tiles emit telemetry only. Every byte downlinked is <strong>evidence the ground station can act on.</strong></div>
            <div className="bw-bar"><div style={{ width: vis ? `${txPct}%` : "0%" }}></div></div>
          </div>
        </div>

        <div className="bw-banner">
          <div className="pct">{TOTALS.pct.toFixed(1)}%</div>
          <div className="copy"><strong>Bandwidth saved.</strong> {fmtBytes(TOTALS.saved)} of imagery never travels — and every alert that does is auditable.</div>
          <div className="ratio">Compression<br/><strong>{Math.round(TOTALS.ratio)}×</strong></div>
        </div>
      </div>
    </section>
  );
}

// ─── PROOF CHAIN ───────────────────────────────────────
function Proof() {
  const [active, setActive] = uS("T_120");
  const a = ALERTS.find(x => x.id === active);
  const bb = a.bbox;
  const left = (bb[0] / 640) * 100, top = (bb[1] / 640) * 100;
  const w = ((bb[2] - bb[0]) / 640) * 100, h = ((bb[3] - bb[1]) / 640) * 100;
  const json = payloadJson(a);
  const summary = json.split("\n").slice(0, 16).join("\n") + "\n  ...";

  return (
    <section className="section paper" id="proof" data-bg="paper" data-screen-label="07 Proof">
      <div className="section-inner">
        <div className="eyebrow">06 / Proof chain — every alert audited</div>
        <h2 className="h-display">
          From <span className="it">image</span> to bbox to crop<br/>
          to JSON to dashboard. <span className="accent">No skipped steps.</span>
        </h2>
        <p className="lede">
          Pick a tile from the orbital pass. The pipeline below renders the actual artifacts on disk in <em>transmission_queue/</em> — bbox, crop, JSON, and reasoning are real.
        </p>

        <div className="chain">
          <div className="chain-tiles">
            <div className="chain-tiles-head">Alerts in pass</div>
            {ALERTS.map(t => (
              <button key={t.id}
                className={"chain-tile" + (t.id === active ? " active" : "")}
                onClick={() => setActive(t.id)}>
                <span className="id">{t.id}</span>
                <span className="conf">{(t.conf * 100).toFixed(0)}%</span>
              </button>
            ))}
          </div>
          <div className="chain-stage" key={active}>
            <div className="chain-step">
              <div className="num">01 / Imagery</div>
              <div className="title">Raw tile</div>
              <div className="body">
                <div className="tile-canvas"><img src={`assets/tiles/${a.id}.jpg`} alt={a.id} /></div>
                <div className="meta"><strong>{a.id}.jpg</strong><br/>640×640 · {fmtBytes(a.orig)}<br/>Roboflow optical fixture</div>
              </div>
              <div className="arrow-after">→</div>
            </div>
            <div className="chain-step">
              <div className="num">02 / Detection</div>
              <div className="title">YOLO detector</div>
              <div className="body">
                <div className="tile-canvas">
                  <img src={`assets/tiles/${a.id}.jpg`} alt={a.id} />
                  <div className="bbox" style={{ left: `${left}%`, top: `${top}%`, width: `${w}%`, height: `${h}%` }}>
                    <div className="bbox-label">KILN · {(a.conf*100).toFixed(0)}%</div>
                  </div>
                </div>
                <div className="meta">bbox · <strong>[{bb.map(x => x.toFixed(0)).join(", ")}]</strong><br/><strong>{a.detections}</strong> det · {a.inferenceMs.toFixed(1)} ms<br/>yolo_ultralytics:v0.1</div>
              </div>
              <div className="arrow-after">→</div>
            </div>
            <div className="chain-step">
              <div className="num">03 / Crop</div>
              <div className="title">Evidence artifact</div>
              <div className="body">
                <div className="tile-canvas" style={{ background: "#000" }}>
                  <img src={`assets/crops/${a.id}.png`} alt={`crop ${a.id}`} style={{ imageRendering: "pixelated" }} />
                </div>
                <div className="meta"><strong>{a.id}_crop.png</strong><br/>~11×10 px · 280–460 B<br/>Real PNG file in queue</div>
              </div>
              <div className="arrow-after">→</div>
            </div>
            <div className="chain-step">
              <div className="num">04 / Payload</div>
              <div className="title">JSON alert</div>
              <div className="body">
                <pre className="json-mini" dangerouslySetInnerHTML={{ __html: hl(summary) }} />
                <div className="meta"><strong>{a.id}.json</strong> · ~{fmtBytes(a.tx - 350)}<br/>bbox · confidence · triage<br/>+ Liquid validity metadata</div>
              </div>
              <div className="arrow-after">→</div>
            </div>
            <div className="chain-step">
              <div className="num">05 / Ground</div>
              <div className="title">Ground station</div>
              <div className="body">
                <div style={{ background: "var(--ink)", color: "var(--paper)", border: "1px solid var(--rule)", padding: 12, fontFamily: "var(--mono)", fontSize: 10, aspectRatio: 1, display: "flex", flexDirection: "column", gap: 8, justifyContent: "center" }}>
                  <div style={{ color: "var(--accent-2)", fontWeight: 700 }}>● ALERT · {a.id}</div>
                  <div style={{ color: "rgba(244,238,226,0.7)" }}>conf <strong style={{color:"var(--paper)"}}>{(a.conf*100).toFixed(0)}%</strong> · risk <strong style={{color:"var(--accent-2)"}}>{a.risk}</strong></div>
                  <div style={{ color: "#8ea8ff" }}>LFM2-VL: review needed</div>
                  <div style={{ color: "rgba(244,238,226,0.6)" }}>raw <strong style={{color:"var(--paper)"}}>{fmtBytes(a.orig)}</strong></div>
                  <div style={{ color: "var(--good)" }}>tx <strong>{fmtBytes(a.tx)}</strong> ✓</div>
                  <div style={{ borderTop: "1px solid rgba(244,238,226,0.15)", paddingTop: 6, marginTop: 4, color: "rgba(244,238,226,0.5)" }}>→ analyst dashboard</div>
                </div>
                <div className="meta"><strong>Queue-only boundary.</strong><br/>Reads <em>transmission_queue/</em> only.<br/>Never opens raw tile folder.</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── ORBITAL PASS ──────────────────────────────────────
function Pass({ onOpen }) {
  let rawAcc = 0;
  const rows = PASS_ORDER.map(p => {
    const a = ALERTS.find(x => x.id === p.id);
    const d = DROPPED.find(x => x.id === p.id);
    const orig = a ? a.orig : d.orig;
    rawAcc += orig;
    return { ...p, orig, tx: a ? a.tx : 0, conf: a ? a.conf : 0 };
  });
  const maxOrig = Math.max(...rows.map(p => p.orig));

  return (
    <section className="section ink" id="pass" data-bg="ink" data-screen-label="08 Pass">
      <div className="section-inner">
        <div className="eyebrow">07 / Orbital pass · live demo telemetry</div>
        <h2 className="h-display">
          Fourteen tiles in. <span className="accent">Five alerts out.</span><br/>
          The other nine <span className="it">never travel.</span>
        </h2>
        <p className="lede">
          Real telemetry from a strict-YOLO orbital pass over the demo set. Click any alert row to inspect the actual JSON payload in the queue.
        </p>

        <div className="pass">
          <div className="pass-stream">
            <div className="pass-head">
              <span>#</span><span>Tile ID</span><span>Conf</span><span>Raw bytes</span><span>Saved</span><span>Decision</span>
            </div>
            {rows.map((p, i) => (
              <div key={p.id}
                className={"pass-row " + (p.act === "ALERT" ? "alert" : "drop")}
                onClick={() => p.act === "ALERT" && onOpen(p.id)}>
                <span className="seq">{String(i+1).padStart(2,'0')}</span>
                <span className="id">{p.id}</span>
                <span>{p.act === "ALERT" ? `${(p.conf*100).toFixed(0)}%` : "—"}</span>
                <span>{fmtBytes(p.orig)}</span>
                <span className="saved-bar"><div style={{ width: `${(p.orig/maxOrig)*100}%` }}></div></span>
                <span className="decision">{p.act === "ALERT" ? "TX_ALERT" : "DROP_RAW"}</span>
              </div>
            ))}
          </div>
          <div className="pass-summary">
            <div className="pass-summary-card"><div className="label">Tiles processed</div><div className="value">{TOTALS.tilesProcessed}</div><div className="sub">onboard, before downlink</div></div>
            <div className="pass-summary-card"><div className="label">Transmitted</div><div className="value warn">{TOTALS.alerts}</div><div className="sub">{fmtBytes(TOTALS.txTotal)}</div></div>
            <div className="pass-summary-card"><div className="label">Dropped</div><div className="value">{TOTALS.dropped}</div><div className="sub">telemetry only · 0 B</div></div>
            <div className="pass-summary-card"><div className="label">Saved</div><div className="value good">{TOTALS.pct.toFixed(1)}%</div><div className="sub">{fmtBytes(TOTALS.saved)}</div></div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── LIQUID ALERTS ─────────────────────────────────────
function LiquidAlerts({ onOpen }) {
  return (
    <section className="section paper" id="liquid" data-bg="paper" data-screen-label="09 Liquid">
      <div className="section-inner">
          <div className="eyebrow">08 / Liquid LFM2-VL · onboard review</div>
        <h2 className="h-display">
          The alerts have <span className="it">reasoning,</span><br/>
          <span className="accent">not labels.</span>
        </h2>
        <p className="lede">
          For each YOLO detection, <em>LiquidAI/LFM2.5-VL-450M</em> runs in-situ on the crop when enabled. Valid structured JSON is displayed as reasoning; parse failures are labelled and kept as raw excerpts.
        </p>

        <div className="alerts-grid">
          {ALERTS.map(a => (
            <article key={a.id} className="alert-card" onClick={() => onOpen(a.id)}>
              <div className="crop">
                <img src={`assets/crops/${a.id}.png`} alt={`crop ${a.id}`} />
                <div className="dim">11×10</div>
              </div>
              <div className="body">
                <div className="head">
                  <span className="id">{a.id}</span>
                  <span>conf <strong>{(a.conf*100).toFixed(0)}%</strong></span>
                  <span>risk <strong style={{color:"var(--accent)"}}>{a.risk}</strong></span>
                  <span>det <strong>{a.detections}</strong></span>
                </div>
                <div className="reason">
                  <div className="label">Liquid LFM2-VL · review status</div>
                  <p><strong>Visual:</strong> {a.visual}</p>
                  <p><strong>Risk:</strong> {a.riskReasoning}</p>
                </div>
                <div className="footer-row">
                  <span>raw <strong style={{color:"var(--ink)"}}>{fmtBytes(a.orig)}</strong></span>
                  <span>→</span>
                  <span style={{color:"var(--good)"}}>tx <strong>{fmtBytes(a.tx)}</strong></span>
                  <span className="open">view payload →</span>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

window.Built = Built;
window.Bandwidth = Bandwidth;
window.Proof = Proof;
window.Pass = Pass;
window.LiquidAlerts = LiquidAlerts;

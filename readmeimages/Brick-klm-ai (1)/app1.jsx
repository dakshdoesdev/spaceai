// KilnWatch v2 — editorial component set (sections 1-4 + reusable utils)
const { useState, useEffect, useRef } = React;

const hl = (text) => text
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/("(?:\\.|[^"\\])*")(\s*:)/g, '<span class="k">$1</span>$2')
  .replace(/:\s*("(?:\\.|[^"\\])*")/g, ': <span class="s">$1</span>')
  .replace(/:\s*(-?\d+\.?\d*(?:[eE][-+]?\d+)?)/g, ': <span class="n">$1</span>')
  .replace(/:\s*(true|false|null)/g, ': <span class="b">$1</span>');

// ─── Topbar ────────────────────────────────────────────
function Topbar() {
  const [onPaper, setOnPaper] = useState(false);
  const [hidden, setHidden] = useState(false);
  useEffect(() => {
    let lastY = window.scrollY;
    let hoverPeek = false;
    const onScroll = () => {
      const y = window.scrollY;
      const els = document.querySelectorAll("[data-bg]");
      let cur = "ink";
      els.forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.top < 80 && r.bottom > 80) cur = el.dataset.bg;
      });
      setOnPaper(cur === "paper");
      const goingDown = y > lastY;
      if (y < 80) setHidden(false);
      else if (goingDown && y > 200) setHidden(true);
      else if (!goingDown) setHidden(false);
      if (hoverPeek) setHidden(false);
      lastY = y;
    };
    const onMove = e => {
      hoverPeek = e.clientY < 70;
      if (hoverPeek) setHidden(false);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("mousemove", onMove, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("mousemove", onMove);
    };
  }, []);
  return (
    <div className={"topbar " + (onPaper ? "on-paper" : "on-ink") + (hidden ? " is-hidden" : "")}>
      <div className="topbar-logo">
        <span className="pip"></span>
        <span>KilnWatch</span>
        <span className="sep">/</span>
        <span className="sub">an AI for the Indo-Gangetic Plain</span>
      </div>
      <nav>
        <a href="#problem">Problem</a>
        <a href="#built">What I built</a>
        <a href="#proof">Proof</a>
        <a href="#liquid">Liquid</a>
        <a href="#honesty">Honesty</a>
        <a href="#built" className="cta cta-demo">demo</a>
        <a href="https://github.com/dakshdoesdev/spaceai" target="_blank" rel="noopener" className="cta">github</a>
      </nav>
    </div>
  );
}

// ─── HERO ──────────────────────────────────────────────
function Hero() {
  return (
    <section className="hero" data-bg="ink" data-screen-label="01 Hero">
      <div className="hero-bg"><div className="satellite-img"></div></div>
      <div className="hero-grain"></div>
      <div className="hero-meta">
        <div className="group"><span className="dot"></span><span>Live demo · GS-01</span></div>
        <span className="pill">AI in Space · Liquid AI × DPhi Space · 2026</span>
        <span className="pill live">5 alerts · {fmtBytes(TOTALS.saved)} saved · {TOTALS.pct.toFixed(1)}%</span>
      </div>
      <div className="hero-main">
        <h1>
          Brick&nbsp;kilns,<br/>
          <span className="it">caught</span> from <span className="tilt">space.</span>
        </h1>
        <div className="hero-sub">
          <p className="hero-lede">
            An Earth-observation AI that decides what's worth downlinking <em>before</em> the satellite spends bandwidth on empty fields. YOLO localizes, Liquid LFM2-VL reviews crop evidence, the ground station only ever sees the evidence.
          </p>
          <div className="hero-cta">
            <a href="#problem" className="primary">Read the brief</a>
            <a href="#built">See it run</a>
          </div>
        </div>
      </div>
      <div className="hero-foot">
        <div className="scroll">scroll</div>
        <div className="stats">
          <div>14 tiles · <span className="v">5 alerts</span></div>
          <div>1.1 MB raw → <span className="v">{fmtBytes(TOTALS.txTotal)} tx</span></div>
          <div>compression · <span className="v">{Math.round(TOTALS.ratio)}×</span></div>
        </div>
      </div>
    </section>
  );
}

// ─── PERSONAL HOOK ─────────────────────────────────────
function Hook() {
  return (
    <section className="section paper" id="hook" data-bg="paper" data-screen-label="02 Hook">
      <div className="section-inner">
        <div className="eyebrow">01 / The air I breathe</div>
        <h2 className="h-display">
          The pollution is <span className="it">created by</span><br/>
          <span className="accent underline">illegal brick kilns.</span>
        </h2>

        <div className="hook">
          <div className="hook-text">
            <div className="body-prose">
              <p>I'm in the Indo-Gangetic Plain. Every winter the air here goes from <em>bad</em> to literally off the AQI scale — hazardous for weeks at a time.</p>
              <p>A huge part of that is <strong>illegal brick kilns</strong>. Thousands of them, burning coal, tyres, plastic, whatever's cheap. Nobody knows where most of them are, because nobody can fly over the whole IGP every week to count them.</p>
              <p>So I built an AI for it.</p>
            </div>
          </div>

          <div className="hook-aside">
            <div className="hook-card">
              <div className="label">Delhi · 14 Nov 2025</div>
              <div className="value">494<span className="unit">AQI</span></div>
              <div className="desc">"Hazardous" begins at 301. The PM2.5 sensor in my room read 380 µg/m³ at 9 AM — over 25× the WHO 24h guideline.</div>
              <div className="aqi-bar"><div className="needle"></div></div>
              <div className="aqi-scale"><span>0</span><span>100</span><span>200</span><span>300</span><span>500+</span></div>
              <div className="source">Source · CPCB Sameer / IQAir</div>
            </div>
            <div className="hook-card">
              <div className="label">Brick kilns in the IGP</div>
              <div className="value">100k<span className="unit">+</span></div>
              <div className="desc">across India, Pakistan, Bangladesh — one of the largest sources of black carbon in the region.</div>
              <div className="source">Source · SentinelKilnDB, NeurIPS 2025</div>
            </div>
          </div>
        </div>

        <p className="pullquote">
          Most of what a satellite sees over the IGP is empty fields. The bandwidth has already been spent <span className="it">— on every tile.</span>
          <span className="attr">— the framing question</span>
        </p>
      </div>
    </section>
  );
}

// ─── PROBLEM ────────────────────────────────────────────
function Problem() {
  return (
    <section className="section ink" id="problem" data-bg="ink" data-screen-label="03 Problem">
      <div className="section-inner">
        <div className="eyebrow">02 / The problem with how this is done today</div>
        <h2 className="h-display">
          Every existing system <span className="it">downlinks first,</span><br/>
          <span className="accent underline">thinks later.</span>
        </h2>
        <p className="lede">
          Brick-kiln detection is a well-studied ground-side problem. The pattern is the same in every paper, every commercial product, every satellite imagery vendor. <em>And it breaks at the same step.</em>
        </p>

        <div className="problem-grid">
          <div className="body-prose">
            <p>The IGP has well over a hundred thousand brick kilns across India, Pakistan, and Bangladesh — that's the public number from the SentinelKilnDB dataset, NeurIPS 2025, Rishabh Mondal's team at IIT Gandhinagar.</p>
            <p>Brick kilns are one of the largest sources of black carbon in the region. Every one of those papers takes the same approach: a satellite captures imagery, the whole image gets downlinked to the ground, a model runs object detection, compliance officers maybe act on it.</p>
            <p>Step two is where it breaks. The bandwidth has already been spent — on <em>every</em> tile, including the ninety-plus percent that contain nothing but farmland and roads. On a small satellite, downlink is the most expensive part of the whole system.</p>
            <p>So the obvious move is: <strong>don't transmit empty fields.</strong> Decide what's worth sending <em>before</em> you send it.</p>
          </div>

          <div className="problem-stats">
            <div className="problem-stat">
              <div className="l">Kilns mapped · IGP</div>
              <div className="v">100k<span className="unit">+</span></div>
              <div className="src">SentinelKilnDB · NeurIPS 2025</div>
            </div>
            <div className="problem-stat">
              <div className="l">Pakistan IGP · APAD2024</div>
              <div className="v">11.3k</div>
              <div className="src">brickkilnscidata · Sci. Data 2024</div>
            </div>
            <div className="problem-stat">
              <div className="l">Tiles per pass</div>
              <div className="v">~10⁴</div>
              <div className="src">Sentinel-2 over IGP</div>
            </div>
            <div className="problem-stat">
              <div className="l">Tiles with kilns</div>
              <div className="v">&lt;5%</div>
              <div className="src">empirical · Mondal et al.</div>
            </div>
          </div>
        </div>

        <div className="workflow-broken">
          <h3>The pipeline every existing system uses</h3>
          <div className="workflow-steps">
            <div className="workflow-step">
              <div className="num">01</div>
              <h4>Capture</h4>
              <p>Satellite collects imagery on a polar orbit pass.</p>
            </div>
            <div className="workflow-step broken">
              <div className="num">02</div>
              <h4>Downlink everything</h4>
              <p>Whole tiles fly through the bandwidth budget. Empty fields cost the same as kilns.</p>
            </div>
            <div className="workflow-step">
              <div className="num">03</div>
              <h4>Detect</h4>
              <p>YOLO / Faster-RCNN runs on a server, finds the &lt;5% that matter.</p>
            </div>
            <div className="workflow-step">
              <div className="num">04</div>
              <h4>Triage</h4>
              <p>Analyst reviews, compliance officer maybe acts.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── HACKATHON FRAMING ────────────────────────────────
function Hackathon() {
  return (
    <section className="section paper" id="hackathon" data-bg="paper" data-screen-label="04 Hackathon">
      <div className="section-inner">
        <div className="eyebrow">03 / Why Liquid AI × DPhi Space</div>
        <h2 className="h-display">
          What would you do with a <span className="it">small VLM</span><br/>
          <span className="accent underline">in orbit?</span>
        </h2>

        <div className="hack-grid">
          <div className="body-prose">
            <p><strong>Liquid AI's LFM2.5-VL-450M</strong> is small enough to run locally and reason over visual evidence. <strong>DPhi Space</strong> provides the satellite simulation layer through SimSat.</p>
            <p>KilnWatch uses that idea directly: <em>process imagery before downlink, turn detections into structured alerts, and send only the evidence the ground station needs.</em></p>
            <p>YOLO localizes the kiln and drives the gate. Liquid LFM2-VL reviews the crop and the payload records whether structured parsing succeeded.</p>
          </div>

          <div className="hack-card">
            <div className="row"><div className="k">Hackathon</div><div className="v"><strong>AI in Space</strong></div></div>
            <div className="row"><div className="k">Hosts</div><div className="v"><span className="pill liquid">Liquid AI</span><span className="pill">DPhi Space</span></div></div>
            <div className="row"><div className="k">Window</div><div className="v">Apr 13 — May 8, 2026</div></div>
            <div className="row"><div className="k">Format</div><div className="v">Online · global · 4 weeks</div></div>
            <div className="row"><div className="k">Brief</div><div className="v">Real-world apps using Liquid VLMs on live satellite imagery</div></div>
            <div className="row"><div className="k">Track</div><div className="v"><strong>Liquid Track</strong> — LFM2-VL / LFM2.5-VL onboard</div></div>
            <div className="row"><div className="k">Tooling</div><div className="v">SimSat orbit API · Sentinel-2 · Mapbox · localhost:9005</div></div>
            <div className="row"><div className="k">Models</div><div className="v"><strong>LiquidAI/LFM2.5-VL-450M</strong></div></div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── WORKFLOW (How KilnWatch thinks before downlink) ───
function Workflow() {
  const steps = [
    { n: "01", title: "Raw tile enters the satellite node", body: "A satellite image tile enters the local edge pipeline. At this stage, the ground station has not received anything yet.", side: "Onboard · pre-decision" },
    { n: "02", title: "YOLO localizes kiln candidates", body: "YOLO scans the tile and returns bounding box, confidence score, tile ID, and detector metadata. The localization step: where is the possible kiln?", side: "Onboard · detect" },
    { n: "03", title: "Crop evidence is generated", body: "If the detection needs review, KilnWatch cuts out the detected region as a real crop PNG. This crop becomes the evidence artifact — no need to downlink the entire tile to show the analyst what mattered.", side: "Onboard · crop" },
    { n: "04", title: "Liquid LFM2-VL reviews the evidence", body: "Liquid LFM2.5-VL reads the visual evidence and adds analyst-facing reasoning when the structured parse is valid. Parse failures are labelled honestly and include raw excerpts.", side: "Onboard · review" },
    { n: "05", title: "Four-tier triage decides what gets sent", body: "IGNORE (telemetry only) · JSON_ALERT_ONLY (compact JSON, no crop) · CROP_OR_REVIEW (JSON + crop for analyst) · FULL_DOWNLINK (request the full tile only when risk justifies the bandwidth).", side: "Onboard · gate" },
    { n: "06", title: "Ground station receives only the queue", body: "The ground station reads from transmission_queue/, not from the raw tile folder. That means the dashboard proves the architecture: raw imagery stays onboard unless the triage gate decides it is worth sending.", side: "Ground · queue-only" },
  ];
  return (
    <section className="section ink" id="workflow" data-bg="ink" data-screen-label="05 Workflow">
      <div className="section-inner">
        <div className="eyebrow">04 / How KilnWatch thinks before downlink</div>
        <h2 className="h-display">
          The first decision <span className="it">happens</span><br/>
          <span className="accent">near the satellite.</span>
        </h2>
        <p className="lede">
          Raw tile → YOLO candidate → crop evidence → Liquid review → four-tier triage → queue-only ground station. The ground station never sees raw tiles by default — only the evidence: <em>JSON alerts, crops, telemetry, and (when required) full-tile requests.</em>
        </p>

        <ol className="flow">
          {steps.map((s, i) => (
            <li key={s.n} className={"flow-step" + (i === 4 ? " gate" : "") + (i === 5 ? " ground" : "")}>
              <div className="flow-num">{s.n}</div>
              <div className="flow-body">
                <h3>{s.title}</h3>
                <p>{s.body}</p>
              </div>
              <div className="flow-side">{s.side}</div>
              {i < steps.length - 1 && <div className="flow-arrow">↓</div>}
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

window.Topbar = Topbar;
window.Hero = Hero;
window.Hook = Hook;
window.Problem = Problem;
window.Hackathon = Hackathon;
window.Workflow = Workflow;
window.hl = hl;

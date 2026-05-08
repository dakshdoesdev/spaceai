// KilnWatch v2 — components 10-14 (cool, prior art, broken, honesty, footer, modal)
const { useState: uSS, useEffect: uEE } = React;

// ─── COOL THINGS ───────────────────────────────────────
function Cool() {
  return (
    <section className="section ink-2" id="cool" data-bg="ink" data-screen-label="10 Cool">
      <div className="section-inner">
        <div className="eyebrow">09 / Three things worth saying out loud</div>
        <h2 className="h-display">
          What's <span className="it">actually cool</span><br/>
          about this.
        </h2>

        <div className="cool">
          <div className="cool-item">
            <div className="num">01</div>
            <h3>On-device, not cloud.</h3>
            <p>No OpenAI, no Anthropic, no Gemini, no Sentinel Hub API. The Liquid model loads from disk and runs on this laptop's CPU in about <strong>three minutes</strong> for the demo set. Valid structured parses are marked valid; parse failures are shown honestly. Liquid's own cookbook documents the same family running on WebGPU, Android, iOS, macOS — KilnWatch only proves the CPU path; the rest are recipes.</p>
          </div>
          <div className="cool-item">
            <div className="num">02</div>
            <h3>Reasoning, not labels.</h3>
            <p>Most kiln-detection demos give you a bbox and a confidence score. KilnWatch gives you the bbox, the confidence, <strong>and Liquid validity metadata</strong>: whether the local model produced structured crop reasoning or only a raw parse-failed excerpt. That's what an analyst actually needs.</p>
          </div>
          <div className="cool-item">
            <div className="num">03</div>
            <h3>The ground side can prove every claim.</h3>
            <p>The dashboard literally cannot read the raw imagery — there's a unit test that fails if it ever tries. Everything you see is reconstructed from downlinked JSON, crop PNGs, and telemetry. The bandwidth-saved number isn't a marketing slide; it's <strong>measured from real file sizes anyone can verify.</strong></p>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── PRIOR ART ────────────────────────────────────────
function PriorArt() {
  const priors = [
    { year: "2025 · NeurIPS", title: "SentinelKilnDB", who: "Mondal et al., IIT Gandhinagar", desc: "Gold-standard ground-side detection. Real Sentinel-2, oriented bounding boxes, train/val/test splits across South Asia. KilnWatch uses their coordinate datasets to ground the pipeline.", label: "Ground-side · post-downlink" },
    { year: "2024 · KDD",     title: "Space-to-Policy", who: "Mondal et al.", desc: "Scalable brick-kiln detection and automatic compliance monitoring with geospatial data. Same pattern.", label: "Ground-side · post-downlink" },
    { year: "2024 · Sci. Data", title: "APAD2024 / brickkilnscidata", who: "Pakistan IGP", desc: "11,277 mapped kilns. Ground-side coordinates dataset used for grounding.", label: "Coordinate dataset" },
    { year: "2021 · PNAS",    title: "Brooks et al.", who: "Original brick-kiln deep-learning paper", desc: '"Scalable deep learning to identify brick kilns and aid regulatory capacity." Same pattern: imagery downlinked, model on the ground.', label: "Ground-side · post-downlink" },
    { year: "2020 · ASPLOS",  title: "Orbital Edge Computing", who: "Denby & Lucia", desc: "The paper that named this entire pattern. Nanosatellite constellations as a new class of computer system. The architectural ancestor.", label: "Architectural inspiration" },
    { year: "2026 · cookbook", title: "Liquid AI · wildfire-prevention", who: "Same model family", desc: "Uses LFM2.5-VL-450M and Sentinel-2 for wildfire risk classification. Same model, same satellite-edge framing — different verb.", label: "Sibling, not same", diff: true },
  ];
  return (
    <section className="section ink" id="prior" data-bg="ink" data-screen-label="11 Prior">
      <div className="section-inner">
        <div className="eyebrow">10 / Prior art — what already exists, and what's different</div>
        <h2 className="h-display">
          The work above is <span className="it">necessary.</span><br/>
          It assumes the bandwidth <span className="accent">has already been spent.</span>
        </h2>
        <p className="lede">
          I want to be honest about what already exists, because none of this happens in a vacuum. Every project below is <em>what to do with imagery once it's already on the ground</em>. KilnWatch is the missing front half — an AI that decides what's worth sending in the first place.
        </p>

        <div className="priors">
          {priors.map((p, i) => (
            <div key={i} className={"prior" + (p.diff ? " diff" : "")}>
              <div className="year">{p.year}</div>
              <div>
                <h4>{p.title}</h4>
                <p>{p.who} — {p.desc}</p>
              </div>
              <div className="label">{p.label}</div>
            </div>
          ))}
        </div>

        <p className="pullquote" style={{ marginTop: 64 }}>
          I'm not claiming a better detector than Mondal's team, or a better fine-tuned VLM than Liquid's cookbook. The contribution is <span className="it">narrow and specific</span> — YOLO + base LFM2.5-VL sitting in the onboard slot, not on a server. That's the gap.
          <span className="attr">— scope, in writing</span>
        </p>
      </div>
    </section>
  );
}

// ─── BROKEN STORIES ────────────────────────────────────
function Broken() {
  return (
    <section className="section paper" id="broken" data-bg="paper" data-screen-label="12 Broken">
      <div className="section-inner">
        <div className="eyebrow">11 / Hackathon honesty — what actually broke</div>
        <h2 className="h-display">
          Three things <span className="it">went wrong.</span><br/>
          Here's how I <span className="accent">fixed them.</span>
        </h2>

        <div className="broken-grid">
          <div className="broken-card">
            <div className="num">Problem 01</div>
            <h3>Ollama can't load LFM2 models.</h3>
            <p>Started with Ollama because I had it installed. The model loads, the manifest <em>says</em> "vision capability", and then the moment you send a request, the runtime crashes with <code>missing tensor 'output_norm'</code>. Reproduced on Q4_0 and Q8_0 official Liquid GGUFs. Upstream bug in Ollama 0.17.5's LFM2 architecture support.</p>
            <div className="fix"><strong>Fix:</strong> Dropped the Ollama path. Switched to Liquid via Hugging Face <code>transformers.AutoModelForImageTextToText</code>. Loads in seconds, ~20s per crop on CPU, no GPU needed.</div>
          </div>
          <div className="broken-card">
            <div className="num">Problem 02</div>
            <h3>Pipeline was binary; architecture was four-tier.</h3>
            <p>The README talked about IGNORE / JSON_ALERT_ONLY / CROP_OR_REVIEW / FULL_DOWNLINK, but the actual code only ever did binary <code>TRANSMIT_ALERT</code> or <code>DROP</code>. The four-tier <code>TriageDecision</code> enum existed in <code>kilnwatch/triage.py</code>; nobody was calling it.</p>
            <div className="fix"><strong>Fix:</strong> Wired <code>compute_triage()</code> in. Every payload + telemetry row now carries the four-tier label. The transmit gate stays binary for now — label is recorded honestly so the schema is ready when the gate flips.</div>
          </div>
          <div className="broken-card">
            <div className="num">Problem 03</div>
            <h3>Provenance — almost shipped a lie.</h3>
            <p>The demo tiles are open-source brick-kiln imagery from Roboflow. Real overhead photos of real kilns. But they are <em>not</em> Sentinel-2, not DPhi SimSat live tiles, not Haryana ground-truth. I almost shipped a slide that said "Sentinel imagery."</p>
            <div className="fix"><strong>Fix:</strong> Removed the slide. README and dashboard both say what the tiles actually are. <strong>Honesty over hype.</strong></div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── NEXT + SOURCES ────────────────────────────────────
function Next() {
  return (
    <section className="section paper" id="next" data-bg="paper" data-screen-label="14 Next">
      <div className="section-inner">
        <div className="eyebrow">13 / What's next, where it came from</div>
        <h2 className="h-display">
          Sources, in <span className="it">writing.</span><br/>
          Next steps, <span className="accent">unshipped.</span>
        </h2>
        <p className="lede">
          To be clear: <em>none</em> of the next-step work below has been run yet in this repo. Every claim above is testable against the code on disk; every claim below is a recipe I'd follow.
        </p>

        <div className="next-grid">
          <div className="next">
            <h3>What I'd do next</h3>
            <ul>
              <li><span className="marker">→</span><span><strong>Fine-tune LFM2.5-VL-450M</strong> on brick-kiln crops using the official Liquid cookbook recipes — <em>satellite-vlm</em> for EO domain adaptation, plus the Unsloth notebook. Legitimate path from base reasoning to domain-tuned reasoning.</span></li>
              <li><span className="marker">→</span><span><strong>Wire the four-tier triage</strong> into the actual transmit gate, not just the label.</span></li>
              <li><span className="marker">→</span><span><strong>Plug into DPhi SimSat live Sentinel-2</strong> — input becomes real Sentinel imagery, not Roboflow demo tiles.</span></li>
              <li><span className="marker">→</span><span><strong>Deployment paths</strong> Liquid documents — llama.cpp, MLX, LEAP SDK, Ollama (when upstream lands). Currently only the transformers CPU path runs.</span></li>
            </ul>
          </div>
          <div className="next">
            <h3>Sources</h3>
            <ul>
              <li><span className="marker">·</span><span><strong>Liquid AI</strong> — LFM2.5-VL-450M, the model doing the onboard reasoning.</span></li>
              <li><span className="marker">·</span><span><strong>DPhi Space</strong> — SimSat orbit/imagery simulator.</span></li>
              <li><span className="marker">·</span><span><strong>Ultralytics YOLOv8</strong> — detector framework.</span></li>
              <li><span className="marker">·</span><span><strong>Mondal et al.</strong> — SentinelKilnDB (NeurIPS 2025), Space-to-Policy (KDD 2024).</span></li>
              <li><span className="marker">·</span><span><strong>APAD2024 / brickkilnscidata</strong> — Pakistan IGP coordinates.</span></li>
              <li><span className="marker">·</span><span><strong>Brooks et al., PNAS 2021</strong> — original brick-kiln deep-learning paper.</span></li>
              <li><span className="marker">·</span><span><strong>Denby & Lucia, ASPLOS 2020</strong> — <em>Orbital Edge Computing</em>, the architectural ancestor.</span></li>
              <li><span className="marker">·</span><span><strong>Roboflow Brick Kiln Detection v1</strong> — the demo imagery.</span></li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── FOOTER ────────────────────────────────────────────
function Footer() {
  return (
    <footer className="footer" data-bg="ink">
      <div className="footer-inner">
        <div className="footer-brand">
          <div className="name">Kiln<em>Watch.</em></div>
          <p>An Earth-observation AI for the Indo-Gangetic Plain. Built for AI in Space — Liquid AI × DPhi Space, 2026. The first decision happens in orbit.</p>
          <a className="gh" href="https://github.com/dakshdoesdev/spaceai" target="_blank" rel="noopener">github.com/dakshdoesdev/spaceai ↗</a>
        </div>
        <div>
          <h4>Run it yourself</h4>
          <ul>
            <li>$ pip install -r requirements.txt</li>
            <li>$ python -m satellite_edge_node.orbital_pass \</li>
            <li style={{ paddingLeft: 16 }}>--detector yolo --reasoner liquid-local</li>
            <li style={{ marginTop: 8 }}>$ streamlit run app.py</li>
            <li style={{ marginTop: 16, opacity: 0.5 }}>Apache 2.0</li>
          </ul>
        </div>
        <div>
          <h4>Honest about</h4>
          <ul>
            <li>Local simulation, not deployed</li>
            <li>Roboflow tiles, not Sentinel-2</li>
            <li>Base LFM2-VL, not fine-tuned</li>
            <li>Architecture, not accuracy</li>
          </ul>
        </div>
      </div>
      <div className="footer-base">
        <span>© 2026 · dakshdoesdev</span>
        <span>Built in 4 weeks for AI in Space</span>
      </div>
    </footer>
  );
}

// ─── MODAL ─────────────────────────────────────────────
function Modal({ id, onClose }) {
  const a = ALERTS.find(x => x.id === id);
  uEE(() => {
    const h = e => e.key === "Escape" && onClose();
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, []);
  if (!a) return null;
  const json = payloadJson(a);
  return (
    <div className="modal-bg" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-head">
          <div><span className="id">{a.id}.json</span><span style={{ color: "rgba(244,238,226,0.5)", marginLeft: 14 }}>← transmission_queue/</span></div>
          <button className="x" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          <div className="modal-side">
            <div className="crop-large"><img src={`assets/crops/${a.id}.png`} alt={`crop ${a.id}`} /></div>
            <div className="field"><span className="k">Detector</span><span className="v">yolo_ultralytics:v0.1</span></div>
            <div className="field"><span className="k">Confidence</span><span className="v" style={{color:"var(--accent-2)"}}>{(a.conf*100).toFixed(2)}%</span></div>
            <div className="field"><span className="k">Bbox (x1,y1,x2,y2)</span><span className="v">{a.bbox.map(x=>x.toFixed(2)).join(", ")}</span></div>
            <div className="field"><span className="k">Detections</span><span className="v">{a.detections}</span></div>
            <div className="field"><span className="k">Inference</span><span className="v">{a.inferenceMs.toFixed(1)} ms</span></div>
            <div className="field"><span className="k">Triage</span><span className="v" style={{color:"var(--accent-2)"}}>{a.decision}</span></div>
            <div className="field"><span className="k">Bandwidth saved</span><span className="v" style={{color:"var(--good)"}}>{fmtBytes(a.orig - a.tx)} ({((1 - a.tx/a.orig)*100).toFixed(1)}%)</span></div>
            <div className="field"><span className="k">Liquid model</span><span className="v" style={{color:"#8ea8ff"}}>LFM2.5-VL-450M</span></div>
          </div>
          <pre className="modal-pre" dangerouslySetInnerHTML={{ __html: hl(json) }} />
        </div>
      </div>
    </div>
  );
}

// ─── HONESTY (compact, contribution-only) ──────────────
function Honesty() {
  return (
    <section className="section ink-2" id="honesty" data-bg="ink" data-screen-label="13 Honesty">
      <div className="section-inner">
        <div className="eyebrow">10 / The contribution</div>
        <h2 className="h-display">
          The <span className="accent">architecture</span> is the<br/>
          <span className="it">contribution.</span>
        </h2>
        <p className="lede">
          Production path: replace the tile source with the DPhi SimSat <em>/data/image/sentinel</em> endpoint, fine-tune YOLO + Liquid on Sentinel-domain kiln labels. <strong>The triage architecture, queue boundary, and ground-station accounting do not change.</strong>
        </p>
      </div>
    </section>
  );
}

// ─── FINAL TALLY (closing) ─────────────────────────────
function FinalTally() {
  return (
    <section className="section ink" id="tally" data-bg="ink" data-screen-label="14 Tally">
      <div className="section-inner">
        <div className="eyebrow">11 / The pass, in numbers</div>
        <h2 className="h-display">
          Fourteen tiles. <span className="it">Five alerts.</span><br/>
          <span className="accent">{TOTALS.pct.toFixed(1)}% saved.</span>
        </h2>

        <div className="tally">
          <div className="tally-cell">
            <div className="l">Tiles processed</div>
            <div className="v">{TOTALS.tilesProcessed}</div>
            <div className="s">onboard, before downlink</div>
          </div>
          <div className="tally-cell accent">
            <div className="l">Alerts transmitted</div>
            <div className="v">{TOTALS.alerts}</div>
            <div className="s">{fmtBytes(TOTALS.txTotal)} total</div>
          </div>
          <div className="tally-cell">
            <div className="l">Compression</div>
            <div className="v">{Math.round(TOTALS.ratio)}<span className="u">×</span></div>
            <div className="s">raw vs transmitted</div>
          </div>
          <div className="tally-cell good">
            <div className="l">Bandwidth saved</div>
            <div className="v">{TOTALS.pct.toFixed(1)}<span className="u">%</span></div>
            <div className="s">{fmtBytes(TOTALS.saved)} kept onboard</div>
          </div>
        </div>

        <div className="tally-cta">
          <a className="primary" href="#built">▶ Run the demo</a>
          <a href="https://github.com/dakshdoesdev/spaceai" target="_blank" rel="noopener">github ↗</a>
          <span className="scope">An Earth-observation AI for the Indo-Gangetic Plain. The first decision happens in orbit.</span>
        </div>
      </div>
    </section>
  );
}

window.Cool = () => null;
window.PriorArt = () => null;
window.Broken = () => null;
window.HonestyV2 = Honesty;
window.NextSection = FinalTally;
window.FooterV2 = () => null;
window.ModalV2 = Modal;

(function(){
  const D = window.QUEUE_DATA;
  const $ = (id) => document.getElementById(id);

  // ---- Helpers ----
  function fmtBytes(b){
    if (b == null) return "—";
    const u = ["B","KB","MB","GB"];
    let i = 0, n = Number(b);
    while (n >= 1024 && i < u.length-1){ n/=1024; i++; }
    return (n>=100?n.toFixed(0):n>=10?n.toFixed(1):n.toFixed(2)) + " " + u[i];
  }
  function fmtNum(n){ return Number(n).toLocaleString(); }

  // ---- Clock + pass id ----
  function pad(n){return String(n).padStart(2,"0")}
  function tickClock(){
    const d = new Date();
    $("clock").textContent = `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())}`;
  }
  setInterval(tickClock, 1000); tickClock();
  $("passId").textContent = "0×" + Math.floor(Math.random()*0xffff).toString(16).padStart(4,"0").toUpperCase();

  // ---- Run button (animated load) ----
  const runBtn = $("runBtn");
  const progressBar = $("progressBar");
  const runMeta = $("runMeta");

  runBtn.addEventListener("click", () => {
    if (runBtn.disabled) return;
    runBtn.disabled = true;
    runBtn.querySelector("span:nth-child(2)").firstChild.nodeValue = "Reading queue…";
    runMeta.textContent = "READING transmission_queue/*.json …";

    const stages = [
      [10,  "READING transmission_queue/*.json …"],
      [28,  "READING transmission_queue/telemetry.jsonl …"],
      [48,  "VERIFYING reasoner_is_real / reasoner_output_valid …"],
      [70,  "RECONCILING payload + telemetry rows …"],
      [88,  "COMPUTING byte accounting …"],
      [100, "QUEUE LOADED · GATE STATE RECONSTRUCTED"]
    ];
    let i = 0;
    const tick = () => {
      const [pct, msg] = stages[i];
      progressBar.style.width = pct + "%";
      runMeta.textContent = msg;
      i++;
      if (i < stages.length){
        setTimeout(tick, 240 + Math.random()*220);
      } else {
        loadDashboard();
        setTimeout(()=>{ progressBar.style.width = "0%"; }, 600);
        runBtn.disabled = false;
        runBtn.querySelector("span:nth-child(2)").firstChild.nodeValue = "Reload Mission Replay";
      }
    };
    tick();
  });

  // ---- JSON syntax highlight ----
  function jsonHighlight(obj){
    const json = JSON.stringify(obj, null, 2);
    return json
      .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
      .replace(/("(\\u[a-fA-F0-9]{4}|\\[^u]|[^\\"])*")(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g,
        (m) => {
          let cls = "n";
          if (/^"/.test(m)) cls = /:$/.test(m) ? "k" : "s";
          else if (/true|false/.test(m)) cls = "b";
          else if (/null/.test(m)) cls = "nl";
          return `<span class="${cls}">${m}</span>`;
        });
  }

  // ---- Build tile rows ----
  let selectedIdx = 0;
  function buildTileTable(){
    const body = $("tileBody");
    body.innerHTML = "";
    D.rows.forEach((r, idx) => {
      const row = document.createElement("div");
      row.className = "tile-row fade-in";
      row.style.animationDelay = (idx * 18) + "ms";
      const gateClass =
        r.triage_decision === "IGNORE"          ? "ignore" :
        r.triage_decision === "JSON_ALERT_ONLY" ? "json"   :
        r.triage_decision === "FULL_DOWNLINK"   ? "full"   : "crop";
      const gateShort =
        r.triage_decision === "IGNORE"          ? "IGNORE" :
        r.triage_decision === "JSON_ALERT_ONLY" ? "JSON"   :
        r.triage_decision === "FULL_DOWNLINK"   ? "FULL"   : "CROP";
      const isAlert = r.triage_decision !== "IGNORE";
      const confPct = Math.min(100, Math.max(0, r.confidence * 100));
      row.innerHTML = `
        <span class="tid">${r.tile_id}</span>
        <span><span class="gate ${gateClass}">${gateShort}</span></span>
        <span>
          <span class="conf ${isAlert?'':'low'}">${r.confidence.toFixed(4)}</span>
          <span class="conf-bar"><i style="width:${confPct}%"></i></span>
        </span>
        <span class="conf ${r.crop_written?'':'low'}">${r.crop_written ? "yes" : "—"}</span>
        <span class="bytes">${fmtBytes(r.transmitted_bytes)}</span>
      `;
      row.addEventListener("click", () => selectRow(idx));
      body.appendChild(row);
    });
    selectRow(firstAlertIdx());
  }

  function firstAlertIdx(){
    for (let i=0;i<D.rows.length;i++) if (D.rows[i].triage_decision !== "IGNORE") return i;
    return 0;
  }

  function selectRow(idx){
    selectedIdx = idx;
    [...document.querySelectorAll(".tile-row")].forEach((el,i)=>{
      el.classList.toggle("selected", i === idx);
    });
    renderDetail(D.rows[idx]);
  }

  // ---- Crop SVG (placeholder evidence visual based on bbox) ----
  function renderCropSVG(row){
    const svg = $("cropSvg");
    if (!row.bbox){
      svg.innerHTML = `
        <defs><pattern id="hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="8" stroke="#1a1a18" stroke-width="6"/>
        </pattern></defs>
        <rect width="400" height="250" fill="#0a0a09"/>
        <rect width="400" height="250" fill="url(#hatch)" opacity=".5"/>
        <text x="200" y="130" text-anchor="middle" fill="#7a7164" font-family="JetBrains Mono" font-size="10" letter-spacing="2">NO CROP TRANSMITTED</text>
        <text x="200" y="148" text-anchor="middle" fill="#4a4238" font-family="JetBrains Mono" font-size="9" letter-spacing="1.5">TILE IGNORED ONBOARD</text>
      `;
      return;
    }
    // Pseudo terrain + bbox highlight
    const seed = row.tile_id.split("").reduce((a,c)=>a + c.charCodeAt(0), 0);
    const rand = (i) => {
      const x = Math.sin(seed * 9999 + i * 13) * 10000;
      return x - Math.floor(x);
    };
    let blocks = "";
    for (let i=0;i<60;i++){
      const x = rand(i)*400, y = rand(i+99)*250;
      const w = 12 + rand(i+2)*40, h = 8 + rand(i+5)*22;
      const op = .15 + rand(i+7)*.4;
      const hue = ["#3a3026","#2c241c","#4a3c2e","#241d18"][Math.floor(rand(i+11)*4)];
      blocks += `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${hue}" opacity="${op}"/>`;
    }
    // chimneys + plumes for high-conf alerts
    let kilns = "";
    if (row.confidence > 0.5){
      const cx = 160 + rand(20)*80;
      const cy = 110 + rand(21)*40;
      const ovens = row.confidence > 0.85 ? 6 : row.confidence > 0.7 ? 3 : 2;
      for (let k=0;k<ovens;k++){
        const ox = cx + (k%3)*22 - 22, oy = cy + Math.floor(k/3)*16;
        kilns += `<rect x="${ox-9}" y="${oy-6}" width="18" height="12" fill="#5a3a26" stroke="#e47a3c" stroke-width=".5" opacity=".9"/>`;
      }
      const stacks = row.confidence > 0.85 ? 3 : row.confidence > 0.7 ? 1 : 1;
      for (let s=0;s<stacks;s++){
        const sx = cx + s*14 - 6;
        kilns += `<rect x="${sx-1.5}" y="${cy-22}" width="3" height="14" fill="#1c1612"/>`;
        if (row.confidence > 0.7){
          kilns += `<ellipse cx="${sx+8}" cy="${cy-26}" rx="22" ry="6" fill="#a79b8c" opacity=".22"/>`;
          kilns += `<ellipse cx="${sx+18}" cy="${cy-30}" rx="30" ry="7" fill="#a79b8c" opacity=".15"/>`;
        }
      }
    }
    // bbox rect mapped from 800x600 → 400x250
    const [x1,y1,x2,y2] = row.bbox;
    const sx = 400/800, sy = 250/600;
    const bx = x1*sx, by = y1*sy, bw = (x2-x1)*sx, bh = (y2-y1)*sy;
    const corner = `<g stroke="#e47a3c" stroke-width="1.5" fill="none">
      <path d="M ${bx} ${by+10} L ${bx} ${by} L ${bx+10} ${by}"/>
      <path d="M ${bx+bw-10} ${by} L ${bx+bw} ${by} L ${bx+bw} ${by+10}"/>
      <path d="M ${bx} ${by+bh-10} L ${bx} ${by+bh} L ${bx+10} ${by+bh}"/>
      <path d="M ${bx+bw-10} ${by+bh} L ${bx+bw} ${by+bh} L ${bx+bw} ${by+bh-10}"/>
    </g>`;
    svg.innerHTML = `
      <rect width="400" height="250" fill="#0a0a09"/>
      ${blocks}
      ${kilns}
      <rect x="${bx}" y="${by}" width="${bw}" height="${bh}" fill="rgba(228,122,60,.06)" stroke="rgba(228,122,60,.45)" stroke-width=".5" stroke-dasharray="3 3"/>
      ${corner}
      <text x="${bx}" y="${by-5}" fill="#e47a3c" font-family="JetBrains Mono" font-size="9" letter-spacing="1">YOLO · ${(row.confidence*100).toFixed(1)}%</text>
    `;
  }

  // ---- Render alert detail ----
  function renderDetail(row){
    $("d-id").textContent = row.tile_id;
    $("d-gate").textContent = row.triage_decision + " · " + row.transmission_action;

    $("d-crop-label").textContent = row.crop_path ? row.crop_path : "no crop transmitted";
    $("d-crop-meta").textContent = row.crop_written ? "PNG · 256×256 · queue" : "—";
    renderCropSVG(row);

    if (row.payload && row.payload.vlm_reasoning){
      const v = row.payload.vlm_reasoning;
      $("d-summary").textContent = v.visual_summary || "—";
      $("d-reasoning").textContent = v.risk_reasoning || "—";
      $("d-raw").textContent = v.raw_output_excerpt || "—";
      $("d-verdict").textContent = v.reasoner_output_valid ? "VALID · STRUCTURED" : "PARSE FAILED";
      $("d-verdict").className = "verdict" + (v.reasoner_output_valid ? "" : " bad");
    } else {
      $("d-summary").textContent = "LFM not invoked for this tile (gate did not require evidence review).";
      $("d-reasoning").textContent = "Liquid only reasons over crops that crossed the boundary. IGNORE tiles never produce a crop.";
      $("d-raw").textContent = "—";
      $("d-verdict").textContent = "NOT INVOKED";
      $("d-verdict").className = "verdict warn";
    }

    $("d-bbox").textContent = row.bbox ? `[${row.bbox.join(", ")}]` : "—";
    $("d-conf").textContent = row.confidence.toFixed(4);
    $("d-risk").textContent = row.compliance_risk;
    $("d-dmode").textContent = row.detector_mode;
    $("d-dreal").textContent = row.detector_is_real ? "true" : "false";

    $("d-raw-b").textContent = fmtBytes(row.raw_bytes);
    $("d-tx-b").textContent = fmtBytes(row.transmitted_bytes);
    $("d-saved-b").textContent = fmtBytes(Math.max(0, (row.raw_bytes||0) - (row.transmitted_bytes||0)));
    $("d-crop-w").textContent = row.crop_written ? "true" : "false";
    $("d-full-w").textContent = row.full_tile_written ? "true" : "false";

    if (row.payload){
      $("d-json").innerHTML = jsonHighlight(row.payload);
    } else {
      $("d-json").textContent = "// IGNORE tile — no payload crossed the boundary.\n// Telemetry-only event recorded in transmission_queue/telemetry.jsonl";
    }
  }

  // ---- Tree ----
  function buildTree(){
    const a = D.artifacts;
    const lines = [];
    lines.push(`<span class="dir">${a.queue_dir}</span>`);
    a.payload_files.forEach(f => lines.push(`  <span class="file">${f}</span>  <span class="dim"># JSON alert</span>`));
    lines.push(`  <span class="dir">crops/</span>`);
    a.crop_files.forEach(f => lines.push(`    <span class="file">${f}</span>  <span class="dim"># bbox crop · evidence</span>`));
    lines.push(`  <span class="dir">full_tiles/</span>`);
    if (a.full_tile_files.length){
      a.full_tile_files.forEach(f => lines.push(`    <span class="new">${f}</span>  <span class="dim"># FULL_DOWNLINK escalation</span>`));
    } else {
      lines.push(`    <span class="dim">(empty unless FULL_DOWNLINK)</span>`);
    }
    a.telemetry_files.forEach(f => lines.push(`  <span class="file">${f}</span>  <span class="dim"># every tile · including IGNORE</span>`));
    $("treeView").innerHTML = lines.join("\n");
  }

  // ---- Top metrics ----
  function fillMetrics(){
    const m = D.metrics, c = D.counts, g = D.gates;
    $("m-saved-pct").textContent = m.bandwidth_saved_percent.toFixed(1) + "%";
    $("m-saved-bytes").textContent = fmtBytes(m.bytes_saved) + " saved";
    $("m-ratio").textContent = m.compression_ratio.toFixed(2) + "×";
    $("m-tiles").textContent = m.tiles_processed;
    $("m-alerts").textContent = c.detections;

    $("m-ignored").textContent = c.ignored_tiles;
    $("m-raw").textContent = fmtBytes(m.raw_bytes_processed);
    $("m-tx").textContent = fmtBytes(m.downlinked_bytes);
    $("m-crops").textContent = c.crops_generated;
    $("m-full").textContent = `${c.full_tiles_generated}/${c.full_downlinks}`;

    $("g-ignore").textContent = g.IGNORE;
    $("g-json").textContent = g.JSON_ALERT_ONLY;
    $("g-crop").textContent = g.CROP_OR_REVIEW;
    $("g-full").textContent = g.FULL_DOWNLINK;

    // Proof status
    const t = D.status.truth_fields, r = t.vlm_reasoning;
    $("ps-detector_mode").textContent = t.detector_mode;
    $("ps-detector_is_real").textContent = t.detector_is_real ? "true" : "false";
    $("ps-simulated").textContent = t.simulated ? "true" : "false";
    $("ps-fallback_used").textContent = t.fallback_used ? "true" : "false";
    $("ps-reasoner_mode").textContent = r.reasoner_mode;
    $("ps-reasoner_is_real").textContent = r.reasoner_is_real ? "true" : "false";
    $("ps-reasoner_output_valid").textContent = r.reasoner_output_valid ? "true" : "false";
    $("ps-reasoned_over").textContent = r.reasoned_over;
    $("ps-model_name").textContent = r.model_name;
    $("ps-queue_path").textContent = D.artifacts.queue_dir;
    $("ps-payload_files").textContent = D.artifacts.payload_files.length;
    const tEl = $("ps-telemetry");
    if (D.artifacts.telemetry_files.length){
      tEl.textContent = "present";
      tEl.classList.add("good");
    }
  }

  function loadDashboard(){
    fillMetrics();
    buildTileTable();
    buildTree();
    document.body.setAttribute("data-loaded","true");
  }

  // ---- Copy buttons ----
  document.querySelectorAll(".copy-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-copy");
      const el = $(id);
      if (!el) return;
      navigator.clipboard.writeText(el.innerText).then(() => {
        btn.classList.add("copied");
        const old = btn.textContent;
        btn.textContent = "copied";
        setTimeout(()=>{ btn.classList.remove("copied"); btn.textContent = old; }, 1400);
      });
    });
  });
})();

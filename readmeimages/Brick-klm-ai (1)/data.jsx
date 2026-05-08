// KilnWatch website data — derived from real artifacts in transmission_queue/

const ALERTS = [
  {
    id: "T_120",
    short: "T_120",
    bbox: [492.896, 299.588, 503.817, 310.079],
    conf: 0.5175,
    orig: 95491,
    tx: 2169,
    detections: 17,
    risk: "medium",
    decision: "CROP_OR_REVIEW",
    inferenceMs: 14.967,
    visual: "The crop appears to be a brick kiln based on rectangular kiln-like forms, fired-clay color, and industrial yard texture.",
    riskReasoning: "The local Liquid output parsed as structured JSON for this crop; visual quality remains limited, so human review is still needed.",
    confidenceNote: "Only this crop parsed as valid structured Liquid JSON in the local probe.",
    humanReviewNeeded: true,
    reasonerOutputValid: true,
  },
  {
    id: "A_84",
    short: "A_84",
    bbox: [49.207, 569.618, 62.267, 580.958],
    conf: 0.4791,
    orig: 110249,
    tx: 2507,
    detections: 2,
    risk: "medium",
    decision: "CROP_OR_REVIEW",
    inferenceMs: 20.319,
    visual: "The image is blurry and lacks clear details, making it difficult to identify specific features or objects.",
    riskReasoning: "The lack of clarity and detail makes it challenging to assess the detector's functionality or identify potential issues.",
    confidenceNote: "The confidence in the assessment is low due to the blurriness of the image.",
    humanReviewNeeded: true,
    reasonerOutputValid: false,
  },
  {
    id: "T_50",
    short: "T_50",
    bbox: [459.893, 549.245, 469.547, 558.879],
    conf: 0.4550,
    orig: 82184,
    tx: 2318,
    detections: 1,
    risk: "medium",
    decision: "CROP_OR_REVIEW",
    inferenceMs: 9.561,
    visual: "The image is a blurred and pixelated representation of a brick kiln detector, likely used for industrial applications. The image lacks clear details and is not distinguishable.",
    riskReasoning: "The image is too blurred and pixelated to accurately identify the object or its function. It is not possible to determine if it is a detector or any other type of equipment.",
    confidenceNote: "Image quality is not a reliable source for identification.",
    humanReviewNeeded: true,
    reasonerOutputValid: false,
  },
  {
    id: "A_103",
    short: "A_103",
    bbox: [42.167, 215.603, 53.963, 225.835],
    conf: 0.4084,
    orig: 116884,
    tx: 2403,
    detections: 3,
    risk: "medium",
    decision: "CROP_OR_REVIEW",
    inferenceMs: 28.101,
    visual: "The image is blurry and lacks clear details, making it difficult to identify specific features of the brick-kiln detector.",
    riskReasoning: "The lack of clarity prevents accurate assessment of the detector's functionality and safety.",
    confidenceNote: "The image quality is insufficient for a definitive assessment.",
    humanReviewNeeded: true,
    reasonerOutputValid: false,
  },
  {
    id: "UP_744",
    short: "UP_744",
    bbox: [560.487, 291.91, 570.571, 300.251],
    conf: 0.2668,
    orig: 86168,
    tx: 2348,
    detections: 1,
    risk: "medium",
    decision: "CROP_OR_REVIEW",
    inferenceMs: 8.394,
    visual: "The image is blurred and lacks clear details, making it difficult to identify specific features or objects.",
    riskReasoning: "The lack of clarity prevents accurate assessment of the detector's performance or potential hazards.",
    confidenceNote: "The image is too blurry to provide a definitive assessment.",
    humanReviewNeeded: true,
    reasonerOutputValid: false,
  },
];

const DROPPED = [
  { id: "1040",          orig: 61686, ms: 1038.555 },
  { id: "1050",          orig: 56700, ms: 14.589 },
  { id: "1117",          orig: 49387, ms: 10.529 },
  { id: "1120",          orig: 54236, ms: 9.528 },
  { id: "Bangladesh_143",orig: 58511, ms: 19.924 },
  { id: "T_250",         orig: 85026, ms: 20.756 },
  { id: "UP_226",        orig: 95431, ms: 20.336 },
  { id: "UP_875",        orig: 86246, ms: 21.875 },
  { id: "UP2_106",       orig: 70242, ms: 8.705 },
];

// Pass order = telemetry order for cumulative chart
const PASS_ORDER = [
  { id: "1040",          act: "DROP" },
  { id: "1050",          act: "DROP" },
  { id: "1117",          act: "DROP" },
  { id: "1120",          act: "DROP" },
  { id: "A_103",         act: "ALERT" },
  { id: "A_84",          act: "ALERT" },
  { id: "Bangladesh_143",act: "DROP" },
  { id: "T_120",         act: "ALERT" },
  { id: "T_250",         act: "DROP" },
  { id: "T_50",          act: "ALERT" },
  { id: "UP_226",        act: "DROP" },
  { id: "UP_744",        act: "ALERT" },
  { id: "UP_875",        act: "DROP" },
  { id: "UP2_106",       act: "DROP" },
];

const TOTALS = (() => {
  const alertOrig = ALERTS.reduce((s, a) => s + a.orig, 0);
  const alertTx   = ALERTS.reduce((s, a) => s + a.tx, 0);
  const dropOrig  = DROPPED.reduce((s, d) => s + d.orig, 0);
  const rawTotal  = alertOrig + dropOrig;
  const txTotal   = alertTx; // dropped tiles transmit 0
  const saved     = rawTotal - txTotal;
  const pct       = (saved / rawTotal) * 100;
  const ratio     = rawTotal / Math.max(1, txTotal);
  return { rawTotal, txTotal, saved, pct, ratio,
           tilesProcessed: ALERTS.length + DROPPED.length,
           alerts: ALERTS.length, dropped: DROPPED.length };
})();

// Pretty bytes
const fmtBytes = (n) => {
  if (n >= 1024 * 1024) return (n / (1024 * 1024)).toFixed(2) + " MB";
  if (n >= 1024) return (n / 1024).toFixed(1) + " KB";
  return n + " B";
};

// Real JSON payload string for inspection (assembled to mirror file)
const payloadJson = (a) => JSON.stringify({
  action: "TRANSMIT_ALERT",
  bbox: a.bbox,
  byte_accounting: {
    bandwidth_saved_bytes: a.orig - a.tx,
    crop_payload_bytes: a.tx - 1500, // approx
    json_payload_bytes: 1500,
    original_payload_bytes: a.orig,
    transmitted_payload_bytes: a.tx,
  },
  compliance_risk: a.risk,
  confidence: a.conf,
  crop_ref: `transmission_queue/crops/${a.id}_crop.png`,
  detector_is_real: true,
  detector_mode: "yolo",
  detector_version: "yolo_ultralytics:v0.1",
  event: "alert",
  signals: ["yolo_detection:Brick-Kiln", `detections=${a.detections}`],
  simulated: false,
  source_tile_name: `${a.id}.jpg`,
  tile_id: a.id,
  triage: {
    decision: a.decision,
    driven_by: "yolo-only",
    reason: "Kiln detected with medium/high risk; send crop or queue analyst review.",
    risk_band_used: a.risk,
    risk_score_used: 0.55,
  },
  vlm_reasoning: {
    compliance_risk: a.risk,
    confidence_note: a.confidenceNote,
    human_review_needed: a.humanReviewNeeded,
    model_name: "LiquidAI/LFM2.5-VL-450M",
    reasoner_is_real: true,
    reasoner_mode: "liquid-local",
    reasoner_output_valid: a.reasonerOutputValid,
    reasoned_over: "crop",
    crop_path_used: `transmission_queue/crops/${a.id}_crop.png`,
    risk_reasoning: a.riskReasoning,
    visual_summary: a.visual,
  },
}, null, 2);

Object.assign(window, { ALERTS, DROPPED, PASS_ORDER, TOTALS, fmtBytes, payloadJson });

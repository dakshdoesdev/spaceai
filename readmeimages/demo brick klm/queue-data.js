// Mock transmission_queue artifacts - shaped exactly like app.py expects
// (payloads from transmission_queue/*.json + telemetry from telemetry.jsonl)

window.QUEUE_DATA = {
  status: {
    detector_label: "STRICT YOLO REAL",
    truth_fields: {
      detector_mode: "yolo",
      detector_is_real: true,
      simulated: false,
      fallback_used: false,
      vlm_reasoning: {
        reasoner_mode: "liquid-local",
        reasoner_is_real: true,
        reasoner_output_valid: true,
        model_name: "LiquidAI/LFM2-VL-450M",
        reasoned_over: "crop",
        crop_path_used: "transmission_queue/crops/T-2034.png"
      }
    }
  },
  statuses: ["liquid-real"],
  artifacts: {
    queue_dir: "transmission_queue/",
    payload_files: [
      "T-2031.json","T-2034.json","T-2037.json","T-2042.json","T-2049.json"
    ],
    crop_files: [
      "T-2031.png","T-2034.png","T-2037.png","T-2042.png","T-2049.png"
    ],
    full_tile_files: ["T-2049_full.png"],
    telemetry_files: ["telemetry.jsonl"]
  },
  metrics: {
    tiles_processed: 14,
    raw_bytes_processed: 84_410_368,   // ~80.5 MB
    downlinked_bytes: 1_843_400,       // ~1.76 MB
    bytes_saved: 82_566_968,
    bandwidth_saved_percent: 97.8,
    compression_ratio: 45.79
  },
  counts: {
    detections: 5,
    ignored_tiles: 9,
    crops_generated: 5,
    full_tiles_generated: 1,
    full_downlinks: 1
  },
  gates: {
    IGNORE: 9,
    JSON_ALERT_ONLY: 1,
    CROP_OR_REVIEW: 3,
    FULL_DOWNLINK: 1
  },

  rows: [
    // 5 alerts first, then 9 ignores
    {
      tile_id: "T-2031", triage_decision: "JSON_ALERT_ONLY", transmission_action: "json",
      confidence: 0.4128, compliance_risk: "low",
      detector_mode: "yolo", detector_is_real: true,
      reasoner_status: "Liquid emitted valid structured crop reasoning.",
      reasoner_output_valid: true,
      raw_bytes: 6_029_312, transmitted_bytes: 1_842,
      crop_written: false, full_tile_written: false,
      crop_path: null,
      bbox: [412, 388, 478, 451],
      payload: {
        tile_id: "T-2031", capture_ts: "2026-05-09T03:18:42Z",
        triage_decision: "JSON_ALERT_ONLY", transmission_action: "json",
        confidence: 0.4128, compliance_risk: "low",
        bbox: [412, 388, 478, 451], detector_mode: "yolo", detector_is_real: true,
        vlm_reasoning: {
          reasoner_mode: "liquid-local", reasoner_is_real: true,
          reasoner_output_valid: true, model_name: "LiquidAI/LFM2-VL-450M",
          reasoned_over: "crop", crop_path_used: "transmission_queue/crops/T-2031.png",
          visual_summary: "Faint rectangular thermal signature; possible kiln stack but image quality is insufficient to confirm.",
          risk_reasoning: "Low confidence detection, no plume visible, no clustered structures.",
          raw_output_excerpt: "{\"verdict\":\"low_confidence\",\"plume\":false,\"chimneys\":1,\"caveat\":\"image quality is insufficient to confirm\"}"
        }
      }
    },
    {
      tile_id: "T-2034", triage_decision: "CROP_OR_REVIEW", transmission_action: "json+crop",
      confidence: 0.7841, compliance_risk: "medium",
      detector_mode: "yolo", detector_is_real: true,
      reasoner_status: "Liquid emitted valid structured crop reasoning.",
      reasoner_output_valid: true,
      raw_bytes: 6_029_312, transmitted_bytes: 124_388,
      crop_written: true, full_tile_written: false,
      crop_path: "transmission_queue/crops/T-2034.png",
      bbox: [128, 244, 311, 402],
      payload: {
        tile_id: "T-2034", capture_ts: "2026-05-09T03:19:11Z",
        triage_decision: "CROP_OR_REVIEW", transmission_action: "json+crop",
        confidence: 0.7841, compliance_risk: "medium",
        bbox: [128, 244, 311, 402], detector_mode: "yolo", detector_is_real: true,
        vlm_reasoning: {
          reasoner_mode: "liquid-local", reasoner_is_real: true,
          reasoner_output_valid: true, model_name: "LiquidAI/LFM2-VL-450M",
          reasoned_over: "crop", crop_path_used: "transmission_queue/crops/T-2034.png",
          visual_summary: "Rectangular kiln ovens with two tall chimneys; faint plume drift north-east.",
          risk_reasoning: "Visible chimneys and clustered firing structures consistent with active brick kiln.",
          raw_output_excerpt: "{\"verdict\":\"likely_kiln\",\"plume\":true,\"chimneys\":2,\"clustered\":true}"
        }
      }
    },
    {
      tile_id: "T-2037", triage_decision: "CROP_OR_REVIEW", transmission_action: "json+crop",
      confidence: 0.6629, compliance_risk: "medium",
      detector_mode: "yolo", detector_is_real: true,
      reasoner_status: "Liquid emitted valid structured crop reasoning.",
      reasoner_output_valid: true,
      raw_bytes: 6_029_312, transmitted_bytes: 96_104,
      crop_written: true, full_tile_written: false,
      crop_path: "transmission_queue/crops/T-2037.png",
      bbox: [502, 121, 638, 244],
      payload: {
        tile_id: "T-2037", capture_ts: "2026-05-09T03:19:48Z",
        triage_decision: "CROP_OR_REVIEW", transmission_action: "json+crop",
        confidence: 0.6629, compliance_risk: "medium",
        bbox: [502, 121, 638, 244], detector_mode: "yolo", detector_is_real: true,
        vlm_reasoning: {
          reasoner_mode: "liquid-local", reasoner_is_real: true,
          reasoner_output_valid: true, model_name: "LiquidAI/LFM2-VL-450M",
          reasoned_over: "crop", crop_path_used: "transmission_queue/crops/T-2037.png",
          visual_summary: "Single chimney over rectangular firing chamber; surface staining suggests recent fire.",
          risk_reasoning: "One chimney plus firing chamber consistent with small kiln; no plume currently visible.",
          raw_output_excerpt: "{\"verdict\":\"possible_kiln\",\"plume\":false,\"chimneys\":1,\"clustered\":false}"
        }
      }
    },
    {
      tile_id: "T-2042", triage_decision: "CROP_OR_REVIEW", transmission_action: "json+crop",
      confidence: 0.7113, compliance_risk: "medium",
      detector_mode: "yolo", detector_is_real: true,
      reasoner_status: "Liquid emitted valid structured crop reasoning.",
      reasoner_output_valid: true,
      raw_bytes: 6_029_312, transmitted_bytes: 108_512,
      crop_written: true, full_tile_written: false,
      crop_path: "transmission_queue/crops/T-2042.png",
      bbox: [88, 502, 244, 661],
      payload: {
        tile_id: "T-2042", capture_ts: "2026-05-09T03:20:31Z",
        triage_decision: "CROP_OR_REVIEW", transmission_action: "json+crop",
        confidence: 0.7113, compliance_risk: "medium",
        bbox: [88, 502, 244, 661], detector_mode: "yolo", detector_is_real: true,
        vlm_reasoning: {
          reasoner_mode: "liquid-local", reasoner_is_real: true,
          reasoner_output_valid: true, model_name: "LiquidAI/LFM2-VL-450M",
          reasoned_over: "crop", crop_path_used: "transmission_queue/crops/T-2042.png",
          visual_summary: "Two adjacent kiln structures with a single shared stack; image quality moderate.",
          risk_reasoning: "Two firing chambers and one chimney; possible co-located kilns, plume not confirmed.",
          raw_output_excerpt: "{\"verdict\":\"likely_kiln\",\"plume\":false,\"chimneys\":1,\"clustered\":true}"
        }
      }
    },
    {
      tile_id: "T-2049", triage_decision: "FULL_DOWNLINK", transmission_action: "json+crop+full",
      confidence: 0.9214, compliance_risk: "high",
      detector_mode: "yolo", detector_is_real: true,
      reasoner_status: "Liquid emitted valid structured crop reasoning.",
      reasoner_output_valid: true,
      raw_bytes: 6_029_312, transmitted_bytes: 1_512_554,
      crop_written: true, full_tile_written: true,
      crop_path: "transmission_queue/crops/T-2049.png",
      bbox: [201, 88, 612, 488],
      payload: {
        tile_id: "T-2049", capture_ts: "2026-05-09T03:21:06Z",
        triage_decision: "FULL_DOWNLINK", transmission_action: "json+crop+full",
        confidence: 0.9214, compliance_risk: "high",
        bbox: [201, 88, 612, 488], detector_mode: "yolo", detector_is_real: true,
        vlm_reasoning: {
          reasoner_mode: "liquid-local", reasoner_is_real: true,
          reasoner_output_valid: true, model_name: "LiquidAI/LFM2-VL-450M",
          reasoned_over: "crop", crop_path_used: "transmission_queue/crops/T-2049.png",
          visual_summary: "Cluster of six rectangular kiln ovens with three tall chimneys and visible plume drifting south.",
          risk_reasoning: "Multiple firing chambers, multiple chimneys, active plume — high-risk kiln cluster, full tile requested for compliance review.",
          raw_output_excerpt: "{\"verdict\":\"active_kiln_cluster\",\"plume\":true,\"chimneys\":3,\"clustered\":true,\"ovens\":6}"
        }
      }
    },

    // ignores
    ...["T-2030","T-2032","T-2033","T-2035","T-2036","T-2038","T-2040","T-2046","T-2050"].map((id, i) => ({
      tile_id: id, triage_decision: "IGNORE", transmission_action: "telemetry",
      confidence: [0.0421,0.0612,0.0188,0.0901,0.0334,0.0712,0.0455,0.0298,0.0816][i],
      compliance_risk: "none",
      detector_mode: "yolo", detector_is_real: true,
      reasoner_status: "LFM not invoked (gate did not require evidence review).",
      reasoner_output_valid: null,
      raw_bytes: 6_029_312, transmitted_bytes: 412,
      crop_written: false, full_tile_written: false,
      crop_path: null,
      bbox: null,
      payload: null
    }))
  ]
};

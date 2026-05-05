# KilnWatch Dataset Schema

## Purpose

The dataset supports tile-level brick kiln detection and compliance triage from locally saved Sentinel-2 tiles. It is deliberately compact for hand-labeling 50-200 tiles and for later use in VLM prompts or fine-tuning.

## Required Row Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `tile_id` | string | yes | Stable unique ID for the tile. Use lowercase letters, numbers, `_`, or `-`. |
| `image_path` | string | yes | Path relative to `datasets/kilnwatch/`, for example `images/train/kw_train_0001.png`. |
| `split` | string enum | yes | One of `train`, `dev`, `test`, or `seed`. |
| `label` | object | yes | Annotation object using the fixed MVP schema below. |
| `location_hint` | string | no | Human-readable region, district, grid ID, bbox ID, or blank if unknown. |
| `source` | string | no | Data source note, for example `Sentinel-2 local tile`. |
| `notes` | string | no | Short free-text note for ambiguous cases. |

## Label Object

```json
{
  "kiln_detected": true,
  "kiln_count_estimate": "1-3",
  "activity_signal": "active",
  "near_settlement": true,
  "compliance_risk": "high",
  "confidence": 0.82
}
```

| Label Field | Allowed Values | Meaning |
| --- | --- | --- |
| `kiln_detected` | `true`, `false` | Whether the tile contains likely brick kiln evidence. |
| `kiln_count_estimate` | `"0"`, `"1-3"`, `"4-10"`, `"10+"` | Coarse count bucket. Use `"0"` when `kiln_detected` is false. |
| `activity_signal` | `"active"`, `"dormant"`, `"unclear"` | Whether the tile suggests current/recent operation. |
| `near_settlement` | `true`, `false` | Whether the suspected kiln area is near visible homes, dense settlement, schools, roads, or village edges. |
| `compliance_risk` | `"low"`, `"medium"`, `"high"` | Triage priority for review. This is not a legal finding. |
| `confidence` | number from `0` to `1` | Labeler confidence in the whole label. |

## Consistency Rules

- If `kiln_detected` is `false`, `kiln_count_estimate` must be `"0"`.
- If `kiln_count_estimate` is `"0"`, `kiln_detected` must be `false`.
- If `kiln_detected` is `false`, `activity_signal` must be `"unclear"` unless there is a documented reason in `notes`.
- `confidence` must be a JSON number, not a string, from `0` to `1` inclusive.
- `compliance_risk` should usually be `low` for negative samples.
- `high` risk should require likely kiln evidence plus at least one escalation signal: active appearance, multiple kiln-like features, or near settlement.
- Do not add kiln type classification fields for the MVP.

## VLM Prompt Compatibility

Rows can be converted directly into prompt examples:

- Input: `image_path` plus a short instruction asking for the label JSON only.
- Target: the `label` object.

The full row keeps metadata for dataset management, while `label` remains the stable model target.

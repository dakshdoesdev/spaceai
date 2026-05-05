# KilnWatch Labeling Guidelines

## Labeling Goal

Assign a compact triage label to each saved satellite tile. Label what is visible in the tile only. Do not classify kiln type. Do not use paid APIs. A labeler can use local image viewers, QGIS, browser-based local files, or free GIS tools to inspect tiles.

## Recommended Manual Workflow

1. Put new tiles in `datasets/kilnwatch/images/unlabeled/`.
2. Open each tile locally using an image viewer or QGIS.
3. Compare against known positive examples when available.
4. Add one JSON object per tile to the target split file under `datasets/kilnwatch/labels/`.
5. Include uncertain negatives and confusing industrial/non-kiln areas as negative samples.
6. Run the validator after each labeling batch.

Use a consistent review order: visible kiln evidence, count bucket, activity signal, settlement proximity, risk, confidence.

## Field Guidance

### `kiln_detected`

Use `true` when the tile shows likely brick kiln evidence such as kiln-like industrial yards, repeated oval/rectangular firing structures, chimney-like points in higher-resolution references, brick stockpiles, or clustered kiln-yard patterns.

Use `false` for rural land, farms, empty fields, ordinary settlements, roads, water bodies, and industrial areas where kiln evidence is not visible.

If unsure, prefer `false` with lower confidence unless the tile has multiple kiln-like cues.

### `kiln_count_estimate`

Use coarse buckets only:

- `"0"`: no likely kiln.
- `"1-3"`: one to three likely kilns or kiln yards.
- `"4-10"`: visible cluster of several likely kilns.
- `"10+"`: dense kiln belt or large cluster.

Do not spend time counting exact units. The bucket should support triage, not inventory-grade mapping.

### `activity_signal`

Use `"active"` when there are visible signs of operation or recent use, such as smoke/plume cues, darkened firing areas, fresh-looking stockpiles, bright exposed clay/brick yards, or strong industrial activity around the suspected kiln.

Use `"dormant"` when kiln-like structures are visible but activity appears absent, overgrown, faded, abandoned, or seasonally inactive.

Use `"unclear"` when image quality, clouds, resolution, seasonality, or weak visual evidence prevents an activity call. Negative samples should normally use `"unclear"`.

### `near_settlement`

Use `true` when the suspected kiln or industrial yard is visibly close to housing, village edges, dense settlement, schools/large public buildings, major roads with settlement, or mixed residential-agricultural areas.

Use `false` when the tile is remote, agricultural, empty, or the suspected feature is isolated from visible settlement.

If no kiln is detected, still label visible settlement proximity around the tile only when useful for negative coverage. Otherwise use `false`.

### `compliance_risk`

This is a review-priority label, not a legal conclusion.

- `"low"`: no kiln detected, weak/unclear evidence, or likely kiln with no active signal and no settlement concern.
- `"medium"`: likely kiln with unclear/dormant activity, or one risk factor such as settlement proximity or multiple possible kilns.
- `"high"`: likely kiln with active signal near settlement, or a large/multiple-kiln cluster that should be reviewed first.

Avoid `high` when `kiln_detected` is `false`.

### `confidence`

Use a number from `0` to `1`:

- `0.90-1.00`: clear label, strong visual evidence.
- `0.70-0.89`: likely label, minor uncertainty.
- `0.50-0.69`: ambiguous but still labelable.
- `<0.50`: weak label; keep only if useful as a hard example and explain in `notes`.

Confidence applies to the whole label, not just kiln presence.

## Negative Sample Checklist

Include negatives that could confuse a model:

- Farms and field boundaries.
- Bare soil or brick-colored land.
- Rural villages without kiln yards.
- Industrial buildings without kiln patterns.
- Roads, rail yards, warehouses, and construction sites.
- Cloudy/hazy tiles where no kiln can be confirmed.

## Quality Rules

- Keep row labels internally consistent.
- Do not invent details outside the visible tile.
- Do not add kiln type labels.
- Use `notes` for ambiguity, cloud cover, image artifacts, or suspected false positives.
- Revisit low-confidence positives during dev/test curation.

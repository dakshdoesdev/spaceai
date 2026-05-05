from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from kilnwatch.triage import TriageDecision, compute_triage


DATASET_ROOT = Path("datasets/kilnwatch")
IMAGE_DIRS = [
    DATASET_ROOT / "images" / "dev",
    DATASET_ROOT / "images" / "train",
    DATASET_ROOT / "images" / "test",
    DATASET_ROOT / "images" / "unlabeled",
]
LABEL_DIR = DATASET_ROOT / "labels"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".svg"}


st.set_page_config(page_title="KilnWatch", layout="wide")


def main() -> None:
    st.title("KilnWatch")
    st.caption("On-board brick kiln compliance triage from satellite imagery")

    image_paths = discover_images()
    if not image_paths:
        st.error("No local image tiles found in datasets/kilnwatch/images.")
        st.stop()

    with st.sidebar:
        st.header("Demo tile")
        selected_image = st.selectbox(
            "Local tile",
            image_paths,
            format_func=lambda path: str(path.relative_to(DATASET_ROOT)),
        )
        raw_tile_mb = st.slider("Raw tile downlink size (MB)", 1.0, 50.0, 12.0, 0.5)
        crop_mb = st.slider("Review crop size (MB)", 0.1, 10.0, 1.2, 0.1)
        json_alert_kb = st.slider("JSON alert size (KB)", 0.5, 25.0, 4.0, 0.5)

    prediction = load_prediction(selected_image)
    prediction["bandwidth_estimate"] = {
        "raw_tile_mb": raw_tile_mb,
        "crop_mb": crop_mb,
        "json_alert_kb": json_alert_kb,
    }
    result = compute_triage(prediction)

    left, right = st.columns([1.15, 0.85], gap="large")
    with left:
        st.subheader("Satellite Tile")
        st.image(str(selected_image), use_container_width=True)
        st.caption(str(selected_image))

    with right:
        decision_badge(result.decision)
        metric_cols = st.columns(3)
        metric_cols[0].metric("Kiln confidence", f"{result.confidence:.0%}")
        metric_cols[1].metric("Compliance risk", f"{result.risk_score:.0%}")
        metric_cols[2].metric("Bandwidth saved", f"{result.bandwidth.savings_percent:.1f}%")

        st.subheader("Compliance Alert")
        st.info(result.alert)

        st.subheader("Downlink Plan")
        st.write(result.reason)
        st.progress(min(result.bandwidth.savings_percent / 100, 1.0))
        st.caption(
            f"Chosen payload: {result.bandwidth.chosen_payload_mb:.3f} MB vs "
            f"{result.bandwidth.raw_tile_mb:.1f} MB raw tile."
        )

    st.subheader("Kiln Detection / Risk JSON")
    st.json(prediction, expanded=True)


def discover_images() -> list[Path]:
    paths: list[Path] = []
    for image_dir in IMAGE_DIRS:
        if image_dir.exists():
            paths.extend(path for path in image_dir.rglob("*") if path.suffix.lower() in IMAGE_EXTENSIONS)
    return sorted(paths)


def load_prediction(image_path: Path) -> dict:
    candidates = [
        LABEL_DIR / f"{image_path.stem}.json",
        image_path.with_suffix(".json"),
    ]
    for candidate in candidates:
        if candidate.exists():
            with candidate.open("r", encoding="utf-8") as handle:
                return json.load(handle)

    return {
        "tile_id": image_path.stem,
        "image_path": str(image_path),
        "kiln_detected": False,
        "confidence": 0.0,
        "compliance_risk_score": 0.0,
        "detections": [],
        "risk_factors": [],
        "notes": "No matching prediction JSON found; defaulting to IGNORE.",
    }


def decision_badge(decision: TriageDecision) -> None:
    colors = {
        TriageDecision.IGNORE: "#6b7280",
        TriageDecision.JSON_ALERT_ONLY: "#2563eb",
        TriageDecision.CROP_OR_REVIEW: "#d97706",
        TriageDecision.FULL_DOWNLINK: "#dc2626",
    }
    st.markdown(
        f"""
        <div style="padding: 0.75rem 1rem; border-radius: 8px; background: {colors[decision]}; color: white;">
            <div style="font-size: 0.8rem; opacity: 0.85;">TRIAGE DECISION</div>
            <div style="font-size: 1.4rem; font-weight: 700;">{decision}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()

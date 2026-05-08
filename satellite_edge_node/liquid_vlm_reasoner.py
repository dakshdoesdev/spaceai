"""Optional Liquid LFM crop-level reasoner for detector candidates."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

from .baseline_detector import DetectionResult


MODEL_NAME = "LiquidAI/LFM2.5-VL-450M"


class LiquidReasonerError(RuntimeError):
    pass


class LiquidReasonerUnavailable(LiquidReasonerError):
    pass


@dataclass(frozen=True)
class VlmReasoning:
    visual_summary: str
    risk_reasoning: str
    compliance_risk: str
    human_review_needed: bool
    confidence_note: str
    reasoner_mode: str
    reasoner_is_real: bool
    model_name: str

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)


class Reasoner(Protocol):
    mode: str

    def reason(
        self,
        *,
        image_path: Path,
        detection: DetectionResult,
        crop_path: Path | None = None,
    ) -> VlmReasoning:
        ...


@dataclass(frozen=True)
class LiquidMockReasoner:
    mode: str = "liquid-mock"

    def reason(
        self,
        *,
        image_path: Path,
        detection: DetectionResult,
        crop_path: Path | None = None,
    ) -> VlmReasoning:
        evidence_path = crop_path or image_path
        review_needed = detection.compliance_risk in {"medium", "high"}
        return VlmReasoning(
            visual_summary=(
                f"Simulated Liquid review for detector candidate `{detection.tile_id}` "
                f"using downlinked evidence `{evidence_path.name}`."
            ),
            risk_reasoning=(
                "Mock reasoner mirrors the detector candidate metadata for demo flow only; "
                "it is not a real Liquid model inference."
            ),
            compliance_risk=detection.compliance_risk,
            human_review_needed=review_needed,
            confidence_note=(
                f"Detector confidence was {detection.confidence:.2f}; Liquid reasoning is simulated."
            ),
            reasoner_mode=self.mode,
            reasoner_is_real=False,
            model_name=f"{MODEL_NAME} (mock)",
        )


class LiquidLocalReasoner:
    mode = "liquid-local"

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        try:
            from transformers import AutoModelForImageTextToText, AutoProcessor
        except ImportError as exc:
            raise LiquidReasonerUnavailable(
                "Liquid local reasoner requires `transformers` with "
                "AutoModelForImageTextToText support. Install a compatible local "
                "Transformers build before using --reasoner liquid-local."
            ) from exc

        try:
            self.processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
            self.model = AutoModelForImageTextToText.from_pretrained(model_name, trust_remote_code=True)
        except Exception as exc:
            raise LiquidReasonerUnavailable(
                f"Liquid local model could not be loaded from {model_name}: {exc}"
            ) from exc

    def reason(
        self,
        *,
        image_path: Path,
        detection: DetectionResult,
        crop_path: Path | None = None,
    ) -> VlmReasoning:
        evidence_path = crop_path or image_path
        try:
            from PIL import Image
        except ImportError as exc:
            raise LiquidReasonerUnavailable(
                "Liquid local reasoner requires Pillow to open crop/tile imagery."
            ) from exc

        # System+user split aligns with the Liquid cookbook satellite-vlm pattern
        # (examples/car-maker-identification/src/.../inference.py) and the VRSBench
        # VQA training format (examples/satellite-vlm/prepare_vrsbench.py).
        system_prompt = (
            "You are an Earth-observation analyst reviewing a small crop from a "
            "satellite tile. An onboard YOLO detector flagged this region as a "
            "possible brick kiln. Assess the crop visually and reason about whether "
            "it is credibly a brick-kiln structure (look for: rectangular kiln "
            "ovens, tall chimneys, fired-clay color, repeated rectangular firing "
            "lots, surrounding spoil heaps). Be specific about visual features. "
            "Do not invent regulatory certainty or geographic context that is not "
            "visible in the crop."
        )
        confidence_pct = int(round(max(0.0, min(1.0, detection.confidence)) * 100))
        signals = ", ".join(detection.signals[:4]) or "no extra signals"
        user_prompt = (
            f"Detector confidence: {confidence_pct}%. Detector signals: {signals}. "
            "Return ONLY a single JSON object with these exact keys, no prose:\n"
            "{\n"
            '  "credible_kiln":         true|false,\n'
            '  "compliance_risk":       "low"|"medium"|"high",\n'
            '  "human_review_needed":   true|false,\n'
            '  "visual_summary":        "<one sentence describing the crop>",\n'
            '  "risk_reasoning":        "<one sentence: why this is or is not a kiln>",\n'
            '  "confidence_note":       "<caveats about image quality or scale>"\n'
            "}"
        )
        try:
            with Image.open(evidence_path) as image:
                conversation = [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "image": image.convert("RGB")},
                            {"type": "text", "text": user_prompt},
                        ],
                    },
                ]
                inputs = self.processor.apply_chat_template(
                    conversation,
                    add_generation_prompt=True,
                    return_tensors="pt",
                    return_dict=True,
                    tokenize=True,
                )
                if hasattr(self.model, "device"):
                    inputs = inputs.to(self.model.device)
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=256,
                    do_sample=False,  # deterministic for demo + JSON reliability
                )
                decoded = self.processor.batch_decode(outputs, skip_special_tokens=True)[0]
        except Exception as exc:
            raise LiquidReasonerError(f"Liquid local inference failed for {evidence_path}: {exc}") from exc

        return _parse_local_response(
            decoded,
            detection=detection,
            reasoner_mode=self.mode,
            model_name=self.model_name,
        )


def build_reasoner(mode: str = "disabled") -> Reasoner | None:
    normalized = mode.lower()
    if normalized == "disabled":
        return None
    if normalized == "liquid-mock":
        return LiquidMockReasoner()
    if normalized == "liquid-local":
        return LiquidLocalReasoner()
    raise ValueError("reasoner mode must be 'disabled', 'liquid-mock', or 'liquid-local'")


def _parse_local_response(
    text: str,
    *,
    detection: DetectionResult,
    reasoner_mode: str,
    model_name: str,
) -> VlmReasoning:
    parsed = _extract_json_object(text)
    return VlmReasoning(
        visual_summary=str(parsed.get("visual_summary") or text.strip()[:500]),
        risk_reasoning=str(parsed.get("risk_reasoning") or "Liquid local model returned unstructured reasoning."),
        compliance_risk=_risk_value(parsed.get("compliance_risk"), detection.compliance_risk),
        human_review_needed=_bool_value(
            parsed.get("human_review_needed"),
            default=detection.compliance_risk in {"medium", "high"},
        ),
        confidence_note=str(
            parsed.get("confidence_note")
            or f"Detector confidence was {detection.confidence:.2f}; Liquid local output was not fine-tuned."
        ),
        reasoner_mode=reasoner_mode,
        reasoner_is_real=True,
        model_name=model_name,
    )


def _extract_json_object(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _risk_value(value: Any, default: str) -> str:
    risk = str(value or default).lower()
    return risk if risk in {"low", "medium", "high"} else default


def _bool_value(value: Any, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    return default

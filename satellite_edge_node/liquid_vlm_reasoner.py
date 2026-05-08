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
    reasoner_output_valid: bool
    model_name: str
    reasoned_over: str
    crop_path_used: str | None
    raw_output_excerpt: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        if payload.get("raw_output_excerpt") is None:
            payload.pop("raw_output_excerpt", None)
        if self.reasoned_over == "source_tile":
            payload["source_tile_reasoning"] = True
        return payload


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
        reasoned_over = "crop" if crop_path else "source_tile"
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
            reasoner_output_valid=True,
            model_name=f"{MODEL_NAME} (mock)",
            reasoned_over=reasoned_over,
            crop_path_used=str(crop_path) if crop_path else None,
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
        reasoned_over = "crop" if crop_path else "source_tile"
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
                    max_new_tokens=512,
                    do_sample=False,  # deterministic for demo + JSON reliability
                )
                decoded = _decode_new_tokens(self.processor, outputs, inputs)
        except Exception as exc:
            raise LiquidReasonerError(f"Liquid local inference failed for {evidence_path}: {exc}") from exc

        return _parse_local_response(
            decoded,
            detection=detection,
            reasoner_mode=self.mode,
            model_name=self.model_name,
            reasoned_over=reasoned_over,
            crop_path_used=crop_path,
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
    reasoned_over: str,
    crop_path_used: Path | None,
) -> VlmReasoning:
    parsed = _extract_json_object(text)
    if not _has_expected_reasoning_json(parsed):
        return VlmReasoning(
            visual_summary="",
            risk_reasoning="Liquid call succeeded, structured parse failed.",
            compliance_risk=detection.compliance_risk,
            human_review_needed=detection.compliance_risk in {"medium", "high"},
            confidence_note=(
                "The local Liquid model ran, but its output was not valid "
                "structured crop-reasoning JSON."
            ),
            reasoner_mode=reasoner_mode,
            reasoner_is_real=True,
            reasoner_output_valid=False,
            model_name=model_name,
            reasoned_over=reasoned_over,
            crop_path_used=str(crop_path_used) if crop_path_used else None,
            raw_output_excerpt=_raw_output_excerpt(text),
        )

    return VlmReasoning(
        visual_summary=str(parsed["visual_summary"]),
        risk_reasoning=str(parsed["risk_reasoning"]),
        compliance_risk=_risk_value(parsed.get("compliance_risk"), detection.compliance_risk),
        human_review_needed=parsed["human_review_needed"],
        confidence_note=str(parsed["confidence_note"]),
        reasoner_mode=reasoner_mode,
        reasoner_is_real=True,
        reasoner_output_valid=True,
        model_name=model_name,
        reasoned_over=reasoned_over,
        crop_path_used=str(crop_path_used) if crop_path_used else None,
    )


def _decode_new_tokens(processor: Any, outputs: Any, inputs: Any) -> str:
    input_ids = inputs["input_ids"]
    input_length = input_ids.shape[-1] if hasattr(input_ids, "shape") else len(input_ids[0])
    generated_only = _slice_generated_tokens(outputs, input_length)
    decoded = processor.batch_decode(
        generated_only,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )
    return decoded[0] if decoded else ""


def _slice_generated_tokens(outputs: Any, input_length: int) -> Any:
    try:
        return outputs[:, input_length:]
    except (TypeError, IndexError):
        return [sequence[input_length:] for sequence in outputs]


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


def _has_expected_reasoning_json(parsed: dict[str, Any]) -> bool:
    required_strings = ("visual_summary", "risk_reasoning", "confidence_note")
    if not all(isinstance(parsed.get(key), str) and parsed[key].strip() for key in required_strings):
        return False
    if _risk_value(parsed.get("compliance_risk"), "") not in {"low", "medium", "high"}:
        return False
    if not isinstance(parsed.get("human_review_needed"), bool):
        return False
    if not isinstance(parsed.get("credible_kiln"), bool):
        return False
    return True


def _raw_output_excerpt(text: str, *, max_chars: int = 500) -> str:
    compact = " ".join(text.strip().split())
    return compact[:max_chars]


def _risk_value(value: Any, default: str) -> str:
    risk = str(value or default).lower()
    return risk if risk in {"low", "medium", "high"} else default

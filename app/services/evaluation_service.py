"""
app/services/evaluation_service.py
"""
import os
import logging
from dataclasses import dataclass, field, asdict
from typing import Any

from flask import current_app

from app.services.gemma_service import GemmaService
from app.services.image_service import ImageService
from app.utils.validators import FileValidator
from app.utils.parsers import ResponseParser
from app.utils.security import InputSanitizer

logger = logging.getLogger(__name__)

_gemma  = GemmaService()
_image  = ImageService()
_valid  = FileValidator()
_parser = ResponseParser()
_sanit  = InputSanitizer()

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "evaluation_prompt.txt")
_prompt_cache: str = ""


@dataclass
class EvaluationResult:
    success: bool
    subject: str = ""
    question_detected: str = ""
    score: int = 0
    max_score: int = 10
    grade: str = "N/A"
    hindi_feedback: str = ""
    english_feedback: str = ""
    mistakes: list = field(default_factory=list)
    correct_points: list = field(default_factory=list)
    improvement_tips: list = field(default_factory=list)
    model_answer_hint: str = ""
    confidence: str = "low"
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_prompt() -> str:
    global _prompt_cache
    if not _prompt_cache:
        with open(PROMPT_PATH, encoding="utf-8") as f:
            _prompt_cache = f.read().strip()
    return _prompt_cache


def evaluate_submission(image_file, question: str, subject: str) -> EvaluationResult:

    # Step 1 — Validate file
    try:
        raw_bytes = _valid.validate_image(image_file)
    except ValueError as e:
        logger.error("STEP1 validation failed: %s", e)
        return EvaluationResult(success=False, error=str(e))

    # Step 2 — Sanitize inputs
    safe_q = _sanit.clean(question or "")
    safe_s = _sanit.clean(subject or "")

    # Step 3 — Preprocess image
    use_pillow = current_app.config.get("USE_PILLOW", True)
    try:
        image_b64, mime = _image.process(raw_bytes, use_pillow=use_pillow)
        logger.info("STEP3 image processed: mime=%s b64_len=%d", mime, len(image_b64))
    except ValueError as e:
        logger.error("STEP3 image failed: %s", e)
        return EvaluationResult(success=False, error=str(e))

    # Step 4 — Build prompts
    system_prompt = _load_prompt()
    user_prompt   = _build_user_prompt(safe_q, safe_s)
    logger.info("STEP4 prompts ready")

    # Step 5 — Call Gemma
    try:
        raw_response = _gemma.generate(image_b64, mime, system_prompt, user_prompt)
        logger.info("STEP5 gemma response len=%d: %s", len(raw_response), raw_response[:200])
    except RuntimeError as e:
        logger.error("STEP5 gemma failed: %s", e)
        return EvaluationResult(success=False, error=str(e))

    # Step 6 — Parse
    parsed = _parser.parse(raw_response)
    logger.info("STEP6 parsed result: %s", parsed)

    if "error" in parsed:
        logger.error("STEP6 parse failed. Raw was: %s", raw_response[:500])
        return EvaluationResult(
            success=False,
            error="AI response could not be parsed. Try again."
        )

    # Step 7 — Return result
    return EvaluationResult(
        success=True,
        subject=str(parsed.get("subject", "")),
        question_detected=str(parsed.get("question_detected", "")),
        score=int(parsed.get("score", 0)),
        max_score=int(parsed.get("max_score", 10)),
        grade=str(parsed.get("grade", "N/A")),
        hindi_feedback=str(parsed.get("hindi_feedback", "")),
        english_feedback=str(parsed.get("english_feedback", "")),
        mistakes=list(parsed.get("mistakes", [])),
        correct_points=list(parsed.get("correct_points", [])),
        improvement_tips=list(parsed.get("improvement_tips", [])),
        model_answer_hint=str(parsed.get("model_answer_hint", "")),
        confidence=str(parsed.get("confidence", "medium")),
    )


def _build_user_prompt(question: str, subject: str) -> str:
    parts = []
    if subject:
        parts.append(f"Subject: {subject}")
    if question:
        parts.append(f"Question: {question}")
    parts.append("Evaluate the handwritten answer in the image.")
    return "\n".join(parts)
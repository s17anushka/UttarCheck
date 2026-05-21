
"""
app/utils/parsers.py

Stable Gemma/Gemini response parser
Handles:
- ```json fenced blocks
- direct JSON
- prose + JSON
- malformed commas
- bullet-style responses
"""

import re
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

DEFAULTS = {
    "subject": "Unknown",
    "question_detected": "",
    "score": 0,
    "max_score": 10,
    "grade": "N/A",
    "hindi_feedback": "मूल्यांकन पूरा नहीं हो सका।",
    "english_feedback": "Evaluation could not be completed.",
    "mistakes": [],
    "correct_points": [],
    "improvement_tips": ["Please upload a clearer photo."],
    "model_answer_hint": "",
    "confidence": "low",
}


class ResponseParser:

    def parse(self, raw: str) -> dict[str, Any]:

        if not raw or not raw.strip():
            return {
                **DEFAULTS,
                "error": "Empty model response"
            }

        logger.info(
            "Parsing response len=%d",
            len(raw)
        )

        logger.info("RAW RESPONSE:\n%s", raw[:2000])

        # =====================================================
        # Strategy 1: ```json fenced block
        # =====================================================

        fenced = re.search(
            r'```(?:json)?\s*(\{[\s\S]*?\})\s*```',
            raw,
            re.IGNORECASE
        )

        if fenced:

            result = self._try_json(
                fenced.group(1)
            )

            if result:
                logger.info(
                    "Parsed via fenced JSON"
                )

                return {
                    **DEFAULTS,
                    **result
                }

        # =====================================================
        # Strategy 2: direct JSON
        # =====================================================

        result = self._try_json(raw)

        if result:

            logger.info(
                "Parsed via direct JSON"
            )

            return {
                **DEFAULTS,
                **result
            }

        # =====================================================
        # Strategy 3: largest JSON object
        # =====================================================

        matches = re.findall(
            r'\{[\s\S]*\}',
            raw
        )

        for block in matches:

            if '"score"' not in block:
                continue

            result = self._try_json(block)

            if result:

                logger.info(
                    "Parsed via largest JSON object"
                )

                return {
                    **DEFAULTS,
                    **result
                }

        # =====================================================
        # Strategy 4: bullet extraction
        # =====================================================

        result = self._extract_from_bullets(raw)

        if result:

            logger.info(
                "Parsed via bullet extraction"
            )

            return {
                **DEFAULTS,
                **result
            }

        # =====================================================
        # FAILURE
        # =====================================================

        logger.error(
            "FAILED TO PARSE RESPONSE"
        )

        logger.error(raw)

        return {
            **DEFAULTS,
            "error": "Could not parse model response"
        }

    # =========================================================
    # JSON PARSER
    # =========================================================

    def _try_json(self, text: str) -> dict | None:

        try:

            cleaned = text.strip()

            # Remove markdown wrappers

            cleaned = re.sub(
                r'^```json',
                '',
                cleaned,
                flags=re.IGNORECASE
            )

            cleaned = re.sub(
                r'^```',
                '',
                cleaned
            )

            cleaned = re.sub(
                r'```$',
                '',
                cleaned
            )

            # Remove trailing commas

            cleaned = re.sub(
                r',\s*([\]}])',
                r'\1',
                cleaned
            )

            data = json.loads(
                cleaned.strip()
            )

            if (
                isinstance(data, dict)
                and len(data) > 0
            ):
                return data

        except Exception as e:

            logger.warning(
                "JSON parse failed: %s",
                e
            )

        return None

    # =========================================================
    # BULLET EXTRACTION
    # =========================================================

    def _extract_from_bullets(
        self,
        text: str
    ) -> dict | None:

        def find(key):

            patterns = [

                rf'[`"\']?{key}[`"\']?\s*[:\-]\s*[`"\']([^`"\'\n]+)[`"\']',

                rf'[`"\']?{key}[`"\']?\s*[:\-]\s*(\d+)'
            ]

            for p in patterns:

                m = re.search(
                    p,
                    text,
                    re.IGNORECASE
                )

                if m:
                    return m.group(1).strip()

            return None

        score_m = re.search(
            r'[`"\']?score[`"\']?\s*[:\-]\s*(\d+)',
            text,
            re.IGNORECASE
        )

        if not score_m:
            return None

        score = int(
            score_m.group(1)
        )

        grade = (
            find("grade")
            or self._score_to_grade(score)
        )

        subject = (
            find("subject")
            or "Science"
        )

        en_fb = (
            find("english_feedback")
            or ""
        )

        hi_fb = (
            find("hindi_feedback")
            or "मूल्यांकन हुआ।"
        )

        hint = (
            find("model_answer_hint")
            or ""
        )

        conf = (
            find("confidence")
            or "medium"
        )

        mistakes = self._extract_list(
            text,
            "mistakes"
        )

        correct = self._extract_list(
            text,
            "correct_points"
        )

        tips = self._extract_list(
            text,
            "improvement_tips"
        )

        return {
            "subject": subject,
            "question_detected":
                find("question_detected") or "",
            "score": score,
            "max_score": 10,
            "grade": grade,
            "hindi_feedback": hi_fb,
            "english_feedback": en_fb,
            "mistakes": mistakes,
            "correct_points": correct,
            "improvement_tips": tips,
            "model_answer_hint": hint,
            "confidence": conf,
        }

    # =========================================================
    # LIST EXTRACTION
    # =========================================================

    def _extract_list(
        self,
        text: str,
        key: str
    ) -> list:

        m = re.search(
            rf'{key}[`"\']?\s*[:\-]\s*\[([^\]]*)\]',
            text,
            re.IGNORECASE | re.DOTALL
        )

        if m:

            items = re.findall(
                r'["\']([^"\']+)["\']',
                m.group(1)
            )

            return items if items else []

        return []

    # =========================================================
    # GRADE LOGIC
    # =========================================================

    @staticmethod
    def _score_to_grade(
        score: int
    ) -> str:

        if score >= 9:
            return "A+"

        if score >= 7:
            return "A"

        if score == 6:
            return "B+"

        if score == 5:
            return "B"

        if score == 4:
            return "C+"

        if score == 3:
            return "C"

        if score == 2:
            return "D"

        return "F"


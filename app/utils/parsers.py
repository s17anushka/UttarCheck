"""
app/utils/parsers.py
Gemma 4 wraps JSON in ```json ... ``` blocks after long prose.
This parser finds and extracts that block reliably.
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
            return {"error": "Empty model response"}

        logger.info("Parsing (len=%d): %s...", len(raw), raw[:100])

        # Strategy 1: ```json ... ``` block — Gemma 4's preferred format
        result = self._extract_fenced(raw)
        if result:
            logger.info("Parsed via fenced block")
            return {**DEFAULTS, **result}

        # Strategy 2: Direct JSON
        result = self._try_json(raw.strip())
        if result:
            logger.info("Parsed via direct JSON")
            return {**DEFAULTS, **result}

        # Strategy 3: Find JSON block containing "score" key
        for m in re.finditer(r'\{[^{}]*"score"[^{}]*\}', raw, re.DOTALL):
            result = self._try_json(m.group())
            if result:
                logger.info("Parsed via score-key search")
                return {**DEFAULTS, **result}

        # Strategy 4: Find largest { ... } block
        matches = list(re.finditer(r'\{[\s\S]*?\}', raw))
        for m in sorted(matches, key=lambda x: len(x.group()), reverse=True):
            result = self._try_json(m.group())
            if result:
                logger.info("Parsed via largest block")
                return {**DEFAULTS, **result}

        # Strategy 5: Fix trailing commas
        m = re.search(r'\{[\s\S]*\}', raw)
        if m:
            fixed = re.sub(r',\s*([\]}])', r'\1', m.group())
            result = self._try_json(fixed)
            if result:
                logger.info("Parsed via comma fix")
                return {**DEFAULTS, **result}

        # Strategy 6: Extract fields directly from Gemma's bullet-point prose
        # Gemma writes: `score`: 7  OR  *   `score`: 7
        result = self._extract_from_bullets(raw)
        if result:
            logger.info("Parsed via bullet extraction")
            return {**DEFAULTS, **result}

        logger.error("ALL strategies failed. Raw: %s", raw[:300])
        return {"error": "Could not parse model response"}

    def _extract_fenced(self, text: str) -> dict | None:
        """Extract from ```json ... ``` or ``` ... ``` blocks."""
        pattern = r'```(?:json)?\s*(\{[\s\S]*?\})\s*```'
        for m in re.finditer(pattern, text, re.IGNORECASE):
            result = self._try_json(m.group(1))
            if result:
                return result
        return None

    def _try_json(self, text: str) -> dict | None:
        try:
            data = json.loads(text.strip())
            if isinstance(data, dict) and len(data) > 0:
                return data
        except Exception:
            pass
        return None

    def _extract_from_bullets(self, text: str) -> dict | None:
        """
        Gemma 4 writes evaluations as bullet points like:
          `score`: 7
          `grade`: "B"
          `hindi_feedback`: "उत्तर सही है"
        This extracts those values directly.
        """
        def find(key):
            # Matches: `key`: value  OR  "key": value  OR  key: value
            patterns = [
                rf'[`"\']?{key}[`"\']?\s*[:\-]\s*[`"\']([^`"\'\n]+)[`"\']',
                rf'[`"\']?{key}[`"\']?\s*[:\-]\s*(\d+)',
            ]
            for p in patterns:
                m = re.search(p, text, re.IGNORECASE)
                if m:
                    return m.group(1).strip()
            return None

        score_m = re.search(r'[`"\']?score[`"\']?\s*[:\-]\s*(\d+)', text, re.IGNORECASE)
        if not score_m:
            return None

        score   = int(score_m.group(1))
        grade   = find("grade") or self._score_to_grade(score)
        subject = find("subject") or "Science"
        en_fb   = find("english_feedback") or ""
        hi_fb   = find("hindi_feedback") or "मूल्यांकन हुआ।"
        hint    = find("model_answer_hint") or ""
        conf    = find("confidence") or "medium"

        # Extract lists from bullets
        mistakes = self._extract_list(text, "mistakes")
        correct  = self._extract_list(text, "correct_points")
        tips     = self._extract_list(text, "improvement_tips")

        return {
            "subject":          subject,
            "question_detected": find("question_detected") or "",
            "score":            score,
            "max_score":        10,
            "grade":            grade,
            "hindi_feedback":   hi_fb,
            "english_feedback": en_fb,
            "mistakes":         mistakes,
            "correct_points":   correct,
            "improvement_tips": tips,
            "model_answer_hint": hint,
            "confidence":       conf,
        }

    def _extract_list(self, text: str, key: str) -> list:
        """Extract array values from bullet-point prose."""
        # Find section after key
        m = re.search(rf'{key}[`"\']?\s*[:\-]\s*\[([^\]]*)\]', text, re.IGNORECASE | re.DOTALL)
        if m:
            items = re.findall(r'["\']([^"\']+)["\']', m.group(1))
            return items if items else []
        return []

    @staticmethod
    def _score_to_grade(score: int) -> str:
        if score >= 9: return "A+"
        if score >= 7: return "A"
        if score == 6: return "B+"
        if score == 5: return "B"
        if score == 4: return "C+"
        if score == 3: return "C"
        if score == 2: return "D"
        return "F"
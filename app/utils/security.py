"""
app/utils/security.py — Input Sanitization
===========================================
Defends against:
  - Prompt injection ("Ignore previous instructions...")
  - XSS (HTML entity encoding)
  - Oversized inputs (length cap)
"""
import re
import html
import logging

logger = logging.getLogger(__name__)

MAX_LEN = 500

_INJECTION = re.compile(
    r"(ignore\s+(all\s+)?(previous|prior|above)\s+instructions?"
    r"|reveal\s+(the\s+)?(system\s+)?prompt"
    r"|forget\s+(everything|all|instructions?)"
    r"|act\s+as\s+"
    r"|you\s+are\s+now\s+"
    r"|jailbreak"
    r"|DAN\s+mode"
    r"|override\s+instructions?)",
    re.IGNORECASE,
)


class InputSanitizer:

    def clean(self, text: str) -> str:
        if not text:
            return ""
        text = text.strip()
        if len(text) > MAX_LEN:
            text = text[:MAX_LEN]
        if _INJECTION.search(text):
            logger.warning("Prompt injection detected: %.80s", text)
            return "[INVALID INPUT]"
        return html.escape(text, quote=True)
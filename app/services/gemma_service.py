"""
app/services/gemma_service.py — AI Model Service
"""
import json
import time
import logging
import urllib.request
import urllib.error
from flask import current_app

logger = logging.getLogger(__name__)


class GemmaService:

    def generate(self, image_b64: str, mime_type: str,
                 system_prompt: str, user_prompt: str) -> str:
        backend = current_app.config.get("INFERENCE_BACKEND", "google")
        if backend == "google":
            return self._call_google(image_b64, mime_type, system_prompt, user_prompt)
        elif backend == "ollama":
            return self._call_ollama(image_b64, mime_type, system_prompt, user_prompt)
        else:
            raise RuntimeError(f"Unknown INFERENCE_BACKEND: {backend!r}")

    def _call_google(self, image_b64: str, mime_type: str,
                     system_prompt: str, user_prompt: str) -> str:
        api_key = current_app.config["GEMMA_API_KEY"]
        model   = current_app.config["MODEL_NAME"]
        base    = current_app.config["GEMMA_API_BASE"]
        timeout = current_app.config["GEMMA_TIMEOUT"]
        max_tok = current_app.config["GEMMA_MAX_TOKENS"]
        temp    = current_app.config["GEMMA_TEMPERATURE"]

        url = f"{base}/{model}:generateContent"

        # Combine system + user prompt into single user message
        # (more compatible across Gemma model versions)
        combined = f"{system_prompt}\n\n---\n\n{user_prompt}"

        payload = {
            "contents": [{
                "parts": [
                    {"inline_data": {"mime_type": mime_type, "data": image_b64}},
                    {"text": combined},
                ]
            }],
            "generationConfig": {
                "temperature": temp,
                "maxOutputTokens": max_tok,
            },
        }

        data = json.dumps(payload).encode("utf-8")
        req  = urllib.request.Request(
            url, data=data,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            method="POST",
        )

        last_exc = None
        for attempt in range(1, 3):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    raw = resp.read().decode("utf-8")
                    result = json.loads(raw)
                    text = self._extract_text(result)
                    logger.info("Gemma raw response (first 300): %s", text[:300])
                    return text

            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")
                logger.error("HTTP %s attempt %d: %s", e.code, attempt, body[:300])

                if e.code == 400:
                    raise RuntimeError(
                        f"API rejected request (400). Detail: {body[:200]}"
                    ) from e
                if e.code == 403:
                    raise RuntimeError("API key invalid or Gemma not enabled (403).") from e
                if e.code == 404:
                    raise RuntimeError(
                        f"Model '{model}' not found (404). "
                        f"Try: gemma-4-31b-it or gemma-4-26b-a4b-it"
                    ) from e
                if e.code == 429:
                    raise RuntimeError("Quota exceeded (429). Try again later.") from e

                last_exc = e
                if attempt < 2:
                    time.sleep(2)

            except urllib.error.URLError as e:
                logger.warning("Network error attempt %d: %s", attempt, e)
                last_exc = e
                if attempt < 2:
                    time.sleep(2)

        raise RuntimeError(f"Gemma API failed after 2 attempts: {last_exc}") from last_exc

    def _extract_text(self, result: dict) -> str:
        candidates = result.get("candidates", [])
        if not candidates:
            block = result.get("promptFeedback", {}).get("blockReason", "unknown")
            raise RuntimeError(f"No candidates. Block reason: {block}")

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise RuntimeError("Candidate had no content parts.")

        return parts[0].get("text", "")

    def _call_ollama(self, image_b64: str, mime_type: str,
                     system_prompt: str, user_prompt: str) -> str:
        base    = current_app.config["OLLAMA_BASE_URL"]
        model   = current_app.config["OLLAMA_MODEL"]
        timeout = current_app.config["GEMMA_TIMEOUT"]

        payload = {
            "model": model,
            "system": system_prompt,
            "prompt": user_prompt,
            "images": [image_b64],
            "stream": False,
            "options": {
                "temperature": current_app.config["GEMMA_TEMPERATURE"],
                "num_predict": current_app.config["GEMMA_MAX_TOKENS"],
            },
        }

        data = json.dumps(payload).encode("utf-8")
        req  = urllib.request.Request(
            f"{base}/api/generate", data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read()).get("response", "")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Ollama unreachable at {base}. Run: ollama serve") from e
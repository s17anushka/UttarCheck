"""
app/utils/validators.py — Secure File Validation
=================================================
Never trust user uploads. Validate:
  1. File presence
  2. Extension whitelist
  3. MIME type whitelist
  4. File size cap
  5. Magic byte verification (prevents format spoofing)
"""
import logging
from flask import current_app

logger = logging.getLogger(__name__)

MAGIC_SIGNATURES = [
    (b"\xff\xd8\xff",       "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n",  "image/png"),
    (b"RIFF",               "image/webp"),
    (b"GIF87a",             "image/gif"),
    (b"GIF89a",             "image/gif"),
]


class FileValidator:

    def validate_image(self, file_storage) -> bytes:
        """
        Validate an uploaded image file.
        Returns raw bytes if valid.
        Raises ValueError with user-friendly message on failure.
        """
        if file_storage is None or not getattr(file_storage, "filename", ""):
            raise ValueError("No file was uploaded.")

        # Extension check
        ext = self._extension(file_storage.filename)
        allowed_exts = current_app.config["ALLOWED_EXTENSIONS"]
        if ext not in allowed_exts:
            raise ValueError(
                f"'.{ext}' files not allowed. Upload: {', '.join(sorted(allowed_exts))}"
            )

        # MIME check (browser-provided, untrusted but still validated)
        mime = (file_storage.content_type or "").lower().split(";")[0].strip()
        if mime and mime not in current_app.config["ALLOWED_MIME_TYPES"]:
            raise ValueError(f"MIME type '{mime}' not allowed.")

        # Read bytes
        raw = file_storage.read()
        file_storage.seek(0)

        if not raw:
            raise ValueError("Uploaded file is empty.")

        max_bytes = current_app.config["MAX_CONTENT_LENGTH"]
        if len(raw) > max_bytes:
            raise ValueError(f"File too large. Max {max_bytes // (1024*1024)} MB.")

        # Magic byte check — the real format check
        if not self._detect_mime(raw):
            raise ValueError(
                "File is not a valid image. Upload a real JPEG, PNG, WEBP, or GIF."
            )

        logger.debug("File valid: name=%s ext=%s size=%d", file_storage.filename, ext, len(raw))
        return raw

    @staticmethod
    def _extension(filename: str) -> str:
        parts = filename.rsplit(".", 1)
        return parts[-1].lower() if len(parts) == 2 else ""

    @staticmethod
    def _detect_mime(data: bytes) -> str | None:
        for sig, mime in MAGIC_SIGNATURES:
            if data[:len(sig)] == sig:
                return mime
        return None
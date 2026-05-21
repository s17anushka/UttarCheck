"""
app/services/image_service.py
Compress image before sending to Gemma API.
Large images cause 500 errors from Google AI.
"""
import io
import base64
import logging

logger = logging.getLogger(__name__)

MAGIC_BYTES = [
    (b"\xff\xd8\xff",       "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n",  "image/png"),
    (b"RIFF",               "image/webp"),
    (b"GIF87a",             "image/gif"),
    (b"GIF89a",             "image/gif"),
]

try:
    from PIL import Image, ImageEnhance, ImageOps
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    logger.warning("Pillow not installed — images sent raw (may cause 500 errors for large photos)")


class ImageService:

    def process(self, raw_bytes: bytes, use_pillow: bool = True) -> tuple[str, str]:
        mime = self._detect_mime(raw_bytes)
        if not mime:
            raise ValueError("Not a valid image. Upload JPEG, PNG, WEBP or GIF.")

        if use_pillow and PILLOW_AVAILABLE:
            return self._compress(raw_bytes)

        # No Pillow — still try to cap size
        if len(raw_bytes) > 1 * 1024 * 1024:
            logger.warning(
                "Image is %d KB but Pillow not available to compress. "
                "Large images may cause Gemma 500 errors. Run: pip install Pillow",
                len(raw_bytes) // 1024
            )

        return base64.b64encode(raw_bytes).decode("utf-8"), mime

    def _compress(self, raw_bytes: bytes) -> tuple[str, str]:
        try:
            img = Image.open(io.BytesIO(raw_bytes))
            img.verify()
            img = Image.open(io.BytesIO(raw_bytes))

            # Convert to RGB
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            # Resize — max 1024px on longest side (smaller = less tokens = no 500)
            w, h = img.size
            max_dim = 1024
            if max(w, h) > max_dim:
                ratio = max_dim / max(w, h)
                img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
                logger.info("Resized image: %dx%d → %dx%d", w, h, img.size[0], img.size[1])

            # Enhance contrast for handwriting
            img = ImageOps.autocontrast(img, cutoff=2)
            img = ImageEnhance.Contrast(img).enhance(1.3)

            # Compress to JPEG quality 75 — good enough for text, much smaller
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=75, optimize=True)
            compressed = buf.getvalue()

            logger.info("Image compressed: %dKB → %dKB",
                        len(raw_bytes) // 1024, len(compressed) // 1024)

            return base64.b64encode(compressed).decode("utf-8"), "image/jpeg"

        except Exception as exc:
            logger.warning("Compression failed (%s), sending raw", exc)
            return base64.b64encode(raw_bytes).decode("utf-8"), "image/jpeg"

    @staticmethod
    def _detect_mime(data: bytes) -> str | None:
        for sig, mime in MAGIC_BYTES:
            if data[:len(sig)] == sig:
                return mime
        return None
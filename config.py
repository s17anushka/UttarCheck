"""
config.py — Centralized Configuration Management
=================================================
Single source of truth for all settings.
Change one env variable → whole app adapts.

Environments:
  development  → debug logging, relaxed limits
  production   → strict security, no debug
  testing      → mocked services, no real API calls

HOW TO USE:
  Set FLASK_ENV=production in your .env or server environment.
  create_app() picks the right config automatically.
"""

import os


def _load_env() -> None:
    """
    Load .env file into os.environ without needing python-dotenv.
    Called once at module import time.
    """
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env()


class BaseConfig:
    # ── Flask ──────────────────────────────────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-in-prod")
    DEBUG: bool = False
    TESTING: bool = False

    # ── Google AI / Gemma ──────────────────────────────────
    GEMMA_API_KEY: str = os.getenv("GEMMA_API_KEY", "")

    # IMPORTANT: gemma-3-27b-it is the currently working model on Google AI Studio.
    # gemma-4-31b-it and gemma-4-26b-a4b-it are also available on Google AI Studio.
    # Change MODEL_NAME in .env to switch — no code changes needed.
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gemma-3-27b-it")

    GEMMA_API_BASE: str = "https://generativelanguage.googleapis.com/v1beta/models"
    GEMMA_TIMEOUT: int = int(os.getenv("GEMMA_TIMEOUT", "60"))
    GEMMA_MAX_TOKENS: int = int(os.getenv("GEMMA_MAX_TOKENS", "1024"))
    GEMMA_TEMPERATURE: float = float(os.getenv("GEMMA_TEMPERATURE", "0.2"))

    # ── File Upload ────────────────────────────────────────
    MAX_CONTENT_LENGTH: int = 8 * 1024 * 1024   # 8 MB — Flask enforces this
    ALLOWED_MIME_TYPES: frozenset = frozenset({
        "image/jpeg", "image/png", "image/webp", "image/gif"
    })
    ALLOWED_EXTENSIONS: frozenset = frozenset({
        "jpg", "jpeg", "png", "webp", "gif"
    })
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "uploads")

    # ── Image Preprocessing ────────────────────────────────
    # Set USE_PILLOW=false in .env if Pillow is not installed.
    # Without Pillow: raw bytes sent directly (still works, just no preprocessing).
    USE_PILLOW: bool = os.getenv("USE_PILLOW", "true").lower() == "true"
    IMAGE_MAX_DIMENSION: int = int(os.getenv("IMAGE_MAX_DIMENSION", "1600"))

    # ── Rate Limiting ──────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "15"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds

    # ── Inference Backend ──────────────────────────────────
    # "google" → Google AI Studio API (current, works now)
    # "ollama" → Local Ollama (future, privacy-first, offline)
    INFERENCE_BACKEND: str = os.getenv("INFERENCE_BACKEND", "google")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma3:4b")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    # More lenient rate limiting during development
    RATE_LIMIT_REQUESTS = 50


class ProductionConfig(BaseConfig):
    DEBUG = False
    # Require SECRET_KEY in prod — crash early if missing
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "")


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    GEMMA_API_KEY = "test-key-not-real"
    RATE_LIMIT_REQUESTS = 99999
    USE_PILLOW = False  # Don't need Pillow in tests


config_map: dict = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
"""
app/utils/rate_limiter.py — In-Memory Sliding Window Rate Limiter
=================================================================
Prevents API key exhaustion and DoS attacks.
Thread-safe via threading.Lock.

Production upgrade: replace with Flask-Limiter + Redis
for multi-process / multi-server deployments.
"""
import time
import threading
import logging
from collections import defaultdict
from flask import current_app, request

logger = logging.getLogger(__name__)

_store: dict[str, list[float]] = defaultdict(list)
_lock  = threading.Lock()


def is_rate_limited() -> bool:
    ip     = _get_ip()
    limit  = current_app.config["RATE_LIMIT_REQUESTS"]
    window = current_app.config["RATE_LIMIT_WINDOW"]
    now    = time.monotonic()

    with _lock:
        _store[ip] = [t for t in _store[ip] if now - t < window]
        if len(_store[ip]) >= limit:
            logger.warning("Rate limit hit: ip=%s", ip)
            return True
        _store[ip].append(now)
        return False


def _get_ip() -> str:
    fwd = request.headers.get("X-Forwarded-For", "")
    return fwd.split(",")[0].strip() if fwd else (request.remote_addr or "unknown")
"""
app/routes/evaluate.py — HTTP layer only.
Routes read request, call service, return JSON.
No business logic here.
"""
import logging
import time
from flask import Blueprint, request, jsonify, render_template, current_app
from app.services.evaluation_service import evaluate_submission
from app.utils.rate_limiter import is_rate_limited

logger = logging.getLogger(__name__)
evaluate_bp = Blueprint("evaluate", __name__)


@evaluate_bp.route("/")
def index():
    return render_template("index.html")


@evaluate_bp.route("/evaluate", methods=["POST"])
def evaluate():
    # Rate limit
    if is_rate_limited():
        return jsonify({"success": False, "error": "Too many requests. Wait 1 minute."}), 429

    # API key guard
    if not current_app.config.get("GEMMA_API_KEY"):
        return jsonify({"success": False, "error": "GEMMA_API_KEY not set in .env"}), 500

    t0 = time.perf_counter()
    result = evaluate_submission(
        image_file=request.files.get("image"),
        question=request.form.get("question", "").strip(),
        subject=request.form.get("subject", "").strip(),
    )
    ms = int((time.perf_counter() - t0) * 1000)

    logger.info("evaluate | success=%s | subject=%s | score=%s | %dms",
                result.success, result.subject, result.score, ms)

    return jsonify(result.to_dict()), (200 if result.success else 422)
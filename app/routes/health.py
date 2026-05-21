"""
app/routes/health.py — Health check endpoint.
Used by load balancers, monitoring tools, mobile apps.
"""
from flask import Blueprint, jsonify, current_app

health_bp = Blueprint("health", __name__)


@health_bp.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "api_key_set": bool(current_app.config.get("GEMMA_API_KEY")),
        "model": current_app.config.get("MODEL_NAME"),
        "backend": current_app.config.get("INFERENCE_BACKEND"),
        "pillow": current_app.config.get("USE_PILLOW"),
    })
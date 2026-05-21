"""
app/utils/error_handlers.py — Global Error Handlers
====================================================
Consistent JSON error responses for all HTTP errors.
Important for mobile clients that parse every response.
"""
import logging
from flask import Flask, jsonify

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"success": False, "error": "Bad request."}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Endpoint not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "error": "Method not allowed."}), 405

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"success": False, "error": "File too large. Max 8 MB."}), 413

    @app.errorhandler(429)
    def too_many(e):
        return jsonify({"success": False, "error": "Too many requests. Wait 1 minute."}), 429

    @app.errorhandler(500)
    def server_error(e):
        logger.exception("Unhandled 500")
        return jsonify({"success": False, "error": "Server error. Please try again."}), 500
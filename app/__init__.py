"""
app/__init__.py — Flask App Factory
"""
import os
import logging
from flask import Flask
from config import config_map


def create_app(env: str = None) -> Flask:
    env = env or os.getenv("FLASK_ENV", "development")
    cfg = config_map.get(env, config_map["development"])

    # Point to root-level templates/ and static/ folders
    root = os.path.dirname(os.path.dirname(__file__))

    app = Flask(
        __name__,
        template_folder=os.path.join(root, "templates"),
        static_folder=os.path.join(root, "static"),
    )
    app.config.from_object(cfg)

    logging.basicConfig(
        level=logging.DEBUG if app.config["DEBUG"] else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    from app.routes.evaluate import evaluate_bp
    from app.routes.health import health_bp
    app.register_blueprint(evaluate_bp)
    app.register_blueprint(health_bp)

    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)

    app.logger.info("UttarCheck started | env=%s | model=%s | backend=%s",
                    env, app.config["MODEL_NAME"], app.config["INFERENCE_BACKEND"])
    return app
"""The Workshop — AMTL Central Service Registry & Launcher.

Flask application factory lives here so the ``app`` package is
directly importable: ``from app import create_app``.
"""

import logging

from flask import Flask
from flask_cors import CORS

import config


def create_app():
    """Create and configure the Flask application."""
    application = Flask(
        __name__,
        template_folder=str(config.BASE_DIR / "templates"),
        static_folder=str(config.BASE_DIR / "static"),
    )

    # CORS — local-only, but Electron renderer needs it.
    CORS(application)

    # Logging
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Register blueprints
    from app.routes.health import health_bp

    application.register_blueprint(health_bp)

    return application

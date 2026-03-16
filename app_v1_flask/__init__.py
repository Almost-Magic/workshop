# Author: Mani Padisetti
"""The Workshop — AMTL Central Service Registry & Launcher.

Flask application factory lives here so the ``app`` package is
directly importable: ``from app import create_app``.
"""

import logging

from flask import Flask, redirect
from flask_cors import CORS

import config
from app.services.service_manager import ServiceManager

# Subpath prefix — all routes live under /workshop
PREFIX = "/workshop"


def create_app(start_health_loop=True):
    """Create and configure the Flask application.

    Args:
        start_health_loop: If True, start the background health-check
            thread.  Set to False during testing.
    """
    application = Flask(
        __name__,
        template_folder=str(config.BASE_DIR / "templates"),
        static_folder=str(config.BASE_DIR / "static"),
        static_url_path=f"{PREFIX}/static",
    )

    # CORS — local-only, but Electron renderer needs it.
    CORS(application)

    # Logging
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Service Manager — canonical registry backed by YAML
    mgr = ServiceManager()
    application.config["SERVICE_MANAGER"] = mgr

    if start_health_loop:
        mgr.start_health_loop()

    # Register blueprints — all under /workshop prefix
    from app.routes.health import health_bp
    from app.routes.services import services_bp
    from app.routes.web import web_bp
    from app.routes.incidents import incidents_bp
    from app.routes.briefing import briefing_bp
    from app.routes.help import help_bp
    from app.routes.constellation import constellation_bp
    from app.routes.registry import registry_bp

    application.register_blueprint(health_bp, url_prefix=PREFIX)
    application.register_blueprint(services_bp, url_prefix=PREFIX)
    application.register_blueprint(web_bp, url_prefix=PREFIX)
    application.register_blueprint(incidents_bp, url_prefix=PREFIX)
    application.register_blueprint(briefing_bp, url_prefix=PREFIX)
    application.register_blueprint(help_bp, url_prefix=PREFIX)
    application.register_blueprint(constellation_bp, url_prefix=PREFIX)
    application.register_blueprint(registry_bp, url_prefix=PREFIX)

    # Root redirect → /workshop/
    @application.route("/")
    def root_redirect():
        return redirect(f"{PREFIX}/")

    return application

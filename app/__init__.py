"""The Workshop — AMTL Central Service Registry & Launcher.

Flask application factory lives here so the ``app`` package is
directly importable: ``from app import create_app``.
"""

import logging

from flask import Flask
from flask_cors import CORS

import config
from app.services import incident_logger
from app.services.service_manager import ServiceManager
from app.services.healer import SelfHealer


def create_app(start_health_loop=True, data_dir=None):
    """Create and configure the Flask application.

    Args:
        start_health_loop: If True, start the background health-check
            thread.  Set to False during testing.
        data_dir: Optional path to data directory.  If None, uses config.DATA_DIR.
            Used for test isolation with tmp_path.
    """
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

    # Set data directory for incident logger (for test isolation)
    if data_dir:
        incident_logger.set_db_path(data_dir / "incidents.db")

    # Service Manager — canonical registry backed by YAML
    # Create healer first, then pass to ServiceManager
    healer = SelfHealer(None)  # Will be set after mgr is created
    mgr = ServiceManager(healer=healer)
    healer._mgr = mgr  # Set manager reference now that it exists
    application.config["SERVICE_MANAGER"] = mgr
    application.config["HEALER"] = healer

    if start_health_loop:
        mgr.start_health_loop()

    # Register blueprints
    from app.routes.health import health_bp
    from app.routes.services import services_bp
    from app.routes.web import web_bp
    from app.routes.incidents import incidents_bp
    from app.routes.briefing import briefing_bp
    from app.routes.help import help_bp
    from app.routes.constellation import constellation_bp

    application.register_blueprint(health_bp)
    application.register_blueprint(services_bp)
    application.register_blueprint(web_bp)
    application.register_blueprint(incidents_bp)
    application.register_blueprint(briefing_bp)
    application.register_blueprint(help_bp)
    application.register_blueprint(constellation_bp)

    return application

"""The Workshop — Entry Point.

AMTL App Zero: Central Service Registry & Launcher.
Port 5003 (sacred — DEC-005). Binds to 127.0.0.1 only.

Run:
    python app.py
"""

import config
from app import create_app

application = create_app()

if __name__ == "__main__":
    application.run(
        host=config.HOST,
        port=config.PORT,
        debug=False,
    )

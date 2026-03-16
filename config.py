# Author: Mani Padisetti
"""Workshop configuration — loads from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
REGISTRY_PATH = BASE_DIR / "registry.yaml"

# Ensure runtime directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Workshop API
PORT = int(os.getenv("AMTL_WKS_PORT", "5001"))
HOST = os.getenv("AMTL_WKS_HOST", "0.0.0.0")
LOG_LEVEL = os.getenv("AMTL_WKS_LOG_LEVEL", "INFO")

# Health checks & self-healing
HEALTH_INTERVAL = int(os.getenv("AMTL_WKS_HEALTH_INTERVAL", "30"))
RESTART_ATTEMPTS = int(os.getenv("AMTL_WKS_RESTART_ATTEMPTS", "3"))
RESTART_DELAY = int(os.getenv("AMTL_WKS_RESTART_DELAY", "10"))

# Heartbeat
HEARTBEAT_HOURS = int(os.getenv("AMTL_WKS_HEARTBEAT_HOURS", "24"))

# Theme
THEME_FILE = os.getenv(
    "AMTL_WKS_THEME_FILE",
    str(Path.home() / ".amtl" / "workshop-theme.json"),
)

# Integration URLs
SUPERVISOR_URL = os.getenv("AMTL_SUPERVISOR_URL", "http://localhost:9000")
ELAINE_URL = os.getenv("AMTL_ELAINE_URL", "http://localhost:5000")
FOREPERSON_URL = os.getenv("AMTL_FOREPERSON_URL", "http://localhost:9100")

# PostgreSQL (AMTL standard — port 5433)
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5433))
POSTGRES_USER = os.getenv("POSTGRES_USER", "amtl")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "amtl")
POSTGRES_DB = "workshop"
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Version
VERSION = "2.0.0"

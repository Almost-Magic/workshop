"""Heartbeat Engine — 24-hour uptime sparkline data.

Stores one row per (app_id, hour) in SQLite.  Each row records whether
the app was up (1) or down (0) during that hour.  The get_heartbeat()
function returns the most recent 24 values for rendering as a sparkline.

Database: data/heartbeat.db
"""

import logging
import sqlite3
import threading
from datetime import datetime, timezone, timedelta

import config

log = logging.getLogger(__name__)

AEST = timezone(timedelta(hours=10))
_DB_PATH = config.DATA_DIR / "heartbeat.db"
_lock = threading.Lock()

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS heartbeat (
    app_id TEXT NOT NULL,
    hour TEXT NOT NULL,
    status INTEGER NOT NULL,
    PRIMARY KEY (app_id, hour)
);
"""


def _connect():
    """Return a SQLite connection (creates table on first call)."""
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute(_CREATE_TABLE)
    return conn


def record(app_id, is_up):
    """Record a heartbeat data point for the current hour.

    Args:
        app_id: Service identifier.
        is_up:  True if the service is healthy, False otherwise.
    """
    hour = datetime.now(AEST).strftime("%Y-%m-%dT%H")
    status = 1 if is_up else 0

    try:
        with _lock, _connect() as conn:
            conn.execute(
                """INSERT INTO heartbeat (app_id, hour, status)
                   VALUES (?, ?, ?)
                   ON CONFLICT(app_id, hour) DO UPDATE SET status = ?""",
                (app_id, hour, status, status),
            )
    except Exception as exc:
        log.error("Failed to record heartbeat for %s: %s", app_id, exc)


def get_heartbeat(app_id, hours=24):
    """Return the last *hours* heartbeat values (1 or 0) for an app.

    Missing hours are filled with 0 (unknown / down).

    Returns:
        List of integers, oldest to newest, length == hours.
    """
    now = datetime.now(AEST)
    # Build list of expected hour keys
    expected = []
    for i in range(hours - 1, -1, -1):
        dt = now - timedelta(hours=i)
        expected.append(dt.strftime("%Y-%m-%dT%H"))

    try:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT hour, status FROM heartbeat WHERE app_id = ? "
                "ORDER BY hour DESC LIMIT ?",
                (app_id, hours * 2),  # Over-fetch to cover edge cases
            ).fetchall()

        lookup = {r["hour"]: r["status"] for r in rows}
        return [lookup.get(h, 0) for h in expected]
    except Exception as exc:
        log.error("Failed to read heartbeat for %s: %s", app_id, exc)
        return [0] * hours


def prune(keep_hours=48):
    """Delete heartbeat data older than *keep_hours*."""
    cutoff = datetime.now(AEST) - timedelta(hours=keep_hours)
    cutoff_key = cutoff.strftime("%Y-%m-%dT%H")

    try:
        with _lock, _connect() as conn:
            cursor = conn.execute(
                "DELETE FROM heartbeat WHERE hour < ?", (cutoff_key,)
            )
            if cursor.rowcount > 0:
                log.info("Pruned %d old heartbeat rows.", cursor.rowcount)
    except Exception as exc:
        log.error("Failed to prune heartbeat data: %s", exc)


def clear_all():
    """Delete all heartbeat data — used in testing only."""
    try:
        with _lock, _connect() as conn:
            conn.execute("DELETE FROM heartbeat")
    except Exception as exc:
        log.error("Failed to clear heartbeat data: %s", exc)

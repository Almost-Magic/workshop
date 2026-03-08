"""Incident Logger — structured event log backed by SQLite.

Every start, stop, crash, restart, and health degradation event is
recorded here.  Incidents can be queried by app and annotated by Mani
or ELAINE.

Database: data/incidents.db
"""

import logging
import sqlite3
import threading
from datetime import datetime, timezone, timedelta

import config

log = logging.getLogger(__name__)

# Australian Eastern Standard Time offset (+10:00)
AEST = timezone(timedelta(hours=10))

_DB_PATH = config.DATA_DIR / "incidents.db"
_lock = threading.Lock()

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS incidents (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    app_id TEXT NOT NULL,
    event TEXT NOT NULL,
    cause TEXT,
    details TEXT,
    outcome TEXT,
    annotation TEXT
);
"""

# Auto-incrementing counter for INC-XXXX IDs
_counter_lock = threading.Lock()
_counter = 0


def _next_id():
    """Generate the next incident ID (INC-0001, INC-0002, …)."""
    global _counter
    with _counter_lock:
        _counter += 1
        return f"INC-{_counter:04d}"


def _connect():
    """Return a SQLite connection (creates table on first call)."""
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute(_CREATE_TABLE)
    return conn


def _init_counter():
    """Set _counter to the highest existing INC number on startup."""
    global _counter
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT id FROM incidents ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if row:
                num = int(row["id"].split("-")[1])
                _counter = num
    except Exception:
        pass


# Initialise counter from DB on import
_init_counter()


def log_event(app_id, event, cause=None, details=None, outcome=None):
    """Record an incident.

    Args:
        app_id:  Service identifier (e.g. 'elaine').
        event:   One of start, stop, crash, restart, health_degraded.
        cause:   Human-readable cause string.
        details: Additional context.
        outcome: recovered | failed | escalated.

    Returns:
        The incident dict that was written.
    """
    incident_id = _next_id()
    timestamp = datetime.now(AEST).isoformat()

    incident = {
        "id": incident_id,
        "timestamp": timestamp,
        "app_id": app_id,
        "event": event,
        "cause": cause,
        "details": details,
        "outcome": outcome,
        "annotation": None,
    }

    try:
        with _lock, _connect() as conn:
            conn.execute(
                """INSERT INTO incidents
                   (id, timestamp, app_id, event, cause, details, outcome, annotation)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    incident_id,
                    timestamp,
                    app_id,
                    event,
                    cause,
                    details,
                    outcome,
                    None,
                ),
            )
        log.info("Incident %s: %s %s (%s)", incident_id, app_id, event, outcome)
    except Exception as exc:
        log.error("Failed to log incident: %s", exc)

    return incident


def get_incidents(limit=50, app_id=None):
    """Retrieve recent incidents, optionally filtered by app.

    Args:
        limit:  Max rows to return (default 50).
        app_id: Filter by service ID (optional).

    Returns:
        List of incident dicts, newest first.
    """
    try:
        with _connect() as conn:
            if app_id:
                rows = conn.execute(
                    "SELECT * FROM incidents WHERE app_id = ? "
                    "ORDER BY timestamp DESC LIMIT ?",
                    (app_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM incidents ORDER BY timestamp DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [dict(r) for r in rows]
    except Exception as exc:
        log.error("Failed to read incidents: %s", exc)
        return []


def annotate(incident_id, note):
    """Add or update the annotation on an incident.

    Args:
        incident_id: The INC-XXXX ID.
        note:        Free-text annotation.

    Returns:
        True if the annotation was saved, False if the ID was not found.
    """
    try:
        with _lock, _connect() as conn:
            cursor = conn.execute(
                "UPDATE incidents SET annotation = ? WHERE id = ?",
                (note, incident_id),
            )
            return cursor.rowcount > 0
    except Exception as exc:
        log.error("Failed to annotate %s: %s", incident_id, exc)
        return False


def clear_all():
    """Delete all incidents — used in testing only."""
    global _counter
    try:
        with _lock, _connect() as conn:
            conn.execute("DELETE FROM incidents")
        _counter = 0
    except Exception as exc:
        log.error("Failed to clear incidents: %s", exc)

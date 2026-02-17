"""Resource Monitor — polls Supervisor for live CPU/RAM/VRAM data.

Fetches resource data from Supervisor (:9000) every 30 seconds and
stores it in memory.  Gracefully degrades when Supervisor is
unreachable — returns empty dicts rather than errors.
"""

import logging
import threading
import time

import requests

import config

log = logging.getLogger(__name__)

_resources = {}  # app_id → {cpu_pct, ram_mb, vram_mb}
_lock = threading.Lock()
_running = False
_thread = None


def get_resources(app_id=None):
    """Return resource data for one or all apps.

    Args:
        app_id: If provided, return resources for that app.
                If None, return the entire dict.

    Returns:
        Dict of {cpu_pct, ram_mb, vram_mb} or {} if unavailable.
    """
    with _lock:
        if app_id:
            return dict(_resources.get(app_id, {}))
        return dict(_resources)


def start_polling():
    """Start the background polling thread."""
    global _running, _thread
    if _thread and _thread.is_alive():
        return
    _running = True
    _thread = threading.Thread(
        target=_poll_loop, daemon=True, name="resource-monitor"
    )
    _thread.start()
    log.info("Resource monitor started (polling Supervisor every %ds).", config.HEALTH_INTERVAL)


def stop_polling():
    """Signal the polling thread to stop."""
    global _running
    _running = False


def _poll_loop():
    """Periodically fetch resource data from Supervisor."""
    while _running:
        _fetch()
        time.sleep(config.HEALTH_INTERVAL)


def _fetch():
    """Single fetch cycle — GET Supervisor /api/resources."""
    url = f"{config.SUPERVISOR_URL}/api/resources"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            with _lock:
                # Supervisor may return per-app resources or system-wide
                if isinstance(data, dict):
                    for app_id, res in data.items():
                        if isinstance(res, dict):
                            _resources[app_id] = {
                                "cpu_pct": res.get("cpu_pct", 0),
                                "ram_mb": res.get("ram_mb", 0),
                                "vram_mb": res.get("vram_mb", 0),
                            }
    except requests.ConnectionError:
        pass  # Graceful degradation — Supervisor not running
    except requests.Timeout:
        log.debug("Supervisor resource poll timed out.")
    except Exception as exc:
        log.debug("Resource monitor error: %s", exc)

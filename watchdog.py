"""Meta-Watchdog — checks Workshop API and Supervisor every 30 seconds.

If either service is unreachable, attempts a restart via nssm.
Registered as the AMTL-Watchdog Windows service.

This script is intentionally simple (~50 lines) and dependency-free
beyond the standard library so it can run even when the Workshop
virtualenv is broken.
"""

import logging
import subprocess
import sys
import time
import urllib.request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WATCHDOG] %(message)s",
)
log = logging.getLogger("watchdog")

SERVICES = {
    "AMTL-Workshop": "http://localhost:5003/api/health",
    "AMTL-Supervisor": "http://localhost:9000/api/health",
}

CHECK_INTERVAL = 30  # seconds
TIMEOUT = 5  # seconds per health check


def is_healthy(url):
    """Return True if the URL responds with HTTP 2xx within TIMEOUT."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return 200 <= resp.status < 400
    except Exception:
        return False


def restart_service(name):
    """Attempt to restart a Windows service via nssm."""
    log.warning("Restarting %s via nssm...", name)
    try:
        subprocess.run(
            ["nssm", "restart", name],
            capture_output=True,
            timeout=30,
        )
        log.info("%s restart command sent.", name)
    except Exception as exc:
        log.error("Failed to restart %s: %s", name, exc)


def main():
    """Run the watchdog loop indefinitely."""
    log.info("Meta-Watchdog started. Monitoring %s.", list(SERVICES.keys()))

    while True:
        for name, url in SERVICES.items():
            if not is_healthy(url):
                log.warning("%s is unreachable at %s.", name, url)
                restart_service(name)
            else:
                log.info("%s healthy.", name)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Watchdog stopped.")
        sys.exit(0)

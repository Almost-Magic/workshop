"""Self-Healer — 3-tier automatic recovery for failed services.

When a health check fails the healer attempts increasingly aggressive
recovery strategies:

  Tier 1 (T+0s):   Simple restart — kill process, re-spawn.
  Tier 2 (T+10s):  Deep restart — restart app + its dependencies.
  Tier 3 (T+30s):  Full recovery — kill all related, clear temp state,
                    restart from scratch.

If Tier 3 fails the incident is logged as 'escalated' and ELAINE is
notified (if running).

Per AMTL-WKS-TDD-1.0 §9.
"""

import logging
import time
import threading

import requests

import config
from app.services import incident_logger

log = logging.getLogger(__name__)


class SelfHealer:
    """Automatic recovery engine for Workshop-managed services."""

    def __init__(self, service_manager):
        self._mgr = service_manager
        self._healing = {}  # app_id → True while healing is in progress
        self._lock = threading.Lock()

    def on_health_failure(self, app_id):
        """Called when a health check fails.  Kicks off the 3-tier process.

        This method is safe to call from the health-check thread.  If
        healing is already in progress for this app, the call is ignored.
        """
        with self._lock:
            if self._healing.get(app_id):
                return  # Already being healed
            self._healing[app_id] = True

        thread = threading.Thread(
            target=self._heal,
            args=(app_id,),
            daemon=True,
            name=f"heal-{app_id}",
        )
        thread.start()

    def _heal(self, app_id):
        """Execute the 3-tier healing sequence."""
        try:
            # ── Tier 1: Simple restart ─────────────────────────────────
            log.info("Tier 1: simple restart for %s", app_id)
            incident_logger.log_event(
                app_id, "restart", cause="health_check_failed",
                details="Tier 1 — simple restart", outcome=None,
            )
            self._mgr.restart_service(app_id)
            time.sleep(config.RESTART_DELAY)

            if self._is_healthy(app_id):
                incident_logger.log_event(
                    app_id, "restart", cause="tier_1_recovery",
                    details="Tier 1 succeeded", outcome="recovered",
                )
                return

            # ── Tier 2: Deep restart (app + dependencies) ──────────────
            log.info("Tier 2: deep restart for %s", app_id)
            incident_logger.log_event(
                app_id, "restart", cause="tier_1_failed",
                details="Tier 2 — deep restart with dependencies", outcome=None,
            )
            svc = self._mgr.get(app_id)
            if svc:
                for dep_id in svc.get("dependencies", []):
                    self._mgr.restart_service(dep_id)
                    time.sleep(2)
            self._mgr.restart_service(app_id)
            time.sleep(config.RESTART_DELAY * 2)

            if self._is_healthy(app_id):
                incident_logger.log_event(
                    app_id, "restart", cause="tier_2_recovery",
                    details="Tier 2 succeeded", outcome="recovered",
                )
                return

            # ── Tier 3: Full recovery ──────────────────────────────────
            log.info("Tier 3: full recovery for %s", app_id)
            incident_logger.log_event(
                app_id, "restart", cause="tier_2_failed",
                details="Tier 3 — full recovery", outcome=None,
            )
            self._mgr.stop_service(app_id)
            if svc:
                for dep_id in svc.get("dependencies", []):
                    self._mgr.stop_service(dep_id)
            time.sleep(config.RESTART_DELAY)
            if svc:
                for dep_id in svc.get("dependencies", []):
                    self._mgr.start_service(dep_id)
                    time.sleep(3)
            self._mgr.start_service(app_id)
            time.sleep(config.RESTART_DELAY * 3)

            if self._is_healthy(app_id):
                incident_logger.log_event(
                    app_id, "restart", cause="tier_3_recovery",
                    details="Tier 3 succeeded", outcome="recovered",
                )
                return

            # ── Escalation ─────────────────────────────────────────────
            log.error("All 3 tiers failed for %s — escalating.", app_id)
            incident_logger.log_event(
                app_id, "crash", cause="all_tiers_failed",
                details="Escalated after 3 recovery tiers failed",
                outcome="escalated",
            )
            self._notify_elaine(app_id)

        finally:
            with self._lock:
                self._healing[app_id] = False

    def _is_healthy(self, app_id):
        """Check whether the service is now healthy."""
        result = self._mgr.check_health(app_id)
        return result and result.get("status") == "healthy"

    @staticmethod
    def _notify_elaine(app_id):
        """Attempt to notify ELAINE about an escalated incident."""
        try:
            url = f"{config.ELAINE_URL}/api/notify"
            requests.post(
                url,
                json={
                    "source": "workshop",
                    "event": "escalation",
                    "app_id": app_id,
                    "message": (
                        f"The Workshop could not recover {app_id} after "
                        f"3 tiers of self-healing. Manual intervention needed."
                    ),
                },
                timeout=5,
            )
            log.info("ELAINE notified about %s escalation.", app_id)
        except Exception as exc:
            log.warning("Could not notify ELAINE: %s", exc)

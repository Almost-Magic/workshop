"""Service Manager — loads registry.yaml and manages all AMTL services.

Responsibilities:
  - Load and parse the canonical YAML registry
  - Track runtime state (running / stopped / starting / not_installed)
  - Health-check every registered service on a background thread
  - Start / stop / restart individual services or groups
  - Expose service data for API consumers
"""

import logging
import os
import signal
import subprocess
import threading
import time
from pathlib import Path

import requests
import yaml

import config

log = logging.getLogger(__name__)


class ServiceManager:
    """Central service registry and lifecycle manager."""

    def __init__(self, registry_path=None):
        self._registry_path = Path(registry_path or config.REGISTRY_PATH)
        self._services = {}          # id → service dict (from YAML + runtime)
        self._health_thread = None
        self._running = False
        self._lock = threading.Lock()
        self._start_time = time.time()

        self._load_registry()

    # ── Registry Loading ───────────────────────────────────────────────────

    def _load_registry(self):
        """Load (or reload) services from registry.yaml."""
        try:
            with open(self._registry_path, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)

            for svc in data.get("services", []):
                svc_id = svc["id"]
                # Preserve runtime state if we already have it
                existing = self._services.get(svc_id, {})
                svc["status"] = existing.get("status", "stopped")
                svc["health"] = existing.get("health", "unknown")
                svc["pid"] = existing.get("pid")
                svc["started_at"] = existing.get("started_at")
                svc["last_health_check"] = existing.get("last_health_check")
                svc["restart_count"] = existing.get("restart_count", 0)
                self._services[svc_id] = svc

            log.info(
                "Registry loaded: %d services (%d active, %d ghost).",
                len(self._services),
                sum(1 for s in self._services.values() if not s.get("ghost")),
                sum(1 for s in self._services.values() if s.get("ghost")),
            )
        except FileNotFoundError:
            log.error("Registry not found at %s.", self._registry_path)
        except yaml.YAMLError as exc:
            log.error("Invalid YAML in registry: %s", exc)

    def reload_registry(self):
        """Hot-reload the registry from disk."""
        with self._lock:
            self._load_registry()

    # ── Queries ────────────────────────────────────────────────────────────

    def get_all(self):
        """Return a list of all service dicts (safe copies)."""
        with self._lock:
            return [self._public_view(s) for s in self._services.values()]

    def get(self, service_id):
        """Return a single service dict or None."""
        with self._lock:
            svc = self._services.get(service_id)
            return self._public_view(svc) if svc else None

    def get_by_group(self, group):
        """Return all services belonging to *group*."""
        with self._lock:
            return [
                self._public_view(s)
                for s in self._services.values()
                if s.get("group") == group
            ]

    @property
    def services_running(self):
        """Count of services currently marked as running."""
        with self._lock:
            return sum(
                1 for s in self._services.values()
                if s.get("status") == "running"
            )

    @property
    def services_total(self):
        """Total registered services (including ghost)."""
        return len(self._services)

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def start_service(self, service_id):
        """Start a service by its ID.  Returns a status dict."""
        with self._lock:
            svc = self._services.get(service_id)
            if svc is None:
                return None  # 404
            if svc.get("ghost"):
                return {"error": "Cannot start a ghost app.", "status": "ghost"}
            if svc.get("status") == "running":
                return {"error": "Service is already running.", "status": "conflict"}

            svc["status"] = "starting"

        # Resolve dependencies first
        deps = svc.get("dependencies", [])
        dep_chain = []
        for dep_id in deps:
            dep = self._services.get(dep_id)
            if dep and dep.get("status") != "running":
                dep_chain.append(dep_id)
                self._spawn(dep)

        self._spawn(svc)

        return {
            "status": "starting",
            "dependency_chain": dep_chain,
        }

    def stop_service(self, service_id):
        """Stop a service by its ID."""
        with self._lock:
            svc = self._services.get(service_id)
            if svc is None:
                return None  # 404
            if svc.get("ghost"):
                return {"error": "Cannot stop a ghost app.", "status": "ghost"}
            if svc.get("status") == "stopped":
                return {"error": "Service is already stopped.", "status": "conflict"}

        self._kill(svc)
        return {"status": "stopped"}

    def restart_service(self, service_id):
        """Stop then start a service."""
        with self._lock:
            svc = self._services.get(service_id)
            if svc is None:
                return None
            if svc.get("ghost"):
                return {"error": "Cannot restart a ghost app.", "status": "ghost"}

        self._kill(svc)
        time.sleep(1)
        self._spawn(svc)
        svc["restart_count"] = svc.get("restart_count", 0) + 1
        return {"status": "restarting", "attempt": svc["restart_count"]}

    def start_group(self, group):
        """Start all non-ghost services in a group."""
        results = {}
        for svc in self._services.values():
            if svc.get("group") == group and not svc.get("ghost"):
                if svc.get("status") != "running":
                    self._spawn(svc)
                    results[svc["id"]] = "starting"
                else:
                    results[svc["id"]] = "already_running"
        return results

    def stop_group(self, group):
        """Stop all services in a group."""
        results = {}
        for svc in self._services.values():
            if svc.get("group") == group and not svc.get("ghost"):
                if svc.get("status") != "stopped":
                    self._kill(svc)
                    results[svc["id"]] = "stopped"
                else:
                    results[svc["id"]] = "already_stopped"
        return results

    # ── Health Checking ────────────────────────────────────────────────────

    def check_health(self, service_id):
        """Perform an immediate health check on a single service."""
        svc = self._services.get(service_id)
        if svc is None:
            return None
        return self._ping(svc)

    def start_health_loop(self):
        """Start the background health-check thread."""
        if self._health_thread and self._health_thread.is_alive():
            return
        self._running = True
        self._health_thread = threading.Thread(
            target=self._health_loop, daemon=True, name="health-check"
        )
        self._health_thread.start()
        log.info("Health-check loop started (every %ds).", config.HEALTH_INTERVAL)

    def stop_health_loop(self):
        """Signal the background thread to stop."""
        self._running = False

    def _health_loop(self):
        """Periodically check every non-ghost service."""
        while self._running:
            for svc in list(self._services.values()):
                if svc.get("ghost"):
                    continue
                self._ping(svc)
            time.sleep(config.HEALTH_INTERVAL)

    def _ping(self, svc):
        """HTTP GET the service's health endpoint.  Updates status in place."""
        port = svc.get("port")
        endpoint = svc.get("health_endpoint", "/api/health")
        url = f"http://localhost:{port}{endpoint}"
        start = time.time()

        try:
            resp = requests.get(url, timeout=3)
            latency = round((time.time() - start) * 1000, 1)
            if resp.status_code < 400:
                svc["health"] = "healthy"
                svc["status"] = "running"
            else:
                svc["health"] = "degraded"
                svc["status"] = "running"
            svc["last_health_check"] = time.time()
            return {
                "status": svc["health"],
                "latency_ms": latency,
                "details": {"status_code": resp.status_code},
            }
        except requests.ConnectionError:
            svc["health"] = "unreachable"
            svc["status"] = "stopped"
            svc["last_health_check"] = time.time()
            return {"status": "unreachable", "latency_ms": None, "details": {}}
        except requests.Timeout:
            svc["health"] = "degraded"
            svc["last_health_check"] = time.time()
            return {"status": "degraded", "latency_ms": 3000, "details": {"timeout": True}}
        except Exception as exc:
            log.warning("Health check failed for %s: %s", svc["id"], exc)
            svc["health"] = "unreachable"
            svc["status"] = "stopped"
            svc["last_health_check"] = time.time()
            return {"status": "unreachable", "latency_ms": None, "details": {"error": str(exc)}}

    # ── Process Management ─────────────────────────────────────────────────

    def _spawn(self, svc):
        """Spawn the service as a subprocess."""
        cmd = svc.get("start_command", "")
        if not cmd:
            log.warning("No start_command for %s — skipping.", svc["id"])
            return

        working_dir = svc.get("working_dir", "")
        if working_dir:
            working_dir = os.path.expanduser(working_dir)

        try:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                cwd=working_dir if working_dir and os.path.isdir(working_dir) else None,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            svc["pid"] = proc.pid
            svc["status"] = "starting"
            svc["started_at"] = time.time()
            log.info("Started %s (pid %d).", svc["id"], proc.pid)
        except Exception as exc:
            log.error("Failed to start %s: %s", svc["id"], exc)
            svc["status"] = "stopped"

    def _kill(self, svc):
        """Kill the service process."""
        pid = svc.get("pid")
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                log.info("Stopped %s (pid %d).", svc["id"], pid)
            except ProcessLookupError:
                log.info("Process %d already gone for %s.", pid, svc["id"])
            except Exception as exc:
                log.warning("Error stopping %s: %s", svc["id"], exc)
        svc["status"] = "stopped"
        svc["pid"] = None
        svc["started_at"] = None

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _public_view(svc):
        """Return a copy of the service dict safe for API responses."""
        if svc is None:
            return None
        return {
            "id": svc.get("id"),
            "name": svc.get("name"),
            "description": svc.get("description"),
            "group": svc.get("group"),
            "port": svc.get("port"),
            "ui_port": svc.get("ui_port"),
            "status": svc.get("status", "stopped"),
            "health": svc.get("health", "unknown"),
            "uptime_seconds": (
                round(time.time() - svc["started_at"], 1)
                if svc.get("started_at")
                else None
            ),
            "last_health_check": svc.get("last_health_check"),
            "restart_count": svc.get("restart_count", 0),
            "ghost": svc.get("ghost", False),
            "ghost_eta": svc.get("ghost_eta"),
            "favicon": svc.get("favicon"),
            "dependencies": svc.get("dependencies", []),
            "heartbeat": svc.get("heartbeat", []),
            "resources": svc.get("resources", {}),
        }

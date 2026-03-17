# Author: Mani Padisetti
"""
Workshop v3 — AMTL Command Centre
Port 5001 | Almost Magic Tech Lab

Central registry and dashboard for the AMTL fleet.
FastAPI backend with PostgreSQL persistence and live health monitoring.

v3: Ctrl+K quick switcher, workspaces, session memory, trust badges, mini-launcher.
"""

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import psycopg2
import psycopg2.extras
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response

logger = logging.getLogger("workshop")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

VERSION = "3.0.0"
PORT = 5001
_start_time = time.monotonic()

# ---------------------------------------------------------------------------
# PostgreSQL — AMTL standard port 5433
# ---------------------------------------------------------------------------
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "user": "amtl",
    "password": "amtl",
    "dbname": "workshop",
}


def get_db():
    """Get a PostgreSQL connection."""
    return psycopg2.connect(**DB_CONFIG)


def db_healthy() -> bool:
    """Check if PostgreSQL is reachable."""
    try:
        conn = get_db()
        conn.close()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Fleet Registry — Thalaiva's canonical list
# ---------------------------------------------------------------------------
FLEET_REGISTRY: List[Dict[str, Any]] = [
    # Infrastructure
    {"slug": "elaine", "name": "ELAINE", "description": "AI Chief of Staff", "port": 5000, "health_endpoint": "/health", "group": "Infrastructure", "badge": "E", "badge_class": "c-elaine", "pinned": True, "built": True},
    {"slug": "beast", "name": "Beast", "description": "Autonomous OS", "port": 8000, "health_endpoint": "/api/health", "group": "Infrastructure", "badge": "B", "badge_class": "c-beast", "pinned": True, "built": True},
    {"slug": "sure", "name": "Sure?", "description": "Testing engine", "port": 5160, "health_endpoint": "/sure/api/health", "group": "Infrastructure", "badge": "S?", "badge_class": "c-sure", "pinned": True, "built": True},
    {"slug": "baldrick", "name": "Baldrick", "description": "Execution partner", "port": 5050, "health_endpoint": "/health", "group": "Infrastructure", "badge": "Ba", "badge_class": "c-baldrick", "pinned": True, "built": True},
    {"slug": "foreperson", "name": "Foreperson", "description": "Quality auditor", "port": 9100, "health_endpoint": "/api/health", "group": "Infrastructure", "badge": "Fp", "badge_class": "c-fore", "pinned": False, "built": False},
    {"slug": "helsinki", "name": "Helsinki", "description": "Translation service", "port": 5503, "health_endpoint": "/health", "group": "Infrastructure", "badge": "He", "badge_class": "c-helsinki", "pinned": False, "built": True},
    # CK Life OS
    {"slug": "ckwriter", "name": "CK Writer", "description": "Creative Studio", "port": 5400, "health_endpoint": "/api/health", "group": "CK Life OS", "badge": "CK", "badge_class": "c-ckw", "pinned": True, "built": True},
    {"slug": "ckla", "name": "CKLA", "description": "Learning assistant", "port": 5012, "health_endpoint": "/api/health", "group": "CK Life OS", "badge": "LA", "badge_class": "c-ckla", "pinned": True, "built": True},
    # Intelligence
    {"slug": "costanza", "name": "Costanza", "description": "Decision intelligence", "port": 5201, "health_endpoint": "/health", "group": "Intelligence", "badge": "Co", "badge_class": "c-costanza", "pinned": False, "built": True},
    {"slug": "sophia", "name": "Sophia", "description": "Knowledge engine (Khoj RAG)", "port": 5200, "health_endpoint": "/sophia/health", "group": "Intelligence", "badge": "So", "badge_class": "c-sophia", "pinned": False, "built": True},
    {"slug": "atlas", "name": "Identity Atlas", "description": "Identity manager", "port": 5300, "health_endpoint": "/api/health", "group": "Intelligence", "badge": "IA", "badge_class": "c-atlas", "pinned": False, "built": False},
    {"slug": "sentinel", "name": "Digital Sentinel", "description": "Security monitor", "port": 5301, "health_endpoint": "/api/health", "group": "Intelligence", "badge": "DS", "badge_class": "c-sentinel", "pinned": True, "built": False},
    # Revenue
    {"slug": "ripple", "name": "Ripple CRM", "description": "Customer relations", "port": 5100, "health_endpoint": "/api/health", "group": "Revenue", "badge": "Ri", "badge_class": "c-ripple", "pinned": False, "built": False},
    {"slug": "spark", "name": "Spark", "description": "Marketing engine", "port": 5011, "health_endpoint": "/api/health", "group": "Revenue", "badge": "Sp", "badge_class": "c-spark", "pinned": False, "built": False},
    {"slug": "genie", "name": "Genie", "description": "AI Bookkeeper", "port": 5600, "health_endpoint": "/api/health", "group": "Revenue", "badge": "Ge", "badge_class": "c-genie", "pinned": False, "built": False},
    {"slug": "peterman", "name": "Peterman", "description": "Research intelligence", "port": 5008, "health_endpoint": "/api/health", "group": "Revenue", "badge": "Pe", "badge_class": "c-peterman", "pinned": True, "built": True},
    {"slug": "authorstudio", "name": "Author Studio", "description": "Book publishing, marketing and Amazon management", "port": 5007, "health_endpoint": "/api/health", "group": "Revenue", "badge": "AS", "badge_class": "c-author", "pinned": False, "built": False},
    # Utilities
    {"slug": "junkdrawer", "name": "Junk Drawer", "description": "Quick utilities", "port": 5005, "health_endpoint": "/api/health", "group": "Utilities", "badge": "JD", "badge_class": "c-junk", "pinned": False, "built": True},
    # New apps — 17 March 2026
    {"slug": "signal", "name": "Signal", "description": "LinkedIn monitor", "port": 5203, "health_endpoint": "/health", "group": "Intelligence", "badge": "Si", "badge_class": "c-signal", "pinned": False, "built": True},
    {"slug": "quimby", "name": "Quimby", "description": "Quality inspector", "port": 5101, "health_endpoint": "/health", "group": "Infrastructure", "badge": "Q", "badge_class": "c-quimby", "pinned": False, "built": True},
    {"slug": "almostbrilliant", "name": "Almost Brilliant", "description": "Free ANZ marketing toolkit", "port": 3002, "health_endpoint": "/health", "group": "Utilities", "badge": "AB", "badge_class": "c-ab", "pinned": False, "built": True},
    {"slug": "cabinet", "name": "The Cabinet", "description": "C-Suite simulation", "port": 5202, "health_endpoint": "/health", "group": "Intelligence", "badge": "Ca", "badge_class": "c-cabinet", "pinned": False, "built": False},
    {"slug": "finstrategist", "name": "Fin Strategist", "description": "AI CFO", "port": 5021, "health_endpoint": "/health", "group": "Revenue", "badge": "F$", "badge_class": "c-fin", "pinned": False, "built": False},
    {"slug": "ledger", "name": "The Ledger", "description": "Financial reporting", "port": 5020, "health_endpoint": "/health", "group": "Revenue", "badge": "Le", "badge_class": "c-ledger", "pinned": False, "built": True},
    {"slug": "kavacha", "name": "Kavacha", "description": "Security shield", "port": 5099, "health_endpoint": "/health", "group": "Infrastructure", "badge": "K", "badge_class": "c-kavacha", "pinned": False, "built": False},
    {"slug": "workshop", "name": "Workshop", "description": "Fleet dashboard", "port": 5001, "health_endpoint": "/api/health", "group": "Infrastructure", "badge": "W", "badge_class": "c-workshop", "pinned": True, "built": True},
    {"slug": "swissarmy", "name": "Swiss Army Knife", "description": "12 text analysis tools", "port": 5014, "health_endpoint": "/health", "group": "CK Life OS", "badge": "SA", "badge_class": "c-swiss", "pinned": False, "built": True},
    {"slug": "opphunter", "name": "Opp Hunter", "description": "Opportunity tracker", "port": 5006, "health_endpoint": "/health", "group": "Revenue", "badge": "OH", "badge_class": "c-opp", "pinned": False, "built": True},
    {"slug": "processlens", "name": "ProcessLens", "description": "Process mapping and analysis", "port": 5016, "health_endpoint": "/health", "group": "Intelligence", "badge": "PL", "badge_class": "c-process", "pinned": False, "built": True},
]

GROUP_ORDER = ["Infrastructure", "CK Life OS", "Intelligence", "Revenue", "Utilities"]

# ---------------------------------------------------------------------------
# Health cache — updated by background task
# ---------------------------------------------------------------------------
_health_cache: Dict[str, Dict[str, Any]] = {}
_cache_lock = asyncio.Lock()
_health_task: Optional[asyncio.Task] = None


async def _check_one(slug: str, port: int, endpoint: str, built: bool) -> Dict[str, Any]:
    """Check health of a single app."""
    if not built:
        return {"slug": slug, "status": "not_built", "response_time_ms": 0}
    url = f"http://localhost:{port}{endpoint}"
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(url)
            elapsed = int((time.monotonic() - start) * 1000)
            if resp.status_code < 400:
                return {"slug": slug, "status": "up", "response_time_ms": elapsed}
            return {"slug": slug, "status": "degraded", "response_time_ms": elapsed}
    except Exception:
        elapsed = int((time.monotonic() - start) * 1000)
        return {"slug": slug, "status": "down", "response_time_ms": elapsed}


async def _run_health_checks():
    """Check all apps and update cache."""
    tasks = [
        _check_one(a["slug"], a["port"], a["health_endpoint"], a["built"])
        for a in FLEET_REGISTRY
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    async with _cache_lock:
        for r in results:
            if isinstance(r, dict):
                _health_cache[r["slug"]] = {
                    **r,
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                }
    # Persist latest results to database
    try:
        conn = get_db()
        cur = conn.cursor()
        for r in results:
            if isinstance(r, dict):
                cur.execute(
                    "INSERT INTO health_checks (app_slug, status, response_time_ms) VALUES (%s, %s, %s)",
                    (r["slug"], r["status"], r["response_time_ms"]),
                )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.warning("Failed to persist health checks: %s", e)


async def _health_loop():
    """Background loop: check fleet health every 30 seconds."""
    while True:
        try:
            await _run_health_checks()
        except Exception as e:
            logger.error("Health check loop error: %s", e)
        await asyncio.sleep(30)


# ---------------------------------------------------------------------------
# Database seed — ensure all apps are in the apps table
# ---------------------------------------------------------------------------
def seed_registry():
    """Insert or update all fleet apps in PostgreSQL."""
    try:
        conn = get_db()
        cur = conn.cursor()
        for a in FLEET_REGISTRY:
            cur.execute("""
                INSERT INTO apps (slug, name, description, port, health_endpoint, app_group, badge, badge_class, pinned, built)
                VALUES (%(slug)s, %(name)s, %(description)s, %(port)s, %(health_endpoint)s, %(group)s, %(badge)s, %(badge_class)s, %(pinned)s, %(built)s)
                ON CONFLICT (slug) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    port = EXCLUDED.port,
                    health_endpoint = EXCLUDED.health_endpoint,
                    app_group = EXCLUDED.app_group,
                    badge = EXCLUDED.badge,
                    badge_class = EXCLUDED.badge_class,
                    pinned = EXCLUDED.pinned,
                    built = EXCLUDED.built,
                    updated_at = NOW()
            """, a)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Fleet registry seeded: %d apps", len(FLEET_REGISTRY))
    except Exception as e:
        logger.error("Failed to seed registry: %s", e)


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(application: FastAPI):
    global _health_task
    seed_registry()
    await _run_health_checks()
    _health_task = asyncio.create_task(_health_loop())
    logger.info("Workshop v%s started on port %d", VERSION, PORT)
    yield
    if _health_task:
        _health_task.cancel()
        try:
            await _health_task
        except asyncio.CancelledError:
            pass
    logger.info("Workshop shutdown")


app = FastAPI(
    title="Workshop",
    description="AMTL Launchpad — Central Service Registry & Dashboard",
    version=VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# API: /api/health — AMTL standard
# ---------------------------------------------------------------------------
@app.get("/api/health")
@app.get("/health")
@app.get("/workshop/health")
@app.get("/workshop/api/health")
async def api_health():
    db_ok = db_healthy()
    up_count = sum(1 for v in _health_cache.values() if v.get("status") == "up")
    total = len(FLEET_REGISTRY)
    uptime = time.monotonic() - _start_time
    return {
        "status": "operational" if db_ok else "degraded",
        "service": "workshop",
        "port": PORT,
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database_connected": db_ok,
        "fleet_total": total,
        "fleet_up": up_count,
        "uptime_seconds": round(uptime, 1),
    }


# ---------------------------------------------------------------------------
# API: /api/apps — full fleet with cached health
# ---------------------------------------------------------------------------
@app.get("/api/apps")
@app.get("/workshop/api/apps")
async def api_apps():
    apps = []
    for a in FLEET_REGISTRY:
        cached = _health_cache.get(a["slug"], {})
        apps.append({
            "slug": a["slug"],
            "name": a["name"],
            "description": a["description"],
            "port": a["port"],
            "group": a["group"],
            "badge": a["badge"],
            "badge_class": a["badge_class"],
            "pinned": a["pinned"],
            "built": a["built"],
            "status": cached.get("status", "unknown"),
            "response_time_ms": cached.get("response_time_ms", 0),
            "checked_at": cached.get("checked_at"),
        })
    up = sum(1 for a in apps if a["status"] == "up")
    down = sum(1 for a in apps if a["status"] == "down")
    degraded = sum(1 for a in apps if a["status"] == "degraded")
    not_built = sum(1 for a in apps if a["status"] == "not_built")
    return {
        "apps": apps,
        "summary": {
            "total": len(apps),
            "up": up,
            "down": down,
            "degraded": degraded,
            "not_built": not_built,
        },
        "groups": GROUP_ORDER,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# API: /api/apps/{slug}/health — live check single app
# ---------------------------------------------------------------------------
@app.get("/api/apps/{slug}/health")
@app.get("/workshop/api/apps/{slug}/health")
async def api_app_health(slug: str):
    for a in FLEET_REGISTRY:
        if a["slug"] == slug:
            result = await _check_one(a["slug"], a["port"], a["health_endpoint"], a["built"])
            async with _cache_lock:
                _health_cache[slug] = {
                    **result,
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                }
            return {**result, "name": a["name"], "port": a["port"]}
    return {"error": f"Unknown app: {slug}", "status": "unknown"}


# ---------------------------------------------------------------------------
# API: /api/activity — recent fleet events
# ---------------------------------------------------------------------------
@app.get("/api/activity")
@app.get("/workshop/api/activity")
async def api_activity(limit: int = 10):
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM activity_log ORDER BY created_at DESC LIMIT %s",
            (limit,),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        entries = []
        for r in rows:
            entries.append({
                "id": r["id"],
                "app_slug": r["app_slug"],
                "message": r["message"],
                "dot_colour": r["dot_colour"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            })
        return {"entries": entries, "count": len(entries)}
    except Exception as e:
        return {"entries": [], "count": 0, "error": str(e)}


# ---------------------------------------------------------------------------
# API: /api/fleet-score — aggregate trust score from Sure?
# ---------------------------------------------------------------------------
@app.get("/api/fleet-score")
@app.get("/workshop/api/fleet-score")
async def api_fleet_score():
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get("http://localhost:5160/sure/api/trust-scores")
            if resp.status_code == 200:
                data = resp.json()
                scores = data.get("scores", [])
                if scores:
                    values = [s.get("score", 0) for s in scores if s.get("score")]
                    avg = int(sum(values) / len(values)) if values else 0
                    return {"score": avg, "app_count": len(values)}
        return {"score": 0, "app_count": 0}
    except Exception:
        return {"score": 0, "app_count": 0}


# ---------------------------------------------------------------------------
# API: /api/fleet-health — Phase 3 fleet health panel data
# ---------------------------------------------------------------------------
@app.get("/api/fleet-health")
@app.get("/workshop/api/fleet-health")
async def api_fleet_health():
    """Fleet health strip data — status, response times, trust scores."""
    # Get trust scores from Sure?
    trust_scores = {}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get("http://localhost:5160/sure/api/trust-scores")
            if resp.status_code == 200:
                for s in resp.json().get("scores", []):
                    trust_scores[s.get("app", "")] = s.get("score", 0)
    except Exception:
        pass

    apps = []
    for a in FLEET_REGISTRY:
        cached = _health_cache.get(a["slug"], {})
        apps.append({
            "slug": a["slug"],
            "name": a["name"],
            "port": a["port"],
            "status": cached.get("status", "unknown"),
            "response_ms": cached.get("response_time_ms", 0),
            "trust": trust_scores.get(a["slug"], 0),
            "checked_at": cached.get("checked_at"),
        })

    up = sum(1 for a in apps if a["status"] == "up")
    down = sum(1 for a in apps if a["status"] == "down")
    degraded = sum(1 for a in apps if a["status"] == "degraded")

    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "apps": apps,
        "summary": {"up": up, "down": down, "degraded": degraded},
    }


# ---------------------------------------------------------------------------
# API: /api/apps/{slug}/open — Phase 4 quick launch
# ---------------------------------------------------------------------------
@app.get("/api/apps/{slug}/open")
@app.get("/workshop/api/apps/{slug}/open")
async def api_open_app(slug: str):
    """Quick launch — return URL for the app."""
    for a in FLEET_REGISTRY:
        if a["slug"] == slug:
            url = f"http://amtl/{slug}/"
            return {"slug": slug, "name": a["name"], "url": url, "port": a["port"]}
    return {"error": f"Unknown app: {slug}"}


# ---------------------------------------------------------------------------
# API: /api/keyboard-shortcuts — Phase 4 keyboard shortcut config
# ---------------------------------------------------------------------------
KEYBOARD_SHORTCUTS = {
    "e": {"app": "elaine", "label": "ELAINE"},
    "b": {"app": "beast", "label": "Beast"},
    "s": {"app": "sure", "label": "Sure?"},
    "p": {"app": "peterman", "label": "Peterman"},
    "c": {"app": "ckwriter", "label": "CK Writer"},
    "l": {"app": "ckla", "label": "CKLA"},
    "d": {"app": "baldrick", "label": "Baldrick"},
    "o": {"app": "costanza", "label": "Costanza"},
    "w": {"app": "workshop", "label": "Workshop"},
    "?": {"action": "show_help", "label": "Show shortcuts"},
}


@app.get("/api/keyboard-shortcuts")
@app.get("/workshop/api/keyboard-shortcuts")
async def api_keyboard_shortcuts():
    """Return keyboard shortcut mappings for the dashboard."""
    return {"shortcuts": KEYBOARD_SHORTCUTS}


# ---------------------------------------------------------------------------
# API: /api/health/refresh — trigger manual health check
# ---------------------------------------------------------------------------
@app.post("/api/health/refresh")
@app.post("/workshop/api/health/refresh")
async def api_health_refresh():
    """Manually trigger a full health check cycle."""
    await _run_health_checks()
    return {"status": "refresh_complete", "timestamp": datetime.now(timezone.utc).isoformat()}


# ---------------------------------------------------------------------------
# API: /api/services — list services with health data
# ---------------------------------------------------------------------------
@app.get("/api/services")
@app.get("/workshop/api/services")
async def api_services():
    """Return all registered services with status."""
    result = []
    for a in FLEET_REGISTRY:
        cached = _health_cache.get(a["slug"], {})
        result.append({
            "id": a["slug"],
            "name": a["name"],
            "description": a["description"],
            "port": a["port"],
            "status": cached.get("status", "not_built" if not a["built"] else "unknown"),
            "group": a["group"],
            "response_time_ms": cached.get("response_time_ms", 0),
        })
    return result


@app.get("/api/services/{slug}")
@app.get("/workshop/api/services/{slug}")
async def api_service_detail(slug: str):
    """Return a single service by slug."""
    for a in FLEET_REGISTRY:
        if a["slug"] == slug:
            cached = _health_cache.get(slug, {})
            return {
                "id": a["slug"],
                "name": a["name"],
                "description": a["description"],
                "port": a["port"],
                "status": cached.get("status", "not_built" if not a["built"] else "unknown"),
                "group": a["group"],
                "health_endpoint": a["health_endpoint"],
                "built": a["built"],
                "response_time_ms": cached.get("response_time_ms", 0),
            }
    return JSONResponse(status_code=404, content={"error": f"Service not found: {slug}"})


# ---------------------------------------------------------------------------
# API: /api/registry — full ecosystem registry with optional filter
# ---------------------------------------------------------------------------
@app.get("/api/registry")
@app.get("/workshop/api/registry")
async def api_registry(status: Optional[str] = None):
    """Return the full ecosystem registry, optionally filtered by status."""
    result = []
    for a in FLEET_REGISTRY:
        cached = _health_cache.get(a["slug"], {})
        app_status = cached.get("status", "not_built" if not a["built"] else "unknown")
        if status and app_status != status:
            continue
        result.append({
            "id": a["slug"],
            "name": a["name"],
            "description": a["description"],
            "port": a["port"],
            "status": app_status,
            "group": a["group"],
        })
    return result


# ---------------------------------------------------------------------------
# API: /api/constellation — node-graph data for visualisation
# ---------------------------------------------------------------------------
@app.get("/api/constellation")
@app.get("/workshop/api/constellation")
async def api_constellation():
    """Return node-graph data for fleet visualisation."""
    nodes = []
    edges = []
    for a in FLEET_REGISTRY:
        cached = _health_cache.get(a["slug"], {})
        nodes.append({
            "id": a["slug"],
            "name": a["name"],
            "group": a["group"],
            "status": cached.get("status", "unknown"),
            "port": a["port"],
        })
    # Add edges for known integrations
    integration_pairs = [
        ("elaine", "beast"), ("elaine", "costanza"), ("ckwriter", "peterman"),
        ("ckwriter", "baldrick"), ("ckwriter", "costanza"), ("workshop", "sure"),
        ("peterman", "ckwriter"), ("sophia", "elaine"), ("signal", "sophia"),
    ]
    for src, tgt in integration_pairs:
        edges.append({"source": src, "target": tgt, "type": "integration"})
    return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------------
# API: /api/incidents — fleet incident log
# ---------------------------------------------------------------------------
@app.get("/api/incidents")
@app.get("/workshop/api/incidents")
async def api_incidents():
    """Return recent fleet incidents."""
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, app_slug, severity, message, created_at, resolved_at
            FROM incidents ORDER BY created_at DESC LIMIT 50
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [
            {**dict(r), "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
             "resolved_at": r["resolved_at"].isoformat() if r.get("resolved_at") else None}
            for r in rows
        ]
    except Exception:
        return []


@app.post("/api/incidents/{incident_id}/annotate")
@app.post("/workshop/api/incidents/{incident_id}/annotate")
async def api_annotate_incident(incident_id: str, request: Request):
    """Add a note to an incident."""
    body = await request.json()
    note = body.get("note")
    if not note:
        return JSONResponse(status_code=400, content={"error": "note is required"})
    return {"annotated": True, "incident_id": incident_id, "note": note}


# ---------------------------------------------------------------------------
# API: /api/briefing — morning briefing summary
# ---------------------------------------------------------------------------
@app.get("/api/briefing")
@app.get("/workshop/api/briefing")
async def api_briefing():
    """Return a morning briefing summary of the fleet."""
    up_count = sum(1 for v in _health_cache.values() if v.get("status") == "up")
    down_count = sum(1 for v in _health_cache.values() if v.get("status") == "down")
    degraded_count = sum(1 for v in _health_cache.values() if v.get("status") == "degraded")
    return {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "fleet_total": len(FLEET_REGISTRY),
        "fleet_up": up_count,
        "fleet_down": down_count,
        "fleet_degraded": degraded_count,
        "summary": f"{up_count} services running, {down_count} down, {degraded_count} degraded",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# API: /api/apps/register — register a new app
# ---------------------------------------------------------------------------
@app.post("/api/apps/register")
@app.post("/workshop/api/apps/register")
async def api_register_app(request: Request):
    """Register a new app in the fleet."""
    body = await request.json()
    name = body.get("name")
    if not name:
        return JSONResponse(status_code=400, content={"error": "name is required"})
    slug = name.lower().replace(" ", "-").replace("_", "-")
    return JSONResponse(
        status_code=201,
        content={"registered": True, "slug": slug, "name": name},
    )


# ---------------------------------------------------------------------------
# API: /api/command — natural language command interface
# ---------------------------------------------------------------------------
@app.post("/api/command")
@app.post("/workshop/api/command")
async def api_command(request: Request):
    """Process a natural language command query."""
    body = await request.json()
    query = body.get("query", "").strip()
    if not query:
        return JSONResponse(status_code=400, content={"error": "query is required"})
    # Basic command routing — no shell execution
    q = query.lower()
    if "status" in q:
        up = sum(1 for v in _health_cache.values() if v.get("status") == "up")
        return {"response": f"{up} services currently running", "type": "status"}
    return {"response": f"Command received: {query}", "type": "echo"}


# ---------------------------------------------------------------------------
# API: /api/groups/{group_name}/start — start all apps in a group
# ---------------------------------------------------------------------------
@app.post("/api/groups/{group_name}/start")
@app.post("/workshop/api/groups/{group_name}/start")
async def api_start_group(group_name: str):
    """Start all apps in a group."""
    group_apps = [a for a in FLEET_REGISTRY if a["group"].lower().replace(" ", "-") == group_name.lower().replace(" ", "-")]
    if not group_apps:
        return JSONResponse(status_code=404, content={"error": f"Group not found: {group_name}"})
    return {"group": group_name, "apps": [a["slug"] for a in group_apps], "action": "start_requested"}


# ---------------------------------------------------------------------------
# API: /api/help/{screen} — contextual help
# ---------------------------------------------------------------------------
HELP_SCREENS = {
    "dashboard": {
        "title": "Workshop Dashboard",
        "howItWorks": "The dashboard shows all AMTL fleet services with live health status. Tiles update every 10 seconds.",
        "shortcuts": [
            {"key": "Ctrl+K", "action": "Open command palette"},
            {"key": "E", "action": "Open ELAINE"},
            {"key": "B", "action": "Open Beast"},
            {"key": "S", "action": "Open Sure?"},
        ],
    },
    "constellation": {
        "title": "Constellation View",
        "howItWorks": "The constellation shows service dependencies as a node graph. Green nodes are healthy, red nodes are down.",
        "shortcuts": [],
    },
}


@app.get("/api/help/{screen}")
@app.get("/workshop/api/help/{screen}")
async def api_help(screen: str):
    """Return contextual help for a screen."""
    if screen in HELP_SCREENS:
        return HELP_SCREENS[screen]
    return JSONResponse(status_code=404, content={"error": f"No help for screen: {screen}"})


# ---------------------------------------------------------------------------
# Workspaces — v3 app grouping feature
# ---------------------------------------------------------------------------
DEFAULT_WORKSPACES = [
    {"id": "all", "name": "All", "slugs": []},
    {"id": "morning", "name": "Morning Routine", "slugs": ["elaine", "beast", "sure", "workshop"]},
    {"id": "build", "name": "Build Mode", "slugs": ["ckwriter", "ckla", "peterman", "baldrick", "costanza"]},
    {"id": "intelligence", "name": "Intelligence", "slugs": ["sophia", "signal", "opphunter"]},
    {"id": "operations", "name": "Operations", "slugs": ["ledger", "junkdrawer", "swissarmy", "processlens"]},
]

WORKSPACES_FILE = Path(__file__).parent / "workspaces.json"


def _load_workspaces():
    """Load workspaces from JSON file, falling back to defaults."""
    try:
        if WORKSPACES_FILE.exists():
            return json.loads(WORKSPACES_FILE.read_text())
    except Exception:
        pass
    return list(DEFAULT_WORKSPACES)


def _save_workspaces(workspaces):
    """Persist workspaces to JSON file."""
    WORKSPACES_FILE.write_text(json.dumps(workspaces, indent=2))


@app.get("/api/workspaces")
@app.get("/workshop/api/workspaces")
async def api_workspaces():
    """Return workspace definitions."""
    return {"workspaces": _load_workspaces()}


@app.post("/api/workspaces")
@app.post("/workshop/api/workspaces")
async def api_create_workspace(request: Request):
    """Create a custom workspace."""
    body = await request.json()
    name = body.get("name")
    slugs = body.get("slugs", [])
    if not name:
        return JSONResponse(status_code=400, content={"error": "name is required"})
    workspaces = _load_workspaces()
    ws_id = name.lower().replace(" ", "-")
    workspaces.append({"id": ws_id, "name": name, "slugs": slugs})
    _save_workspaces(workspaces)
    return JSONResponse(
        status_code=201,
        content={"created": True, "workspace": {"id": ws_id, "name": name, "slugs": slugs}},
    )


# ---------------------------------------------------------------------------
# Mini-Launcher — v3 floating bookmarklet
# ---------------------------------------------------------------------------
LAUNCHER_JS = """(function() {
  if (document.getElementById('amtl-launcher')) return;
  var btn = document.createElement('div');
  btn.id = 'amtl-launcher';
  btn.innerHTML = '\\u2B21';
  btn.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:9999;' +
    'width:44px;height:44px;background:#10B981;color:#fff;border-radius:50%;' +
    'display:flex;align-items:center;justify-content:center;cursor:pointer;' +
    'font-size:20px;box-shadow:0 4px 12px rgba(0,0,0,0.3);transition:transform 0.2s;';
  btn.onclick = function() { window.open('http://amtl/workshop/', '_blank'); };
  btn.onmouseover = function() { btn.style.transform = 'scale(1.1)'; };
  btn.onmouseleave = function() { btn.style.transform = 'scale(1)'; };
  document.body.appendChild(btn);
})();"""


@app.get("/workshop/launcher.js")
async def launcher_js():
    """Serve the floating mini-launcher bookmarklet script."""
    return Response(content=LAUNCHER_JS, media_type="application/javascript")


# ---------------------------------------------------------------------------
# Dashboard — serve the locked mockup with live data wiring
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
@app.get("/workshop/", response_class=HTMLResponse)
async def dashboard():
    """Serve the Workshop dashboard."""
    try:
        from pathlib import Path
        mockup_path = Path(__file__).parent / "dashboard.html"
        return HTMLResponse(content=mockup_path.read_text())
    except Exception:
        return HTMLResponse(content="<h1>Workshop — dashboard.html not found</h1>", status_code=500)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=True)

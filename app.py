# Author: Mani Padisetti
"""
Workshop v2 — AMTL Launchpad
Port 5001 | Almost Magic Tech Lab

Central registry and dashboard for the AMTL fleet.
FastAPI backend with PostgreSQL persistence and live health monitoring.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
import psycopg2
import psycopg2.extras
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

logger = logging.getLogger("workshop")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

VERSION = "2.0.0"
PORT = 5001

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
    # CK Life OS
    {"slug": "ckwriter", "name": "CK Writer", "description": "Creative Studio", "port": 5004, "health_endpoint": "/api/health", "group": "CK Life OS", "badge": "CK", "badge_class": "c-ckw", "pinned": True, "built": True},
    {"slug": "ckla", "name": "CKLA", "description": "Learning assistant", "port": 5012, "health_endpoint": "/api/health", "group": "CK Life OS", "badge": "LA", "badge_class": "c-ckla", "pinned": True, "built": True},
    # Intelligence
    {"slug": "costanza", "name": "Costanza", "description": "Decision intelligence", "port": 5201, "health_endpoint": "/health", "group": "Intelligence", "badge": "Co", "badge_class": "c-costanza", "pinned": False, "built": True},
    {"slug": "sophia", "name": "Sophia", "description": "Knowledge engine", "port": 5200, "health_endpoint": "/api/health", "group": "Intelligence", "badge": "So", "badge_class": "c-sophia", "pinned": False, "built": False},
    {"slug": "atlas", "name": "Identity Atlas", "description": "Identity manager", "port": 5300, "health_endpoint": "/api/health", "group": "Intelligence", "badge": "IA", "badge_class": "c-atlas", "pinned": False, "built": False},
    {"slug": "sentinel", "name": "Digital Sentinel", "description": "Security monitor", "port": 5301, "health_endpoint": "/api/health", "group": "Intelligence", "badge": "DS", "badge_class": "c-sentinel", "pinned": True, "built": False},
    # Revenue
    {"slug": "ripple", "name": "Ripple CRM", "description": "Customer relations", "port": 5001, "health_endpoint": "/api/health", "group": "Revenue", "badge": "Ri", "badge_class": "c-ripple", "pinned": False, "built": False},
    {"slug": "spark", "name": "Spark", "description": "Marketing engine", "port": 5011, "health_endpoint": "/api/health", "group": "Revenue", "badge": "Sp", "badge_class": "c-spark", "pinned": False, "built": False},
    {"slug": "genie", "name": "Genie", "description": "AI Bookkeeper", "port": 5600, "health_endpoint": "/api/health", "group": "Revenue", "badge": "Ge", "badge_class": "c-genie", "pinned": False, "built": False},
    {"slug": "peterman", "name": "Peterman", "description": "Research intelligence", "port": 5008, "health_endpoint": "/api/health", "group": "Revenue", "badge": "Pe", "badge_class": "c-peterman", "pinned": True, "built": True},
    # Utilities
    {"slug": "junkdrawer", "name": "Junk Drawer", "description": "Quick utilities", "port": 5005, "health_endpoint": "/api/health", "group": "Utilities", "badge": "JD", "badge_class": "c-junk", "pinned": False, "built": True},
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
    return {
        "status": "ok" if db_ok else "degraded",
        "service": "workshop",
        "port": PORT,
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database_connected": db_ok,
        "fleet_total": total,
        "fleet_up": up_count,
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

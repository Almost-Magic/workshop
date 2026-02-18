# The Workshop

**AMTL Central Service Registry, Launcher, and Ecosystem Nerve Centre.**

App Zero of the Almost Magic Tech Lab ecosystem. The Workshop manages all 24 AMTL
services from a single dashboard — starting, stopping, health-checking, and
self-healing automatically.

## Architecture

```
registry.yaml (source of truth)
       │
  ServiceManager ──▶ Health Loop (30s)
       │                   │
  Flask API (:5003)   HeartbeatEngine ──▶ heartbeat.db
       │                   │
  Electron Desktop    SelfHealer (3-tier)
       │                   │
  Browser Fallback    IncidentLogger ──▶ incidents.db
```

- **Flask 3.0.2** application factory with blueprints
- **YAML registry** — canonical source for all 24 apps (20 active + 4 ghost)
- **SQLite** for incidents and heartbeat data
- **Background health loop** — 30-second polling, auto-healing
- **3-tier self-healing**: simple restart → deep restart → full recovery → ELAINE escalation

## Quick Start

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Run
python app.py
# → http://localhost:5003
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Overall health summary |
| POST | `/api/health/refresh` | Force health check cycle |
| GET | `/api/services` | All registered services |
| GET | `/api/services/{id}` | Single service detail |
| POST | `/api/services/{id}/start` | Start a service |
| POST | `/api/services/{id}/stop` | Stop a service |
| POST | `/api/services/{id}/restart` | Restart a service |
| GET | `/api/services/{id}/health` | Health check one service |
| POST | `/api/groups/{group}/start` | Start all in group |
| POST | `/api/groups/{group}/stop` | Stop all in group |
| POST | `/api/command` | Command palette action |
| GET | `/api/incidents` | Incident log |
| POST | `/api/incidents/{id}/annotate` | Annotate an incident |
| GET | `/api/briefing` | Morning briefing data |
| GET | `/api/help/{screen_id}` | Context-aware help |
| GET | `/api/constellation` | Node graph data |

## Service Groups

| Group | Apps |
|-------|------|
| Core | ELAINE, Workshop, Supervisor, Foreperson, Inspector |
| CK Personal | CK Writer, Learning Assistant, Costanza, Author Studio |
| CK Business | Ripple CRM, Junk Drawer, Opp Hunter, The Ledger, Genie |
| Intelligence | Peterman, Identity Atlas, Digital Sentinel |
| Marketing | Spark |
| Operations | ProcessLens, Signal |
| Ghost | Sophia, AMTL TTS, Dhamma Mirror, After I Go |

## Windows Service

```powershell
# Install as Windows service via nssm
.\install_service.ps1
```

## Testing

```bash
python -m pytest tests/ -v
# 116 tests across 8 test files
```

## Configuration

All configuration via environment variables with sensible defaults:

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKSHOP_PORT` | `5003` | API port (sacred — DEC-005) |
| `WORKSHOP_HOST` | `127.0.0.1` | Bind address |
| `HEALTH_INTERVAL` | `30` | Health check interval (seconds) |
| `LOG_LEVEL` | `INFO` | Logging level |

## Licence

Proprietary — Almost Magic Tech Lab. All rights reserved.

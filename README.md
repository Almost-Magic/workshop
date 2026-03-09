# The Workshop V2 — AMTL Ecosystem Registry & Dashboard

**Port 5001** | Almost Magic Tech Lab

The Workshop is App 0 — the homepage and command centre for the entire AMTL ecosystem. It provides a status-first sidebar dashboard showing all 55 AMTL apps with live health, filterable by status and category, and serves as the central service registry and launcher.

## Features

- **55-App Ecosystem Registry** — Every AMTL app tracked with status, category, test count, and spec coverage
- **Status-First Sidebar** — Filter by Live (25), Building (5), Planned (25), or by category
- **Six Categories** — Internal (26), Open Source (7), Commercial (4), Consulting (4), Content (6), Infra (8)
- **Live Health Checks** — Background polling with heartbeat history and resource monitoring
- **Service Manager** — Start, stop, restart individual services or groups
- **Command Bar** — Fuzzy-match services by name or port number
- **Incident Tracking** — Log and annotate service incidents
- **Constellation View** — Visual map of service relationships
- **Context-Aware Help** — Per-screen help with shortcuts, tips, and tooltips
- **Morning Briefing** — Daily ecosystem status summary
- **Dark/Light Theme** — AMTL Midnight (#0A0E14) default, toggle in header with localStorage persistence
- **Self-Registration API** — Apps can register themselves dynamically

## Quick Start

```bash
cd ~/workshop
source .venv/bin/activate
gunicorn wsgi:application --bind 0.0.0.0:5001 --workers 2
```

Production (systemd):
```bash
sudo systemctl start workshop
sudo systemctl status workshop
```

## API Endpoints

All routes are served under the `/workshop` subpath for NGINX reverse proxy compliance.

### Registry API (V2)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/workshop/api/registry` | All 55 ecosystem items (filterable) |
| GET | `/workshop/api/registry?status=live` | Filter by status: live, building, planned |
| GET | `/workshop/api/registry?cat=internal` | Filter by category: internal, opensource, commercial, consulting, content, infra |
| GET | `/workshop/api/registry?status=live&cat=internal` | Combined filters |
| GET | `/workshop/api/health/all` | Aggregate health check across all live services |
| POST | `/workshop/api/apps/register` | Register a new app dynamically |

### Service Manager API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/workshop/api/services` | All services with live health, heartbeat, resources |
| GET | `/workshop/api/services/<id>` | Single service detail |
| POST | `/workshop/api/services/<id>/start` | Start a service |
| POST | `/workshop/api/services/<id>/stop` | Stop a service |
| POST | `/workshop/api/services/<id>/restart` | Restart a service |
| POST | `/workshop/api/groups/<group>/start` | Start all services in a group |
| POST | `/workshop/api/groups/<group>/stop` | Stop all services in a group |
| POST | `/workshop/api/command` | Fuzzy-match command bar |

### Other Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/workshop/` | Dashboard (HTML) |
| GET | `/workshop/health` | Health check shortcut |
| GET | `/workshop/api/health` | Health check |
| GET | `/workshop/api/briefing` | Morning briefing |
| GET | `/workshop/api/incidents` | Incident log |
| GET | `/workshop/api/constellation` | Service relationship map |
| GET | `/workshop/api/help/<screen_id>` | Context-aware help |

## Testing

```bash
cd ~/workshop
source .venv/bin/activate
python -m pytest tests/ -v --ignore=tests/test_workshop.py --ignore=tests/test_beast.py
```

164+ tests across 12 test files covering:

| File | Tests | Coverage |
|------|-------|----------|
| `test_registry.py` | 34 | Registry API, filters, UI elements, subpath compliance, data integrity |
| `test_services.py` | 28 | Service CRUD, groups, command bar, edge cases |
| `test_help.py` | 30 | Context-aware help for all 4 screens |
| `test_incidents.py` | 17 | Incident logging and annotation |
| `test_briefing.py` | 12 | Morning briefing generation |
| `test_constellation.py` | 10 | Constellation view data |
| `test_health.py` | 7 | Health endpoints |
| `test_integration.py` | 5 | Heartbeat, resources, cross-service |
| `test_healer.py` | -- | Self-healing watchdog |
| `e2e/test_workshop_e2e.py` | 5 | Playwright browser tests (sidebar, filters, search, theme) |

### End-to-End Tests (Playwright)

```bash
cd ~/workshop
python -m pytest tests/e2e/ -v
```

Requires the Workshop service running on port 5001.

## Architecture

- **Framework**: Flask with application factory pattern (`create_app`)
- **WSGI Server**: Gunicorn (2 workers, 30s timeout)
- **Blueprints**: health, services, web, incidents, briefing, help, constellation, registry
- **Registry**: `data/registry.json` (55 items, JSON)
- **Service Config**: `data/services.yaml` (24 managed services)
- **Frontend**: Server-rendered Jinja2 template with client-side JS fetching from API
- **Fonts**: Lora (headings), Inter 300 (body), JetBrains Mono (data/ports) via Google Fonts CDN
- **Theme**: AMTL Midnight dark mode default, CSS custom properties, localStorage persistence
- **Health Checking**: Background thread polling services every 30s
- **Subpath**: All routes under `/workshop/` prefix for NGINX compliance

## Browser Access

Via NGINX reverse proxy: `http://amtl/workshop/`

Root redirect: `http://amtl/` loads The Workshop dashboard.

## Registry Data Format

Each item in `data/registry.json`:

```json
{
  "id": "elaine",
  "name": "ELAINE",
  "emoji": "\ud83e\udde0",
  "port": "5000",
  "description": "AI Chief of Staff",
  "category": "internal",
  "status": "live",
  "tests": "783",
  "tests_verified": true,
  "has_spec": true,
  "github_repo": "Almost-Magic/elaine"
}
```

### Valid Values

- **status**: `live`, `building`, `planned`
- **category**: `internal`, `opensource`, `commercial`, `consulting`, `content`, `infra`

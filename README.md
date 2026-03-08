# The Workshop — AMTL Central Service Registry & Launcher

**Port 5001** | Almost Magic Tech Lab

The Workshop is App 0 — the homepage and launchpad for the entire AMTL ecosystem. It provides a visual dashboard showing every AMTL app with live health status, and serves as the central service registry.

## Features

- **App Launcher Grid** — Cards for all 12 AMTL apps with live/down/coming soon status
- **Ecosystem Health Strip** — Running/down/not built counts, auto-refreshes every 30 seconds
- **ELAINE Status Widget** — Green/red dot showing ELAINE availability, links to ELAINE docs
- **Quick Actions** — Start All (triggers start-all.sh), View Logs (tmux output per app)
- **Dark/Light Theme** — AMTL Midnight (#0A0E14) default, toggle in header
- **Service Registry API** — JSON endpoints for all service metadata and health

## Quick Start

```bash
cd ~/CK/Elaine/workshop
uvicorn app:app --host 0.0.0.0 --port 5001 --reload
```

Or via tmux (production):
```bash
tmux new-session -d -s workshop
tmux send-keys -t workshop "cd ~/CK/Elaine/workshop && uvicorn app:app --host 0.0.0.0 --port 5001 --reload" Enter
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/health` | Health check (alias) |
| GET | `/` | Launcher dashboard (HTML) |
| GET | `/dashboard` | Launcher dashboard (alias) |
| GET | `/api/services` | All services with live health status |
| GET | `/api/services/{id}/health` | Single service health check |
| POST | `/api/start-all` | Trigger start-all.sh |
| GET | `/api/logs/{id}` | Recent tmux output for a service |

## Registered Apps

| App | ID | Port | Built |
|-----|----|------|-------|
| ELAINE | elaine | 5000 | Yes |
| Workshop | workshop | 5001 | Yes |
| Baldrick | baldrick | 5050 | Yes |
| Quimby | quimby | 5101 | Yes |
| Costanza | costanza | 5201 | Yes |
| Peterman | peterman | 5008 | Yes |
| CK Writer | ckwriter | 5004 | Yes |
| Sophia | sophia | 5200 | Yes |
| Identity Atlas | atlas | 5009 | No |
| Digital Sentinel | sentinel | 5300 | No |
| CK Creative Studio | studio | 5400 | No |
| Genie | genie | 5600 | No |

## Testing

```bash
cd ~/CK/Elaine/workshop
python3 -m pytest tests/ -v
```

30 tests covering health endpoints, dashboard rendering, registry validation, service API, and log retrieval.

## Architecture

- **Framework**: FastAPI (async)
- **Frontend**: Self-contained HTML/CSS/JS (no build step, no external dependencies)
- **Health checking**: httpx with 8-second timeout, concurrent via asyncio.gather
- **Fonts**: DM Serif Display, DM Sans, JetBrains Mono (Google Fonts CDN)
- **Theme**: AMTL Midnight dark mode default, light mode toggle with localStorage persistence
- **Logs**: Reads tmux capture-pane output for each service
- **Start All**: Triggers `/home/mani/amtl/start-all.sh` via subprocess

## Browser Access

Via Nginx reverse proxy: `http://amtl/workshop/`

The Workshop is also the default route — `http://amtl/` loads the Workshop dashboard.

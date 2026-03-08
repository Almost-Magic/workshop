"""
Workshop — Central Service Registry & Launcher
Port 5001 | Almost Magic Tech Lab

The Workshop is App 0 — the central registry that knows about every
AMTL service, its port, URL, health endpoint, and launch command.
It serves the launcher grid dashboard as the AMTL homepage.
"""

import asyncio
import subprocess
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="Workshop",
    description="Central Service Registry & Launcher — Almost Magic Tech Lab",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Canonical AMTL service registry — ordered per spec
# ---------------------------------------------------------------------------
SERVICES = [
    {
        "name": "ELAINE",
        "id": "elaine",
        "port": 5000,
        "health": "/health",
        "description": "AI Chief of Staff",
        "built": True,
        "emoji": "\U0001f9e0",
        "group": "Core",
        "url": "http://amtl/elaine/",
    },
    {
        "name": "Workshop",
        "id": "workshop",
        "port": 5001,
        "health": "/health",
        "description": "Central Service Registry & Launcher",
        "built": True,
        "emoji": "\u2699\ufe0f",
        "group": "Core",
        "url": "http://amtl/workshop/",
    },
    {
        "name": "Baldrick",
        "id": "baldrick",
        "port": 5050,
        "health": "/health",
        "description": "Task Delegation Agent",
        "built": True,
        "emoji": "\U0001f3af",
        "group": "AI Agents",
        "url": "http://amtl/baldrick/",
    },
    {
        "name": "Quimby",
        "id": "quimby",
        "port": 5101,
        "health": "/health",
        "description": "Quality Inspection Layer",
        "built": True,
        "emoji": "\U0001f50d",
        "group": "Quality",
        "url": "http://amtl/quimby/",
    },
    {
        "name": "Costanza",
        "id": "costanza",
        "port": 5201,
        "health": "/health",
        "description": "Mental Models Engine",
        "built": True,
        "emoji": "\U0001f4ad",
        "group": "AI Agents",
        "url": "http://amtl/costanza/",
    },
    {
        "name": "Peterman",
        "id": "peterman",
        "port": 5008,
        "health": "/health",
        "description": "Brand Intelligence Engine",
        "built": True,
        "emoji": "\U0001f3f7\ufe0f",
        "group": "Creative",
        "url": "http://amtl/peterman/",
    },
    {
        "name": "CK Writer",
        "id": "ckwriter",
        "port": 5004,
        "health": "/",
        "description": "Multi-Format Writing Studio",
        "built": True,
        "emoji": "\u270d\ufe0f",
        "group": "Creative",
        "url": "http://amtl/ckwriter/",
    },
    {
        "name": "Identity Atlas",
        "id": "atlas",
        "port": 5009,
        "health": "/health",
        "description": "Identity & Access Manager",
        "built": False,
        "emoji": "\U0001f510",
        "group": "Security",
        "url": "http://amtl/atlas/",
    },
    {
        "name": "Digital Sentinel",
        "id": "sentinel",
        "port": 5300,
        "health": "/health",
        "description": "Security Monitor",
        "built": False,
        "emoji": "\U0001f6e1\ufe0f",
        "group": "Security",
        "url": "http://amtl/sentinel/",
    },
    {
        "name": "CK Creative Studio",
        "id": "studio",
        "port": 5400,
        "health": "/health",
        "description": "Creative Asset Studio",
        "built": False,
        "emoji": "\U0001f3a8",
        "group": "Creative",
        "url": "http://amtl/studio/",
    },
    {
        "name": "Genie",
        "id": "genie",
        "port": 5600,
        "health": "/health",
        "description": "AI Bookkeeper",
        "built": False,
        "emoji": "\U0001f4b0",
        "group": "Finance",
        "url": "http://amtl/genie/",
    },
    {
        "name": "Sophia",
        "id": "sophia",
        "port": 5200,
        "health": "/health",
        "description": "Workflow & Knowledge Brain",
        "built": True,
        "emoji": "\U0001f4da",
        "group": "AI Agents",
        "url": "http://amtl/sophia/",
    },
    {
        "name": "Sure?",
        "id": "sure",
        "port": 5160,
        "health": "/sure/health",
        "description": "Unified Testing Engine",
        "built": True,
        "emoji": "\U0001f9ea",
        "group": "Quality",
        "url": "http://amtl/sure/",
    },
    {
        "name": "CK",
        "id": "ck",
        "port": 5010,
        "health": "/ck/health",
        "description": "Your Life OS",
        "built": True,
        "emoji": "\U0001f9e0",
        "group": "Personal",
        "url": "http://amtl/ck/",
    },
]


async def _ping_service(svc: dict) -> dict:
    """Ping a service's health endpoint. Returns status: live/down/not_built."""
    if not svc["built"]:
        return {**svc, "status": "not_built"}
    url = f"http://localhost:{svc['port']}{svc['health']}"
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(url)
            status = "live" if resp.status_code < 400 else "down"
            return {**svc, "status": status}
    except Exception:
        return {**svc, "status": "down"}


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
@app.get("/api/health")
async def health():
    """Workshop health check."""
    return {
        "status": "operational",
        "service": "workshop",
        "version": "2.0.0",
        "description": "Central Service Registry & Launcher",
        "total_services": len(SERVICES),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/services")
async def list_services():
    """Return all services with live health status."""
    tasks = [_ping_service(svc) for svc in SERVICES]
    results = await asyncio.gather(*tasks)
    live = sum(1 for r in results if r["status"] == "live")
    down = sum(1 for r in results if r["status"] == "down")
    not_built = sum(1 for r in results if r["status"] == "not_built")
    return {
        "services": results,
        "summary": {"live": live, "down": down, "not_built": not_built},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/services/{service_id}/health")
async def check_service_health(service_id: str):
    """Check health of a specific service."""
    for svc in SERVICES:
        if svc["id"] == service_id:
            return await _ping_service(svc)
    return {"error": f"Unknown service: {service_id}", "status": "unknown"}


@app.post("/api/start-all")
async def start_all():
    """Trigger start-all.sh on the server."""
    try:
        proc = subprocess.Popen(
            ["/bin/bash", "/home/mani/amtl/start-all.sh"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return {"status": "triggered", "pid": proc.pid}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/api/logs/{service_id}")
async def get_logs(service_id: str):
    """Get recent tmux output for a service."""
    try:
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", service_id, "-p"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            return {"service": service_id, "lines": lines[-50:]}
        return {"service": service_id, "error": "No tmux session found"}
    except Exception as e:
        return {"service": service_id, "error": str(e)}


# ---------------------------------------------------------------------------
# Dashboard HTML (self-contained — no external files needed)
# ---------------------------------------------------------------------------
DASHBOARD_HTML = """\
<!DOCTYPE html>
<html lang="en-AU">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Workshop — AMTL Launcher</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=DM+Serif+Display&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #0A0E14;
  --surface: #131820;
  --border: #1E2530;
  --text: #E8E0D4;
  --text-muted: #8A8070;
  --accent: #C9944A;
  --green: #4CAF7D;
  --red: #E05858;
  --grey: #555;
  --sidebar-w: 240px;
  --statusbar-h: 28px;
  --font-heading: 'DM Serif Display', serif;
  --font-body: 'DM Sans', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}
[data-theme="light"] {
  --bg: #F5F0EB;
  --surface: #FFFFFF;
  --border: #E0D8D0;
  --text: #1A1410;
  --text-muted: #6A6050;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: var(--font-body);
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  display: flex;
  flex-direction: row;
}

/* ── Sidebar ──────────────────────────────────────── */
.sidebar {
  width: var(--sidebar-w);
  min-width: var(--sidebar-w);
  height: 100vh;
  position: fixed;
  left: 0; top: 0;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  z-index: 10;
}
.sidebar-title {
  font-family: var(--font-heading);
  font-size: 1.25rem;
  color: var(--accent);
  padding: 1.2rem 1rem 0.6rem;
  border-bottom: 1px solid var(--border);
}
.sidebar-section-label {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: 1rem 1rem 0.4rem;
}
.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.45rem 1rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  user-select: none;
  transition: color 0.2s;
}
.group-header:hover { color: var(--text); }
.group-header .chevron {
  font-size: 0.6rem;
  transition: transform 0.2s;
}
.group-header.collapsed .chevron { transform: rotate(-90deg); }
.group-items { overflow: hidden; }
.group-items.collapsed { display: none; }
.app-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.35rem 1rem 0.35rem 1.4rem;
  font-size: 0.8rem;
  cursor: pointer;
  transition: background 0.15s;
  text-decoration: none;
  color: var(--text);
}
.app-row:hover { background: var(--border); }
.app-row .emoji { font-size: 0.85rem; width: 1.2rem; text-align: center; }
.app-row .app-name { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.app-row .app-port {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  color: var(--text-muted);
}
.app-row .status-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--grey);
  flex-shrink: 0;
}
.app-row .status-dot.live { background: var(--green); }
.app-row .status-dot.down { background: var(--red); }
.sidebar-bottom {
  margin-top: auto;
  padding: 0.8rem 1rem;
  border-top: 1px solid var(--border);
  display: flex;
  gap: 0.5rem;
}
.sidebar-bottom button {
  flex: 1;
  font-family: var(--font-body);
  font-size: 0.8rem;
  padding: 0.4rem 0;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  cursor: pointer;
  transition: border-color 0.2s;
}
.sidebar-bottom button:hover { border-color: var(--accent); color: var(--accent); }
.sidebar-bottom button.running { border-color: var(--green); color: var(--green); cursor: wait; }

/* ── Main Content ─────────────────────────────────── */
.main-content {
  margin-left: var(--sidebar-w);
  flex: 1;
  padding: 2rem 2.5rem;
  padding-bottom: calc(var(--statusbar-h) + 2rem);
  min-height: 100vh;
  overflow-y: auto;
}
#greeting {
  font-family: var(--font-heading);
  font-size: 1.8rem;
  margin-bottom: 0.3rem;
}
#statLine {
  font-family: var(--font-body);
  font-size: 2rem;
  font-weight: 700;
  color: var(--accent);
  margin-bottom: 2rem;
}
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.2rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  transition: all 0.2s;
  position: relative;
}
.card:hover { border-color: var(--accent); transform: translateY(-2px); }
.card.not-built { opacity: 0.5; }
.card.not-built:hover { border-color: var(--border); transform: none; }
.card.highlight { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-name {
  font-family: var(--font-heading);
  font-size: 1.15rem;
}
.status-badge {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-weight: 500;
  text-transform: uppercase;
}
.status-badge.live { background: rgba(76,175,125,0.15); color: var(--green); }
.status-badge.down { background: rgba(224,88,88,0.15); color: var(--red); }
.status-badge.not-built { background: rgba(85,85,85,0.15); color: var(--grey); }
.card-desc {
  font-size: 0.85rem;
  color: var(--text-muted);
  line-height: 1.4;
}
.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 0.3rem;
}
.card-port {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--text-muted);
}
.launch-btn {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  padding: 0.25rem 0.6rem;
  border-radius: 4px;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--accent);
  cursor: pointer;
  text-decoration: none;
  transition: all 0.2s;
}
.launch-btn:hover { background: var(--accent); color: var(--bg); }
.card.not-built .launch-btn { display: none; }

/* ── Status Bar ───────────────────────────────────── */
.status-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: var(--statusbar-h);
  background: var(--surface);
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--text-muted);
  z-index: 20;
  padding: 0 1rem;
}

/* ── Logs Modal ───────────────────────────────────── */
.modal-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  z-index: 100;
  align-items: center;
  justify-content: center;
}
.modal-overlay.show { display: flex; }
.modal {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  width: 90%;
  max-width: 700px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.2rem;
  border-bottom: 1px solid var(--border);
}
.modal-header h2 {
  font-family: var(--font-heading);
  font-size: 1.2rem;
  color: var(--accent);
}
.modal-close {
  background: none; border: none;
  color: var(--text-muted); cursor: pointer;
  font-size: 1.2rem;
}
.modal-body {
  padding: 1rem 1.2rem;
  overflow-y: auto;
  flex: 1;
}
.modal-body pre {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--text-muted);
}
</style>
</head>
<body>

<!-- Sidebar -->
<aside class="sidebar">
  <div class="sidebar-title">\u2699 The Workshop</div>
  <div class="sidebar-section-label">SERVICES</div>
  <div id="sidebarGroups"></div>
  <div class="sidebar-bottom">
    <button id="btnStartAll">Start All</button>
    <button id="btnViewLogs">Logs</button>
    <button id="themeToggle" title="Toggle theme">&#9790;</button>
  </div>
</aside>

<!-- Main Content -->
<main class="main-content">
  <div id="greeting"></div>
  <div id="statLine"></div>
  <div class="card-grid" id="cardGrid"></div>
</main>

<!-- Status Bar -->
<div class="status-bar" id="statusBar">Workshop v2.0.0</div>

<!-- Logs Modal -->
<div class="modal-overlay" id="logsModal">
  <div class="modal">
    <div class="modal-header">
      <h2 id="logsTitle">Logs</h2>
      <button class="modal-close" id="logsClose">&times;</button>
    </div>
    <div class="modal-body">
      <div id="logsAppList" style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1rem;"></div>
      <pre id="logsContent">Select an app above to view its logs.</pre>
    </div>
  </div>
</div>

<script>
let servicesData = [];
const GROUP_ORDER = ['Core', 'AI Agents', 'Quality', 'Creative', 'Security', 'Finance'];

// ── Greeting ──────────────────────────────────────────────────────────
function updateGreeting() {
  const h = new Date().getHours();
  let g = 'Good evening';
  if (h < 12) g = 'Good morning';
  else if (h < 17) g = 'Good afternoon';
  document.getElementById('greeting').textContent = g;
}
updateGreeting();

// ── Fetch + render ────────────────────────────────────────────────────
async function fetchServices() {
  try {
    const resp = await fetch('/api/services');
    const data = await resp.json();
    servicesData = data.services;
    renderSidebar(servicesData);
    renderCards(servicesData);
    updateStatLine(data.summary);
    updateStatusBar(data.summary);
  } catch (e) {
    console.error('Fetch failed:', e);
  }
}

function renderSidebar(services) {
  const container = document.getElementById('sidebarGroups');
  const groups = {};
  services.forEach(svc => {
    const g = svc.group || 'Other';
    if (!groups[g]) groups[g] = [];
    groups[g].push(svc);
  });
  container.innerHTML = '';
  GROUP_ORDER.forEach(groupName => {
    if (!groups[groupName]) return;
    const items = groups[groupName];
    const hdr = document.createElement('div');
    hdr.className = 'group-header';
    hdr.innerHTML = `<span>${groupName}</span><span class="chevron">&#9660;</span>`;
    const list = document.createElement('div');
    list.className = 'group-items';
    items.forEach(svc => {
      const row = document.createElement('div');
      row.className = 'app-row';
      row.dataset.id = svc.id;
      const dotClass = svc.status === 'live' ? 'live' : svc.status === 'down' ? 'down' : '';
      row.innerHTML = `
        <span class="emoji">${svc.emoji || ''}</span>
        <span class="app-name">${svc.name}</span>
        <span class="app-port">${svc.port}</span>
        <span class="status-dot ${dotClass}"></span>
      `;
      row.addEventListener('click', () => {
        const card = document.getElementById('card-' + svc.id);
        if (card) {
          card.scrollIntoView({ behavior: 'smooth', block: 'center' });
          card.classList.add('highlight');
          setTimeout(() => card.classList.remove('highlight'), 1500);
        }
      });
      list.appendChild(row);
    });
    hdr.addEventListener('click', () => {
      hdr.classList.toggle('collapsed');
      list.classList.toggle('collapsed');
    });
    container.appendChild(hdr);
    container.appendChild(list);
  });
}

function renderCards(services) {
  const grid = document.getElementById('cardGrid');
  grid.innerHTML = '';
  services.forEach(svc => {
    const card = document.createElement('div');
    card.className = 'card' + (svc.status === 'not_built' ? ' not-built' : '');
    card.id = 'card-' + svc.id;
    const badgeClass = svc.status === 'live' ? 'live' : svc.status === 'down' ? 'down' : 'not-built';
    const badgeText = svc.status === 'live' ? 'LIVE' : svc.status === 'down' ? 'DOWN' : 'COMING SOON';
    const url = svc.url || `http://amtl/${svc.id}/`;
    card.innerHTML = `
      <div class="card-header">
        <span class="card-name">${svc.emoji || ''} ${svc.name}</span>
        <span class="status-badge ${badgeClass}">${badgeText}</span>
      </div>
      <div class="card-desc">${svc.description}</div>
      <div class="card-footer">
        <span class="card-port">port ${svc.port}</span>
        <a class="launch-btn" href="${url}" target="_blank" onclick="event.stopPropagation()">Open &rarr;</a>
      </div>
    `;
    if (svc.status !== 'not_built') {
      card.style.cursor = 'pointer';
      card.addEventListener('click', () => window.open(url, '_blank'));
    }
    grid.appendChild(card);
  });
}

function updateStatLine(summary) {
  document.getElementById('statLine').textContent = summary.live + ' services running';
}

function updateStatusBar(summary) {
  document.getElementById('statusBar').textContent =
    `Workshop v2.0.0 \\u2014 ${summary.live} live \\u00b7 ${summary.down} down \\u00b7 ${summary.not_built} not built`;
}

// ── Theme toggle ──────────────────────────────────────────────────────
const themeBtn = document.getElementById('themeToggle');
const saved = localStorage.getItem('amtl-theme');
if (saved === 'light') {
  document.documentElement.setAttribute('data-theme', 'light');
  themeBtn.innerHTML = '&#9788;';
}
themeBtn.addEventListener('click', () => {
  const current = document.documentElement.getAttribute('data-theme');
  if (current === 'light') {
    document.documentElement.removeAttribute('data-theme');
    localStorage.setItem('amtl-theme', 'dark');
    themeBtn.innerHTML = '&#9790;';
  } else {
    document.documentElement.setAttribute('data-theme', 'light');
    localStorage.setItem('amtl-theme', 'light');
    themeBtn.innerHTML = '&#9788;';
  }
});

// ── Start All ─────────────────────────────────────────────────────────
document.getElementById('btnStartAll').addEventListener('click', async function() {
  this.textContent = 'Starting...';
  this.classList.add('running');
  try {
    await fetch('/api/start-all', { method: 'POST' });
    this.textContent = 'Done!';
    setTimeout(() => { this.textContent = 'Start All'; this.classList.remove('running'); }, 5000);
    setTimeout(fetchServices, 8000);
  } catch (e) {
    this.textContent = 'Error';
    setTimeout(() => { this.textContent = 'Start All'; this.classList.remove('running'); }, 3000);
  }
});

// ── View Logs ─────────────────────────────────────────────────────────
document.getElementById('btnViewLogs').addEventListener('click', () => {
  const modal = document.getElementById('logsModal');
  modal.classList.add('show');
  const list = document.getElementById('logsAppList');
  list.innerHTML = '';
  servicesData.filter(s => s.built).forEach(svc => {
    const btn = document.createElement('button');
    btn.textContent = svc.name;
    btn.style.cssText = 'font-family:var(--font-mono);font-size:0.8rem;padding:0.3rem 0.7rem;border-radius:4px;border:1px solid var(--border);background:var(--surface);color:var(--text);cursor:pointer;';
    btn.addEventListener('click', () => loadLogs(svc.id, svc.name));
    list.appendChild(btn);
  });
});

async function loadLogs(id, name) {
  document.getElementById('logsTitle').textContent = `Logs \\u2014 ${name}`;
  document.getElementById('logsContent').textContent = 'Loading...';
  try {
    const resp = await fetch(`/api/logs/${id}`);
    const data = await resp.json();
    if (data.lines) {
      document.getElementById('logsContent').textContent = data.lines.join('\\n');
    } else {
      document.getElementById('logsContent').textContent = data.error || 'No logs available';
    }
  } catch (e) {
    document.getElementById('logsContent').textContent = 'Failed to load logs';
  }
}

document.getElementById('logsClose').addEventListener('click', () => {
  document.getElementById('logsModal').classList.remove('show');
});
document.getElementById('logsModal').addEventListener('click', (e) => {
  if (e.target === e.currentTarget) e.currentTarget.classList.remove('show');
});

// ── Poll every 10 seconds ─────────────────────────────────────────────
fetchServices();
setInterval(fetchServices, 10000);
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Render the Workshop launcher dashboard."""
    return HTMLResponse(content=DASHBOARD_HTML)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5001,
        reload=True,
    )

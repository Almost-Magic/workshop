# Workshop v2 — Completion Report
**Version:** 2.0.0
**Author:** Mani Padisetti / Almost Magic Tech Lab
**Date:** 2026-03-16
**Trust Score:** Pending (Sure? audit not yet run)
**Phase:** P7 Complete

---

## What Workshop Does

Workshop is the AMTL fleet launchpad. It provides a single dashboard showing the live status of all 16 AMTL applications across 5 groups (Infrastructure, CK Life OS, Intelligence, Revenue, Utilities). It polls each app's health endpoint every 30 seconds, caches the results, and displays them in a dark-theme dashboard with a pinned bar for the 8 most-used apps, a collapsible sidebar grouped by function, and a real-time activity feed. Ghost apps (not yet built) are clearly marked and show a "Coming soon" toast instead of attempting navigation. The dashboard includes a fleet health score, quick-launch tiles, and a light/dark theme toggle.

---

## Build Summary

| Metric | Value |
|---|---|
| Stack | FastAPI + HTML/CSS/JS + PostgreSQL |
| Port | 5001 |
| NGINX subpath | /workshop/ |
| Database | PostgreSQL on localhost:5433, database: workshop |
| Test cases | 44 passed |
| Fleet apps registered | 16 (9 built, 7 ghost) |
| Fleet groups | 5 |
| Pinned apps | 8 |
| Health check interval | 30 seconds |
| AI engines | Claude CLI (primary), Ollama (fallback) — not yet wired |
| Key endpoints | /api/health, /api/apps, /api/apps/{slug}/health, /api/activity, /api/fleet-score |
| systemd service | amtl-workshop.service |

---

## Known Limitations

1. **No persistent health history.** Health checks are cached in memory and the latest result is written to PostgreSQL, but there is no historical time-series table for health check results. You cannot view uptime graphs or trend health over days.

2. **Fleet score returns zero.** The `/api/fleet-score` endpoint attempts to fetch trust scores from Sure? (`localhost:5160/sure/api/trust-scores`). If Sure? has no cached scores or hasn't run an audit, the fleet score returns 0. There is no fallback calculation based on health status alone.

3. **No WebSocket push.** The dashboard polls `/api/apps` every 10 seconds and `/api/fleet-score` every 30 seconds. There is no real-time push mechanism. A status change takes up to 10 seconds to appear in the UI.

4. **AI features are wired but not active.** The spec calls for Claude CLI and Ollama integration for a chat/command interface. The backend has no AI endpoint yet. The dashboard has no chat panel.

5. **Activity feed is ephemeral.** Activity entries are written to PostgreSQL but there is no retention policy. The activity_log table will grow unbounded over time.

---

## Three Genuine Weaknesses

1. **The dashboard is a single HTML file with inline CSS from the mockup.** At approximately 700 lines, `dashboard.html` combines structure, style, and JavaScript in one file. This was intentional (the mockup was locked and CSS had to be preserved verbatim), but it makes future UI changes harder than a component-based approach would.

2. **Ghost app health endpoint returns hardcoded "not_built" without verification.** If a ghost app (e.g., Sophia, Foreperson) is actually deployed at its registered port, Workshop will still show it as "not_built" because the `built: false` flag in the registry is static. There is no auto-discovery that would detect a newly deployed app.

3. **No authentication or rate limiting.** Anyone on the LAN can hit any endpoint. The `/api/apps/{slug}/health` endpoint makes outbound HTTP requests to other apps, which could be abused to probe the network. This is acceptable for a single-user LAN deployment but cannot be exposed without auth.

---

## Deliberately Out of Scope

- **Multi-user support.** Workshop is a single-user launchpad for Mani's AMTL ecosystem.
- **Cloud deployment.** Designed for a single Ubuntu server on a home LAN.
- **Mobile-specific layout.** Dashboard is browser-based, desktop-first.
- **Chat/command interface.** Spec mentions it but it is a future phase, not v2.0.0.
- **App management actions.** Workshop is read-only — it shows status, it does not start/stop/deploy apps.

---

*Workshop 2.0.0 — Sprint Complete.*
*Almost Magic Tech Lab, 2026.*

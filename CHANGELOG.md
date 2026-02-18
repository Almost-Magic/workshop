# Changelog

All notable changes to The Workshop are documented here.

## [1.0.0] — 2026-02-18

### Added

- **Phase 0**: Project skeleton — Flask factory, config, venv, nssm service, watchdog
- **Phase 1**: YAML registry (24 apps), ServiceManager, all API routes, command palette, browser fallback dashboard
- **Phase 2**: Incident Logger (SQLite), 3-tier Self-Healer with ELAINE escalation
- **Phase 3**: Heartbeat Engine (24h sparklines), Resource Monitor (Supervisor polling)
- **Phase 4**: Morning Briefing service with ELAINE/Foreperson graceful fallbacks
- **Phase 5**: Context-aware Help API (4 screens: dashboard, service-manager, constellation, incidents)
- **Phase 6**: Constellation API — node graph data with dependency edges and ghost flags
- **Phase 7**: Help API tests with firstVisitTooltip coverage (31 parametrised tests)
- **Phase 8**: README, CHANGELOG, Foreperson spec, v1.0.0 release

### Technical

- 116 tests, zero flake8 warnings
- Flask 3.0.2, YAML registry, SQLite storage
- Background health loop (30s), dependency resolution
- Australian English throughout

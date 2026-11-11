---
status: template   # ha-onboard changes this to "ready" once filled in
---

# This home

The facts an agent needs that aren't obvious from the export. Kept short and current —
the `ha-onboard` skill fills it in on first run; update it whenever something here changes.

**Never put secrets here** (passwords, tokens, codes, MCP URLs, your public domain if you'd
rather it stayed private). This file is committed.

## System

| | |
|---|---|
| Install type | _HA OS / Supervised / Container / Core_ |
| HA version | see `homeassistant/export-info.yaml` |
| Local URL | _e.g. `http://homeassistant.local:8123` — agents use this first_ |
| Remote access | _none / Nabu Casa / reverse proxy / Cloudflare tunnel — agents treat it as read-only fallback_ |
| Node-RED | _yes (add-on) / no_ |
| Marketplace (HACS) | _yes / no — custom cards live in `/local/community/`_ |
| Recorder | _default SQLite / MariaDB / PostgreSQL_ |
| Backups | _schedule, and where the off-site copy goes_ |

## AI access

| Client | How it connects | Scope |
|---|---|---|
| Coding agent on this machine | _ha-mcp, local network URL, added at user scope_ | _full admin (LAN only)_ |
| Phone / claude.ai | _official MCP Server, `/api/mcp/assist`, non-admin user — or none_ | _entities exposed to Assist only_ |

## People and notifications

Use roles or first names only. Notify targets are service names, not secrets.

| Who | Notify action | Notes |
|---|---|---|
| _Owner_ | _`notify.mobile_app_<phone>`_ | _gets critical alerts_ |

## Conventions in use

- Entity naming: see [conventions.md](conventions.md)
- Dashboards: _main dashboard and its look, e.g. "sections view, tile cards"_
- Automations live in: _HA automations / Node-RED / both (say which kind goes where)_

## Keep list

Things that look dead but must not be removed (seasonal automations kept disabled,
devices that are only sometimes online, dashboards used by wall panels…):

- _none yet_

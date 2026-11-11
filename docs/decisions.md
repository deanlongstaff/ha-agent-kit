# Decisions

Short records of choices that shape the system, newest first. Add one whenever you make
a choice someone (or an agent) might later question — it stops the next session from
"fixing" it back.

Format: `### YYYY-MM-DD · Decision in one line`, then two to five sentences: what, why,
what was rejected.

### YYYY-MM-DD · The repo mirrors the live system; live stays the source of truth
Home Assistant and Node-RED are edited in their own UIs and APIs, then exported here by
`tools/collect.js` + `tools/sync.py`. Managed folders are regenerated on each sync so
deletions show up. Secrets are redacted at export and blocked at commit (pre-commit hook,
CI, gitleaks). The repo is private.

### YYYY-MM-DD · Two MCP servers with different reach
Agent work (building automations, dashboards, debugging) goes through ha-mcp on the local
network only. Phone and web AI goes through Home Assistant's official MCP Server's
device-control endpoint as a non-admin user, so it can only touch entities exposed to
Assist. See [SECURITY.md](../SECURITY.md).

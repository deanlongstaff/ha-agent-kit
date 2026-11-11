# Connecting your AI to Home Assistant (MCP)

[MCP](https://modelcontextprotocol.io) is how an AI agent gets "hands" on Home Assistant.
There are two servers worth knowing, and they do **very different jobs**:

| | **ha-mcp** (community) | **MCP Server** (built into HA) |
|---|---|---|
| Job | *Building and maintaining* your setup | *Using* your home day to day |
| Can it edit automations, dashboards, helpers? | Yes | No |
| Reads history, logs, traces? | Yes | Only the admin tool set |
| Which entities? | All of them | Only those exposed to Assist (device-control endpoint) |
| Typical client | Your coding agent on your computer | Claude on your phone / claude.ai |
| Where it should listen | **Local network only** | Wherever your HA is reachable |
| Docs | [homeassistant-ai/ha-mcp](https://github.com/homeassistant-ai/ha-mcp) | [MCP Server integration](https://www.home-assistant.io/integrations/mcp_server/) |

This kit is built around **ha-mcp for the agent in this repo**. The built-in server is
optional and covered at the end.

> Products move fast. Steps below were right in November 2026 (HA 2026.11, ha-mcp 9.x).
> If a screen looks different, the linked docs win.

---

## 1. ha-mcp for your coding agent

### Install it (recommended: the integration)

1. **Create a dedicated user** for it: Settings › People › Add person, turn on
   *Allow login*, **Local access only**, **Administrator**. Call it something like
   `ha-mcp`. Don't use your own login — if the credential ever leaks, you revoke one
   account instead of yours.
2. **Install HA-MCP** from the Marketplace (Settings › Marketplace — called HACS before
   HA 2026.11), then restart Home Assistant.
3. Settings › Devices & services › **Add integration** › *HA-MCP* › *HA-MCP Server*.
   Sign in with the dedicated user from step 1 (ha-mcp then creates its own token).
4. Under connection options, turn on **Network access: Local network**. Leave remote
   access **off** unless you really need it (see [SECURITY.md](../../SECURITY.md)).
5. Open the entry's **Configure** screen and copy the connect URL. It looks like
   `http://<ha-ip>:9584/private_<random>`.

> 🔑 **That URL is a password.** Anyone on your network with it has admin over your home.
> Never commit it, paste it into an issue, or put it in a project `.mcp.json`. The
> pre-commit hook blocks `/private_…` URLs just in case.

Other install methods (the add-on, Docker, `uvx`) are in the
[ha-mcp README](https://github.com/homeassistant-ai/ha-mcp). Run only one of them.

### Start read-only (recommended for your first week)

Append `/readonly` to the URL: `http://<ha-ip>:9584/private_<random>/readonly`. Your agent
can explore, audit and export, but every write is blocked. Swap to the full URL when you're
comfortable with how it works.

### Connect Claude Code

Add it at **user scope**, so the URL lives in your user config, not in the repo:

```bash
claude mcp add --transport http --scope user home-assistant "http://<ha-ip>:9584/private_<random>"
```

Check it with `claude mcp list` (or `/mcp` inside a session). The tools show up as
`ha_*`. In the Claude desktop app's Code tab the same user-scope config is used.

### Other agents

AGENTS.md is read by most coding agents (Codex, Cursor, Gemini CLI, Copilot, Windsurf…).
Add the same connect URL as a **streamable HTTP** MCP server in that tool's *user/global*
settings, never in a file inside this repo. The `.claude/skills/` folder is Claude-specific;
other agents can still read the skill files if you point them at them.

### Check it works

Ask your agent: *"Use the Home Assistant MCP tools to tell me my HA version and how many
automations I have."* Then run `python3 tools/doctor.py`.

---

## 2. No MCP? Two fallbacks

The kit works without MCP — it's just slower:

- **Browser.** If your agent can drive a browser (Claude's built-in browser, Claude in
  Chrome), it opens your local HA URL, you log in, and it uses the page's own `hass`
  connection. Nothing to configure, no tokens. The collector runs this way too.
- **Terminal collector.** `node tools/collect-cli.mjs` exports everything with a
  long-lived token (`HA_URL` / `HA_TOKEN` in a git-ignored `.env`, or from your password
  manager). It only reads; changes still go through the UI.

---

## 3. Optional: the built-in MCP Server for your phone

Want *"turn off the downstairs lights"* from Claude on your phone? Use Home Assistant's own
MCP Server, **not** ha-mcp's remote access. It goes through Assist, so the AI can only reach
what you've exposed to voice assistants.

1. Your HA must be reachable over HTTPS from the internet (Nabu Casa, a reverse proxy or a
   tunnel) — claude.ai connects from the cloud.
2. Create a **non-admin** user for it (e.g. `claude-phone`).
3. Settings › Devices & services › Add integration › **Model Context Protocol Server**.
4. Use the **device-control** URL (`https://<your-ha>/api/mcp/assist`), not the main
   `/api/mcp` URL (which exposes admin tools and needs an administrator).
5. In claude.ai: Settings › Connectors › Add custom connector › paste the URL › sign in
   **as the non-admin user**.
6. Curate exposure: Settings › Voice assistants › Expose. Turn **off** "expose new
   entities" and leave out locks, alarm panels, garage doors, cameras, sirens and anything
   that powers your network. Your agent can audit this for you:
   *"List every entity exposed to Assist that could open, unlock or disarm something."*

---

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `ha_*` tools don't appear | Server added at project scope in another folder, or the session started before you added it — restart the session |
| Connection hangs | Two entries for the same server in one client — remove one |
| 401 / auth errors | The dedicated user was disabled, or the token/URL was regenerated |
| Works at home, fails elsewhere | Expected: ha-mcp is local-network only. Use the browser fallback or wait until home |
| Browser calls blocked with 403 | You're on the public URL behind a WAF/proxy — use the local URL |

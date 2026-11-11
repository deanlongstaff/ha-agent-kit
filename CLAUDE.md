# CLAUDE.md

@AGENTS.md

## Claude-specific notes

- Skills in `.claude/skills/` load automatically. `ha-onboard` runs the first-time
  setup; `ha-sync` covers collect → sync → commit and runs at the end of every change.
- Load `home-assistant-best-practices` first on any Home Assistant request.
- MCP servers are added at **user scope** (`claude mcp add --scope user …`), never in a
  repo `.mcp.json`: an ha-mcp connect URL *is* the credential. If `ha_*` tools aren't
  available in a session, fall back to the browser (AGENTS.md §6).
- Browser work happens in Claude's browser tool on the **local** HA URL. Large JavaScript
  results (the collector's output) are saved to a tool-results file — pass that file
  straight to `python3 tools/sync.py`; don't read the payload into context.
- Batch browser JavaScript into as few calls as possible: private-network pages may need
  the owner's approval per action.

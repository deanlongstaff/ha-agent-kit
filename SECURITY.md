# Security model

Giving an AI admin access to the house you sleep in deserves some thought. This is how the
kit keeps that sane. The short version:

> **The agent gets full access on your local network, your phone gets only what you
> expose, your repo is private, and secrets never reach git.**

## 1. Who can do what

```
                     ┌──────────────────────────────┐
  Coding agent  ───▶ │ ha-mcp  (LAN only, admin)    │──┐
  on your computer   └──────────────────────────────┘  │
                                                       ├──▶  Home Assistant
  Claude on your ──▶ ┌──────────────────────────────┐  │
  phone / web        │ MCP Server /api/mcp/assist   │──┘
                     │ (non-admin, Assist entities) │
                     └──────────────────────────────┘
```

| Rule | Why |
|---|---|
| ha-mcp listens on the **local network only**; remote access off | An admin MCP endpoint on the internet is one leaked URL away from someone controlling your locks |
| ha-mcp signs in as a **dedicated local-only admin user** | Revoke one account if it leaks; your own login stays untouched |
| Start with the **`/readonly`** URL | Learn what the agent does before it can change anything |
| Phone/web AI uses the built-in **device-control** endpoint as a **non-admin** user | It can only reach entities exposed to Assist |
| Curate **Assist exposure**; turn off "expose new entities" | Exposure *is* AI reach. Locks, alarms, garage doors, cameras, sirens and network power stay unexposed unless you decide otherwise |
| Don't enable ha-mcp's own LLM-API exposure for Assist | That would hand ha-mcp's admin tools to every Assist-connected AI |

## 2. Credentials

- **The ha-mcp connect URL is a credential.** Add it at *user* scope in your agent
  (`claude mcp add --scope user …`). Never in a repo `.mcp.json`, an issue or a screenshot.
- **Long-lived tokens** (only for `tools/collect-cli.mjs`) live in a git-ignored `.env` or,
  better, come from your password manager at run time.
- **The agent never types passwords.** You log in to HA in the browser; you enter
  integration credentials and Node-RED credential env vars yourself. AGENTS.md tells the
  agent to ask you rather than to ask for the secret.
- **Rotate if in doubt.** Regenerate the ha-mcp URL, revoke tokens under Profile ›
  Security, and check Settings › People for users you don't recognise.

## 3. What reaches git — four layers

1. **Redaction at export** (`tools/sync.py` + `tools/redact.py`): secret-shaped YAML values
   become `!secret <name>`, add-on options and Node-RED env vars become `<redacted>`,
   e-mail addresses are removed. Node-RED never exports credential values;
   `secrets.yaml` and `.storage/` are never collected.
2. **Your denylist** (`.secrets-denylist`, git-ignored): your surname, street, postcode,
   Wi-Fi name, alarm code — things that don't *look* secret but identify you.
3. **Pre-commit hook** (`tools/check_secrets.py --staged`): blocks tokens, keys, JWTs,
   private keys, URLs with passwords, ha-mcp and webhook URLs, e-mail addresses, phone
   numbers, precise coordinates and every denylist entry.
4. **CI** re-runs the scan and [gitleaks](https://github.com/gitleaks/gitleaks) over the
   full history on every push.

If a check fails: fix the redaction rule (`tools/redact.py`), re-sync, and commit again.
Never `--no-verify`, never allowlist a real value. If a secret ever *was* pushed, rotate
it — rewriting history doesn't un-leak it.

## 4. Keep your home repo private

This kit is public; **your copy of it should be private.** Even fully redacted, an export
describes your home: rooms, cameras and where they point, door sensors, when the alarm
arms, when "vacation mode" kicks in, which devices are on which network. `tools/doctor.py`
warns if your remote is public.

Want to share something? Copy the one automation or card into a gist, read it first, then share.

## 5. The agent's own guard rails

AGENTS.md makes the agent:

- confirm before deleting, restarting, restoring backups or installing updates;
- snapshot to git before every change and commit after, so everything is revertible;
- change only what you asked for, and propose the rest;
- ask before exposing anything that unlocks, opens, disarms or powers down.

Your agent client adds its own layer — Claude Code asks before tool calls unless you've
allowed them. Allow the read-only `ha_get_*`/`ha_search` tools freely; keep approvals on
for writes and deletes until you trust the workflow.

## Reporting a vulnerability in the kit

Please open a private security advisory on this repository rather than a public issue.

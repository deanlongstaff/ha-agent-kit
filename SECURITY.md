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

- **The ha-mcp connect URL is a credential.** `python3 tools/connect.py` adds it at *user*
  scope with hidden input, so it never passes through the agent's chat or your shell
  history. The agent is denied running that script; you run it yourself. Never in a repo `.mcp.json`, an issue or a screenshot.
- **Long-lived tokens** (only for terminal exports with `tools/collect-cli.mjs`) are stored
  by `tools/connect.py` with hidden input in the git-ignored `.env` (owner-only permissions on
  macOS/Linux), or come from your password manager at run time. Create them as the dedicated
  ha-mcp user, so revoking one never touches your own login.
- **Agent permissions.** Claude Code gets `.claude/settings.json`, which denies reading
  `.env`, `secrets.yaml` and the denylist, running `connect.py`, and `--no-verify`. Other
  agents follow the same rules from `AGENTS.md`; if yours has its own permission or sandbox
  settings (Codex approval modes, Gemini CLI policies), mirror those denials there.
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
   private keys, URLs with passwords, ha-mcp and webhook URLs and every denylist entry —
   plus personal data according to your [privacy level](#privacy-levels).
4. **CI** re-runs the scan and [gitleaks](https://github.com/gitleaks/gitleaks) over the
   full history on every push.

### Privacy levels

People differ in how much of their home they're happy to have in git. Pick a level in
`privacy.yaml` (onboarding asks); change it any time.

| | relaxed | standard (default) | strict |
|---|---|---|---|
| For | A private repo only you read | A private repo | Publishing your config |
| Secrets: keys, tokens, passwords, MCP/webhook URLs | 🚫 block | 🚫 block | 🚫 block |
| Your `.secrets-denylist` | 🚫 block | 🚫 block | 🚫 block |
| E-mails, phone numbers, precise coordinates | ⚠️ warn | 🚫 block | 🚫 block |
| People's names, zone names, your home's name | ✅ allowed | ✅ allowed | 🚫 block, hidden in inventory |
| Public GitHub repo (`doctor.py`) | ❌ | ❌ | ⚠️ allowed |

Secrets are never negotiable: there's no level at which a leaked token is fine.

**How strict works.** Every sync learns the names of the people and zones in Home Assistant
and your home's name, and keeps them in the git-ignored `.export/privacy-terms.txt`. The
generated inventory and reference pages show them as `(hidden)`. Anywhere else — a dashboard
card, an automation called "Notify Sam" — the commit is blocked, because those files have to
stay restorable: rename the thing in Home Assistant (roles work well: "Notify parents"), or
allowlist a deliberate exception. Strict lowers the risk of publishing; it can't remove it.
Even at strict, read the diff before every public push: room layouts, cameras and routines
still describe your home.

If a check fails: fix the redaction rule (`tools/redact.py`), re-sync, and commit again.
Never `--no-verify`, never allowlist a real value. If a secret ever *was* pushed, rotate
it — rewriting history doesn't un-leak it.

## 4. Keep your home repo private

This kit is public; **your copy of it should be private.** Even fully redacted, an export
describes your home: rooms, cameras and where they point, door sensors, when the alarm
arms, when "vacation mode" kicks in, which devices are on which network. `tools/doctor.py`
fails a public remote unless you've chosen the `strict` [privacy level](#privacy-levels)
on purpose.

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

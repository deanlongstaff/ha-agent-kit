# Agent instructions

You are working on a **live smart home**: Home Assistant (and, if installed, Node-RED).
People live here. Lights, heating, locks and alarms you touch do real things.

This repo is the **mirror and documentation** of that system. The live system is the
source of truth; the repo is how changes are reviewed, explained and rolled back.

Read this file fully before changing anything, then read [docs/home.md](docs/home.md)
for this home's specifics (install type, URLs, people, notify targets, quirks).
`CLAUDE.md` points here, so every agent gets the same rules.

> **First run?** If `docs/home.md` still says `status: template`, the repo hasn't been set
> up yet. Load the `ha-onboard` skill and follow it before doing anything else.

## 1. The golden rules

1. **Every change ends in git.** Any change you make to Home Assistant or Node-RED
   ends with: collect → sync → checks → docs → commit (→ push if a remote exists).
   See section 5. A task is not finished until the commit exists.
2. **Never commit sensitive data.** No passwords, tokens or keys of any kind, alarm or
   door codes, e-mail addresses, phone numbers, home coordinates, addresses, or MCP
   connect URLs. `tools/sync.py` redacts, `tools/check_secrets.py` blocks. If a check
   fails, fix the redaction — never bypass the hook (`--no-verify`) and never put a real
   value in an allowlist.
3. **Never handle credentials.** The owner logs in and types secrets themselves (Node-RED
   credential env vars, integration passwords, tokens). Ask them to; don't ask them to
   paste a secret into chat.
4. **Confirm before anything irreversible or ambiguous**: deleting entities, devices,
   flows, dashboards or integrations; restarting HA; restoring or deleting backups;
   installing updates. Things that look dead often aren't (section 7).
5. **Snapshot before you change.** Sync the repo *before* a change so the commit shows
   exactly what you changed, and keep a copy of anything you're about to overwrite.
6. **Change only what you were asked to.** Edit the one card, not the whole dashboard.
   Deploy only the Node-RED nodes you changed. No drive-by "improvements" — suggest them.
7. **Native first.** Native triggers, conditions and helpers over Jinja templates; native
   Node-RED nodes over big function nodes. A person must be able to read the automation
   in the UI. Details in the `home-assistant-best-practices` skill and
   [docs/node-red.md](docs/node-red.md).
8. **Exposure is reach.** Anything exposed to Assist can be controlled by every AI or
   voice assistant connected to this home. Ask before exposing locks, alarms, garage
   doors, cameras, sirens or power to infrastructure. See [SECURITY.md](SECURITY.md).

## 2. The system

The specifics live in [docs/home.md](docs/home.md): install type, local URL, which
add-ons exist, who lives here and how to notify them. Always read it. Bigger picture:
[docs/architecture.md](docs/architecture.md).

## 3. Skills to load

In `.claude/skills/` (third-party ones are pinned and listed in
[VENDORED.md](.claude/skills/VENDORED.md)):

| Task | Load |
|---|---|
| First run, or `docs/home.md` is still a template | `ha-onboard` |
| Any HA request — load it first, before exploring | `home-assistant-best-practices` |
| Exporting, committing, "sync", "back up to GitHub" | `ha-sync` |
| Node-RED flows | `node-red` |
| Dashboards with Bubble Card (optional style) | `ha-bubble-dashboard` |

This repo's rules beat the skills where they differ. Node-RED changes are deployed
through the admin API (section 6), not handed to the user as JSON to import, when you
have access. ha-mcp ships its own copy of the best-practices skill
(`ha_get_skill_guide`) — use the pinned copy here instead.

## 4. Where things are

```
homeassistant/
  automations/ scripts/ scenes/   one YAML per item (from the API, redacted)
  dashboards/        one YAML per dashboard (= Raw configuration editor content)
  helpers/           input_* helpers + UI (config-entry) helpers
  inventory/         areas, entities.csv, devices.csv, integrations, add-ons
  config/ esphome/   raw config files, when Studio Code Server was running (redacted)
node-red/            only if Node-RED is installed
  flows/<tab>.json   one importable file per tab
  functions/         GENERATED read-only .js mirrors of function nodes (for grep)
docs/                hand-written docs + docs/reference/ (GENERATED, don't edit)
tools/               collect.js, collect-cli.mjs, sync.py, check_secrets.py, validate.py, doctor.py
```

Use the repo to answer "where is X used?" before you touch X:
`grep -rn "sensor.foo" homeassistant node-red` covers dashboards, automations, helpers and flows.

## 5. Keeping the repo in sync (every change)

The `ha-sync` skill has the exact steps. In short:

1. **Before:** collect + sync; if anything drifted, commit it as `chore(sync): pre-change snapshot`.
2. Make the change in the live system.
3. **After:** collect + sync again (`tools/collect.js` in a browser tab, or
   `node tools/collect-cli.mjs`; then `python3 tools/sync.py <file>`).
4. Review `git diff`: your change and nothing surprising.
5. `python3 tools/check_secrets.py && python3 tools/validate.py` (the pre-commit hook runs both).
6. Update hand-written docs if behaviour or conventions changed; add a line to
   [CHANGELOG.md](CHANGELOG.md); record real choices in [docs/decisions.md](docs/decisions.md).
7. Commit (`feat(ha): …`, `fix(node-red): …`, `feat(dashboard): …`, `docs: …`,
   `chore(sync): …`) and push if there's a remote.

If sync prints warnings or notes, mention them in one line rather than ignoring them.

## 6. Working on the live system

**Which access to use, in order:**

1. **ha-mcp tools** (`ha_*`), when connected — validated config API, no browser needed.
   Reads: `ha_search`, `ha_get_state`, `ha_get_entity`, `ha_get_history`, `ha_get_logs`,
   `ha_get_automation_traces`, `ha_eval_template`. Writes:
   `ha_config_set_automation|script|scene|helper|dashboard`, `ha_set_entity`, `ha_reload_core`.
   Rule 4 still applies to every `ha_remove_*`, `ha_config_delete_*`, `ha_restart`,
   backup restore/delete and update install. ha-mcp's own per-edit backups don't replace
   the pre-change commit.
2. **A browser tab** on the **local** HA URL, using
   `document.querySelector('home-assistant').hass` (`callWS`, `callApi`; check
   `hass.connected`). Needed for `tools/collect.js` and Node-RED via ingress.
3. **The terminal** with a token (`tools/collect-cli.mjs`) — for collecting only.
4. **Nothing connected?** Don't stall. Show the user the exact YAML/UI change and let them
   apply it, then sync.

**Prefer the local URL** for all agent work. Public URLs often sit behind proxies, WAFs or
Cloudflare that block WebSocket commands. A logged-out tab means "ask the owner to log
in", not "unavailable".

**Dashboards.** Read the config, change the smallest piece, keep everything else
byte-identical, save the whole config back. Take a screenshot at desktop and phone width
afterwards if you can.

**Automations.** Give every automation a clear `alias` and a `description` saying *why*
it exists. Use `mode` deliberately. Reference entities by `entity_id`, never `device_id`.
Shared rules (seasons, "evening", "someone home") become helpers that automations use,
not templates copied between automations.

**Node-RED** (if installed — [docs/node-red.md](docs/node-red.md)):
- Through ingress: `supervisor/api` `POST /ingress/session` → cookie `ingress_session`,
  then `<ingress_url>flows`.
- `GET flows` with `Node-RED-API-Version: v2`, keep the `rev`, modify only your nodes,
  `POST` with `Node-RED-API-Version: v2` and `Node-RED-Deployment-Type: nodes`.
- Secrets live in **tab environment variables of type credential**, read with
  `$env("NAME")` / `env.get("NAME")`. The owner enters the value.
- Context and `delay`/`trigger` timers are memory-only: anything that must turn *off*
  needs a fail-safe that survives a restart.

**Entities.** Before renaming or removing, grep the repo for every consumer and update
them in the same change ([docs/conventions.md](docs/conventions.md)).

## 7. Things that look dead but aren't

Seasonal automations are kept **disabled**, not deleted. Some devices are only sometimes
online. Offline ≠ removed. This home's list is in [docs/home.md](docs/home.md#keep-list);
check [docs/known-issues.md](docs/known-issues.md) before "fixing" something odd.

## 7a. When the live system looks different

Home Assistant ships monthly and regularly renames or moves things. When a sync, API
result or UI doesn't match these docs, tools or skills:

1. Compare `ha_version` in `homeassistant/export-info.yaml` with the previous one
   (`git log -p homeassistant/export-info.yaml`) and read the release notes for every
   version in between, including *Backward-incompatible changes*.
2. If a release explains it, **adapt, don't work around**: update the docs/tools in the
   same change and add a `CHANGELOG.md` line naming the release. Vendored skills are
   pinned upstream copies: note conflicts in `.claude/skills/VENDORED.md` instead of editing them.
3. If nothing explains it, treat it as unexpected (the owner's change, or a fault) and ask.

## 8. Writing for the owner

Short, direct answers. Say what changed, how to undo it, and what they need to do (if
anything). Don't paste large configs back — they're in the repo.

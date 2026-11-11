# Agent instructions

You are working on a **live smart home**: Home Assistant, with its own automations and,
if installed, Node-RED.
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
   credential env vars, integration passwords, tokens, MCP URLs via `tools/connect.py`).
   Ask them to; don't ask them to paste a secret into chat. Never read or print `.env`,
   `.secrets-denylist`, `secrets.yaml` or your agent's MCP config, and never run
   `tools/connect.py` yourself.
4. **Confirm before anything irreversible or ambiguous**: deleting entities, devices,
   flows, dashboards or integrations; restarting HA; restoring or deleting backups;
   installing updates. Things that look dead often aren't (section 7).
5. **Snapshot before you change.** Sync the repo *before* a change so the commit shows
   exactly what you changed, and keep a copy of anything you're about to overwrite.
6. **Change only what you were asked to.** Edit the one card, not the whole dashboard.
   Deploy only the Node-RED nodes you changed. No drive-by "improvements" — suggest them.
7. **Native first.** Native triggers, conditions and helpers over Jinja templates; native
   Node-RED nodes over big function nodes. A person must be able to read the automation
   in the UI. Details in [docs/automations.md](docs/automations.md),
   [docs/node-red.md](docs/node-red.md) and the `home-assistant-best-practices` skill.
   New automations go where [docs/home.md](docs/home.md#conventions-in-use) says (HA,
   Node-RED, or the rule for choosing) — never the same behaviour in both.
8. **Exposure is reach.** Anything exposed to Assist can be controlled by every AI or
   voice assistant connected to this home. Ask before exposing locks, alarms, garage
   doors, cameras, sirens or power to infrastructure. See [SECURITY.md](SECURITY.md).

## 2. The system

The specifics live in [docs/home.md](docs/home.md): install type, local URL, which
add-ons exist, who lives here and how to notify them. Always read it. Bigger picture:
[docs/architecture.md](docs/architecture.md).

## 3. Skills to load

In `.claude/skills/` (Claude Code, GitHub Copilot), copied to `.agents/skills/` by
`tools/setup.py` for Codex, Gemini CLI, Cursor and others. If your agent doesn't load
skills by itself, read the matching `SKILL.md` before starting the task. Third-party
skills are pinned and listed in [VENDORED.md](.claude/skills/VENDORED.md):

| Task | Load |
|---|---|
| First run, or `docs/home.md` is still a template | `ha-onboard` |
| Any HA request — load it first, before exploring (automations, scripts, helpers, blueprints) | `home-assistant-best-practices` |
| Exporting, committing, "sync", "back up to GitHub" | `ha-sync` |
| Node-RED flows | `node-red` |
| Dashboards — card options and layout (with docs/dashboards.md) | `home-assistant-best-practices` |
| Dashboards built with Bubble Card (optional) | `ha-bubble-dashboard` |

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
tools/               setup.py, connect.py (owner only), collect.js, collect-cli.mjs, sync.py,
                     check_secrets.py, validate.py, automation_lint.py, function_lint.py,
                     doctor.py, update_kit.py — all Python/Node: Windows, macOS, Linux
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
3. **The terminal** with a token in `.env` (`tools/collect-cli.mjs`, set up by the owner
   with `tools/connect.py`) — for collecting only. This is the export path for agents
   without a browser tool.
4. **Nothing connected?** Don't stall. Show the user the exact YAML/UI change and let them
   apply it, then sync.

**Prefer the local URL** for all agent work. Public URLs often sit behind proxies, WAFs or
Cloudflare that block WebSocket commands. A logged-out tab means "ask the owner to log
in", not "unavailable".

**Dashboards** ([docs/dashboards.md](docs/dashboards.md), this home's look in
[docs/style-guide.md](docs/style-guide.md)):
- Follow the design rules: attention first, phone first, one section per area or purpose,
  native cards first, colour only from the theme and only to mean state, confirmations on
  real-world actions. Copy a pattern from the style guide before inventing one.
- Read the config, change the smallest piece, keep everything else byte-identical, save
  the whole config back.
- Look at the result: screenshot at phone and desktop width (and dark mode), fix what
  looks off before reporting done. Ask before adding a new custom card.

**HA automations and scripts** ([docs/automations.md](docs/automations.md)):
- Read the current config, write the **whole** automation back (`ha_config_set_automation`,
  or `POST config/automation/config/<id>`); HA validates and reloads it. New ones need a
  new unique `id`.
- Every automation has an `alias` (what) and a `description` (why); `mode` chosen on
  purpose; `entity_id`/`area_id`, never `device_id`; current syntax (`triggers`/`actions`);
  no Jinja block over 10 lines — shared logic becomes a helper. `tools/automation_lint.py`
  enforces these on commit.
- Debug with traces (`ha_get_automation_traces`) before changing anything. Running an
  automation by hand does the real thing: ask first.
- Never edit `automations.yaml` on the host while the UI owns it.

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

## 7a. When something updates

Home Assistant ships monthly, and so does almost everything around it: core integrations
(covered by HA's release notes), custom integrations and cards from the Marketplace,
add-ons, Node-RED and its palette, device firmware (ESPHome, Zigbee, Z-Wave, Wi-Fi
devices), and even ha-mcp and the skills here. Any of them can rename entities, change
attributes, drop options or deprecate actions.

**Before installing updates** (the owner asks "is it safe to update?"):
1. Pending updates are `update.*` entities that are `on` (`latest_version`, `release_url`).
2. Read the notes for each one, every version in between: HA's release blog
   (*Backward-incompatible changes*, plus the section for every integration listed in
   `homeassistant/inventory/integrations.yaml`); for everything else its GitHub releases or
   changelog (`release_url`, or `documentation` in `inventory/versions.yaml`).
3. Grep the repo for what each breaking change touches (entity ids, attributes, actions,
   card types, Node-RED node types) and report the risk per update: *safe / needs a
   change first / read yourself*.
4. Snapshot first. Installing is the owner's call (rule 4) — offer, don't do.

**After an update, or when the live system doesn't match these docs, tools or skills:**
1. Find what changed. The sync diff shows it: `homeassistant/export-info.yaml` (HA),
   `inventory/versions.yaml` (custom integrations, add-ons, Marketplace items, firmware),
   `inventory/addons.yaml`, `node-red/palette.yaml`, `dashboards/resources.yaml`. Use
   `git log -p` on those files for older changes.
2. Read the notes for every version in between, as above.
3. Check the fallout: Settings › Repairs, `ha_get_logs`, automations or entities that went
   `unavailable`, cards that show errors, Node-RED nodes in an error state.
4. If an update explains it, **adapt, don't work around**: fix the affected automations,
   dashboards and flows (with the owner's OK), update the docs/tools in the same change,
   and add a `CHANGELOG.md` line naming the update. Vendored skills are pinned upstream
   copies: note conflicts in `.claude/skills/VENDORED.md` instead of editing them.
5. If nothing explains it, treat it as unexpected (the owner's change, or a fault) and ask.

## 8. Writing for the owner

Short, direct answers. Say what changed, how to undo it, and what they need to do (if
anything). Don't paste large configs back — they're in the repo.

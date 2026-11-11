---
name: ha-onboard
description: First-time setup of this repo for a Home Assistant install, new or existing. Use when the user says "set up this repo", "onboard me", "get started", "first sync", or when docs/home.md still has `status: template`. Checks the environment, connects MCP, protects privacy, makes the first export and commit, and fills in docs/home.md.
---

# HA onboard

Goal: in one friendly session, take the user from a fresh clone to a private repo that
mirrors their Home Assistant, with docs an agent can work from. Be warm and brief. Ask
one small group of questions at a time. Never ask for passwords, tokens or MCP URLs in
chat — tell the user where to put them instead.

Work through the steps in order. Tell the user which step you're on.

## 1. Health check

Run `python3 tools/doctor.py` and fix what you can yourself:

| Doctor says | You do |
|---|---|
| PyYAML missing | `python3 -m pip install pyyaml` (ask first if it's a system Python) |
| hook not enabled | `git config core.hooksPath .githooks` |
| no denylist | `cp .secrets-denylist.example .secrets-denylist` (filled in step 3) |
| remote is public | Stop. Explain why it should be private (SECURITY.md §4) and let the user decide |
| no remote | Fine for now; offer `gh repo create <name> --private --source . --push` at the end |

## 2. Which path, and can we reach HA?

Ask:
1. **New or existing** Home Assistant? (new = little or nothing configured yet)
2. **Install type** — HA OS / Supervised (add-ons available) or Container / Core?
3. **Local URL** — e.g. `http://homeassistant.local:8123` or `http://192.168.1.20:8123`.
4. Do they use **Node-RED**?

Then check access, best first:
- `ha_*` tools available? Call a harmless read (`ha_get_overview` or `ha_search`) and
  report the HA version. If the URL ends `/readonly`, say so — fine for existing installs
  until step 6.
- No MCP: walk them through `docs/guides/mcp-setup.md`. They run `claude mcp add …`
  themselves (the URL is a secret), then restart the session. If they'd rather not, use
  the browser fallback (they log in) or the terminal collector.

## 3. Privacy first

Before anything is exported, help them build `.secrets-denylist` (git-ignored). Explain
it in one sentence, then ask for things that identify them but don't look secret:
surname, street, town, postcode/ZIP, Wi-Fi name, public domain. Append them with
`printf '%s\n' 'Value' >> .secrets-denylist` (agents are denied *reading* the file, on
purpose — it may hold codes).

For **codes and PINs** (alarm, door keypad): ask them to add those lines themselves in
their editor, so the values never pass through the chat.

## 4. First export

Follow the `ha-sync` skill steps 1–2 (collect → sync → checks), but **don't commit yet**.

Then review the export for anything personal the rules didn't catch:
```bash
git add -A -n | wc -l
grep -rniE "<each denylist-worthy word the user mentioned>" homeassistant node-red | head
```
Look in particular at `inventory/devices.csv` and `entities.csv` (devices named after
people — "Sam's iPhone"), `integrations.yaml` titles (account e-mails, addresses), and
`zone.*` entities. Show the user anything doubtful and let them choose: add to the
denylist (the commit is then blocked until it's fixed — rename it in HA), or accept it
(the repo is private).

Summarise what was exported: dashboards, automations, scripts, helpers, areas,
integrations, Node-RED tabs. Something to be proud of — make it fun.

If Node-RED is present: `python3 tools/function_lint.py --baseline` (grandfathers
today's function nodes so the lint applies only to new ones).

Commit: `chore(sync): initial snapshot`.

## 5. Write the house docs

Fill `docs/home.md` from what you learned plus the export (install type, URLs — local
only, never tokens or MCP URLs — add-ons, recorder, backups). Ask only what you can't
infer:
- Who lives here (first names or roles) and each person's `notify.mobile_app_*` target
  (find candidates with `ha_search` / the entity list; confirm with the user).
- Anything that looks dead but must stay (seasonal automations, sometimes-offline
  devices, wall-panel dashboards) → **Keep list**.
- Where new automations should live: HA, Node-RED, or a rule for which goes where.
- Their naming conventions — offer `docs/conventions.md` as the default and note changes.

Draft `docs/architecture.md` from `inventory/` (add-ons, main integrations, areas).
Change `status: template` to `status: ready` in `docs/home.md`.

Replace the kit's `README.md` with a short one for *their* home: a title, one paragraph,
the "What's here" table, and a line "Built with [HA Agent Kit](https://github.com/deanlongstaff/ha-agent-kit)".
Keep the kit's README text out of their repo.

Fill in the first line of `CHANGELOG.md` and the two example entries in
`docs/decisions.md` with today's date.

Commit: `docs: house profile and architecture`.

## 6. Next steps — by path

**Existing install:** offer the read-only audit:
*"Shall I audit your setup against the best practices and list findings in
docs/known-issues.md, without changing anything?"* If yes, load
`home-assistant-best-practices` and check: `device_id` in automations, templates where
native triggers/conditions exist, automations without description or with default mode
where it matters, entities without an area, unused helpers, things exposed to Assist that
can unlock/open/disarm. Write findings, commit (`docs: initial audit`), and suggest
switching from the `/readonly` URL when they're ready to fix things.

**New install:** walk the foundations in `docs/guides/new-install.md` §4 — one at a time,
each ending in its own commit: areas and floors, backups, people and presence, modes as
helpers, a first useful automation, a first dashboard.

## 7. Wrap up

- Run `python3 tools/doctor.py` once more and show the result.
- Offer to create the **private** GitHub remote if there isn't one.
- Point them to `docs/guides/prompts.md` for ideas.
- Remind them: every change ends with a sync and a commit, so anything can be undone.

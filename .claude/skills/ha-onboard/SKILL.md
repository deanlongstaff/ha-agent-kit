---
name: ha-onboard
description: Complete first-time setup of HA Agent Kit for a Home Assistant install, new or existing, from a single prompt. Use when the user says "set up HA Agent Kit", "set up this repo", "onboard me", "get started", "continue onboarding", "first sync", or when docs/home.md says `status: template` or `status: onboarding`. Creates their private repo, installs prerequisites, protects privacy, connects Home Assistant, makes the first export and commit, and writes the house docs.
---

# HA onboard

Goal: one friendly conversation takes the user from nothing to a private repo that mirrors
their Home Assistant, with docs an agent can work from. **You do the work; the user only
answers questions and does the few things that involve secrets.** Be warm and brief, ask
one small group of questions at a time, and say which step you're on ("Step 3 of 8").

Hard rules, all the way through:
- Never ask for passwords, tokens, codes or MCP URLs in chat. Secrets go where the user
  types them themselves: Home Assistant's UI, their own terminal (`bash tools/connect-mcp.sh`),
  or their editor.
- Never install system-wide software without asking. `bash tools/setup.sh` installs nothing
  system-wide; anything needing `sudo` or a password, the user runs.
- Never push anywhere public.

## Where are we?

Onboarding survives restarts (connecting MCP needs one). Work out the current step from
the state, then continue from there — don't repeat finished steps:

| If… | Go to |
|---|---|
| This folder isn't a kit repo (no `AGENTS.md` + `bash tools/setup.sh`) | Step 1 |
| `python3 tools/doctor.py` reports PyYAML missing or the hook not enabled | Step 2 |
| `docs/home.md` still says `status: template` | Step 3 |
| `.secrets-denylist` has no entries (doctor warns) | Step 4 |
| No `ha_*` tools, no browser tool, no `HA_URL` in the environment | Step 5 |
| No `homeassistant/export-info.yaml` | Step 6 |
| `docs/home.md` says `status: onboarding` | Step 7 |
| `status: ready` | Step 8, or onboarding is done — say so |

## Step 1 — Their own private copy

Skip if you're already inside a kit repo.

Ask for a folder/repo name (default `my-home`) and where to put it (default: the current
folder). Then, best first:

- **`gh` installed and logged in** (`gh auth status`):
  `gh repo create <name> --template deanlongstaff/ha-agent-kit --private --clone`
  (if the clone comes back empty, wait a few seconds and `gh repo clone <name>`).
  It's private from the start.
- **Otherwise:** `git clone https://github.com/deanlongstaff/ha-agent-kit.git <name>`, then
  inside it `rm -rf .git && git init -q -b main && git add -A && git commit -qm "chore: start from HA Agent Kit"`
  (a fresh history that's theirs). The private remote comes in step 8.

Work inside the new folder from now on. If this session was started elsewhere, read the
new folder's `AGENTS.md` now, and tell the user that future sessions should be opened in
that folder (terminal: `cd <name> && claude`; desktop app: choose the folder) so the
rules and skills load automatically.

## Step 2 — Prerequisites

Run `bash tools/setup.sh`. It checks git and Python 3.9+, makes PyYAML available (a private
`.venv` if needed), enables the pre-commit hook, creates `.secrets-denylist` and runs the
doctor.

If it stops on a missing tool, show the one install command it printed and offer to run
it (Homebrew/winget you may run with their OK; `sudo apt …` they run themselves), then
re-run setup. Node is optional — mention it only if they want the terminal collector.

## Step 3 — About their home

Ask, in one message:
1. **New or existing** Home Assistant? (new = little or nothing set up yet)
2. **Install type** — HA OS / Supervised (has add-ons) or Container / Core? ("Settings ›
   About" shows it, if they're unsure.)
3. **Local address** — e.g. `http://homeassistant.local:8123` or `http://192.168.1.20:8123`.
4. **How do they like to automate?** Home Assistant's built-in automations, Node-RED, or
   both? One sentence on each if unsure (`docs/automations.md` § *HA automations or
   Node-RED?*). New installs: built-in automations are the simpler default.

Write the answers into `docs/home.md` straight away (System table, *Automations live
in*), and change `status: template` to `status: onboarding`, so a restart doesn't lose
them. Use their automation choice in every example from here on; skip Node-RED entirely
if they don't use it.

## Step 4 — Privacy first

Explain in one sentence: the denylist blocks any commit containing things that identify
them but don't look secret. Ask for: surname, street, town, postcode/ZIP, Wi-Fi name,
public domain, family names if they'd rather keep them out. Append each with
`printf '%s\n' 'Value' >> .secrets-denylist` (you're denied *reading* the file on purpose
— it may hold codes).

For **codes and PINs** (alarm, door keypad): ask them to open `.secrets-denylist` in their
editor and add those lines themselves.

## Step 5 — Connect to Home Assistant

Check what you already have, best first:
1. `ha_*` tools → call `ha_get_overview` (or `ha_search`), report the HA version, done.
   If it's the `/readonly` URL, say that's perfect for now.
2. Nothing yet → set up **ha-mcp** (`docs/guides/mcp-setup.md`). Talk them through it in
   plain steps:
   - In Home Assistant: create a dedicated user (Settings › People: *Local access only*,
     *Administrator*, a password they keep in their password manager), install **HA-MCP**
     from Settings › Marketplace, restart HA, add the **HA-MCP Server** integration signed
     in as that user, turn on **Local network** access, then open *Configure* and copy
     the connect URL.
   - If you have a browser tool, offer to open their local HA address and point at each
     screen as they go. They log in and type every password; restarting HA needs their OK.
   - Then, **in their own terminal** (not through you): `bash tools/connect-mcp.sh` from the
     repo folder. It asks for the URL with hidden input, offers read-only mode, tests it
     and adds it at user scope.
   - Then they restart Claude Code **in the repo folder** and say *"continue onboarding"*.
     Stop here and tell them exactly that.
3. They'd rather not use MCP → the browser fallback (they log in, you run
   `tools/collect.js`) or the terminal collector (they put `HA_URL`/`HA_TOKEN` in `.env`
   themselves, see `.env.example`). Either works for the export; changes later go
   through the browser or as YAML they paste.

## Step 6 — First export

Follow the `ha-sync` skill steps 1–2 (collect → sync → checks), but **don't commit yet**.

Review the export for anything personal the rules didn't catch. Grep for the words they
gave you and look at `inventory/devices.csv` and `entities.csv` (devices named after
people — "Sam's iPhone"), `integrations.yaml` titles (account names, addresses), and
`zone.*` entities. Show anything doubtful and let them choose: denylist it (the commit is
then blocked until they rename it in HA) or accept it (the repo is private).

Grandfather what exists today so the commit checks apply only to new work:
`python3 tools/automation_lint.py --baseline`, plus `python3 tools/function_lint.py --baseline`
if Node-RED is present.

Celebrate a little: how many dashboards, automations, scripts, helpers, areas,
integrations, Node-RED tabs; how many were grandfathered (their improvement backlog);
any automations without an `id` (listed in `docs/reference/automations.md`).

Commit: `chore(sync): initial snapshot`.

## Step 7 — House docs

Fill `docs/home.md` from the answers and the export (add-ons, recorder, backups — local
address only, never tokens or MCP URLs). Ask only what you can't infer:
- Who lives here (first names or roles) and each person's `notify.mobile_app_*` target
  (find candidates with `ha_search` or `inventory/entities.csv`; confirm).
- Anything that looks dead but must stay → **Keep list**.
- If they use both engines: the rule for which goes where.
- Naming conventions: offer `docs/conventions.md` as is, note any changes.

Draft `docs/architecture.md` from `inventory/`. Existing dashboards: draft
`docs/style-guide.md` from the main dashboard's YAML (theme, card family, layout, colours,
two or three repeated patterns with snippets) and fill the table in `docs/dashboards.md`.

Replace the kit's `README.md` with a short one for *their* home (title, one paragraph,
a "What's here" table, and "Built with [HA Agent Kit](https://github.com/deanlongstaff/ha-agent-kit)"),
and delete `assets/` (the kit README's images). Put today's date in `CHANGELOG.md` and the
two example entries in `docs/decisions.md`. Set `status: ready` in `docs/home.md`.

Commit: `docs: house profile and architecture`.

## Step 8 — Finish

- **Remote:** if there isn't one, offer to create it private:
  `gh repo create <name> --private --source . --push` (or tell them how on github.com and
  `git remote add origin … && git push -u origin main`). Never public.
- Run `python3 tools/doctor.py` and show the result.
- **What next, by path:**
  - *Existing install:* offer the read-only audit — load `home-assistant-best-practices`
    and check the lint baselines, templates where native triggers/conditions exist,
    `mode` choices that drop or double-run triggers, automations without an `id`,
    near-duplicates that could be one blueprint, entities without an area, unused helpers,
    Assist exposure of anything that unlocks/opens/disarms, dashboards against
    `docs/dashboards.md`, and pending updates with breaking changes (AGENTS.md §7a).
    Write findings to `docs/known-issues.md`, commit `docs: initial audit`, and suggest
    re-running `bash tools/connect-mcp.sh` without read-only when they're ready to fix things.
  - *New install:* the foundations in `docs/guides/new-install.md` (areas and floors,
    backups, people and presence, modes as helpers, automation engine, first automation,
    first dashboard), one at a time, each its own commit.
- Point them to `docs/guides/prompts.md`, and remind them: every change ends in a commit,
  so anything can be undone.

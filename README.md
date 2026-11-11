<p align="center">
  <img src="assets/banner.svg" alt="HA Agent Kit — your AI co-pilot for Home Assistant. Every change reviewed, explained, and one git revert away from undone." width="100%">
</p>

<p align="center">
  <a href="https://github.com/deanlongstaff/ha-agent-kit/generate"><img src="https://img.shields.io/badge/Use_this_template-2ea44f?style=for-the-badge&logo=github" alt="Use this template"></a>
  <a href="https://www.home-assistant.io"><img src="https://img.shields.io/badge/Home_Assistant-2026.11+-41BDF5?style=for-the-badge&logo=homeassistant&logoColor=white" alt="Home Assistant 2026.11+"></a>
  <a href="#-works-with-your-agent-on-your-computer"><img src="https://img.shields.io/badge/Agents-Claude_Code_·_Codex_·_Gemini_·_more-D97757?style=for-the-badge" alt="Works with Claude Code, Codex, Gemini CLI and more"></a>
  <a href="#-works-with-your-agent-on-your-computer"><img src="https://img.shields.io/badge/OS-Windows_·_macOS_·_Linux-6366f1?style=for-the-badge" alt="Windows, macOS and Linux"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="MIT licence"></a>
</p>

<p align="center">
  <b>Let an AI agent build and look after your Home Assistant — safely.</b><br>
  Every change it makes is exported, scrubbed of secrets, explained and committed to <i>your</i> private git repo.<br>
  For brand-new installs and ten-year-old ones.
</p>

<p align="center">
  <a href="#-quick-start"><b>Quick start</b></a> ·
  <a href="docs/guides/new-install.md">New install</a> ·
  <a href="docs/guides/existing-install.md">Existing install</a> ·
  <a href="docs/guides/mcp-setup.md">MCP setup</a> ·
  <a href="SECURITY.md">Security</a> ·
  <a href="docs/guides/prompts.md">Prompt ideas</a>
</p>

---

## 🤔 Why?

AI agents are genuinely good at Home Assistant now — automations, dashboards, traces,
Node-RED. But point one at the house you live in and the same questions come up:

| 😬 Without the kit | 😌 With the kit |
|---|---|
| *"What did it just change?"* | Every change is a commit with a readable diff |
| *"How do I undo that?"* | `git revert` — or just *"undo yesterday's hallway change"* |
| *"Did it just put my token in a file?"* | Four layers stop secrets long before GitHub |
| *"Why is it set up like this?"* | A changelog and decision log the agent reads every session |
| *"What is this 120-line template?"* | Native-first rules: triggers, conditions and helpers a human can read |
| *"It deleted my Christmas lights automation!"* | Confirm-before-delete, plus a keep-list of things that only *look* dead |
| *"My dashboard is a wall of 200 entities."* | Twelve design rules, your own style guide, and a screenshot check on every change |
| *"An update broke everything."* | Every sync records versions; the agent reads the changelogs before *and* after you update |

**The idea in one line:** your live Home Assistant stays the source of truth, and this repo
becomes its **mirror and its memory**.

## 🔁 How it works

<p align="center">
  <img src="assets/loop.svg" alt="The loop: 1 you ask, 2 snapshot, 3 change live through MCP, 4 export and scrub, 5 check and commit" width="100%">
</p>

The agent never edits files in the repo to change your house. It changes the **live system**
through Home Assistant's own APIs (so HA validates everything), then **exports** the result.
The repo can't drift into a fantasy version of your home.

## 🚀 Quick start — one prompt

You need Home Assistant and an AI coding agent: [Claude Code](https://claude.com/claude-code)
(recommended), Codex, Gemini CLI, Cursor, Copilot… On Windows, macOS or Linux. That's it:
the agent sets up everything else.

Open your agent in the folder where you keep projects and paste:

```text
Set up HA Agent Kit for my Home Assistant: make me a private copy of
https://github.com/deanlongstaff/ha-agent-kit called my-home, then follow its
.claude/skills/ha-onboard/SKILL.md
```

Then answer a few questions. ☕

| Step | | Who |
|---|---|---|
| 1 | Creates your **private** repo | 🤖 |
| 2 | Installs what's needed — inside the repo, nothing system-wide | 🤖 |
| 3 | Asks about your home: new or existing, install type, built-in automations or Node-RED | 🙋 you answer |
| 4 | Builds your privacy denylist (codes and PINs you type yourself) | 🙋 + 🤖 |
| 5 | Walks you through connecting Home Assistant; you paste the secret URL into `python3 tools/connect.py` in your own terminal, never the chat | 🙋 + 🤖 |
| 6 | Exports everything, checks it for personal data, makes the first commit | 🤖 |
| 7 | Writes your house docs, asking only what it can't work out | 🤖 |
| 8 | Pushes to a private GitHub repo and suggests what to do next | 🤖 |

There's one restart in the middle (agents pick up a new connection when they start): open
it again in your `my-home` folder and say ***"continue onboarding"***.

<p align="center">
  <img src="assets/onboarding.svg" alt="Example onboarding session: health check, read-only connection, privacy denylist, first export of dashboards, automations, helpers and Node-RED tabs, then an initial snapshot commit" width="88%">
</p>

<details>
<summary><b>Prefer to do it by hand?</b></summary>

1. **[Use this template](https://github.com/deanlongstaff/ha-agent-kit/generate)** → **Private**
   ([why](SECURITY.md#4-keep-your-home-repo-private)) → clone it and `cd` into it.
2. `python3 tools/setup.py` — checks git and Python, installs PyYAML privately, enables the safety hook.
3. Install [ha-mcp](https://github.com/homeassistant-ai/ha-mcp) in Home Assistant
   ([guide](docs/guides/mcp-setup.md)), then `python3 tools/connect.py` to connect it to your agent.
4. Start your agent in the folder, then: ***"continue onboarding"***.

On Windows, type `py` instead of `python3`.

</details>

## 🤖 Works with your agent, on your computer

| | Claude Code | Codex | Gemini CLI | Cursor · Copilot · others |
|---|---|---|---|---|
| Reads the rules (`AGENTS.md`) | ✅ via `CLAUDE.md` | ✅ | ✅ via `.gemini/settings.json` | ✅ |
| Skills (onboarding, sync, best practices) | ✅ `.claude/skills/` | ✅ `.agents/skills/` | ✅ `.agents/skills/` | ✅ either folder¹ |
| `connect.py` adds ha-mcp for you | ✅ | ✅ | ✅ | tells you where to paste it |
| Exports | browser tool² or terminal | terminal | terminal | terminal |
| Safety rails | git hook + CI + agent permissions | git hook + CI | git hook + CI | git hook + CI |

¹ `tools/setup.py` copies the skills to `.agents/skills/`, where most agents look; an agent
that doesn't load skills by itself is told by `AGENTS.md` to read the right `SKILL.md`.
² Claude desktop app or Claude in Chrome. Terminal exports need Node 22+ and a token that
`connect.py` stores in the git-ignored `.env`.

**Windows, macOS and Linux** are all supported and tested on every push: every tool is
Python or Node, files are written as UTF-8 with LF line endings, and the git hook runs
under Git for Windows. On Windows, type `py` where the docs say `python3`.

## 🛤️ Pick your path

<table>
<tr>
<td width="50%" valign="top">

### 🌱 Path A — New install

Start clean and *stay* clean. The agent helps you lay foundations in the right order:
areas and floors, naming conventions, encrypted off-site backups, presence, modes as
helpers, then your first automations and dashboard — every step a reviewed commit.

**→ [New install guide](docs/guides/new-install.md)**

</td>
<td width="50%" valign="top">

### 🏚️ Path B — Existing install

Years of automations? Perfect. Export everything (read-only), review it for privacy,
commit a snapshot, let the agent write your house docs, then get a **best-practice audit**
of what to improve. Fix things one commit at a time.

**→ [Existing install guide](docs/guides/existing-install.md)**

</td>
</tr>
</table>

## 🧠 Built-in automations, Node-RED, or both

Use whichever you love. The kit treats both as first-class, and onboarding asks which you
prefer so the agent builds new things in the right place.

| | 🏠 Home Assistant automations | 🔴 Node-RED |
|---|---|---|
| **Exported as** | One YAML file per automation, script and scene | One importable JSON file per tab |
| **Generated reference** | Alias, mode, triggers and description of every automation | Every tab with node counts |
| **House rules** | Description says why · `entity_id` not `device_id` · current syntax · short templates | Native nodes first · small, single-job function nodes |
| **Checked on every commit** | `automation_lint.py` | `function_lint.py` + wiring check |
| **Existing setups** | Today's automations are grandfathered; rules apply to new work | Same for today's function nodes |
| **Guide** | [automations.md](docs/automations.md) | [node-red.md](docs/node-red.md) |

Not sure? [Here's how to choose](docs/automations.md#ha-automations-or-node-red). Using
both? Write the rule for which goes where in `docs/home.md`, and the agent sticks to it.

## 🎨 Dashboards, not just automations

The agent is just as handy with your UI. It designs to a set of
[design rules](docs/dashboards.md#design-rules), records *your* look in a
[style guide](docs/style-guide.md) so card #50 matches card #1, and **looks at its own work**:
screenshots at phone and desktop width before it calls anything done.

<p align="center">
  <img src="assets/dashboards.svg" alt="A phone dashboard annotated with the design rules: attention first, one section per area and phone first, colour means state, guard real-world actions, checked by eye on every change" width="100%">
</p>

Native cards first (tile, heading, badges, area, thermostat), with an optional skill for
[Bubble Card](https://github.com/Clooos/Bubble-Card) if you like a more styled look. Existing
dashboards? Onboarding drafts your style guide from what you already have.

## 🔄 Update-aware

Home Assistant ships monthly, and your integrations, add-ons, custom cards and device
firmware update constantly. Every sync records what's installed
(`inventory/versions.yaml`), so the diff shows exactly what changed. Then:

- **Before you update:** *"Is it safe to install the pending updates?"* — the agent reads
  every changelog in between, greps your setup for what each breaking change touches, and
  rates each update *safe / needs a change first / read yourself*.
- **After you update:** it spots what changed, checks Repairs, logs and unavailable
  entities, and fixes or flags the fallout — updating its own docs and tools rather than
  working around surprises.

## ✨ What's included

| | |
|---|---|
| 🔁 **The loop** | Snapshot → change → export → review → commit. Every AI change is one `git revert` away from undone. |
| 📸 **A complete export** | Dashboards, automations, scripts, scenes, helpers, areas, devices, entities, integrations, add-ons and Node-RED flows — clean YAML/JSON, one file per thing. HA OS, Supervised, Container and Core. Old YAML automations it can't read are listed, not silently skipped. |
| 🎨 **Dashboard design rules** | Attention first, phone first, native cards, colour that means something, guarded actions — plus your own style guide and a screenshot check. |
| 🔄 **Update-aware** | Versions of HA, custom integrations, add-ons, cards and firmware in every sync; changelogs read before and after updates. |
| ✅ **Quality checks on every commit** | HA automations need a *why*, use `entity_id` and current syntax; Node-RED function nodes stay small. Existing work is grandfathered. |
| 🛡️ **Four layers of secret protection** | Redaction, your personal denylist, a pre-commit hook, and CI with gitleaks. |
| 📜 **Agent rules that hold up** | An [`AGENTS.md`](AGENTS.md) refined on a real, busy house: confirm before deleting, native-first, change only what was asked, never touch credentials. |
| 🧭 **Guided onboarding** | Say *"set up this repo"* and the agent interviews you, connects, protects your privacy and makes the first commit. |
| 🧩 **Skills, ready to go** | `ha-onboard` and `ha-sync`, plus pinned community skills for HA best practices, Node-RED and Bubble Card dashboards. |
| 🩺 **A doctor** | `python3 tools/doctor.py` checks hooks, denylist, repo visibility, skills and exports in one go. |
| 📚 **Docs that keep up** | Reference pages regenerated on every sync, plus templates for the human *why*: house profile, conventions, decisions, known issues. |

## 💬 Things you can ask

```text
"Give me a tour of my setup — rooms, busiest integrations, most-run automations."
"The porch light didn't come on last night. Check the traces and tell me why."
"When the washing machine finishes, tell whoever's home. Nag again after 30 min."
"Find automations using device_id and convert them to entity_id, one commit each."
"Add an open-windows card to the Home dashboard. Change nothing else."
"Redesign the Living room section to follow the design rules — show me before and after."
"Is it safe to install the pending updates? Check every changelog for breaking changes."
"List everything exposed to Assist that can unlock, open or disarm something."
"What changed this week, and why?"
```

More in **[prompts.md](docs/guides/prompts.md)**.

## 🛡️ Security, in one screen

<p align="center">
  <img src="assets/protection.svg" alt="Four layers: redaction at export, your denylist, a pre-commit hook, and CI with gitleaks, before a private repo" width="100%">
</p>

| | |
|---|---|
| 🏠 **Agent access stays local** | ha-mcp listens on your LAN only, as a dedicated local-only admin user. No admin endpoint on the internet. |
| 📱 **Phone AI gets the minimum** | Claude on your phone uses HA's built-in MCP Server's device-control endpoint as a **non-admin** user — it can only reach what you expose to Assist. |
| 🔑 **The agent never handles secrets** | You log in; you type passwords and codes. MCP URLs live in user config, never the repo. |
| 🧹 **Nothing sensitive reaches git** | Redaction → denylist → pre-commit hook → CI + gitleaks over full history. |
| 🔒 **Your repo stays private** | The kit is public; your home isn't. `doctor.py` shouts if your remote is public. |
| ✋ **Destructive = ask first** | Deletes, restarts, restores and updates always need your OK. |

Read the full model in **[SECURITY.md](SECURITY.md)**.

## 🗂️ What's in the box

```
AGENTS.md                 the rules every agent follows (CLAUDE.md points here)
SECURITY.md               the security model
docs/
  home.md                 YOUR house: install, URLs, people, keep-list (filled by onboarding)
  conventions.md          naming, helper and notification conventions
  automations.md          HA automation house rules; node-red.md for flows
  dashboards.md           dashboard design rules + workflow; style-guide.md for your look
  architecture.md …       templates for the human "why"
  guides/                 new install · existing install · MCP setup · prompt ideas
  reference/              generated on every sync
.claude/skills/
  ha-onboard/             first-run setup interview
  ha-sync/                collect → sync → check → docs → commit
  home-assistant-best-practices/ node-red/ ha-bubble-dashboard/   pinned community skills
tools/
  collect.js              read-only exporter — run in a browser tab (no token)
  collect-cli.mjs         …or from the terminal with a token
  sync.py  redact.py      turn the export into clean, redacted files
  check_secrets.py        secret + personal-data scanner (hook + CI)
  validate.py             YAML/JSON/Node-RED wiring checks, runs both linters
  automation_lint.py      house rules for HA automations and scripts
  function_lint.py        house rules for Node-RED function nodes
  doctor.py               setup checker
  setup.py                one-time local setup (private .venv, hooks, denylist, skills copy)
  connect.py              YOU run it: connects your agent(s) to ha-mcp; secrets never touch the chat
  update_kit.py           pull kit updates without touching your home's files
assets/                   the images in this README (onboarding removes them from your copy)
```

After your first sync you'll also have `homeassistant/` (dashboards, automations, scripts,
scenes, helpers, inventory) and, if you use it, `node-red/` (one file per tab).

## 🧰 Requirements and compatibility

| | |
|---|---|
| Home Assistant | 2026.8+ recommended (ha-mcp integration). HA OS / Supervised get the full export (add-ons, Node-RED, config files); Container / Core get everything else. |
| Agent | Claude Code, Codex, Gemini CLI, Cursor, Copilot or any agent that reads `AGENTS.md` — [details](#-works-with-your-agent-on-your-computer). |
| Computer | Windows, macOS or Linux. git and Python 3.9+ (the agent checks and helps install them; PyYAML goes in a private `.venv`). Node 22+ for terminal exports. |
| Optional | Node-RED add-on, Studio Code Server add-on (for raw config files), `gh` CLI. |

## 🔄 Updating the kit

Your repo is yours, but the kit keeps improving. Pull new tools, skills and rules without
touching your house's files:

```bash
python3 tools/update_kit.py
git diff                       # review
git commit -am "chore(repo): update HA Agent Kit"
```

## ❓ FAQ

<details>
<summary><b>Does the AI edit my YAML files directly?</b></summary>

No. Changes go to the live system through Home Assistant's APIs (via MCP or the browser),
where HA validates them. The repo is then regenerated from the live system. Hand-editing
files in `homeassistant/` does nothing — the next sync overwrites them.
</details>

<details>
<summary><b>Is this a backup?</b></summary>

It's a *history*, not a backup. It has no database, no `.storage`, no secrets. Keep Home
Assistant's own encrypted, off-site backups too — the agent can help you set them up.
</details>

<details>
<summary><b>I don't use Node-RED. / I only use Node-RED.</b></summary>

Both are fine — see [Built-in automations, Node-RED, or both](#-built-in-automations-node-red-or-both).
Without Node-RED the `node-red/` parts are skipped and the agent never suggests it. With
it, every tab is an importable file and the agent deploys only the nodes it changed.
</details>

<details>
<summary><b>Can I use this without MCP?</b></summary>

Yes. The agent can work through a browser tab where you're logged in, or hand you the exact
change to apply. Exports work from the browser (`tools/collect.js`) or the terminal
(`tools/collect-cli.mjs`).
</details>

<details>
<summary><b>Will it work with Codex / Gemini / Cursor / Copilot?</b></summary>

Yes — see [Works with your agent](#-works-with-your-agent-on-your-computer). The rules are
in `AGENTS.md`, the skills use the open `SKILL.md` format, and `connect.py` sets up ha-mcp
for Claude Code, Codex and Gemini CLI. It was built day-to-day with Claude Code, which has
the extra comforts: a browser tool for exports and per-tool permissions that stop the
agent reading `.env` or running `connect.py`.
</details>

<details>
<summary><b>What if Home Assistant changes something in a release?</b></summary>

HA ships monthly. The rules tell the agent to compare versions, read the release notes and
*adapt the docs and tools* rather than work around surprises.
</details>

## 🙏 Credits

Standing on the shoulders of:

- [Home Assistant](https://www.home-assistant.io) and its wonderful community
- [ha-mcp](https://github.com/homeassistant-ai/ha-mcp) and [homeassistant-ai/skills](https://github.com/homeassistant-ai/skills)
- [aurora-smart-home](https://github.com/tonylofgren/aurora-smart-home) (Node-RED skill)
- [HA_Bubble_Skill](https://github.com/johnnyh1975/HA_Bubble_Skill) (Bubble Card skill)
- [gitleaks](https://github.com/gitleaks/gitleaks)

Born from a real, busy smart home where an AI agent has been making changes every day —
and every one of them is in git.

## 🤝 Contributing

Issues and PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). The golden rule applies to
contributions too: **nothing from your own home** in issues or PRs.

## 📄 License

[MIT](LICENSE). Vendored skills keep their own MIT licences.

<div align="center">

**If this made your smart home a little less scary to hand to an AI, give it a ⭐**

</div>

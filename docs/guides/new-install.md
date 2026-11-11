# Path A — a brand-new Home Assistant

You get to do it right from day one: clean names, areas that make sense, automations
that explain themselves, and a git history of every decision. The agent does the typing;
you make the calls.

**Time:** an evening for the foundations, then grow it a room at a time.

## 0. Before you start

- **Hardware:** Home Assistant Green/Yellow, a Raspberry Pi 5, a mini PC or a VM.
- **Install HA OS** following the [official guide](https://www.home-assistant.io/installation/).
  HA OS (or Supervised) gives you add-ons — Node-RED, Studio Code Server, ESPHome — which
  this kit can use. Container/Core installs work too; the add-on parts are skipped.
- **Finish HA's onboarding** in the browser: create *your* owner account, set your
  location and units, let it discover devices. Don't add integrations yet beyond what it
  finds automatically.
- **An AI coding agent** — this kit is built and tested with
  [Claude Code](https://claude.com/claude-code) (terminal, desktop app or IDE). Anything
  that reads `AGENTS.md` can follow the rules.

## 1. Make your repo

Click **Use this template** on GitHub › **Private** repository › clone it:

```bash
git clone https://github.com/<you>/my-home.git && cd my-home
python3 -m pip install pyyaml
git config core.hooksPath .githooks
cp .secrets-denylist.example .secrets-denylist   # then add your surname, street, postcode…
python3 tools/doctor.py
```

## 2. Connect the agent

Follow [mcp-setup.md](mcp-setup.md) to install ha-mcp and add it to your agent at user
scope. Start with the `/readonly` URL if you like — Path A needs write access from step 4.

## 3. Let the agent onboard you

Open the repo in your agent and say:

> **Set up this repo for my new Home Assistant.**

The `ha-onboard` skill takes over. It checks your setup, asks a short set of questions
(who lives here, which rooms, phones for notifications, what you want automated first),
then fills in `docs/home.md` and makes the first export and commit.

## 4. Lay the foundations (in this order)

Ask for each step; the agent proposes, you approve, it builds and commits.

1. **Floors and areas.** *"Create floors and areas for my house: ground floor has a
   kitchen, living room, hallway…"* Areas drive everything else — dashboards, voice,
   room-based automations.
2. **Naming conventions.** Read [conventions.md](../conventions.md) together and adjust.
   *"Rename every entity to match our conventions as we add devices."*
3. **Backups first.** *"Set up automatic encrypted backups, keep 7, and tell me how to get
   an off-site copy."* Store the encryption key in your password manager.
4. **People and presence.** Install the Companion App on each phone, then *"set up
   presence for each person and record their notify targets in docs/home.md."*
5. **Integrations.** Add them yourself in the UI (they usually need logins). After each:
   *"I just added Hue — assign the new devices to areas and rename them to our conventions."*
6. **Modes as helpers.** *"Create guest mode, vacation mode and a 'someone home' group."*
7. **First automations.** Start small and useful: hallway motion lights, a leak alert,
   "everything off when the last person leaves". Each one gets an alias, a *why*, a
   commit, and a changelog line.
8. **A dashboard.** *"Build a sections-view dashboard with one section per area."*

## 5. Keep going

Every change follows the same loop, so your repo always mirrors the house. Browse
[prompts.md](prompts.md) for ideas. When something breaks, ask *"what changed recently
that could affect the hallway lights?"* — the git log knows.

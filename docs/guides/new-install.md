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

## 1. One prompt

Open Claude Code in the folder where you keep projects and paste:

```text
Set up HA Agent Kit for my Home Assistant: make me a private copy of
https://github.com/deanlongstaff/ha-agent-kit called my-home, then follow its
.claude/skills/ha-onboard/SKILL.md
```

Say it's a **new** install when it asks. The `ha-onboard` skill then:

1. creates your **private** repo and installs what it needs (privately, inside the repo);
2. asks about your home — install type, local address, built-in automations or Node-RED;
3. builds your privacy denylist with you;
4. walks you through installing **ha-mcp** in Home Assistant, then has you run
   `bash tools/connect-mcp.sh` in your own terminal so the secret URL never touches the chat
   (details: [mcp-setup.md](mcp-setup.md));
5. after one restart (*"continue onboarding"*), exports your fresh install, writes your
   house docs and makes the first commits.

Path A needs write access for the foundations below, so say **no** to read-only when
`connect-mcp.sh` asks — or start read-only and re-run it later.

<details>
<summary>By hand instead</summary>

**Use this template** → **Private** → clone → `bash tools/setup.sh` → install ha-mcp →
`bash tools/connect-mcp.sh` → `claude` → *"continue onboarding"*.

</details>

## 2. Lay the foundations (in this order)

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
7. **Pick your automation engine.** Home Assistant's built-in automations are the simple
   default: everything in one UI, traces and blueprints built in. Node-RED (an add-on) is
   great if you think visually. Or both, with a rule for which goes where. See
   [automations.md](../automations.md#ha-automations-or-node-red) — onboarding records
   your choice in `docs/home.md`.
8. **First automations.** Start small and useful: hallway motion lights, a leak alert,
   "everything off when the last person leaves". Each one gets an alias, a *why*, a
   commit, and a changelog line.
9. **A dashboard.** *"Build me a phone-first home dashboard: things that need attention
   at the top, then one section per area."* The agent follows the
   [design rules](../dashboards.md#design-rules), screenshots it at phone and desktop width,
   and writes the look it chose into `docs/style-guide.md` so every later card matches.

## 3. Keep going

Every change follows the same loop, so your repo always mirrors the house. Browse
[prompts.md](prompts.md) for ideas. When something breaks, ask *"what changed recently
that could affect the hallway lights?"* — the git log knows.

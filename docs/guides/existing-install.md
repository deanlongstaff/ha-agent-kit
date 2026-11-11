# Path B — an existing Home Assistant

You already have years of automations, dashboards and helpers. Path B gets all of it into
a reviewed, secret-free repo first, *then* lets the agent help — without breaking anything
along the way.

**Time:** about 30 minutes to your first commit.

## 1. One prompt

Open Claude Code in the folder where you keep projects and paste:

```text
Set up HA Agent Kit for my Home Assistant: make me a private copy of
https://github.com/deanlongstaff/ha-agent-kit called my-home, then follow its
.claude/skills/ha-onboard/SKILL.md
```

Say it's an **existing** install when it asks.

Already keep your config in git? Let it create a **new** repo anyway, and keep the old one
as an archive. This kit's layout is generated, and mixing the two gets confusing.

## 2. What onboarding does

1. Creates your **private** repo and installs what it needs (privately, inside the repo).
2. Asks about your home: install type, local address, built-in automations or Node-RED.
3. Builds your privacy denylist with you.
4. Walks you through installing **ha-mcp**, then has you run `bash tools/connect-mcp.sh` in your
   own terminal — say **yes to read-only**, so for now the agent can look at everything and
   change nothing. The secret URL never touches the chat ([mcp-setup.md](mcp-setup.md)).
5. After one restart (*"continue onboarding"*): **exports everything** and shows you a
   summary — dashboards, automations, helpers, Node-RED tabs, integrations.
6. **Reviews the export for privacy before anything is committed**, and helps you extend
   the denylist.
7. Grandfathers what exists today, so the commit checks only apply to new work:
   automations that break the [house rules](../automations.md#house-rules) and, with
   Node-RED, large function nodes. That list is your improvement backlog.
8. Makes the first commit, drafts `docs/home.md`, `docs/architecture.md` and your
   dashboard style guide, and pushes to a private GitHub repo.

<details>
<summary>By hand instead</summary>

**Use this template** → **Private** → clone → `bash tools/setup.sh` → install ha-mcp →
`bash tools/connect-mcp.sh` → `claude` → *"continue onboarding"*.

</details>

## 3. Your first look around

> **Give me a tour of my setup.**

## 4. Get a health check (still read-only)

> **Audit my setup against the best practices and write the findings to docs/known-issues.md. Don't change anything.**

Typical findings: automations using `device_id`, templates where a native trigger
exists, near-identical automations that could be one blueprint, `mode` choices that drop
triggers, old YAML automations without an `id` (they can't be exported until they have
one), entities with no area, orphaned helpers, things exposed to Assist that shouldn't be,
and dashboards that break the [design rules](../dashboards.md#design-rules) (hex colours,
locks without a confirmation, cards pointing at entities that no longer exist). You decide what to fix, and when.

## 5. Switch to full access and improve, one change at a time

Swap the MCP URL to the full one (without `/readonly`). Then pick items from
`known-issues.md`:

> **Fix the device_id automations in the kitchen. One commit per automation.**

Each change is snapshot → change → export → review → commit, so every one is a single
`git revert` away from undone.

## Tips

- **HA automations, Node-RED, or both?** Onboarding asks and records your answer, so the
  agent builds new things where you want them. Both get the same treatment: one file per
  automation or tab, house rules checked on every commit, and a guide
  ([automations.md](../automations.md), [node-red.md](../node-red.md)).

- **Studio Code Server** (add-on) lets the collector also export `configuration.yaml` and
  ESPHome configs. Optional — start it when you want those, stop it afterwards.
- **Changed something by hand?** The next sync picks it up. Your agent commits it as
  `chore(sync): …` separately from its own work.
- **Huge install?** The first export can be several MB. That's fine; diffs after that are small.

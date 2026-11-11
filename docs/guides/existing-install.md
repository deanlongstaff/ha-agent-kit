# Path B — an existing Home Assistant

You already have years of automations, dashboards and helpers. Path B gets all of it into
a reviewed, secret-free repo first, *then* lets the agent help — without breaking anything
along the way.

**Time:** about 30 minutes to your first commit.

## 1. Make your repo

Click **Use this template** on GitHub › **Private** repository › clone it:

```bash
git clone https://github.com/<you>/my-home.git && cd my-home
python3 -m pip install pyyaml
git config core.hooksPath .githooks
cp .secrets-denylist.example .secrets-denylist   # then add your surname, street, postcode, Wi-Fi name…
python3 tools/doctor.py
```

Already keep your config in git? Use a **new** repo anyway, and keep the old one as an
archive. This kit's layout is generated, and mixing the two gets confusing.

## 2. Connect the agent — read-only first

Follow [mcp-setup.md](mcp-setup.md) and add ha-mcp with the **`/readonly`** URL. For the
first session the agent can look at everything and change nothing.

## 3. Onboard

Open the repo in your agent and say:

> **Set up this repo for my existing Home Assistant.**

The `ha-onboard` skill will:

1. Check your setup (`tools/doctor.py`).
2. **Export everything** (collect → sync) and show you a summary: how many dashboards,
   automations, helpers, Node-RED tabs, integrations.
3. **Review the export for privacy before anything is committed.** It greps for names,
   addresses and anything your denylist should catch, and helps you extend the denylist.
4. Make the first commit: `chore(sync): initial snapshot`.
5. Draft `docs/home.md` and `docs/architecture.md` from the inventory, then ask you to
   fill the gaps only you know (who lives here, what must never be touched).
6. Grandfather what exists today, so the commit checks only apply to new work: automations
   that break the [house rules](../automations.md#house-rules) (no description, `device_id`,
   old syntax, long templates) and, with Node-RED, large function nodes. That list becomes
   your improvement backlog.

## 4. Get a health check (still read-only)

> **Audit my setup against the best practices and write the findings to docs/known-issues.md. Don't change anything.**

Typical findings: automations using `device_id`, templates where a native trigger
exists, near-identical automations that could be one blueprint, `mode` choices that drop
triggers, old YAML automations without an `id` (they can't be exported until they have
one), entities with no area, orphaned helpers, things exposed to Assist that shouldn't be. You decide what to fix, and when.

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

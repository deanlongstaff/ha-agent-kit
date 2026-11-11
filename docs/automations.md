# Automations (Home Assistant)

Home Assistant's built-in automations and scripts. Use this guide whether they're your
only automation engine or you use them alongside Node-RED ([node-red.md](node-red.md)).
This home's choice is recorded in [home.md](home.md#conventions-in-use).

The `home-assistant-best-practices` skill has the detail (exact keys, worked examples). This
page has the house rules and how agents work on automations here.

## Files in this repo

- `homeassistant/automations/<alias>.yaml` — one file per automation, exported from the API
  (redacted). `scripts/` and `scenes/` work the same way.
- `docs/reference/automations.md` — generated table: alias, id, mode, trigger types,
  description, plus any automations that **couldn't be exported** (see below).
- `homeassistant/config/automations.yaml` — the raw file, only when Studio Code Server was
  running at export time.

These files are a mirror. Editing them changes nothing in your house; the next sync
overwrites them.

## Native first

An automation should read in the UI editor: what starts it, what it checks, what it does.
The same principle as Node-RED's "native nodes first", for the same reason: a person has
to be able to maintain it.

| Job | Use |
|---|---|
| Start on a change | `state` / `numeric_state` trigger, with `for:` instead of a delay-then-check |
| Start on a time | `time` (fixed or from an `input_datetime`), `time_pattern`, `sun` |
| Start on arrival / leaving | `zone` trigger, or `state` on `person.*` / a "someone home" group |
| A button or remote press | its **event entity** (`event.received`); a device trigger only when no entity exists |
| Check another entity | `state` / `numeric_state` condition |
| "Is it evening?", "is it the season?" | a `schedule`, `tod` (times of day) or template **helper**, then a `state` condition on it |
| Choose between outcomes | `choose` with clearly named options, or separate automations |
| Wait for something | `wait_for_trigger` with a `timeout` and `continue_on_timeout` set on purpose |
| "Off after 10 minutes" | `restart` mode + `delay`, *plus* a fail-safe (below) |
| Reuse the same steps | a **script** with fields, called from several automations |
| The same automation for many rooms | a **blueprint** with selectors, one automation per room |
| Target lights in a room | `target: area_id` or a light group, not a list of every bulb |

**When a template is right:** maths, text for a notification, or picking a value from
a list. Keep it short. A template used by more than one automation becomes a **template
helper** (Settings › Helpers › Template) that automations reference by entity, so it's
written and tested once.

## House rules

`tools/automation_lint.py` (run by `validate.py`, so the pre-commit hook) enforces the
first four on every automation and script:

1. **A description that says why.** `alias` says what; `description` says why it exists
   and anything surprising ("Runs at 06:40 because the boiler needs 20 min to warm up").
2. **`entity_id`, never `device_id`.** Device IDs change when a device is re-added, and the
   automation breaks silently. Device-only triggers (some remotes) are the exception —
   waive them with a reason (below).
3. **Current syntax.** `triggers:` / `trigger:`, `conditions:`, `actions:` / `action:`
   (HA 2024.10+), not `platform:` and `service:`. HA migrates when you save in the UI.
4. **Short templates.** No Jinja block over 10 lines — move it into a template helper.

And by review:

5. **Choose `mode` on purpose.** `single` (default) for one-shots, `restart` for "reset
   the timer" (motion lights), `queued` when every trigger must run, `parallel` rarely.
6. **Fail-safes for anything time-limited.** A `delay` is lost on restart or reload. Boosts,
   timed fans and "off after N minutes" also need a trigger like
   `state … for: "00:30:00"` or a check at `homeassistant` start.
7. **One behaviour per automation.** Easier to read, trace, disable and revert.
8. **Seasonal automations are disabled out of season, not deleted** (add them to the
   [keep list](home.md#keep-list)).
9. **Notifications go to the targets in [home.md](home.md#people-and-notifications)**,
   critical ones separate from nice-to-know ones.

### Waivers and existing automations

At your first sync, run `python3 tools/automation_lint.py --baseline`. It records every
automation that fails today in `tools/automation_baseline.json`, so the rules apply only to
new and changed ones. To waive one rule-breaker on purpose:

```bash
python3 tools/automation_lint.py --allow 1712345678901 "Hue dimmer has no event entity"
```

The baseline is a to-do list: shrink it, never grow it except with a reason.

## Changing automations from an agent

1. Snapshot (sync) first.
2. Read the current config: `ha_config_get_automation` (ha-mcp), or in a browser tab
   `await hass.callApi('GET', 'config/automation/config/<id>')`.
3. Write the whole automation back: `ha_config_set_automation`, or
   `await hass.callApi('POST', 'config/automation/config/<id>', config)`. HA validates it and
   reloads automations by itself. A **new** automation needs a new unique `id` (a
   millisecond timestamp, like the UI uses).
4. Check it loaded: the entity `automation.<…>` exists and isn't `unavailable`, and
   `ha_get_logs` shows no errors for it.
5. Sync, check, commit.

Never edit `automations.yaml` on the host while the UI owns it — the two will fight.

## Testing and debugging

- **Traces** are the first stop: `ha_get_automation_traces`, or Settings › Automations ›
  ⋮ › Traces. They show which trigger fired, each condition's result and every step.
- **Templates:** test with `ha_eval_template` (or Developer tools › Template) before
  saving.
- **Running one by hand** (`automation.trigger`) does the real thing: lights, locks,
  notifications. Ask the owner before running anything with side effects, and use
  `skip_condition: false` to test the conditions too.
- **"It didn't run":** check the trace exists (trigger never fired?), then conditions,
  then `mode` (a `single` automation drops triggers while it's running).

## Automations that can't be exported

The API only reads automations that have an `id` (anything made in the UI does). Older
YAML automations — `automations.yaml` entries without `id:`, or automations in packages —
show up in `docs/reference/automations.md` under *Not exported*. To bring them in:

- **Best:** open each one in the UI, copy it into a new automation, save, then delete the
  old YAML entry (the agent can do this with you, one at a time).
- **Or:** add an `id:` to each in the YAML file and reload automations.
- **Or:** keep Studio Code Server running during syncs, so the raw files are exported
  to `homeassistant/config/` (packages aren't collected).

## HA automations or Node-RED?

Both are good. Pick one as the default and write it in [home.md](home.md#conventions-in-use)
so agents don't scatter logic across both.

| Prefer HA automations when… | Prefer Node-RED when… |
|---|---|
| You want everything in one place, in the HA UI | You think visually and like seeing the flow |
| The logic is trigger → check → act | There's long-running state (state machines, multi-step sequences) |
| Phones, voice and other people should find and toggle them | You call lots of external APIs or need complex data shaping |
| You want traces, blueprints and backups built in | You already have years of flows that work |

Mixing is fine with a rule, e.g. *"simple room automations in HA, anything stateful in
Node-RED"*. Never implement the same behaviour in both.

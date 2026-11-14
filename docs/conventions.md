# Conventions

House rules that keep the system readable for people and agents. These are sensible
defaults — change them to suit your home, but write the change down here.

## Entity naming

Entity IDs are `<domain>.<area>_<thing>`, lower snake case. Friendly names are
`<Area> <Thing>`. One word for one thing — no `door_door`, no device model numbers in IDs
where a room name will do.

| Pattern | Example |
|---|---|
| Room light group | `light.<area>_lights` |
| Door / window contact | `binary_sensor.<area>_door`, `binary_sensor.<area>_window` |
| Motion / occupancy | `binary_sensor.<area>_motion`, `binary_sensor.<area>_occupancy` |
| Climate readings | `sensor.<area>_temperature`, `sensor.<area>_humidity` |
| Modes | `input_boolean.guest_mode`, `input_boolean.vacation_mode` |
| Per-room automation switch | `input_boolean.<area>_auto_lights` |

Area slugs (fill in yours): `kitchen`, `living_room`, `hallway`, `bedroom`, …

Leave long integration-generated IDs alone when lots of things already use them, and
note them here.

## Renaming or removing an entity

1. `grep -rn "<entity_id>" homeassistant node-red` — dashboards, automations, helpers
   and flows all live here, so this finds every consumer.
2. Rename in HA (Settings › Devices & services › Entities). It is permanent across restarts.
3. Update every consumer **in the same change**: dashboards, automations, scripts,
   helpers, Node-RED nodes (`entityId`, function code, JSONata), YAML config.
4. Sync, then `grep -rn "<old_id>" homeassistant node-red` should return nothing.
5. Removing: confirm with the owner first — offline isn't dead.

## Automations

House rules, the native-first table and how agents change automations:
[automations.md](automations.md) (Home Assistant) and [node-red.md](node-red.md) (Node-RED).
Both share the same ideas: a person can read it in the UI, shared rules are helpers,
anything time-limited has a fail-safe, and seasonal automations are disabled, not deleted.

## Fail-safes

A fail-safe puts something back to a safe state from the current state, not from an event or
a running timer, so it still works after a restart, a reload or a missed event. Common shapes:

| Shape | Example | Catches out |
|---|---|---|
| Poll (`time_pattern`, or a Node-RED `inject` every N s) → conditions → off | Every 15 s: hall group on and no motion for 5 min → group off | Acts on **groups and areas**: anything new that holds one member on gets switched off |
| "Quiet for N min" (`for:` on a state trigger) → off | Motion clear for 10 min → room lights off | Turns off whatever is showing now, including a scene you added |
| Schedule (`time`, `sun`, Node-RED cron) → off | 23:00 night switch-off | Fires daily whatever the state; your feature must end with it or be known to it |
| `last_changed` cap | Heater on for 2 h → off | A feature that legitimately runs longer must be known to the cap |
| On start (`homeassistant: start`, Node-RED *on start*) | Boost found still on after a restart → off | Your feature's state after a restart |

**Find them:** `python3 tools/failsafes.py [--off] <entity> <group> <area> …`. Name every
group, area and label the entity belongs to, because a fail-safe on `light.ground_floor` or
`area_id: hall` reaches the bulb inside it.

**Rules**
- Anything an automation leaves on has a fail-safe. Use a timed check of current state or
  `last_changed`, not a `delay` (lost on restart), and give it a description that says what it
  protects.
- Before a new or changed automation, check the fail-safes on its devices (AGENTS.md §6b).
- A conflict is fixed by teaching the fail-safe the new state with a native condition on a
  helper (`input_boolean`, `input_text`, `input_select`), sending the "skip" branch to whatever
  should still happen. Never by disabling or deleting the fail-safe.
- Whatever marks "my feature is active" is cleared on every way out, or the fail-safe stays
  bypassed for good.
- Record the interaction in the feature's docs, so the next change sees it.

## Helpers

Prefer the UI helper that fits (group, threshold, derivative, history stats, schedule,
times of day, template) over a template sensor; prefer a template sensor over Jinja
repeated in several automations.

## Notifications

One notify target per person, recorded in [home.md](home.md). Critical alerts (leaks,
smoke, alarm) are separate from nice-to-know ones, so people can mute one without the other.

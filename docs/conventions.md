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

- Every automation has an `alias` (what) and a `description` (why).
- Choose `mode` on purpose: `single` for one-shots, `restart` for "reset the timer"
  (motion lights), `queued` when every trigger must run, `parallel` rarely.
- Triggers and conditions use native options (`state`, `numeric_state`, `for:`, `sun`,
  `zone`, `time`) before templates.
- Anything time-limited ("off after 30 min", boosts) has a fail-safe that still works
  after a restart.
- Shared rules ("evening", "someone home", "season") are helpers — a `schedule`,
  `tod`, template binary sensor or group — that automations trigger on.
- Seasonal automations are disabled out of season, not deleted.

## Helpers

Prefer the UI helper that fits (group, threshold, derivative, history stats, schedule,
times of day, template) over a template sensor; prefer a template sensor over Jinja
repeated in several automations.

## Notifications

One notify target per person, recorded in [home.md](home.md). Critical alerts (leaks,
smoke, alarm) are separate from nice-to-know ones, so people can mute one without the other.

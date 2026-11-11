# Dashboards

How dashboards are designed and changed here. Generic rules that make any dashboard
better; **this home's look** (theme, colours, card recipes) lives in
[style-guide.md](style-guide.md). Exact card options are in the
`home-assistant-best-practices` skill (`references/dashboard-guide.md`,
`dashboard-cards.md`); Bubble Card has its own optional skill, `ha-bubble-dashboard`.

What each dashboard contains is generated on every sync:
[reference/dashboards.md](reference/dashboards.md).

## Design rules

**1. Design for the question, not the device list.** A dashboard answers *"is anything
wrong?"*, *"is everyone home?"*, *"is it warm?"*, *"turn the lights off"* — in that order.
Don't mirror the entity list; nobody needs 40 battery sensors on the home screen.

**2. Attention first.** The top of the main view shows only what needs a person right now
(a door left open, a leak, a low battery, a failed backup, an update that broke something)
and is **empty when all is well**. Use conditional visibility so problems appear and
disappear on their own.

**3. Phone first, then wide screens.** Most use is one-handed on a phone. Use the
**sections** view, check every change at phone width (~390 px) and desktop width, and keep
tap targets at least 44 px. Wall panels and tablets get their own dashboard or view when
they need a different layout, not a squeezed copy.

**4. One section per area or purpose.** Group by room (Kitchen, Bedroom…) or by job
(Security, Climate, Energy), start each section with a heading card, and keep the order
the same everywhere so people learn where things are.

**5. Native cards first.** Tile, heading, badges, area, thermostat, media, history and
statistics graphs cover most needs and survive HA updates. Reach for a custom card only
when native can't do it, and then use **one** card family consistently rather than five
that each look different. Every custom card is another thing that can break on update
(AGENTS.md §7a).

**6. Colour means something.** Colour shows *state* — on, open, warning, alert — and is
used the same way everywhere. Take colours from the theme (`var(--state-icon-active-color)`,
`var(--error-color)`, named HA colours like `amber`), never hex codes in card config, so
light and dark mode and theme changes keep working. Check contrast in both modes.

**7. Quiet when idle.** Idle things are muted; active things stand out. A screen where
everything is bright is a screen where nothing is.

**8. Show state and the way to change it together.** A light tile shows whether it's on
*and* toggles it. Details (history, settings, rarely used controls) go one tap away — a
more-info dialog, a pop-up or a sub-view — not on the main screen.

**9. Guard real-world actions.** Anything easy to fat-finger with a real effect (arming,
unlocking, "all off", modes, heating schedules) uses a `confirmation`. Locks and alarms
never sit where a scroll can tap them.

**10. Show offline, don't hide it.** An unavailable device should look unavailable, so a
person notices. Hide things only when they're irrelevant (seasonal, a guest-mode panel
outside guest mode), not when they're broken.

**11. Words matter.** Short, sentence-case labels ("Back door", "Last 24 hours"), area
names instead of device names, the same name for the same thing everywhere. Icons from
`mdi:`, one icon per concept.

**12. Consistency beats novelty.** Copy an existing card pattern from
[style-guide.md](style-guide.md) before inventing one. A new pattern gets added there.

## Working on dashboards (agents)

1. **Read first.** Get the current config (`ha_config_get_dashboard`, or `lovelace/config`
   with `url_path`) and the style guide.
2. **Change the smallest piece.** Edit the one card or section asked for; keep everything
   else byte-identical; save the whole config back (`ha_config_set_dashboard`, or
   `lovelace/config/save`).
3. **Look at it.** Screenshot at phone and desktop width, in light and dark mode if the
   theme supports both, and fix what looks off *before* reporting done. Open any pop-up
   or more-info you changed.
4. **New custom card?** Ask first — it's a new dependency. Install it from the
   Marketplace, add it to the style guide.
5. **Sync and commit** (`feat(dashboard): …`). New patterns go in the style guide in the
   same commit.

Never hand-edit `homeassistant/dashboards/*.yaml` to change a dashboard — they're an
export. To restore one, paste it into the Raw configuration editor
([backup-and-restore.md](backup-and-restore.md#restore-a-dashboard)).

## Dashboards in this home

_Fill in as they're built: purpose, audience, who it's for._

| Dashboard | Path | For | Notes |
|---|---|---|---|
| | | | |

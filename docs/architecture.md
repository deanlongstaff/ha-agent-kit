# Architecture

The big picture of this home's smart system. `ha-onboard` drafts it from the first
export; keep it current when hardware, add-ons or integrations change. Detail lives in
the generated files — link to them rather than copying lists here.

## Platform

- **Home Assistant** — install type, hardware, version: see [home.md](home.md) and
  [`export-info.yaml`](../homeassistant/export-info.yaml).
- **Network** — _how devices connect: Wi-Fi, Zigbee coordinator, Thread border routers, Z-Wave stick…_
- **Remote access** — _how, and what it's used for_

## Add-ons

Full list: [`inventory/addons.yaml`](../homeassistant/inventory/addons.yaml).

| Add-on | Used for |
|---|---|
| | |

## Integrations (highlights)

Full list: [`inventory/integrations.yaml`](../homeassistant/inventory/integrations.yaml).

| Integration | What it brings |
|---|---|
| | |

## Where logic lives

_Which behaviours are HA automations, which are Node-RED flows, which are blueprints,
and why. Agents follow this when adding something new._

## Areas

Generated: [reference/areas.md](reference/areas.md).

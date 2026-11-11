# Style guide

This home's look, so every new card matches the last one. The general rules are in
[dashboards.md](dashboards.md); this page records *your* choices. Agents fill it in
while building the first dashboard and add to it whenever a new pattern appears.

## Foundations

| | |
|---|---|
| Theme | _default / name of your theme (and where it lives: Marketplace or `/config/themes`)_ |
| Light / dark | _follows the system / always dark / always light_ |
| Layout | _sections view, max columns, typical card width_ |
| Card family | _native tile cards / Mushroom / Bubble Card / …_ |
| Icons | _`mdi:` set; fixed icons per area listed below_ |
| Copy | _sentence case, units style (`21.5°`, `21.5 °C`), separators_ |

## Colours

Theme variables or HA named colours only — no hex in card config.

| Meaning | Colour |
|---|---|
| On / active | _e.g. `var(--state-icon-active-color)`_ |
| Warning | _e.g. `amber`_ |
| Alert | _e.g. `var(--error-color)`_ |
| Per area (optional) | _e.g. Kitchen `orange`, Bedroom `purple`_ |

## Card patterns

One entry per reusable pattern, with a short YAML snippet. Copy these before inventing.

### _Pattern name (e.g. "Room tile")_

_What it's for, where it's used._

```yaml
# snippet
```

## Gotchas

_Things that bit you: a card option that doesn't work on phones, a custom card's CSS
quirk, a wall panel's old browser._

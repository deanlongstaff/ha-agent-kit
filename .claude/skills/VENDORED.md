# Skills

| Skill | Source | Purpose |
|---|---|---|
| `ha-onboard` | this kit | First-run setup: health check, MCP, privacy, first export, house docs |
| `ha-sync` | this kit | Collect → sync → checks → docs → commit, after every change |
| `home-assistant-best-practices` | vendored | Native-first HA automations, helpers, templates, safe refactoring |
| `node-red` | vendored | Node-RED flows with the Home Assistant websocket nodes |
| `ha-bubble-dashboard` | vendored (optional) | Bubble Card dashboards, themes and CSS |

## Vendored third-party skills

Copied in so every agent session gets them without installing anything. All are MIT
licensed; each folder keeps its licence. Huge thanks to their authors.

| Skill | Upstream | Path | Local changes |
|---|---|---|---|
| `home-assistant-best-practices` | [homeassistant-ai/skills](https://github.com/homeassistant-ai/skills) | `skills/home-assistant-best-practices` | Added upstream `LICENSE` |
| `node-red` | [tonylofgren/aurora-smart-home](https://github.com/tonylofgren/aurora-smart-home) | `node-red` | Frontmatter `name: Node-RED` → `node-red` (skill names must be kebab-case) |
| `ha-bubble-dashboard` | [johnnyh1975/HA_Bubble_Skill](https://github.com/johnnyh1975/HA_Bubble_Skill) | repo root (packaged files only) | Dropped `scripts/`, `.github/`; added `LICENSE` from the README's MIT statement |

Refresh with `tools/update_skills.sh` (pulls upstream HEAD and prints the commits).
Review the diff before committing.

`AGENTS.md` wins over anything in these skills. Known drift (the skills can lag Home
Assistant):
- HA 2026.11 built HACS in as the **Marketplace**: cards install to `/local/community/…`
  (`/hacsfiles/…` still works), and `integration_entities('hacs')` is now
  `integration_entities('marketplace')`. Some skills still say HACS / `/hacsfiles/`.
- `ha-bubble-dashboard` targets Bubble Card 3.3 and its own CSS theme. Optional: delete
  the folder if you don't use Bubble Card.

ha-mcp bundles its own copy of `home-assistant-best-practices` (`ha_get_skill_guide`).
Prefer the pinned copy here so behaviour doesn't change under you when ha-mcp updates.

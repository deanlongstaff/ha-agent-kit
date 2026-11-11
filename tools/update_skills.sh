#!/usr/bin/env bash
# Refresh the vendored third-party skills in .claude/skills from upstream HEAD.
# Our own skills (ha-sync, ha-onboard) are not touched. Review the diff before committing.
set -euo pipefail
cd "$(dirname "$0")/.."
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT

fetch() { git clone -q --depth 1 "https://github.com/$1.git" "$tmp/$2"; echo "$1 @ $(git -C "$tmp/$2" rev-parse HEAD)"; }

fetch johnnyh1975/HA_Bubble_Skill bubble
rm -rf .claude/skills/ha-bubble-dashboard && mkdir -p .claude/skills/ha-bubble-dashboard
cp -r "$tmp/bubble/"{SKILL.md,README.md,CHANGELOG.md,references,theme} .claude/skills/ha-bubble-dashboard/
printf 'MIT License (as stated in the upstream README)\n\nCopyright (c) johnnyh1975 — https://github.com/johnnyh1975/HA_Bubble_Skill\n' > .claude/skills/ha-bubble-dashboard/LICENSE

fetch homeassistant-ai/skills hass
rm -rf .claude/skills/home-assistant-best-practices
cp -r "$tmp/hass/skills/home-assistant-best-practices" .claude/skills/
cp "$tmp/hass/LICENSE" .claude/skills/home-assistant-best-practices/LICENSE

fetch tonylofgren/aurora-smart-home aurora
rm -rf .claude/skills/node-red
cp -r "$tmp/aurora/node-red" .claude/skills/
sed -i.bak 's/^name: Node-RED$/name: node-red/' .claude/skills/node-red/SKILL.md && rm -f .claude/skills/node-red/SKILL.md.bak

echo "Done. Update the commit table in .claude/skills/VENDORED.md."

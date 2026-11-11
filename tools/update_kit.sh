#!/usr/bin/env bash
# Pull the latest HA Agent Kit tooling into your home repo, leaving your home's files alone.
#
#   tools/update_kit.sh            # from the default kit repo
#   KIT_REPO=<git url> tools/update_kit.sh
#
# Kit-owned (overwritten): AGENTS.md, CLAUDE.md, SECURITY.md, tools/, .githooks/,
#   .github/workflows/, .claude/skills/, docs/guides/, .gitleaks.toml, .env.example,
#   .secrets-denylist.example
# Yours (never touched): README.md, CHANGELOG.md, docs/*.md, homeassistant/, node-red/,
#   tools/function_baseline.json, tools/automation_baseline.json, .claude/settings.local.json
#
# Nothing is committed: review `git diff`, then commit as `chore(repo): update HA Agent Kit`.
set -euo pipefail
cd "$(dirname "$0")/.."
KIT_REPO="${KIT_REPO:-https://github.com/deanlongstaff/ha-agent-kit.git}"

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Commit or stash your changes first, so the kit update is its own diff." >&2
  exit 1
fi

git fetch --quiet --depth 1 "$KIT_REPO" main
keep=$(mktemp -d)
for f in function_baseline.json automation_baseline.json; do cp "tools/$f" "$keep/$f" 2>/dev/null || true; done
git checkout FETCH_HEAD -- AGENTS.md CLAUDE.md SECURITY.md tools .githooks .github/workflows \
  .claude/skills docs/guides .gitleaks.toml .env.example .secrets-denylist.example .claude/settings.json
for f in function_baseline.json automation_baseline.json; do [ -f "$keep/$f" ] && cp "$keep/$f" "tools/$f"; done
rm -rf "$keep"
chmod +x .githooks/* tools/*.py tools/*.sh tools/*.mjs 2>/dev/null || true

echo "Updated to kit $(git rev-parse --short FETCH_HEAD). Review:"
git status --short

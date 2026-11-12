#!/usr/bin/env python3
"""Pull the latest HA Agent Kit tooling into your home repo, leaving your home's files alone.

    python3 tools/update_kit.py                     (Windows: py tools/update_kit.py)
    KIT_REPO=<git url> python3 tools/update_kit.py

Kit-owned (overwritten): AGENTS.md, CLAUDE.md, SECURITY.md, tools/, .githooks/,
  .github/workflows/, .claude/skills/, .claude/settings.json, .gemini/settings.json,
  docs/guides/, tests/, .gitleaks.toml, .env.example, .secrets-denylist.example
Yours (never touched): README.md, CHANGELOG.md, privacy.yaml, docs/*.md, homeassistant/, node-red/,
  tools/function_baseline.json, tools/automation_baseline.json, .claude/settings.local.json

Nothing is committed: review `git diff`, then commit as `chore(repo): update HA Agent Kit`.
"""
import os, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _env import ROOT, utf8_console  # noqa: E402

utf8_console()
KIT = os.environ.get("KIT_REPO", "https://github.com/deanlongstaff/ha-agent-kit.git")
KIT_PATHS = ["AGENTS.md", "CLAUDE.md", "SECURITY.md", "tools", ".githooks", ".github/workflows", ".claude/skills",
             ".claude/settings.json", ".gemini/settings.json", "docs/guides", "tests", ".gitleaks.toml", ".env.example",
             ".secrets-denylist.example"]
KEEP = ["tools/function_baseline.json", "tools/automation_baseline.json"]


def git(*args, check=True):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode:
        sys.exit(f"git {' '.join(args)} failed:\n{r.stderr.strip()}")
    return r.stdout


if git("status", "--porcelain").strip():
    sys.exit("Commit or stash your changes first, so the kit update is its own diff.")

git("fetch", "--quiet", "--depth", "1", KIT, "main")
kept = {p: (ROOT / p).read_bytes() for p in KEEP if (ROOT / p).exists()}
available = set(git("ls-tree", "-r", "--name-only", "FETCH_HEAD").splitlines())
paths = [p for p in KIT_PATHS if p in available or any(a.startswith(p + "/") for a in available)]
git("checkout", "FETCH_HEAD", "--", *paths)
for p, data in kept.items():
    (ROOT / p).write_bytes(data)

print(f"Updated to kit {git('rev-parse', '--short', 'FETCH_HEAD').strip()}. Refreshing setup…\n")
subprocess.call([sys.executable, str(ROOT / "tools" / "setup.py")], cwd=ROOT)
print("\nReview with `git diff`, then: git commit -am \"chore(repo): update HA Agent Kit\"")
print(git("status", "--short"))

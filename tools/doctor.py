#!/usr/bin/env python3
"""Check this clone is set up safely. Run it any time:  python3 tools/doctor.py

Read-only: it reports what's missing and how to fix it, and changes nothing.
"""
from __future__ import annotations

import json, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from _env import PRIVACY_TERMS, privacy_level, utf8_console, venv_python  # noqa: E402

utf8_console()
OK, WARN, FAIL = "✅", "⚠️ ", "❌"
results: list[tuple[str, str, str]] = []


def add(status: str, what: str, fix: str = ""):
    results.append((status, what, fix))


def run(*cmd: str) -> str:
    try:
        return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


# Python + PyYAML
if sys.version_info < (3, 9):
    add(FAIL, f"Python {sys.version.split()[0]}", "use Python 3.9 or newer")
try:
    import yaml  # noqa: F401
    add(OK, "PyYAML installed")
except ImportError:
    venv = venv_python()
    if venv and subprocess.run([str(venv), "-c", "import yaml"], capture_output=True).returncode == 0:
        add(OK, "PyYAML installed in the repo's .venv (tools use it automatically)")
    else:
        add(FAIL, "PyYAML missing", "python3 tools/setup.py   (Windows: py tools/setup.py)")

# Node (only for the terminal collector)
node = run("node", "--version")
if node and int(node.lstrip("v").split(".")[0]) >= 22:
    add(OK, f"Node {node} (terminal collector available)")
else:
    add(WARN, f"Node 22+ not found ({node or 'none'})", "optional: only needed for tools/collect-cli.mjs; the browser collector works without it")

# Git hook
hooks = run("git", "config", "core.hooksPath")
if hooks == ".githooks":
    add(OK, "pre-commit hook enabled (secret scan + validation)")
else:
    add(FAIL, "pre-commit hook not enabled", "python3 tools/setup.py")

# Denylist
deny = ROOT / ".secrets-denylist"
entries = [l for l in deny.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")] if deny.exists() else []
if entries:
    add(OK, f".secrets-denylist has {len(entries)} entries")
else:
    add(WARN, "personal denylist is empty", "add your surname, street, postcode, Wi-Fi name… to .secrets-denylist (onboarding helps)")

# Things that must never be tracked
tracked = run("git", "ls-files").splitlines()
bad = [f for f in tracked if Path(f).name in {".env", "secrets.yaml", ".secrets-denylist", ".mcp.json", "flows_cred.json"} or f.startswith(".storage/")]
add(FAIL if bad else OK, f"sensitive files tracked by git: {', '.join(bad)}" if bad else "no sensitive files tracked",
    "git rm --cached <file> and rotate anything it contained" if bad else "")

# .env token hygiene
env = ROOT / ".env"
if env.exists() and "HA_TOKEN=" in env.read_text(encoding="utf-8") and "HA_TOKEN=\n" not in env.read_text(encoding="utf-8") + "\n":
    add(WARN, ".env holds a Home Assistant token", "fine for a single-user machine; better: pass it from a password manager (see .env.example)")

# Project-scoped MCP config would put the connect URL (a credential) in the repo
if (ROOT / ".mcp.json").exists():
    add(FAIL, ".mcp.json in the repo", "MCP URLs are credentials: add the server at user scope (claude mcp add --scope user …) and delete .mcp.json")

# Privacy level
level = privacy_level()
learned = [l for l in PRIVACY_TERMS.read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")] if PRIVACY_TERMS.exists() else []
add(OK, f"privacy level: {level}" + (f" ({len(learned)} names learned from HA)" if level == "strict" else ""),
    "" if level != "strict" or learned else "run a sync so strict mode learns the names to keep out")

# GitHub remote visibility
remote = run("git", "remote", "get-url", "origin")
if not remote:
    add(WARN, "no git remote yet", "create a PRIVATE repo (gh repo create my-home --private --source . --push)")
elif shutil.which("gh"):
    info = run("gh", "repo", "view", "--json", "visibility,nameWithOwner")
    try:
        v = json.loads(info)
        if v.get("nameWithOwner", "").lower().endswith("/ha-agent-kit") and v.get("visibility") == "PUBLIC":
            add(FAIL, f"origin is the public kit itself ({v['nameWithOwner']})",
                "make your own private copy: ask your agent to 'set up HA Agent Kit', or: git remote remove origin")
        elif v.get("visibility") == "PUBLIC" and level == "strict":
            add(WARN, f"{v['nameWithOwner']} is PUBLIC (privacy: strict)",
                "fine if you mean to share it; re-read SECURITY.md › Privacy levels before each push")
        elif v.get("visibility") == "PUBLIC":
            add(FAIL, f"{v['nameWithOwner']} is PUBLIC at privacy level '{level}'",
                "make it private (gh repo edit --visibility private --accept-visibility-change-consequences), "
                "or set level: strict in privacy.yaml if you mean to publish it")
        else:
            add(OK, f"{v['nameWithOwner']} is {v.get('visibility', '?').lower()}")
    except (json.JSONDecodeError, KeyError):
        add(WARN, f"couldn't read the remote's visibility ({remote.split('@')[-1]})", "check it's private on GitHub")
else:
    add(WARN, "can't check remote visibility (no gh CLI)", "make sure the GitHub repo is private")

# Skills present
skills = ROOT / ".claude" / "skills"
have = sorted(p.parent.name for p in skills.glob("*/SKILL.md"))
need = {"ha-sync", "ha-onboard", "home-assistant-best-practices"}
missing = need - set(have)
add(FAIL if missing else OK, f"skills missing: {', '.join(sorted(missing))}" if missing else f"skills: {', '.join(have)}",
    "restore .claude/skills from the kit, or run tools/update_skills.sh" if missing else "")

# Skills copy for non-Claude agents (.agents/skills, made by setup.py)
mirror = ROOT / ".agents" / "skills"
if mirror.is_dir():
    stale = any(not (mirror / p.relative_to(skills)).exists() or (mirror / p.relative_to(skills)).read_bytes() != p.read_bytes()
                for p in skills.rglob("*") if p.is_file())
    add(WARN if stale else OK, ".agents/skills is out of date" if stale else ".agents/skills in step (Codex, Gemini CLI and others)",
        "python3 tools/setup.py" if stale else "")

# Export state
info = ROOT / "homeassistant" / "export-info.yaml"
if info.exists():
    add(OK, "export present: " + " · ".join(l.strip() for l in info.read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")))
else:
    add(WARN, "nothing exported yet", "ask your agent to 'continue onboarding'")

# Secret scan of the working tree
if (ROOT / "tools" / "check_secrets.py").exists():
    r = subprocess.run([sys.executable, "tools/check_secrets.py"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    add(OK if r.returncode == 0 else FAIL, "secret scan clean" if r.returncode == 0 else "secret scan found problems",
        "" if r.returncode == 0 else "python3 tools/check_secrets.py")

print("\nHA Agent Kit — doctor\n")
for status, what, fix in results:
    print(f"  {status} {what}" + (f"\n       → {fix}" if fix else ""))
fails = sum(1 for s, _, _ in results if s == FAIL)
print(f"\n{'All good.' if not fails else f'{fails} problem(s) to fix.'}\n")
sys.exit(1 if fails else 0)

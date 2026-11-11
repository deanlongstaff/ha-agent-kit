#!/usr/bin/env python3
"""One-time local setup. Safe to re-run. Installs nothing system-wide.

    python3 tools/setup.py        (Windows: py tools/setup.py)

- checks git and Python 3.9+ (and Node 22+, optional), with an install hint for your OS
- makes PyYAML available: your Python's copy if it has one, otherwise a private .venv
  inside this repo (git-ignored)
- enables the pre-commit hook (secret scan + validation)
- creates your git-ignored .secrets-denylist from the example
- copies the skills to .agents/skills/ for agents other than Claude Code (Codex, Gemini
  CLI, Cursor, Copilot…), git-ignored, refreshed on every run
- runs tools/doctor.py

Your agent runs this during onboarding.
"""
from __future__ import annotations

import platform, shutil, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _env import ROOT, utf8_console, venv_python  # noqa: E402

utf8_console()
OS = platform.system()  # Darwin / Linux / Windows

HINTS = {
    "Darwin": {"git": "xcode-select --install   (or: brew install git)",
               "python": "brew install python   (or download from python.org)",
               "node": "brew install node   (or download from nodejs.org)"},
    "Linux": {"git": "sudo apt install git   (or your distro's package manager)",
              "python": "sudo apt install python3 python3-venv",
              "venv": "sudo apt install python3-venv",
              "node": "see https://nodejs.org/en/download (Node 22 or newer)"},
    "Windows": {"git": "winget install Git.Git",
                "python": "winget install Python.Python.3.12",
                "node": "winget install OpenJS.NodeJS.LTS"},
}


def hint(tool: str) -> str:
    h = HINTS.get(OS, {})
    return h.get(tool) or h.get("python", f"install {tool} for your system")


def ok(msg): print(f"  ✅ {msg}")
def warn(msg): print(f"  ⚠️  {msg}")


def fail(msg):
    print(f"  ❌ {msg}")
    sys.exit(1)


def run(*cmd, **kw):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


print("\nHA Agent Kit — setup\n")

# git
if not shutil.which("git"):
    fail(f"git not found — {hint('git')}")
ok(run("git", "--version").stdout.strip())

# Python
if sys.version_info < (3, 9):
    fail(f"Python {platform.python_version()} is too old — {hint('python')}")
ok(f"Python {platform.python_version()}")

# PyYAML: this Python, or a private .venv
try:
    import yaml  # noqa: F401
    ok("PyYAML available")
except ImportError:
    py = venv_python()
    if not py:
        r = run(sys.executable, "-m", "venv", ".venv")
        py = venv_python()
        if r.returncode or not py:
            fail(f"couldn't create .venv — {hint('venv')}\n     {r.stderr.strip()[-300:]}")
    r = run(str(py), "-m", "pip", "install", "--quiet", "--disable-pip-version-check", "pyyaml")
    if r.returncode:
        fail(f"couldn't install PyYAML into .venv (offline?)\n     {r.stderr.strip()[-300:]}")
    ok("PyYAML installed in .venv (private to this repo)")

# Node (optional)
node = shutil.which("node")
ver = run(node, "-p", "process.versions.node").stdout.strip() if node else ""
if ver and int(ver.split(".")[0]) >= 22:
    ok(f"Node {ver} (terminal collector available)")
else:
    warn(f"Node 22+ not found — optional, only for tools/collect-cli.mjs ({hint('node')})")

# git plumbing
if not (ROOT / ".git").exists():
    run("git", "init", "-q", "-b", "main")
    ok("git repository created")
run("git", "config", "core.hooksPath", ".githooks")
ok("pre-commit hook enabled")
if OS != "Windows":
    for p in [*ROOT.glob(".githooks/*"), *ROOT.glob("tools/*.py"), *ROOT.glob("tools/*.sh"), *ROOT.glob("tools/*.mjs")]:
        p.chmod(p.stat().st_mode | 0o111)

# denylist
deny = ROOT / ".secrets-denylist"
if deny.exists():
    ok(".secrets-denylist present")
else:
    shutil.copyfile(ROOT / ".secrets-denylist.example", deny)
    ok(".secrets-denylist created (filled in during onboarding)")

# skills for other agents: .claude/skills -> .agents/skills (git-ignored copy)
src, dst = ROOT / ".claude" / "skills", ROOT / ".agents" / "skills"
if src.is_dir():
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(src, dst)
    ok(f"skills copied to .agents/skills for Codex, Gemini CLI and other agents ({len(list(dst.glob('*/SKILL.md')))} skills)")

print()
sys.exit(subprocess.call([sys.executable, str(ROOT / "tools" / "doctor.py")], cwd=ROOT) and 0)

#!/usr/bin/env bash
# One-time local setup for this repo. Safe to re-run. Installs nothing system-wide.
#
#   bash tools/setup.sh
#
# - checks git and Python 3.9+ (and Node 22+, optional)
# - makes PyYAML available: uses your Python's copy if it has one, otherwise creates a
#   private .venv inside this repo (git-ignored) and installs it there
# - enables the pre-commit hook (secret scan + validation)
# - creates your git-ignored .secrets-denylist from the example
# - runs tools/doctor.py
#
# Your agent runs this during onboarding. On Windows, run it from Git Bash.
set -uo pipefail
cd "$(dirname "$0")/.."

ok()   { printf '  ✅ %s\n' "$*"; }
warn() { printf '  ⚠️  %s\n' "$*"; }
fail() { printf '  ❌ %s\n' "$*"; exit 1; }
has()  { command -v "$1" >/dev/null 2>&1; }

os="$(uname -s 2>/dev/null || echo unknown)"
hint() {  # how to install $1 on this OS
  case "$os:$1" in
    Darwin:git|Darwin:python) echo "run: xcode-select --install   (or: brew install $1)" ;;
    Darwin:node)              echo "run: brew install node   (or download from nodejs.org)" ;;
    Linux:git)                echo "run: sudo apt install git   (or your distro's package manager)" ;;
    Linux:python)             echo "run: sudo apt install python3 python3-venv" ;;
    Linux:node)               echo "see https://nodejs.org/en/download (Node 22 or newer)" ;;
    MINGW*:git|MSYS*:git|CYGWIN*:git)       echo "run: winget install Git.Git" ;;
    MINGW*:python|MSYS*:python|CYGWIN*:python) echo "run: winget install Python.Python.3.12" ;;
    MINGW*:node|MSYS*:node|CYGWIN*:node)    echo "run: winget install OpenJS.NodeJS.LTS" ;;
    *) echo "install $1 for your system" ;;
  esac
}

echo
echo "HA Agent Kit — setup"
echo

# git
has git || fail "git not found — $(hint git)"
ok "git $(git --version | awk '{print $3}')"

# Python 3.9+
PY=""
for c in python3 python; do
  if has "$c" && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then PY="$c"; break; fi
done
[ -n "$PY" ] || fail "Python 3.9 or newer not found — $(hint python)"
ok "Python $("$PY" -c 'import platform; print(platform.python_version())')"

# PyYAML — system copy, or a private .venv
if "$PY" -c 'import yaml' 2>/dev/null; then
  ok "PyYAML available"
else
  VPY=".venv/bin/python"; [ -x "$VPY" ] || VPY=".venv/Scripts/python.exe"
  if [ ! -x "$VPY" ]; then
    "$PY" -m venv .venv >/dev/null 2>&1 || fail "couldn't create .venv — $(hint python)"
    VPY=".venv/bin/python"; [ -x "$VPY" ] || VPY=".venv/Scripts/python.exe"
  fi
  "$VPY" -m pip install --quiet --disable-pip-version-check pyyaml || fail "couldn't install PyYAML into .venv (offline?)"
  ok "PyYAML installed in .venv (private to this repo)"
fi

# Node (optional: terminal collector only)
if has node && [ "$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)" -ge 22 ]; then
  ok "Node $(node --version) (terminal collector available)"
else
  warn "Node 22+ not found — optional, only for tools/collect-cli.mjs ($(hint node))"
fi

# Repo plumbing
[ -d .git ] || { git init -q -b main && ok "git repository created"; }
git config core.hooksPath .githooks && ok "pre-commit hook enabled"
chmod +x .githooks/* tools/*.py tools/*.sh tools/*.mjs 2>/dev/null || true
if [ -f .secrets-denylist ]; then ok ".secrets-denylist present"
else cp .secrets-denylist.example .secrets-denylist && ok ".secrets-denylist created (filled in during onboarding)"; fi

echo
"$PY" tools/doctor.py
exit 0

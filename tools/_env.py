"""Shared start-up for the kit's Python tools: works the same on Windows, macOS and Linux.

- ensure_yaml(): PyYAML from the current Python, or else from the repo's private .venv
  (tools/setup.py creates it only when needed), re-running the tool with that Python.
- utf8_console(): print emoji and other non-ASCII text on Windows consoles too.
"""
import os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHONS = (ROOT / ".venv" / "bin" / "python", ROOT / ".venv" / "Scripts" / "python.exe")


def utf8_console():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


LEVELS = ("relaxed", "standard", "strict")
PRIVACY_TERMS = ROOT / ".export" / "privacy-terms.txt"  # names learned by sync at strict level (git-ignored)


def privacy_level() -> str:
    """The `level:` in privacy.yaml (relaxed / standard / strict); standard if missing or unknown."""
    import re
    p = ROOT / "privacy.yaml"
    m = re.search(r"^level:\s*([a-z]+)", p.read_text(encoding="utf-8"), re.M) if p.exists() else None
    return m.group(1) if m and m.group(1) in LEVELS else "standard"


def venv_python():
    return next((p for p in VENV_PYTHONS if p.exists()), None)


def ensure_yaml():
    utf8_console()
    try:
        import yaml
        return yaml
    except ImportError:
        pass
    py = venv_python()
    if py and not os.environ.get("HA_KIT_REEXEC") and os.path.abspath(sys.executable) != os.path.abspath(py):
        env = dict(os.environ, HA_KIT_REEXEC="1")
        sys.exit(subprocess.call([str(py), *sys.argv], env=env))  # not os.execv: it misbehaves on Windows
    sys.exit("PyYAML is missing — run: python3 tools/setup.py   (Windows: py tools/setup.py)")

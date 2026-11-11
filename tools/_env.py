"""Find PyYAML: the current Python if it has it, otherwise the repo's private .venv.

bash tools/setup.sh creates .venv only when the system Python lacks PyYAML, so nothing is
installed system-wide. Every tool calls ensure_yaml() and can be run as plain
`python3 tools/<tool>.py` either way.
"""
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHONS = (ROOT / ".venv" / "bin" / "python", ROOT / ".venv" / "Scripts" / "python.exe")


def ensure_yaml():
    try:
        import yaml
        return yaml
    except ImportError:
        pass
    if not os.environ.get("HA_KIT_REEXEC"):
        for py in VENV_PYTHONS:
            if py.exists() and os.path.abspath(sys.executable) != os.path.abspath(py):
                os.environ["HA_KIT_REEXEC"] = "1"
                os.execv(str(py), [str(py), *sys.argv])
    sys.exit("PyYAML is missing — run bash tools/setup.sh (or: python3 -m pip install pyyaml)")

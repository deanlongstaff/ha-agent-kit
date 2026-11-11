#!/usr/bin/env python3
"""Structural checks run in CI and by the pre-commit hook.

- every YAML file parses (HA tags like !secret / !include are accepted)
- every JSON file parses
- node-red/ split files reassemble with no duplicate or dangling node ids
- new function nodes stay small and don't read HA state directly (function_lint.py)
- new automations and scripts follow the house rules (automation_lint.py)
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from _env import ensure_yaml  # noqa: E402

yaml = ensure_yaml()
from nodered_build import build  # noqa: E402
from function_lint import check as check_functions  # noqa: E402
from automation_lint import check as check_automations  # noqa: E402


class Loader(yaml.SafeLoader):
    pass


Loader.add_multi_constructor("!", lambda loader, suffix, node: None)

errors = []
for p in ROOT.rglob("*"):
    rel = p.relative_to(ROOT).as_posix()
    if not p.is_file() or rel.startswith((".git/", ".export/", ".claude/skills/", ".agents/", ".venv/", "node_modules/")):
        continue
    try:
        if p.suffix in (".yaml", ".yml"):
            yaml.load(p.read_text(encoding="utf-8"), Loader=Loader)
        elif p.suffix == ".json":
            json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        errors.append(f"{rel}: {e}")

if (ROOT / "node-red" / "index.json").exists():
    flows = build()
    ids = [n["id"] for n in flows]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        errors.append(f"node-red: duplicate ids {sorted(dupes)[:5]}")
    errors += check_functions(flows)
    known = set(ids)
    for n in flows:
        for out in n.get("wires") or []:
            for target in out:
                if target not in known:
                    errors.append(f"node-red: {n['id']} ({n.get('name') or n['type']}) wires to missing node {target}")

if (ROOT / "homeassistant" / "automations").exists() or (ROOT / "homeassistant" / "scripts").exists():
    errors += check_automations()

if errors:
    print("\n".join(errors))
    sys.exit(1)
print("validate: OK")

#!/usr/bin/env python3
"""Keep Home Assistant automations and scripts readable (docs/automations.md#house-rules).

Checks every file in homeassistant/automations/ and homeassistant/scripts/:
  description  has a description saying why it exists
  device       uses entity_id / area_id, not device_id or device triggers
  syntax       uses current syntax (triggers/trigger:, actions/action:), not platform:/service:
  template     no Jinja block longer than MAX_TEMPLATE_LINES (make it a template helper)

Automations listed in tools/automation_baseline.json are skipped: the ones that existed
at your first sync (--baseline) and deliberate waivers (--allow, with a reason).

  python3 tools/automation_lint.py                       check (run by validate.py)
  python3 tools/automation_lint.py --baseline            grandfather everything that fails today
  python3 tools/automation_lint.py --allow <id> "<why>"  waive one automation/script, with a reason
  python3 tools/automation_lint.py --prune               list baseline entries that now pass
"""
from __future__ import annotations

import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _env import ensure_yaml  # noqa: E402

yaml = ensure_yaml()
ROOT = Path(__file__).resolve().parent.parent
HA = ROOT / "homeassistant"
BASELINE = ROOT / "tools" / "automation_baseline.json"
MAX_TEMPLATE_LINES = 10
SERVICE = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")


class Loader(yaml.SafeLoader):
    pass


Loader.add_multi_constructor("!", lambda loader, suffix, node: f"!{suffix}")

HINTS = {
    "description": "add a description saying why it exists",
    "device": "use entity_id / area_id targets and state or event-entity triggers (waive device-only remotes with --allow)",
    "syntax": "re-save it in the UI editor, or use triggers:/trigger: and actions:/action: (HA 2024.10+)",
    "template": f"move the Jinja into a template helper (max {MAX_TEMPLATE_LINES} lines inline)",
}


def _walk(obj, parent_key=None):
    """Yield (key_of_parent, value) for every nested value."""
    yield parent_key, obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk(v, k)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v, parent_key)


def problems(item: dict, kind: str) -> list[str]:
    out = []
    if not str(item.get("description") or "").strip():
        out.append("description")
    device = syntax = template = False
    if kind == "automation" and any(k in item for k in ("trigger", "condition", "action")):
        syntax = True
    for parent, v in _walk(item):
        if isinstance(v, dict):
            if "device_id" in v or v.get("trigger") == "device" or v.get("platform") == "device" or v.get("condition") == "device":
                device = True
            if parent in ("trigger", "triggers", "wait_for_trigger") and "platform" in v and "trigger" not in v:
                syntax = True
            if isinstance(v.get("service"), str) and SERVICE.match(v["service"]) and "action" not in v:
                syntax = True
        elif isinstance(v, str) and ("{{" in v or "{%" in v):
            if len([l for l in v.splitlines() if l.strip()]) > MAX_TEMPLATE_LINES:
                template = True
    out += [name for name, hit in (("device", device), ("syntax", syntax), ("template", template)) if hit]
    return out


def items():
    """(key, kind, name, config) for every exported automation and script."""
    for kind, folder in (("automation", "automations"), ("script", "scripts")):
        for p in sorted((HA / folder).glob("*.yaml")):
            cfg = yaml.load(p.read_text(), Loader=Loader) or {}
            key = str(cfg.get("id")) if kind == "automation" else f"script.{cfg.get('id') or p.stem}"
            yield key, kind, cfg.get("alias") or p.stem, cfg


def load_baseline() -> dict:
    if not BASELINE.exists():
        return {}
    data = json.loads(BASELINE.read_text())
    return data if isinstance(data, dict) else {k: "existing before the kit" for k in data}


def save_baseline(data: dict):
    BASELINE.write_text(json.dumps(dict(sorted(data.items())), indent=2, ensure_ascii=False) + "\n")


def check() -> list[str]:
    baseline = load_baseline()
    errors = []
    for key, kind, name, cfg in items():
        if key in baseline:
            continue
        for p in problems(cfg, kind):
            errors.append(f"{kind} '{name}' ({key}): {p} — {HINTS[p]}")
    return errors


def main():
    args = sys.argv[1:]
    if not (HA / "automations").exists() and not (HA / "scripts").exists():
        sys.exit("automation_lint: nothing exported yet — run a sync first")
    if args[:1] == ["--baseline"]:
        base = load_baseline()
        added = {k: "existing before the kit" for k, kind, _, cfg in items() if problems(cfg, kind) and k not in base}
        save_baseline({**base, **added})
        print(f"automation_lint: grandfathered {len(added)} automations/scripts in {BASELINE.relative_to(ROOT)}")
    elif args[:1] == ["--allow"]:
        if len(args) < 3:
            sys.exit('usage: automation_lint.py --allow <automation id | script.<id>> "<reason>"')
        known = {k for k, *_ in items()}
        if args[1] not in known:
            sys.exit(f"automation_lint: no exported automation or script '{args[1]}'")
        save_baseline({**load_baseline(), args[1]: " ".join(args[2:])})
        print(f"automation_lint: waived {args[1]}")
    elif args[:1] == ["--prune"]:
        byk = {k: (kind, cfg) for k, kind, _, cfg in items()}
        gone = [k for k in load_baseline() if k not in byk or not problems(byk[k][1], byk[k][0])]
        print("baseline entries that can be removed:", gone or "none")
    else:
        errs = check()
        print("\n".join(errs) or "automation_lint: OK")
        sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()

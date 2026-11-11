#!/usr/bin/env python3
"""Keep Node-RED function nodes small and readable (docs/node-red.md#native-nodes-first).

A function node fails the check when it is over MAX_LINES lines or reads Home Assistant
state directly (global.get('homeassistant')) — unless it says why in a `// why-js: <reason>`
comment, or it is grandfathered in tools/function_baseline.json.

  python3 tools/function_lint.py               check (run by validate.py)
  python3 tools/function_lint.py --baseline    grandfather every node that fails today
                                               (run once, right after your first sync)
  python3 tools/function_lint.py --prune       list baseline nodes that now pass (remove them)
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "tools" / "function_baseline.json"
MAX_LINES = 40
HA_STATE = re.compile(r"""global\.get\(\s*['"]homeassistant['"]""")


def problems(node):
    code = node.get("func") or ""
    if "// why-js:" in code:
        return []
    out = []
    lines = len([l for l in code.splitlines() if l.strip()])
    if lines > MAX_LINES:
        out.append(f"{lines} lines (max {MAX_LINES})")
    if HA_STATE.search(code):
        out.append("reads HA state directly (use a current-state / trigger node upstream)")
    return out


def check(flows):
    baseline = set(json.loads(BASELINE.read_text(encoding="utf-8"))) if BASELINE.exists() else set()
    tabs = {n["id"]: n.get("label") for n in flows if n.get("type") == "tab"}
    errors = []
    for n in flows:
        if n.get("type") != "function" or n["id"] in baseline:
            continue
        for p in problems(n):
            errors.append(f"node-red function '{n.get('name') or n['id']}' ({tabs.get(n.get('z'), n.get('z'))}): {p}"
                          " — split it into native nodes or add '// why-js: <reason>'")
    return errors


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "tools"))
    from nodered_build import build
    if not (ROOT / "node-red" / "index.json").exists():
        sys.exit("function_lint: no node-red/ export yet — nothing to check")
    flows = build()
    if "--baseline" in sys.argv:
        ids = sorted(n["id"] for n in flows if n.get("type") == "function" and problems(n))
        with open(BASELINE, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(ids, indent=2) + "\n")
        print(f"function_lint: grandfathered {len(ids)} existing function nodes in {BASELINE.relative_to(ROOT)}")
        sys.exit(0)
    if "--prune" in sys.argv:
        baseline = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else []
        byid = {n["id"]: n for n in flows}
        gone = [i for i in baseline if i not in byid or not problems(byid[i])]
        print("baseline entries that can be removed:", gone or "none")
        sys.exit(0)
    errs = check(flows)
    print("\n".join(errs) or "function_lint: OK")
    sys.exit(1 if errs else 0)

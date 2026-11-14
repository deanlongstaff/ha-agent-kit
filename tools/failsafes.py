#!/usr/bin/env python3
"""List the automations that act on their own: schedules, polls and "quiet for N min" timeouts.

Fail-safes (and other timed switch-offs) put things back to a safe state from the current
state, so they work after a restart or a missed event. They also run regardless of any
feature you add later, so they quietly undo new behaviour: a poll that switches off a light
*group* will switch off the mood, scene or boost you just built on one of its members. Run this
before adding or changing anything that leaves a device on (docs/conventions.md#fail-safes).

    python3 tools/failsafes.py                              # every timed path, HA and Node-RED
    python3 tools/failsafes.py light.hall light.ground_floor  # only paths that act on or check these
    python3 tools/failsafes.py --off light.hall             # only switch-off style actions

Name the entity AND every group or area it belongs to: a fail-safe that turns off
`light.ground_floor` (a group) or `area_id: hall` turns off `light.hall` too. Node-RED call nodes
with no fixed action are shown with the function that feeds them; read that function.

Reads the repo only (sync first if the live system may have changed). Read-only, no network.
"""
from __future__ import annotations

import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _env import ensure_yaml, utf8_console  # noqa: E402

yaml = ensure_yaml()
utf8_console()
ROOT = Path(__file__).resolve().parent.parent
HA = ROOT / "homeassistant"
OFFISH = re.compile(r"(turn_off|close|stop|lock|toggle|set_hvac_mode|set_value|select_option|^)$")
TARGET_KEYS = ("entity_id", "area_id", "floor_id", "label_id", "device_id")


class Loader(yaml.SafeLoader):
    pass


Loader.add_multi_constructor("!", lambda loader, suffix, node: f"!{suffix}")


def as_list(v) -> list:
    return v if isinstance(v, list) else [] if v is None else [v]


def dur(v) -> str:
    if isinstance(v, dict):
        return " ".join(f"{v[k]}{k[0]}" for k in ("hours", "minutes", "seconds") if v.get(k))
    return str(v)


# ── Home Assistant automations ────────────────────────────────────────────────

def timed_trigger(t: dict) -> str | None:
    kind = t.get("trigger") or t.get("platform")
    if kind == "time_pattern":
        return "every " + " ".join(f"{k}={t[k]}" for k in ("hours", "minutes", "seconds") if k in t)
    if kind == "time":
        return f"at {t.get('at')}"
    if kind == "sun":
        return f"at {t.get('event')}"
    if kind == "homeassistant":
        return f"on HA {t.get('event')}"
    if t.get("for") is not None:
        ents = ", ".join(map(str, as_list(t.get("entity_id")) + as_list((t.get("target") or {}).get("entity_id"))))
        to = t.get("to", t.get("below", t.get("above", "any")))
        return f"{ents or kind} = {to} for {dur(t['for'])}"
    return None


def walk_actions(steps, conds: list, out: list):
    """Collect (action, targets, conditions on the way) from a list of HA actions."""
    for s in as_list(steps):
        if not isinstance(s, dict):
            continue
        action = s.get("action") or s.get("service")
        if action:
            tg = []
            for src in (s.get("target") or {}, s.get("data") or {}, s):
                if isinstance(src, dict):
                    for k in TARGET_KEYS:
                        tg += [f"{k.replace('_id', '')}:{x}" if k != "entity_id" else str(x) for x in as_list(src.get(k))]
            out.append((str(action), tg, conds))
        for key in ("sequence", "then", "else", "default", "parallel"):
            if key in s:
                walk_actions(s[key], conds + cond_text(s.get("if")), out)
        for opt in as_list(s.get("choose")):
            if isinstance(opt, dict):
                walk_actions(opt.get("sequence"), conds + cond_text(opt.get("conditions")), out)
        if isinstance(s.get("repeat"), dict):
            walk_actions(s["repeat"].get("sequence"), conds, out)


def cond_text(conds) -> list:
    out = []
    for c in as_list(conds):
        if isinstance(c, dict):
            kind = c.get("condition", "?")
            ents = ", ".join(map(str, as_list(c.get("entity_id"))))
            val = c.get("state", c.get("above", c.get("below", c.get("after", c.get("value_template", "")))))
            out.append(f"{kind} {ents} {val}".strip() + (f" for {dur(c['for'])}" if c.get("for") else ""))
        elif isinstance(c, str):
            out.append(c)
    return out


def ha_rows() -> list:
    rows = []
    for f in sorted((HA / "automations").glob("*.yaml")) if (HA / "automations").is_dir() else []:
        try:
            a = yaml.load(f.read_text(encoding="utf-8"), Loader=Loader) or {}
        except yaml.YAMLError:
            continue
        starts = [k for k in (timed_trigger(t) for t in as_list(a.get("triggers", a.get("trigger"))) if isinstance(t, dict)) if k]
        if not starts:
            continue
        acts: list = []
        walk_actions(a.get("actions", a.get("action")), cond_text(a.get("conditions", a.get("condition"))), acts)
        for action, tg, conds in acts:
            rows.append(("Home Assistant", f"{a.get('alias') or f.stem} ({'; '.join(starts)})", f.name, conds, action, tg, ""))
    return rows


# ── Node-RED ──────────────────────────────────────────────────────────────────

def nr_start(n: dict) -> str | None:
    if n.get("type") == "inject" and (n.get("repeat") or n.get("crontab")):
        return f"every {n['repeat']} s" if n.get("repeat") else f"cron {n['crontab']}"
    if n.get("type") in ("server-state-changed", "trigger-state") and str(n.get("for") or "0") not in ("0", ""):
        ents = ", ".join((n.get("entities") or {}).get("entity") or []) or n.get("entity_id") or "?"
        return f"{ents} = {n.get('ifState') or 'any'} for {n['for']} {n.get('forUnits', '')}".strip()
    return None


def nr_check(n: dict) -> str:
    if n.get("type") == "api-current-state":
        f = f" for {n['for']} {n.get('forUnits', '')}" if str(n.get("for") or "0") not in ("0", "") else ""
        return f"{n.get('entity_id')} {n.get('halt_if_compare', 'is')} {n.get('halt_if')!r}{f}"
    return f"time {n.get('startTime')}-{n.get('endTime')}"


def nr_rows() -> list:
    if not (ROOT / "node-red" / "index.json").exists():
        return []
    from nodered_build import build
    flows = build()
    by = {n["id"]: n for n in flows}
    tabs = {n["id"]: n.get("label", "?") for n in flows if n.get("type") == "tab"}
    rows = []
    for s in flows:
        kind = nr_start(s)
        if not kind or s.get("d"):
            continue
        seen, stack = set(), [(s["id"], [], None)]
        while stack:
            nid, checks, feeder = stack.pop()
            if nid in seen or nid not in by or by[nid].get("d"):
                continue
            seen.add(nid)
            n = by[nid]
            if n.get("type") in ("api-current-state", "time-range-switch"):
                checks = checks + [nr_check(n)]
            if n.get("type") == "function":
                feeder = n
            if n.get("type") == "api-call-service":
                action = n.get("action") or (f"{n['domain']}.{n['service']}" if n.get("domain") and n.get("service") else "")
                tg = list(n.get("entityId") or []) + [f"area:{x}" for x in n.get("areaId") or []] + \
                    [f"floor:{x}" for x in n.get("floorId") or []] + [f"label:{x}" for x in n.get("labelId") or []]
                extra = str(n.get("data") or "") + ((feeder or {}).get("func", "") if not action else "")
                shown = action or f"payload-driven (fed by function: {(feeder or {}).get('name') or '?'})"
                rows.append((f"Node-RED · {tabs.get(s.get('z'), '?')}", f"{s.get('name') or s['type']} ({kind})", "",
                             checks, shown, tg, extra + " " + (n.get("name") or "")))
            for out in n.get("wires") or []:
                stack += [(w, checks, feeder) for w in out]
    return rows


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    only_off = "--off" in sys.argv
    rows = []
    for where, start, src, checks, action, tg, extra in ha_rows() + nr_rows():
        text = " ".join(tg + checks + [action, extra])
        if only_off and not OFFISH.search(action.split(".")[-1].split(" ")[0]):
            continue
        if args and not any(a in text for a in args):
            continue
        rows.append((where, start, src, checks, action, tg))
    if not rows:
        print("No timed paths act on or check that." if args else "No timed paths found.")
        return
    last = None
    for where, start, src, checks, action, tg in sorted(rows, key=lambda r: (r[0], r[1])):
        if where != last:
            print(f"\n## {where}")
            last = where
        print(f"- {start}{f'  [{src}]' if src else ''}\n    checks: {' → '.join(checks) or '(none)'}\n    does:   {action} {', '.join(tg)}")


if __name__ == "__main__":
    main()

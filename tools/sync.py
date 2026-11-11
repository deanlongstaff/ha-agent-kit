#!/usr/bin/env python3
"""Turn a bundle from tools/collect.js into the repo layout.

    python3 tools/sync.py <bundle>

<bundle> may be the raw 'B64START...B64END<n>' text (tools/collect-cli.mjs writes it
to .export/bundle.txt), a browser-tool result file that contains it, or an
already-decoded bundle JSON. The decoded bundle is kept
in .export/ (git-ignored) and never committed.

Managed folders are regenerated from scratch so deletions in Home Assistant or
Node-RED show up as deletions in git. Every write is redacted (tools/redact.py)
and dashboards / flows are round-trip checked before the script exits.
"""
from __future__ import annotations

import base64, csv, gzip, io, json, re, shutil, sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from nodered_build import build as build_flows  # noqa: E402
from redact import redact_addon_options, redact_emails, redact_yaml_text  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
HA, NR, REF = ROOT / "homeassistant", ROOT / "node-red", ROOT / "docs" / "reference"


# ── output helpers ──────────────────────────────────────────────────────────
class Dumper(yaml.SafeDumper):
    pass


def _str(d, s):
    return d.represent_scalar("tag:yaml.org,2002:str", s, style="|" if "\n" in s else None)


Dumper.add_representer(str, _str)


def dump_yaml(obj) -> str:
    return yaml.dump(obj, Dumper=Dumper, sort_keys=False, allow_unicode=True, width=4096, default_flow_style=False)


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def write_json(path: Path, obj):
    write(path, json.dumps(obj, indent=2, ensure_ascii=False))


def write_yaml(path: Path, obj, header: str | None = None):
    write(path, (f"# {header}\n" if header else "") + dump_yaml(obj))


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-") or "unnamed"


def reset(*dirs: Path):
    for d in dirs:
        if d.exists():
            shutil.rmtree(d)


# ── bundle loading ──────────────────────────────────────────────────────────
def load_bundle(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    if raw.lstrip().startswith("{"):
        return json.loads(raw)
    if raw.lstrip().startswith("["):  # browser tool result: [{type, text}, ...]
        raw = "".join(x.get("text", "") for x in json.loads(raw))
    m = re.search(r"B64START([A-Za-z0-9+/=]+)B64END(\d+)", raw)
    if not m:
        sys.exit("No B64START...B64END payload found")
    if len(m[1]) != int(m[2]):
        sys.exit(f"Payload truncated: got {len(m[1])} of {m[2]} characters")
    return json.loads(gzip.decompress(base64.b64decode(m[1])))


# ── Home Assistant ──────────────────────────────────────────────────────────
def sync_dashboards(b: dict) -> list[str]:
    d = HA / "dashboards"
    reset(d)
    index = []
    for url, item in sorted(b["dashboards"].items()):
        meta = {k: v for k, v in item["meta"].items() if k != "id"}
        index.append(meta)
        if item.get("config") is not None:
            write_yaml(d / f"{url}.yaml", item["config"],
                       f"Dashboard '{meta.get('title')}' (/{url}). Restore: dashboard › ⋮ › Edit › ⋮ › Raw configuration editor › paste.")
    write_yaml(d / "_index.yaml", index, "Dashboard registry (Settings › Dashboards)")
    if b.get("resources") is not None:
        write_yaml(d / "resources.yaml", [{"url": r["url"], "type": r["type"]} for r in b["resources"]],
                   "Lovelace resources (Settings › Dashboards › ⋮ › Resources)")
    return [u for u, i in b["dashboards"].items() if i.get("config") is not None]


def sync_themes(b: dict):
    t = b.get("themes") or {}
    reset(HA / "themes")
    for name, theme in (t.get("custom") or {}).items():
        write_yaml(HA / "themes" / f"{slug(name)}.yaml", {name: theme},
                   f"Snapshot of theme '{name}' as loaded by HA (themes/ folder, merged named)")
    return {"default": t.get("default"), "default_dark": t.get("default_dark"), "installed": sorted(t.get("installed") or [])}


def sync_helpers(b: dict):
    d = HA / "helpers"
    reset(d)
    for domain, items in (b.get("helpers") or {}).items():
        if items:
            write_yaml(d / f"{domain}.yaml", items, f"{domain} helpers (Settings › Devices & services › Helpers)")
    by = defaultdict(list)
    for e in b.get("entry_helpers") or []:
        by[e["domain"]].append({"title": e["title"], "entry_id": e["entry_id"], **(e.get("options") or {})})
    for domain, items in by.items():
        write_yaml(d / "config-entry" / f"{domain}.yaml", sorted(items, key=lambda x: x["title"]),
                   f"UI-created {domain} helpers (options as shown in the helper's settings)")


def sync_automations(b: dict) -> dict:
    """One file per automation / script / scene, from the API. Works on every install type."""
    counts = {}
    for kind, items in (("automations", b.get("automations") or []),
                        ("scripts", [{"id": k, **(v or {})} for k, v in (b.get("scripts") or {}).items() if v]),
                        ("scenes", b.get("scenes") or [])):
        d = HA / kind
        reset(d)
        used = set()
        for item in items:
            if not item:
                continue
            s = slug(item.get("alias") or item.get("name") or str(item.get("id")))
            if s in used:
                s = f"{s}-{slug(str(item.get('id')))[:8]}"
            used.add(s)
            text, _ = redact_yaml_text(dump_yaml(redact_emails(item)))
            write(d / f"{s}.yaml", text)
        counts[kind] = len(used)
    return counts


SECRET_REF = re.compile(r"!secret\s+([A-Za-z0-9_]+)")  # every reference, ours and ones already in the live file


def sync_files(b: dict) -> list[str]:
    files = b.get("files") or {}
    secrets: dict[str, list[str]] = defaultdict(list)
    have_config = any(k.startswith("config/") and v is not None for k, v in files.items())
    if have_config:
        reset(HA / "config", HA / "esphome")
    for key, text in sorted(files.items()):
        if text is None:
            continue
        if key.startswith("config/"):
            text, _ = redact_yaml_text(text)
            secrets["config"] += SECRET_REF.findall(text)
            write(HA / "config" / key[7:], text)
        elif key.startswith("esphome/"):
            text, _ = redact_yaml_text(text, prefix=Path(key).stem)
            secrets["esphome"] += SECRET_REF.findall(text)
            write(HA / "esphome" / key[8:], text)
        elif key.startswith("www/"):
            write(HA / "www" / key[4:], text)
    for scope, names in secrets.items():
        if names:
            folder = HA / ("config" if scope == "config" else "esphome")
            write_yaml(folder / "secrets.example.yaml", {n: "<redacted>" for n in sorted(set(names))},
                       "Keys referenced with !secret in this folder. Real values live only in secrets.yaml on the HA host.")
    return [k for k, v in files.items() if v is not None]


def sync_inventory(b: dict, themes: dict):
    d = HA / "inventory"
    reset(d)
    reg = b.get("registry") or {}
    areas = {a["area_id"]: a for a in reg.get("areas") or []}
    floors = {f["floor_id"]: f for f in reg.get("floors") or []}
    devices = {x["id"]: x for x in reg.get("devices") or []}

    write_yaml(d / "areas.yaml", {
        "floors": [{"id": f["floor_id"], "name": f["name"], "level": f.get("level"), "icon": f.get("icon")} for f in floors.values()],
        "areas": [{"id": a["area_id"], "name": a["name"], "floor": a.get("floor_id"), "icon": a.get("icon")} for a in areas.values()],
    }, "Floors and areas")
    if reg.get("labels"):
        write_yaml(d / "labels.yaml", [{"id": l["label_id"], "name": l["name"], "icon": l.get("icon"), "color": l.get("color")} for l in reg["labels"]])

    def area_name(e):
        a = e.get("area_id") or (devices.get(e.get("device_id")) or {}).get("area_id")
        return areas.get(a, {}).get("name", "")

    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["entity_id", "name", "area", "device", "platform", "status"])
    for e in sorted(reg.get("entities") or [], key=lambda x: x["entity_id"]):
        status = "disabled" if e.get("disabled_by") else "hidden" if e.get("hidden_by") else ""
        w.writerow([e["entity_id"], e.get("name") or e.get("original_name") or "", area_name(e),
                    (devices.get(e.get("device_id")) or {}).get("name") or "", e.get("platform"), status])
    write(d / "entities.csv", redact_emails(buf.getvalue()))

    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["name", "area", "manufacturer", "model", "status"])
    for x in sorted(devices.values(), key=lambda x: ((x.get("name") or "").lower())):
        if x.get("entry_type") == "service":
            continue
        w.writerow([x.get("name") or "", areas.get(x.get("area_id"), {}).get("name", ""), x.get("manufacturer") or "",
                    x.get("model") or "", "disabled" if x.get("disabled_by") else ""])
    write(d / "devices.csv", redact_emails(buf.getvalue()))

    write_yaml(d / "integrations.yaml", redact_emails(sorted(
        [{"domain": e["domain"], "title": e["title"], "state": e["state"], **({"disabled_by": e["disabled_by"]} if e.get("disabled_by") else {})}
         for e in b.get("integrations") or []], key=lambda x: (x["domain"], x["title"] or ""))), "Integrations (config entries)")
    write_yaml(d / "addons.yaml", sorted(b.get("addons") or [], key=lambda a: a["slug"]), "Installed add-ons (state at export time)")
    write_yaml(d / "themes.yaml", themes, "Themes known to the frontend")
    bp = {dom: sorted([{"path": p, "name": (v.get("metadata") or {}).get("name"), "source_url": (v.get("metadata") or {}).get("source_url")}
                       for p, v in (items or {}).items()], key=lambda x: x["path"]) for dom, items in (b.get("blueprints") or {}).items()}
    write_yaml(d / "blueprints.yaml", bp, "Blueprints installed (files live in /config/blueprints)")
    if b.get("energy"):
        write_yaml(HA / "energy.yaml", b["energy"], "Energy dashboard preferences (Settings › Dashboards › Energy)")


# ── Node-RED ────────────────────────────────────────────────────────────────
def sync_nodered(b: dict) -> dict | None:
    if not (b.get("nodered") or {}).get("flows"):
        return None  # no Node-RED (or it wasn't running): leave node-red/ as it is
    flows = b["nodered"]["flows"]
    reset(NR / "flows", NR / "subflows", NR / "functions")
    tabs = [n for n in flows if n["type"] == "tab"]
    subflows = [n for n in flows if n["type"] == "subflow"]
    owners = {n["id"] for n in tabs + subflows}
    config = [n for n in flows if n["type"] not in ("tab", "subflow") and n.get("z") not in owners]
    by_z = defaultdict(list)
    for n in flows:
        if n.get("z") in owners:
            by_z[n["z"]].append(n)

    used, index = set(), {"tabs": [], "subflows": [], "config_nodes": "config-nodes.json"}

    def fname(label, nid):
        s = slug(label)
        if s in used:
            s = f"{s}-{nid[:6]}"
        used.add(s)
        return s

    for t in tabs:
        s = fname(t.get("label"), t["id"])
        write_json(NR / "flows" / f"{s}.json", [t, *by_z[t["id"]]])
        index["tabs"].append({"id": t["id"], "label": t.get("label"), "file": f"flows/{s}.json", **({"disabled": True} if t.get("disabled") else {})})
    for sf in subflows:
        s = fname(sf.get("name"), sf["id"])
        write_json(NR / "subflows" / f"{s}.json", [sf, *by_z[sf["id"]]])
        index["subflows"].append({"id": sf["id"], "name": sf.get("name"), "file": f"subflows/{s}.json"})
    write_json(NR / "config-nodes.json", config)
    write_json(NR / "index.json", index)

    # Read-only mirrors of function code, for review and search
    for t in tabs + subflows:
        group = slug(t.get("label") or t.get("name"))
        seen = set()
        for n in by_z[t["id"]]:
            if n["type"] != "function":
                continue
            s = slug(n.get("name")) if n.get("name") else f"function-{n['id'][:8]}"
            if s in seen:
                s = f"{s}-{n['id'][:6]}"
            seen.add(s)
            parts = [f"// GENERATED by tools/sync.py — edit in Node-RED, not here.\n// Tab: {t.get('label') or t.get('name')} · Node: {n.get('name') or '(unnamed)'} · id {n['id']}"
                     + (" · DISABLED" if n.get("d") else "")]
            if (n.get("initialize") or "").strip():
                parts.append(f"// ── On Start ──\n{n['initialize']}")
            parts.append(("// ── On Message ──\n" if (n.get("initialize") or n.get("finalize") or "").strip() else "") + (n.get("func") or ""))
            if (n.get("finalize") or "").strip():
                parts.append(f"// ── On Stop ──\n{n['finalize']}")
            write(NR / "functions" / group / f"{s}.js", "\n\n".join(parts))

    if b.get("nodered_palette"):
        write_yaml(NR / "palette.yaml", sorted(b["nodered_palette"], key=lambda x: x["module"]),
                   "Installed Node-RED modules (Manage palette)")
    if b.get("nodered_addon"):
        write_yaml(NR / "addon.yaml", {"version": b["nodered_addon"]["version"], "options": redact_addon_options(b["nodered_addon"]["options"])},
                   "Node-RED add-on options (secrets redacted)")
    return {"tabs": tabs, "by_z": by_z, "files": {t["id"]: t["file"] for t in index["tabs"]}}


# ── generated reference docs ────────────────────────────────────────────────
GEN = "<!-- GENERATED by tools/sync.py — do not edit by hand. -->\n\n"


def md_escape(s) -> str:
    return str(s or "").replace("|", "\\|").replace("\n", " ")


def ref_dashboards(b: dict):
    out = [GEN, "# Dashboards (reference)\n\nWhat each dashboard contains, generated from `homeassistant/dashboards/`. "
           "For the why, see [../dashboards.md](../dashboards.md).\n"]
    for url, item in sorted(b["dashboards"].items(), key=lambda kv: (kv[0] != "lovelace", kv[0])):
        cfg, meta = item.get("config") or {}, item["meta"]
        out.append(f"\n## {meta.get('title')} — `/{url}`\n")
        out.append(f"Sidebar: {'yes' if meta.get('show_in_sidebar') else 'no'} · Admin only: {'yes' if meta.get('require_admin') else 'no'}"
                   + (f" · Kiosk mode: `{json.dumps(cfg['kiosk_mode'])}`" if cfg.get("kiosk_mode") else "")
                   + (" · Strategy dashboard" if cfg.get("strategy") else "") + "\n")
        for v in cfg.get("views", []):
            out.append(f"\n### View: {v.get('title') or '(untitled)'} (`{v.get('path') or '-'}`, {v.get('type') or 'masonry'})\n")
            popups, rows = [], []
            sections = v.get("sections") or [{"cards": v.get("cards", [])}]
            for i, s in enumerate(sections):
                names = []
                for c in s.get("cards", []):
                    if c.get("card_type") == "pop-up":
                        popups.append(c)
                    elif c.get("card_type") != "separator":
                        n = c.get("name") or c.get("title") or c.get("entity") or c.get("card_type") or c.get("type")
                        names.append("(template)" if "{" in str(n) else str(n))
                sep = next((c.get("name") for c in s.get("cards", []) if c.get("card_type") == "separator"), None)
                if names:
                    rows.append(f"| {i} | {md_escape(sep or '—')} | {md_escape(', '.join(names))} |")
            if rows:
                out += ["\n| Section | Heading | Cards |", "|---|---|---|", *rows]
            if popups:
                out += ["\n\n**Pop-ups**\n", "| Hash | Name | Header entity | Cards |", "|---|---|---|---|"]
                out += [f"| `{p.get('hash')}` | {md_escape(p.get('name'))} | `{p.get('entity') or '-'}` | {len(p.get('cards', []))} |" for p in popups]
            out.append("")
    write(REF / "dashboards.md", "\n".join(out))


def ref_nodered(nr: dict):
    rows = []
    for t in nr["tabs"]:
        nodes = nr["by_z"][t["id"]]
        c = Counter(n["type"] for n in nodes)
        disabled = sum(1 for n in nodes if n.get("d"))
        rows.append(f"| [{md_escape(t.get('label'))}](../../node-red/{nr['files'][t['id']]}) | {len(nodes)} | {c['function']} | "
                    f"{disabled or ''} | {'yes' if t.get('disabled') else ''} | {md_escape((t.get('info') or '').split(chr(10))[0][:120])} |")
    write(REF / "node-red.md", GEN + "# Node-RED tabs (reference)\n\nFor conventions and how each flow works, see [../node-red.md](../node-red.md).\n\n"
          "| Tab | Nodes | Functions | Disabled nodes | Tab disabled | Description |\n|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n")


def ref_automations(b: dict):
    rows = []
    for a in sorted([a for a in b.get("automations") or [] if a], key=lambda a: (a.get("alias") or "").lower()):
        trig = a.get("triggers", a.get("trigger")) or []
        trig = trig if isinstance(trig, list) else [trig]
        kinds = sorted({t.get("trigger", t.get("platform", "?")) for t in trig if isinstance(t, dict)})
        rows.append(f"| {md_escape(a.get('alias'))} | `{a.get('id')}` | {a.get('mode') or 'single'} | {md_escape(', '.join(kinds))} | "
                    f"{md_escape((a.get('description') or '')[:120])} |")
    scripts = sorted((b.get("scripts") or {}).items())
    missing = b.get("automations_without_id") or []
    out = [GEN + "# Automations and scripts (reference)\n\nOne YAML file each in `homeassistant/automations/`, `scripts/` and `scenes/`.\n",
           f"\n## Automations ({len(rows)})\n", "| Alias | ID | Mode | Triggers | Description |", "|---|---|---|---|---|", *rows,
           f"\n## Scripts ({len(scripts)})\n", "| Script | Alias | Mode | Description |", "|---|---|---|---|"]
    out += [f"| `script.{k}` | {md_escape((v or {}).get('alias'))} | {(v or {}).get('mode') or 'single'} | {md_escape(((v or {}).get('description') or '')[:120])} |"
            for k, v in scripts]
    if missing:
        out += [f"\n## Not exported ({len(missing)})\n",
                "These automations have no `id` (old YAML or packages), so the API can't read them. "
                "See [../automations.md](../automations.md#automations-that-cant-be-exported) for how to bring them in.\n",
                "| Entity | Name | State |", "|---|---|---|"]
        out += [f"| `{m['entity_id']}` | {md_escape(m.get('name'))} | {m.get('state')} |" for m in sorted(missing, key=lambda m: m["entity_id"])]
    write(REF / "automations.md", "\n".join(out) + "\n")


def ref_helpers(b: dict):
    out = [GEN, "# Helpers (reference)\n"]
    for domain, items in (b.get("helpers") or {}).items():
        if items:
            out += [f"\n## {domain}\n", "| Entity | Name | Icon |", "|---|---|---|"]
            out += [f"| `{domain}.{i['id']}` | {md_escape(i.get('name'))} | {i.get('icon') or ''} |" for i in sorted(items, key=lambda x: x["id"])]
    by = defaultdict(list)
    for e in b.get("entry_helpers") or []:
        by[e["domain"]].append(e)
    for domain, items in sorted(by.items()):
        out += [f"\n## {domain} (UI helper)\n", "| Title | Step | Key settings |", "|---|---|---|"]
        for e in sorted(items, key=lambda x: x["title"]):
            f = (e.get("options") or {}).get("fields") or {}
            key = f.get("entities") or f.get("entity_id") or f.get("state") or f.get("value_template") or f.get("template_type") or ""
            out.append(f"| {md_escape(e['title'])} | {(e.get('options') or {}).get('step') or ''} | {md_escape(json.dumps(key, ensure_ascii=False)[:160])} |")
    write(REF / "helpers.md", "\n".join(out) + "\n")


def ref_areas(b: dict):
    reg = b.get("registry") or {}
    devices = {x["id"]: x for x in reg.get("devices") or []}
    count = Counter()
    for e in reg.get("entities") or []:
        if not e.get("disabled_by"):
            count[e.get("area_id") or (devices.get(e.get("device_id")) or {}).get("area_id")] += 1
    floors = {f["floor_id"]: f["name"] for f in reg.get("floors") or []}
    rows = [f"| {md_escape(a['name'])} | `{a['area_id']}` | {floors.get(a.get('floor_id'), '')} | {count[a['area_id']]} |"
            for a in sorted(reg.get("areas") or [], key=lambda a: (floors.get(a.get("floor_id"), "~"), a["name"]))]
    write(REF / "areas.md", GEN + "# Areas (reference)\n\nFull entity list: [`homeassistant/inventory/entities.csv`](../../homeassistant/inventory/entities.csv).\n\n"
          "| Area | ID | Floor | Enabled entities |\n|---|---|---|---|\n" + "\n".join(rows) + f"\n\nEntities with no area: {count[None]}\n")


# ── checks ──────────────────────────────────────────────────────────────────
def roundtrip(b: dict, dashboards: list[str]):
    for url in dashboards:
        text = (HA / "dashboards" / f"{url}.yaml").read_text()
        assert yaml.safe_load(text) == b["dashboards"][url]["config"], f"dashboard {url} does not round-trip"
    if (b.get("nodered") or {}).get("flows"):
        a = {n["id"]: n for n in build_flows()}
        o = {n["id"]: n for n in b["nodered"]["flows"]}
        assert a == o, "Node-RED flows do not round-trip"


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    b = load_bundle(Path(sys.argv[1]))
    (ROOT / ".export").mkdir(exist_ok=True)
    (ROOT / ".export" / "bundle.json").write_text(json.dumps(b), encoding="utf-8")

    dashboards = sync_dashboards(b)
    themes = sync_themes(b)
    sync_helpers(b)
    files = sync_files(b)
    sync_inventory(b, themes)
    autos = sync_automations(b)
    nr = sync_nodered(b)
    for f in ("dashboards.md", "helpers.md", "areas.md", "automations.md"):
        (REF / f).unlink(missing_ok=True)
    ref_dashboards(b); ref_helpers(b); ref_areas(b); ref_automations(b)
    if nr:
        ref_nodered(nr)
    roundtrip(b, dashboards)

    meta = b.get("meta", {})
    write_yaml(ROOT / "homeassistant" / "export-info.yaml", {"ha_version": meta.get("ha_version"), "exported_at": meta.get("exported_at")},
               "When the files in this repo were last exported from the live system")
    print(f"HA {meta.get('ha_version')} exported {meta.get('exported_at')}")
    nodes = len(b["nodered"]["flows"]) if nr else 0
    print(f"dashboards={len(dashboards)} automations={autos['automations']} scripts={autos['scripts']} scenes={autos['scenes']} "
          f"node-red nodes={nodes} files={len(files)}")
    for e in meta.get("errors") or []:
        print(f"warning: {e}")
    if not any(f.startswith("config/") for f in files):
        print("note: config files not collected (Studio Code Server not running) — homeassistant/config/ and esphome/ left unchanged")
    if not nr:
        print("note: no Node-RED flows in this bundle — node-red/ left unchanged")


if __name__ == "__main__":
    main()

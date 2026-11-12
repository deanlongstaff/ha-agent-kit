#!/usr/bin/env python3
"""End-to-end smoke test of the kit's tools on this OS (CI runs it on Windows, macOS, Linux).

    python3 tests/smoke.py

Copies the kit to a temp folder, syncs a made-up export (with non-ASCII text and planted
secrets), then runs the linters, validation, the secret scan, the doctor and connect.py's
input checks. Uses no network and touches nothing outside the temp folder.
"""
from __future__ import annotations

import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KIT / "tools"))
from _env import utf8_console, venv_python  # noqa: E402

utf8_console()
PY = str(venv_python() or sys.executable)  # the Python that has PyYAML (setup.py made sure)
SKIP = {".git", ".venv", ".agents", ".export", "homeassistant", "node-red", "__pycache__"}
AT = "@"
failures: list[str] = []


def run(*args, stdin: str | None = None, cwd: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        return subprocess.run([PY, *args], cwd=cwd, input=stdin if stdin is not None else "", capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=env, timeout=180)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(args, 124, "", f"TIMED OUT: {' '.join(args)}")


def check(name: str, cond: bool, detail: str = ""):
    print(f"  {'✅' if cond else '❌'} {name}" + (f"\n{detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def txt(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def bundle() -> dict:
    flows = [
        {"id": "t1", "type": "tab", "label": "Lights — café"},
        {"id": "n1", "type": "inject", "z": "t1", "name": "Every morning", "wires": [["n2"]]},
        {"id": "n2", "type": "function", "z": "t1", "name": "Pick scene", "func": "msg.payload = 'ok';\nreturn msg;", "wires": [["n3"]]},
        {"id": "n3", "type": "debug", "z": "t1", "name": "", "wires": []},
        {"id": "s1", "type": "server", "name": "Home Assistant"},
    ]
    return {
        "schema": 1,
        "meta": {"ha_version": "2026.11.0", "exported_at": "2026-11-11T00:00:00Z", "errors": []},
        "dashboards": {"lovelace": {"meta": {"url_path": "lovelace", "title": "Home"},
                                    "config": {"views": [{"title": "Home 🏠", "type": "sections", "sections": [
                                        {"type": "grid", "cards": [{"type": "heading", "heading": "Café"},
                                                                   {"type": "tile", "entity": "light.cafe"}]}]}]}}},
        "resources": [],
        "themes": {"default": "default", "default_dark": None, "installed": [], "custom": {}},
        "helpers": {"input_boolean": [{"id": "guest_mode", "name": "Guest mode", "icon": "mdi:account"}]},
        "registry": {"areas": [{"area_id": "cafe", "name": "Café", "floor_id": None}], "floors": [], "labels": [],
                     "devices": [{"id": "d1", "name": "Kitchen lamp", "area_id": "cafe", "manufacturer": "Acme", "model": "L1"}],
                     "entities": [{"entity_id": "light.cafe", "name": "Café light", "platform": "hue", "device_id": "d1"},
                                  {"entity_id": "person.robin", "name": "Robin Example", "platform": "person"},
                                  {"entity_id": "zone.home", "name": "Maple Cottage", "platform": "zone"}]},
        "integrations": [{"entry_id": "e1", "domain": "hue", "title": "someone" + AT + "gmail.com", "state": "loaded"}],
        "custom_integrations": [{"domain": "powercalc", "name": "Powercalc", "version": "1.0.0"}],
        "installed_versions": [{"entity_id": "update.node_red", "title": "Node-RED", "version": "19.0.0"}],
        "entry_helpers": [],
        "automations": [
            {"id": "1", "alias": "Café lights at sunset", "description": "Warm light when it gets dark ☀️",
             "triggers": [{"trigger": "sun", "event": "sunset"}], "actions": [{"action": "light.turn_on", "target": {"area_id": "cafe"}}]},
            {"id": "3", "alias": "Notify Robin", "description": "Tell Robin the washing is done",
             "triggers": [{"trigger": "state", "entity_id": "sensor.washer", "to": "done"}],
             "actions": [{"action": "notify.notify", "data": {"message": "Done"}}]},
            {"id": "2", "alias": "Old style", "description": "", "trigger": [{"platform": "state", "entity_id": "light.cafe"}],
             "action": [{"service": "light.turn_off", "target": {"device_id": "d1"}}]},
        ],
        "automations_without_id": [{"entity_id": "automation.legacy", "name": "Legacy", "state": "on"}],
        "scripts": {"good_night": {"alias": "Good night", "description": "Everything off", "sequence": [{"action": "light.turn_off", "target": {"area_id": "cafe"}}]}},
        "scenes": [],
        "privacy_names": {"home": "Maple Cottage", "people": ["Robin Example", "Alex"], "zones": ["Home", "Office"]},
        "blueprints": {"automation": {}, "script": {}},
        "addons": [{"slug": "a0d7b954_nodered", "name": "Node-RED", "version": "19.0.0", "state": "started"}],
        "nodered": {"flows": flows},
        "nodered_palette": [{"module": "node-red", "version": "4.1.0"}],
        "files": {"config/configuration.yaml": "default_config:\nhttp:\n  api_key: " + "abcdef" + "123456\n"},
    }


def main():
    tmp = Path(tempfile.mkdtemp(prefix="ha-kit-smoke-"))
    repo = tmp / "kit"
    try:
        shutil.copytree(KIT, repo, ignore=lambda d, names: [n for n in names if n in SKIP])
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
        (repo / ".export").mkdir()
        (repo / ".export" / "bundle.json").write_text(json.dumps(bundle(), ensure_ascii=False), encoding="utf-8")
        print(f"\nSmoke test on {sys.platform} with {PY}\n")

        r = run("tools/sync.py", ".export/bundle.json", cwd=repo)
        check("sync.py runs", r.returncode == 0, r.stdout + r.stderr)
        auto = repo / "homeassistant" / "automations" / "cafe-lights-at-sunset.yaml"
        check("automation exported with non-ASCII intact", "Café" in txt(auto))
        check("files written with LF line endings", auto.exists() and b"\r\n" not in auto.read_bytes())
        cfg = repo / "homeassistant" / "config" / "configuration.yaml"
        check("secret in config redacted to !secret", "!secret" in txt(cfg))
        integ = txt(repo / "homeassistant" / "inventory" / "integrations.yaml")
        check("e-mail redacted from inventory", integ != "" and "gmail.com" not in integ)
        check("versions.yaml written", (repo / "homeassistant" / "inventory" / "versions.yaml").exists())
        check("Node-RED tab exported", (repo / "node-red" / "flows").is_dir() and any((repo / "node-red" / "flows").glob("*.json")))
        ref = txt(repo / "docs" / "reference" / "automations.md")
        check("id-less automation listed as not exported", "automation.legacy" in ref)

        r = run("tools/automation_lint.py", cwd=repo)
        check("automation lint catches the old-style automation", r.returncode == 1 and "Old style" in r.stdout, r.stdout)
        check("automation lint --baseline", run("tools/automation_lint.py", "--baseline", cwd=repo).returncode == 0)
        check("function lint --baseline", run("tools/function_lint.py", "--baseline", cwd=repo).returncode == 0)

        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        r = run("tools/validate.py", cwd=repo)
        check("validate.py passes", r.returncode == 0, r.stdout + r.stderr)
        r = run("tools/check_secrets.py", cwd=repo)
        check("secret scan passes on the redacted export", r.returncode == 0, r.stdout + r.stderr)

        leak = repo / "leak.txt"
        leak.write_text("token: " + "ghp_" + "a" * 36 + "\n", encoding="utf-8")
        subprocess.run(["git", "add", "leak.txt"], cwd=repo, check=True)
        r = run("tools/check_secrets.py", "--staged", cwd=repo)
        check("secret scan blocks a planted token", r.returncode == 1 and "GitHub token" in r.stdout, r.stdout)
        subprocess.run(["git", "rm", "-q", "--cached", "leak.txt"], cwd=repo, check=True)
        leak.unlink()

        # privacy levels: personal data warns at relaxed, blocks at standard; secrets always block
        note = repo / "note.md"
        note.write_text("Ask Sam at sam.jones" + AT + "gmail.com or " + "+44 7700 " + "900123\n", encoding="utf-8")
        subprocess.run(["git", "add", "note.md"], cwd=repo, check=True)
        privacy = repo / "privacy.yaml"
        for level, want in (("relaxed", 0), ("standard", 1)):
            privacy.write_text(f"level: {level}\n", encoding="utf-8")
            r = run("tools/check_secrets.py", "--staged", cwd=repo)
            check(f"privacy {level}: e-mail and phone {'warn' if want == 0 else 'block'}", r.returncode == want and "e-mail address" in r.stdout, r.stdout)
        privacy.write_text("level: relaxed\n", encoding="utf-8")
        leak.write_text("token: " + "ghp_" + "b" * 36 + "\n", encoding="utf-8")
        subprocess.run(["git", "add", "leak.txt"], cwd=repo, check=True)
        check("privacy relaxed: secrets still block", run("tools/check_secrets.py", "--staged", cwd=repo).returncode == 1)
        subprocess.run(["git", "rm", "-q", "--cached", "leak.txt", "note.md"], cwd=repo, check=True)
        leak.unlink(); note.unlink()

        # strict: sync learns people/zone/home names, hides them in inventory, blocks them elsewhere
        privacy.write_text("level: strict\n", encoding="utf-8")
        r = run("tools/sync.py", ".export/bundle.json", cwd=repo)
        check("privacy strict: sync runs", r.returncode == 0 and "privacy strict" in r.stdout, r.stdout + r.stderr)
        ents = txt(repo / "homeassistant" / "inventory" / "entities.csv")
        check("privacy strict: names hidden in inventory", "(hidden)" in ents and "Robin" not in ents and "Maple Cottage" not in ents, ents[:400])
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        r = run("tools/check_secrets.py", cwd=repo)
        check("privacy strict: a person's name in an automation is blocked", r.returncode == 1 and "privacy: strict" in r.stdout
              and "notify-robin" in r.stdout, r.stdout)
        privacy.write_text("level: standard\n", encoding="utf-8")
        r = run("tools/check_secrets.py", cwd=repo)
        check("privacy standard: the same export passes", r.returncode == 0, r.stdout)

        r = run("tools/doctor.py", cwd=repo)
        check("doctor runs and prints its report", r.returncode in (0, 1) and "doctor" in r.stdout, r.stdout + r.stderr)

        r = run("tools/connect.py", stdin="y\nhttps://example.com/not-mcp\nn\n", cwd=repo)
        check("connect.py rejects a bad URL and changes nothing", r.returncode == 0 and "Nothing changed" in r.stdout, r.stdout + r.stderr)
        check(".env not created by a cancelled connect", not (repo / ".env").exists())

        node = shutil.which("node")
        if node:
            r = subprocess.run([node, "--check", str(repo / "tools" / "collect-cli.mjs")], capture_output=True, text=True)
            check("collect-cli.mjs parses", r.returncode == 0, r.stderr)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{'All passed.' if not failures else f'{len(failures)} failed: ' + ', '.join(failures)}\n")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

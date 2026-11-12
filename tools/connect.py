#!/usr/bin/env python3
"""Connect your AI agent to Home Assistant WITHOUT secrets passing through the chat.

Run it yourself, in your own terminal (not through the agent):

    python3 tools/connect.py        (Windows: py tools/connect.py, in PowerShell or Windows Terminal)

1. ha-mcp: asks for the connect URL with hidden input, offers read-only mode, checks it
   answers, and adds it at USER scope to the agents you pick: Claude Code, Codex, Gemini CLI
   (others: it tells you where to paste it).
2. Optional — exports from the terminal: if your agent has no browser tool, stores your local
   HA address and a long-lived token in the git-ignored .env for tools/collect-cli.mjs.

Then restart your agent in this folder and say "continue onboarding".
"""
from __future__ import annotations

import getpass, json, os, re, shutil, subprocess, sys, urllib.error, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _env import ROOT, utf8_console  # noqa: E402

utf8_console()
NAME = os.environ.get("MCP_NAME", "home-assistant")

# How each agent CLI adds / lists / removes a user-scope streamable-HTTP MCP server
AGENTS = {
    "claude": {"label": "Claude Code", "add": ["claude", "mcp", "add", "--transport", "http", "--scope", "user", NAME, "{url}"],
               "has": ["claude", "mcp", "get", NAME], "remove": ["claude", "mcp", "remove", "--scope", "user", NAME]},
    "codex": {"label": "Codex", "add": ["codex", "mcp", "add", NAME, "--url", "{url}"],
              "has": ["codex", "mcp", "get", NAME], "remove": ["codex", "mcp", "remove", NAME]},
    "gemini": {"label": "Gemini CLI", "add": ["gemini", "mcp", "add", "--transport", "http", "--scope", "user", NAME, "{url}"],
               "has": None, "list": ["gemini", "mcp", "list"], "remove": ["gemini", "mcp", "remove", "--scope", "user", NAME]},
}
OTHERS = """  • Cursor: Settings › MCP › Add new global MCP server (type: streamable HTTP)
  • VS Code / GitHub Copilot: Command Palette › "MCP: Add Server…" › HTTP › Global
  • Anything else: add a streamable-HTTP MCP server in its *user/global* settings
  Never in a file inside this repo."""


def ask(prompt: str, default: str = "") -> str:
    try:
        return input(prompt).strip() or default
    except EOFError:
        return default


def yes(prompt: str, default: bool) -> bool:
    a = ask(f"{prompt} [{'Y/n' if default else 'y/N'}] ").lower()
    return default if not a else a.startswith("y")


def secret(prompt: str) -> str:
    """Hidden input in a terminal. getpass reads the Windows console directly, so piped input
    (scripts, tests) would hang it: read those normally."""
    if sys.stdin.isatty():
        return getpass.getpass(prompt)
    print(prompt, end="", flush=True)
    return sys.stdin.readline().strip()


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    exe = shutil.which(cmd[0]) or cmd[0]  # resolves .cmd/.exe shims on Windows
    return subprocess.run([exe, *cmd[1:]], capture_output=True, text=True, encoding="utf-8", errors="replace")


def probe(url: str) -> str:
    """POST an MCP initialize request. Nothing is changed in Home Assistant."""
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "ha-agent-kit-check", "version": "1"}}}).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return str(r.status)
    except urllib.error.HTTPError as e:
        return str(e.code)
    except Exception as e:  # noqa: BLE001
        return type(e).__name__


def connect_mcp():
    print("""
Connect Home Assistant (ha-mcp)
───────────────────────────────
Copy the connect URL from Home Assistant:
  Settings › Devices & services › HA-MCP › Configure
It looks like  http://<ha-ip>:9584/private_…   (treat it like a password)
""")
    url = re.sub(r"\s+", "", secret("Paste the URL (input hidden), then press Enter: ")).rstrip("/")
    if not re.match(r"^https?://[^/]+/.*private_[^/]+", url):
        print("That doesn't look like an ha-mcp connect URL (…/private_<secret>). Nothing changed.")
        return False
    mode = "read-only" if url.endswith("/readonly") else "full access"
    if mode == "full access" and yes("Start in read-only mode? Recommended for your first sessions.", True):
        url, mode = url + "/readonly", "read-only"

    status = probe(url)
    if status != "200":
        print(f"Couldn't get a good answer from that URL ({status}).")
        print("Check: same network as Home Assistant? HA-MCP's 'Local network' access turned on?")
        if not yes("Add it anyway?", False):
            print("Nothing changed.")
            return False

    found = [k for k, a in AGENTS.items() if shutil.which(a["add"][0])]
    if found:
        print("\nAgents found on this computer: " + ", ".join(f"{i + 1}) {AGENTS[k]['label']}" for i, k in enumerate(found)))
        pick = ask("Connect which? Numbers separated by commas, Enter for all: ")
        chosen = [found[int(n) - 1] for n in re.findall(r"\d+", pick) if 0 < int(n) <= len(found)] or found
    else:
        chosen = []
        print("\nNo Claude Code, Codex or Gemini CLI found on your PATH.")

    done = []
    for k in chosen:
        a = AGENTS[k]
        exists = run(a["has"]).returncode == 0 if a.get("has") else NAME in run(a["list"]).stdout
        if exists:
            if not yes(f"{a['label']} already has an MCP server called '{NAME}'. Replace it?", False):
                print(f"  {a['label']}: left as it was.")
                continue
            run(a["remove"])
        r = run([url if part == "{url}" else part for part in a["add"]])
        if r.returncode == 0:
            done.append(a["label"])
            print(f"  ✅ {a['label']}: connected ({mode}, user scope)")
        else:
            print(f"  ❌ {a['label']}: adding failed — {(r.stderr or r.stdout).strip()[-200:]}")
    del url
    print("\nUsing another agent too? Add the same URL in its own settings:\n" + OTHERS)
    if done:
        print(f"\nRestart {' / '.join(done)} in this folder and say:  continue onboarding")
        if mode == "read-only":
            print("(Later, run this again and choose full access to let the agent make changes.)")
    return True


def store_token():
    print("""
Exports from the terminal (optional)
────────────────────────────────────
Needed only if your agent can't open a browser (Codex, Gemini CLI, Claude Code in a plain
terminal…). Saves your local HA address and a long-lived token in .env, which git ignores.
Create the token in Home Assistant: your profile › Security › Long-lived access tokens.
Tip: sign in as your dedicated ha-mcp user first, so revoking it never touches your login.
""")
    if not yes("Set this up now?", False):
        return
    env = ROOT / ".env"
    current = env.read_text(encoding="utf-8") if env.exists() else ""
    ha_url = ask("Local Home Assistant address [http://homeassistant.local:8123]: ", "http://homeassistant.local:8123").rstrip("/")
    token = secret("Paste the token (input hidden): ").strip()
    if not token:
        print("No token given. Nothing changed.")
        return
    lines = [l for l in current.splitlines() if not l.startswith(("HA_URL=", "HA_TOKEN="))]
    lines += [f"HA_URL={ha_url}", f"HA_TOKEN={token}"]
    with open(env, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    if os.name != "nt":
        env.chmod(0o600)
    del token
    print("  ✅ saved to .env (git-ignored). Test it with:  node tools/collect-cli.mjs")


if __name__ == "__main__":
    print("\nHA Agent Kit — connect")
    if yes("\nConnect your agent to ha-mcp now?", True):
        connect_mcp()
    store_token()
    print()

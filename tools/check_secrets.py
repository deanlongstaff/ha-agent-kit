#!/usr/bin/env python3
"""Fail if anything secret-shaped is about to be committed.

    python3 tools/check_secrets.py            # scan all tracked + staged files
    python3 tools/check_secrets.py --staged   # scan only staged changes (pre-commit hook)

Also checks every literal in `.secrets-denylist` (one per line, case-insensitive,
git-ignored, kept only on machines that work on this repo) — use it for things that
don't *look* secret but identify you: your surname, street, town, postcode, Wi-Fi
name, alarm code. False positives go in `.secrets-allowlist` as `path:regex` lines.
"""
from __future__ import annotations

import re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# vendored third-party skills: full of example placeholders (our own skills are still scanned)
SKIP_DIRS = (".claude/skills/home-assistant-best-practices/", ".claude/skills/node-red/", ".claude/skills/ha-bubble-dashboard/")
SKIP_FILES = {"tools/check_secrets.py", "tools/redact.py", ".secrets-denylist.example"}

RULES: list[tuple[str, re.Pattern]] = [
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("JWT / HA long-lived token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("GitHub token", re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{40,}")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("AWS key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("Telegram bot token", re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b")),
    ("Amazon OAuth secret", re.compile(r"amzn1\.oa2-cs\.[A-Za-z0-9.]+")),
    ("OpenAI / Anthropic key", re.compile(r"\bsk-(ant-)?[A-Za-z0-9_-]{20,}")),
    ("ha-mcp secret URL", re.compile(r"/private_[A-Za-z0-9_-]{12,}")),
    ("HA webhook URL", re.compile(r"/api/webhook/[A-Za-z0-9_-]{16,}")),
    ("URL with credentials", re.compile(r"\b[a-z][a-z0-9+.-]*://[^/\s:@'\"]+:[^/\s@'\"]+@")),
    ("ESPHome API key", re.compile(r"""\bkey:\s*["']?[A-Za-z0-9+/]{43}=""")),
    ("inline secret value", re.compile(
        r"""(?i)\b(password|passwd|client_secret|api_?key|access_token|auth_token|secret)\b["']?\s*[:=]\s*["']?(?!\s*(!secret|<redacted>|__PWRD__|\$env|env\.|\{\{|\$\{|\(|msg\.|flow\.|global\.|""|''|true|false|null|none|""))[^\s"',}{]{6,}""")),
    ("property UPRN", re.compile(r"(?i)\buprn\b\s*[:=]\s*\d{6,}")),
    ("e-mail address", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9.-]*[a-z]{2,}")),
    ("phone number (international)", re.compile(r"(?<![\w.+])\+[1-9]\d{0,2}[ -]?\(?\d{2,4}\)?[ -]?\d{3,4}[ -]?\d{3,4}(?![\w.])")),
    ("phone number (UK mobile)", re.compile(r"(?<![\w.])07\d{3}\s?\d{3}\s?\d{3}(?![\w.])")),
    ("phone number (US)", re.compile(r"(?<![\w.])\(?[2-9]\d{2}\)?[ .-]\d{3}[ .-]\d{4}(?![\w.])")),
    ("precise coordinates", re.compile(r"""(?i)["']?(latitude|longitude|lat|lon|lng)["']?\s*[:=]\s*-?\d{1,3}\.\d{4,}""")),
]
ALLOWED_EMAIL = re.compile(r"noreply@anthropic\.com|@users\.noreply\.github\.com|@example\.(com|org|net)")


def files(staged: bool) -> list[str]:
    if staged:
        out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"], cwd=ROOT, capture_output=True, text=True).stdout
    else:
        out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT, capture_output=True, text=True).stdout
    return [f for f in out.splitlines() if f and f not in SKIP_FILES and not f.startswith(SKIP_DIRS)]


def read_list(name: str) -> list[str]:
    p = ROOT / name
    return [l.strip() for l in p.read_text().splitlines() if l.strip() and not l.startswith("#")] if p.exists() else []


def main() -> int:
    staged = "--staged" in sys.argv
    deny = read_list(".secrets-denylist")
    allow = [(a.split(":", 1)[0], re.compile(a.split(":", 1)[1])) for a in read_list(".secrets-allowlist") if ":" in a]
    problems = []
    for f in files(staged):
        p = ROOT / f
        if not p.is_file():
            continue
        if staged:
            text = subprocess.run(["git", "show", f":{f}"], cwd=ROOT, capture_output=True, text=True, errors="replace").stdout
        else:
            text = p.read_text(errors="replace")
        for n, line in enumerate(text.splitlines(), 1):
            hits = [name for name, rx in RULES if rx.search(line) and not (name == "e-mail address" and ALLOWED_EMAIL.search(line))]
            hits += ["denylisted value" for d in deny if re.search(rf"(?<![\w]){re.escape(d)}(?![\w])", line, re.I)]
            hits = [h for h in hits if not any(f.startswith(path) and rx.search(line) for path, rx in allow)]
            for h in hits:
                problems.append(f"{f}:{n}: {h}")
    if problems:
        print("Possible secrets / personal data found — fix, redact (tools/redact.py) or allowlist:\n")
        print("\n".join(sorted(set(problems))))
        return 1
    print(f"check_secrets: OK ({'staged' if staged else 'all'} files, {len(deny)} denylist entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

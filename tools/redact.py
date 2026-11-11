"""Redaction rules applied by tools/sync.py before anything is written to the repo.

Anything secret-shaped becomes a `!secret <name>` reference (YAML) or `<redacted>`
(everything else), so the repo stays restorable without holding the values.
"""
import re

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# YAML keys whose literal values are always secret
SECRET_KEYS = {
    "client_secret", "client_id", "password", "api_key", "apikey", "token", "access_token",
    "secret", "uprn", "latitude", "longitude", "webhook_id", "ssid", "username", "refresh_token",
    "private_key", "api_password", "auth_key", "bearer_token",
}
SAFE_VALUE = re.compile(r"""^(!secret|!include|!env_var|!input|["']?\{\{|["']?\{%|""|''|~|null|true|false)""", re.I)
LINE = re.compile(r"^(?P<indent>\s*)(?P<dash>-\s+)?(?P<key>[A-Za-z_][\w-]*):(?P<sep>\s*)(?P<val>.*?)\s*$")


def _is_secret(key: str, val: str, parents: list[str]) -> bool:
    if not val or SAFE_VALUE.match(val):
        return False
    if key in SECRET_KEYS:
        return True
    if key == "key" and parents and parents[-1] == "encryption":
        return True
    if key in ("code", "pin") and re.fullmatch(r"""["']?\d{4,8}["']?""", val):
        return True
    return False


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def redact_yaml_text(text: str, prefix: str = "") -> tuple[str, list[str]]:
    """Replace literal secret values with `!secret <name>`. Returns (text, secret names)."""
    lines, stack, names = text.split("\n"), [], []
    for i, line in enumerate(lines):
        if line.lstrip().startswith("#"):
            continue
        m = LINE.match(line)
        if not m:
            continue
        indent = len(m["indent"]) + len(m["dash"] or "")
        key, val = m["key"], m["val"]
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parents = [k for _, k in stack]
        if val == "":
            stack.append((indent, key))
            continue
        if _is_secret(key, val, parents):
            name = _slug("_".join([p for p in [prefix, *parents, key] if p]))
            lines[i] = f"{line[:m.start('val')]}!secret {name}"
            names.append(name)
    return "\n".join(lines), names


def redact_emails(obj):
    """Recursively replace e-mail addresses in strings."""
    if isinstance(obj, str):
        return EMAIL.sub("<email>", obj)
    if isinstance(obj, list):
        return [redact_emails(v) for v in obj]
    if isinstance(obj, dict):
        return {k: redact_emails(v) for k, v in obj.items()}
    return obj


def redact_addon_options(obj):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k == "env_vars":
                out[k] = [{"name": x.get("name"), "value": "<redacted>"} for x in (v or [])]
            elif re.search(r"secret|password|token|apikey|api_key", k, re.I) and v not in ("", None):
                out[k] = "<redacted>"
            else:
                out[k] = redact_addon_options(v)
        return out
    if isinstance(obj, list):
        return [redact_addon_options(v) for v in obj]
    return obj

#!/usr/bin/env bash
# Connect Claude Code to ha-mcp WITHOUT the secret URL ever passing through the chat.
#
# Run this yourself, in your own terminal (not through the agent):
#   bash tools/connect-mcp.sh
#
# It asks for the HA-MCP connect URL with hidden input, offers read-only mode, checks it
# answers, and adds it to Claude Code at USER scope (your user config, never this repo).
# Then restart Claude Code in this folder and say "continue onboarding".
set -uo pipefail
NAME="${MCP_NAME:-home-assistant}"

command -v claude >/dev/null 2>&1 || {
  echo "Claude Code's CLI ('claude') isn't on your PATH. Install it: https://claude.com/claude-code"
  echo "Using another agent? Add the URL as a streamable-HTTP MCP server in its *user* settings instead."
  exit 1
}

cat <<'TXT'

Connect Home Assistant to Claude Code
─────────────────────────────────────
Copy the connect URL from Home Assistant:
  Settings › Devices & services › HA-MCP › Configure
It looks like  http://<ha-ip>:9584/private_…   (treat it like a password)

TXT
printf 'Paste the URL (input hidden), then press Enter: '
read -rs URL; echo
URL="$(printf '%s' "$URL" | tr -d '[:space:]')"; URL="${URL%/}"

case "$URL" in
  http://*/private_*|https://*/private_*) ;;
  *) echo "That doesn't look like an ha-mcp connect URL (…/private_<secret>). Nothing changed."; exit 1 ;;
esac

mode="full access"
case "$URL" in
  */readonly) mode="read-only" ;;
  *) printf 'Start in read-only mode? Recommended for your first sessions. [Y/n] '
     read -r ro
     case "${ro:-y}" in [Nn]*) ;; *) URL="$URL/readonly"; mode="read-only" ;; esac ;;
esac

# Does it answer? (an MCP initialize request; nothing is changed in Home Assistant)
code="$(curl -s -o /dev/null -w '%{http_code}' -m 10 -X POST "$URL" \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  --data '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"ha-agent-kit-check","version":"1"}}}' 2>/dev/null)"
[ -n "$code" ] || code=000
if [ "$code" != "200" ]; then
  echo "Couldn't get a good answer from that URL (HTTP $code)."
  echo "Check: same network as Home Assistant? HA-MCP's 'Local network' access turned on?"
  printf 'Add it anyway? [y/N] '; read -r anyway
  case "${anyway:-n}" in [Yy]*) ;; *) echo "Nothing changed."; exit 1 ;; esac
fi

if claude mcp get "$NAME" >/dev/null 2>&1; then
  printf "Claude Code already has an MCP server called '%s'. Replace it? [y/N] " "$NAME"
  read -r replace
  case "${replace:-n}" in [Yy]*) claude mcp remove --scope user "$NAME" >/dev/null 2>&1 || true ;; *) echo "Nothing changed."; exit 1 ;; esac
fi

claude mcp add --transport http --scope user "$NAME" "$URL" >/dev/null || { echo "claude mcp add failed. Nothing else changed."; exit 1; }
unset URL

cat <<TXT

✅ Home Assistant connected to Claude Code ($mode), at user scope.

Next: restart Claude Code in this folder and say:  continue onboarding
TXT
[ "$mode" = "read-only" ] && echo "(Later, run this again without read-only to let the agent make changes.)"
exit 0

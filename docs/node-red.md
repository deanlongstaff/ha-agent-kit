# Node-RED

Only relevant if Node-RED is installed (the `a0d7b954_nodered` add-on with
`node-red-contrib-home-assistant-websocket`). If it isn't, `tools/sync.py` leaves
`node-red/` alone and none of this applies.

## Files in this repo

- `node-red/flows/<tab>.json` — the tab plus all of its nodes, in Node-RED's export format.
  Import one file via ☰ › Import to restore one tab.
- `node-red/subflows/<name>.json` — subflow definitions.
- `node-red/config-nodes.json` — the HA server node and other global config nodes.
- `node-red/index.json` — tab order; `tools/nodered_build.py` rebuilds the full flows.
- `node-red/functions/` — generated copies of function code. Read and grep them; edit in Node-RED.
- `docs/reference/node-red.md` — generated tab list with node counts.

## Native nodes first

A flow should read on the canvas: what starts it, what it checks, what it does. Build from
native nodes and keep JavaScript small, so a person can maintain it by eye.

| Job | Use |
|---|---|
| Start on a state change | `trigger-state` / `server-state-changed` (with conditions and `for`) |
| Start on a time | `inject` (cron), `time-range-switch`, `sun-position` |
| Check another entity | `api-current-state` (one per entity, so it shows on the canvas) |
| Decide / route | `switch` (one output per case, labelled) |
| Set or reshape `msg` | `change` (with JSONata for small expressions) |
| Debounce, rate-limit, "one at a time" | `delay` in rate-limit mode |
| Timeout, "off after N min", restartable timer | `trigger` (extend) or `delay` |
| Loop over a list | `split` → … → `join` |
| Notification text | `template` node, or mustache in the action data |
| A rule several flows share (season, evening) | an **HA helper** the flows trigger on |
| "Already done today" that must survive a restart | an HA helper (`input_datetime`, `input_text`) |

**When a function node is right:** one job that would take 3+ native nodes or a fragile
JSONata expression — maths, picking from a table, parsing an API reply. Then:

- ~30 lines or less, one job, named for what it does (*Pick scene*, not *Function 3*).
- No whole automations: triggers, entity checks, routing and actions stay as nodes.
- Read entities through `api-current-state` / trigger nodes upstream, not
  `global.get('homeassistant')`, so every dependency is visible.
- Set a short `node.status()` summary — it's how flows are debugged at a glance.
- If it must break these rules, say why in a first-line comment `// why-js: <reason>`.

`tools/function_lint.py` (run by `validate.py`, so the pre-commit hook) fails on a *new*
function over 40 lines or reading HA state directly unless it has that comment. Functions
that existed at your first sync are grandfathered in `tools/function_baseline.json`
(`python3 tools/function_lint.py --baseline` writes it). Shrink that list, never grow it.

## Conventions

- **Secrets** go in **tab environment variables of type credential** (encrypted in
  `flows_cred.json`, never exported), read as `$env("NAME")` in JSONata or
  `env.get("NAME")` in a function. The owner types the value in the editor.
- **Notify targets** are service names, not secrets: keep them in one place (e.g. a
  global set by an *On start* inject) so a new phone means one edit.
- **Context is memory-only.** Global/flow context and `delay`/`trigger` timers vanish on
  restart or full deploy. Anything that must end needs a fail-safe that re-checks state.
- **Comments.** Split each tab into labelled areas with comment nodes; give tabs with
  non-obvious behaviour a description.

## Deploying from an agent

1. Ingress session: `supervisor/api` `POST /ingress/session` → set cookie
   `ingress_session=<session>; path=/api/hassio_ingress/`.
2. `GET <ingress_url>flows` with header `Node-RED-API-Version: v2` → `{rev, flows}`.
3. Save a copy, change only your nodes (new node ids: 16 hex characters).
4. `POST <ingress_url>flows` with `{rev, flows}` and headers
   `Node-RED-API-Version: v2`, `Node-RED-Deployment-Type: nodes`.
5. Check node status / debug output, then sync the repo.

```js
const hass = document.querySelector('home-assistant').hass;
const sup = (endpoint, method = 'get') => hass.callWS({ type: 'supervisor/api', endpoint, method });
const nr = await sup('/addons/a0d7b954_nodered/info');
const { session } = await sup('/ingress/session', 'post');
document.cookie = `ingress_session=${session};path=/api/hassio_ingress/;SameSite=Strict`;
const { rev, flows } = await (await fetch(`${nr.ingress_url}flows`, { headers: { 'Node-RED-API-Version': 'v2' } })).json();
// …change only your nodes in `flows`…
await fetch(`${nr.ingress_url}flows`, { method: 'POST', body: JSON.stringify({ rev, flows }),
  headers: { 'Content-Type': 'application/json', 'Node-RED-API-Version': 'v2', 'Node-RED-Deployment-Type': 'nodes' } });
```

Do this on the **local** HA URL.

## Tabs at a glance

_Fill in as the flows grow: one line per tab saying what it does._

| Tab | What it does |
|---|---|
| | |

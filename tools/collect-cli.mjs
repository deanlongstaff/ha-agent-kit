#!/usr/bin/env node
// Run tools/collect.js from a terminal instead of a browser tab.
//
//   node tools/collect-cli.mjs                 # writes .export/bundle.txt
//   python3 tools/sync.py .export/bundle.txt
//
// Needs Node 22+ and two settings, read from the environment or a git-ignored .env file:
//   HA_URL    e.g. http://homeassistant.local:8123   (use your LOCAL address)
//   HA_TOKEN  a long-lived access token (Profile › Security). Admin is needed for add-ons,
//             Node-RED and config files; everything else works with any user.
//
// Tip: keep the token out of files entirely with a password-manager CLI, e.g.
//   HA_TOKEN="$(op read 'op://Private/Home Assistant/token')" node tools/collect-cli.mjs
//
// This builds a tiny stand-in for the browser's `hass` object (WebSocket + REST with your
// token) and runs the exact same collector, so both paths export the same data.
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const dotenv = existsSync(join(ROOT, '.env'))
  ? Object.fromEntries(readFileSync(join(ROOT, '.env'), 'utf8').split('\n')
    .map((l) => l.match(/^\s*([A-Z_][A-Z0-9_]*)\s*=\s*"?(.*?)"?\s*$/)).filter(Boolean).map((m) => [m[1], m[2]]))
  : {};
const cfg = { ...dotenv, ...process.env };
const BASE = (cfg.HA_URL || '').replace(/\/+$/, '');
const TOKEN = cfg.HA_TOKEN || '';
if (!BASE || !TOKEN) {
  console.error('Set HA_URL and HA_TOKEN (environment or .env — see .env.example).');
  process.exit(2);
}
if (typeof WebSocket === 'undefined' || typeof CompressionStream === 'undefined') {
  console.error(`Node ${process.version} is too old: use Node 22 or newer.`);
  process.exit(2);
}

// ── WebSocket API ───────────────────────────────────────────────────────────
const sock = new WebSocket(`${BASE.replace(/^http/, 'ws')}/api/websocket`);
const pending = new Map();
let nextId = 1;
await new Promise((resolve, reject) => {
  sock.addEventListener('error', () => reject(new Error(`Cannot connect to ${BASE}`)));
  sock.addEventListener('message', (ev) => {
    const m = JSON.parse(ev.data);
    if (m.type === 'auth_required') sock.send(JSON.stringify({ type: 'auth', access_token: TOKEN }));
    else if (m.type === 'auth_ok') resolve();
    else if (m.type === 'auth_invalid') reject(new Error('Home Assistant rejected the token'));
    else if (m.type === 'result' && pending.has(m.id)) {
      const { ok, fail } = pending.get(m.id);
      pending.delete(m.id);
      m.success ? ok(m.result) : fail(m.error);
    }
  });
});
const callWS = (msg) => new Promise((ok, fail) => {
  const id = nextId++;
  pending.set(id, { ok, fail });
  sock.send(JSON.stringify({ ...msg, id }));
});

// ── REST API + cookie-aware fetch for ingress ───────────────────────────────
const realFetch = globalThis.fetch;
let cookie = '';
const callApi = async (method, path, body) => {
  const r = await realFetch(`${BASE}/api/${path}`, {
    method, headers: { Authorization: `Bearer ${TOKEN}`, 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${method} ${path}: HTTP ${r.status}`);
  const text = await r.text();
  return text ? JSON.parse(text) : null;
};
globalThis.fetch = (url, opts = {}) => realFetch(String(url).startsWith('http') ? url : `${BASE}${url}`,
  { ...opts, headers: { ...(opts.headers || {}), ...(cookie ? { Cookie: cookie } : {}) } });

// ── the `hass` stand-in ─────────────────────────────────────────────────────
const [config, stateList, themes] = await Promise.all([
  callWS({ type: 'get_config' }), callWS({ type: 'get_states' }), callWS({ type: 'frontend/get_themes' }),
]);
const hass = {
  callWS, callApi, config,
  states: Object.fromEntries(stateList.map((s) => [s.entity_id, s])),
  themes: { theme: themes.default_theme, default_dark_theme: themes.default_dark_theme, themes: themes.themes },
};
globalThis.document = {
  querySelector: () => ({ hass }),
  set cookie(v) { cookie = String(v).split(';')[0]; },
  get cookie() { return cookie; },
};
globalThis.location = new URL(BASE);

// ── run the shared collector ────────────────────────────────────────────────
try {
  const result = await (0, eval)(readFileSync(join(ROOT, 'tools', 'collect.js'), 'utf8'));
  mkdirSync(join(ROOT, '.export'), { recursive: true });
  const file = join(ROOT, '.export', 'bundle.txt');
  writeFileSync(file, result);
  console.log(`Collected from Home Assistant ${config.version}: ${(result.length / 1024).toFixed(0)} KiB → .export/bundle.txt`);
  console.log('Next: python3 tools/sync.py .export/bundle.txt');
} finally {
  sock.close();
}

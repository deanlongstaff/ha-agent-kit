// Home Assistant (+ optional Node-RED) read-only collector.
//
// Two ways to run it:
//   • Browser (no token needed): paste into the devtools console of a logged-in Home
//     Assistant tab, or have your agent run it with its browser tool. Prefix with `await`.
//   • Terminal: `node tools/collect-cli.mjs` (uses HA_URL + HA_TOKEN from .env).
//
// It only READS: dashboards, helpers, registries, automations, scripts, scenes,
// Node-RED flows (Node-RED never returns credential values) and an allowlist of
// config files. It never reads secrets.yaml or .storage/.
//
// Everything that needs the Supervisor (add-ons, Node-RED, config files) is optional:
// on HA Container / Core installs those parts are skipped with a warning.
//
// Config files (configuration.yaml, ESPHome) are read through the Studio Code Server
// add-on when it is running. It is optional: automations, scripts and scenes are
// always collected through the API anyway.
//
// Output: 'B64START<gzip+base64 JSON>B64END<length>'. Save it to a file and run:
//   python3 tools/sync.py <that file>
(async () => {
  // ── settings (edit freely) ────────────────────────────────────────────────
  const CONFIG_FILES = ['configuration.yaml', 'automations.yaml', 'scripts.yaml', 'scenes.yaml'];
  const CUSTOM_THEMES = [];   // names of themes you wrote yourself, to snapshot (Marketplace themes are skipped)
  const NODERED = 'a0d7b954_nodered', VSCODE = 'a0d7b954_vscode', ESPHOME = '5c53de3b_esphome';
  const ENTRY_HELPER_DOMAINS = ['template', 'history_stats', 'utility_meter', 'derivative', 'threshold', 'min_max', 'group',
    'statistics', 'integration', 'trend', 'filter', 'tod', 'switch_as_x', 'mold_indicator', 'generic_thermostat',
    'generic_hygrostat', 'random', 'compensation'];
  const INPUT_HELPERS = ['input_boolean', 'input_number', 'input_select', 'input_text', 'input_datetime', 'input_button',
    'timer', 'counter', 'schedule'];

  const hass = document.querySelector('home-assistant').hass;
  const ws = (m) => hass.callWS(m);
  const api = (method, path, body) => hass.callApi(method, path, body);
  const sup = (endpoint, method = 'get') => ws({ type: 'supervisor/api', endpoint, method });
  const errors = [];
  const safe = async (label, fn) => { try { return await fn(); } catch (e) { errors.push(`${label}: ${e?.message || e?.error || JSON.stringify(e)}`); return null; } };
  const out = { schema: 1, meta: { ha_version: hass.config.version, exported_at: new Date().toISOString(), errors } };

  // ── dashboards ────────────────────────────────────────────────────────────
  out.dashboards = {};
  for (const d of await ws({ type: 'lovelace/dashboards/list' })) {
    out.dashboards[d.url_path] = { meta: d, config: await safe(`dashboard ${d.url_path}`, () => ws({ type: 'lovelace/config', url_path: d.url_path === 'lovelace' ? null : d.url_path })) };
  }
  if (!out.dashboards.lovelace) out.dashboards.lovelace = { meta: { url_path: 'lovelace', title: 'Overview', mode: 'storage' },
    config: await safe('dashboard default (auto-generated dashboards have no config; that is fine)', () => ws({ type: 'lovelace/config', url_path: null })) };
  out.resources = await safe('resources', () => ws({ type: 'lovelace/resources' }));
  out.themes = { default: hass.themes.theme, default_dark: hass.themes.default_dark_theme, installed: Object.keys(hass.themes.themes || {}),
    custom: Object.fromEntries(CUSTOM_THEMES.filter((t) => hass.themes.themes?.[t]).map((t) => [t, hass.themes.themes[t]])) };

  // ── helpers ───────────────────────────────────────────────────────────────
  out.helpers = {};
  for (const d of INPUT_HELPERS) out.helpers[d] = await safe(`helper ${d}`, () => ws({ type: `${d}/list` }));

  // ── registries (trimmed to what's useful for humans and agents) ───────────
  out.registry = {
    areas: await safe('areas', () => ws({ type: 'config/area_registry/list' })),
    floors: await safe('floors', () => ws({ type: 'config/floor_registry/list' })),
    labels: await safe('labels', () => ws({ type: 'config/label_registry/list' })),
    devices: (await safe('devices', () => ws({ type: 'config/device_registry/list' })))?.map((d) => ({ id: d.id, name: d.name_by_user || d.name,
      area_id: d.area_id, manufacturer: d.manufacturer, model: d.model, disabled_by: d.disabled_by, entry_type: d.entry_type, labels: d.labels })),
    entities: (await safe('entities', () => ws({ type: 'config/entity_registry/list' })))?.map((e) => ({ entity_id: e.entity_id, name: e.name,
      original_name: e.original_name, platform: e.platform, device_id: e.device_id, area_id: e.area_id, disabled_by: e.disabled_by,
      hidden_by: e.hidden_by, labels: e.labels, icon: e.icon })),
  };
  out.integrations = (await safe('config entries', () => ws({ type: 'config_entries/get' })))?.map((e) => ({ entry_id: e.entry_id,
    domain: e.domain, title: e.title, source: e.source, state: e.state, disabled_by: e.disabled_by }));

  // UI helpers stored as config entries: read options through an options flow that is aborted (nothing is saved)
  out.entry_helpers = [];
  for (const e of (out.integrations || []).filter((e) => ENTRY_HELPER_DOMAINS.includes(e.domain))) {
    const options = await safe(`options ${e.domain} ${e.title}`, async () => {
      const f = await api('POST', 'config/config_entries/options/flow', { handler: e.entry_id, show_advanced_options: true });
      const fields = {};
      for (const s of f.data_schema || []) fields[s.name] = s.description?.suggested_value ?? s.default ?? null;
      if (f.flow_id) await api('DELETE', `config/config_entries/options/flow/${f.flow_id}`).catch(() => {});
      return { step: f.step_id, fields };
    });
    out.entry_helpers.push({ domain: e.domain, title: e.title, entry_id: e.entry_id, options });
  }

  // ── automations / scripts / scenes (API copy; works on every install type) ─
  const states = Object.values(hass.states);
  out.automations = [];
  for (const s of states.filter((s) => s.entity_id.startsWith('automation.') && s.attributes.id))
    out.automations.push(await safe(`automation ${s.entity_id}`, () => api('GET', `config/automation/config/${s.attributes.id}`)));
  out.scripts = {};
  for (const s of states.filter((s) => s.entity_id.startsWith('script.')))
    out.scripts[s.entity_id.slice(7)] = await safe(`script ${s.entity_id}`, () => api('GET', `config/script/config/${s.entity_id.slice(7)}`));
  out.scenes = [];
  for (const s of states.filter((s) => s.entity_id.startsWith('scene.') && s.attributes.id))
    out.scenes.push(await safe(`scene ${s.entity_id}`, () => api('GET', `config/scene/config/${s.attributes.id}`)));
  out.blueprints = { automation: await safe('blueprints automation', () => ws({ type: 'blueprint/list', domain: 'automation' })),
    script: await safe('blueprints script', () => ws({ type: 'blueprint/list', domain: 'script' })) };
  out.energy = await safe('energy', () => ws({ type: 'energy/get_prefs' }));

  // ── Supervisor parts (HA OS / Supervised only) ────────────────────────────
  const addons = await sup('/addons').catch(() => null);
  if (!addons) {
    errors.push('No Supervisor (HA Container/Core?): add-ons, Node-RED and config files skipped');
  } else {
    out.addons = (addons.addons || addons).map((a) => ({ slug: a.slug, name: a.name, version: a.version, state: a.state, repository: a.repository }));
    const installed = new Set(out.addons.map((a) => a.slug));
    const ingress = async (slug) => {
      const info = await sup(`/addons/${slug}/info`);
      const sess = await sup('/ingress/session', 'post');
      document.cookie = `ingress_session=${sess.session};path=/api/hassio_ingress/;SameSite=Strict${location.protocol === 'https:' ? ';Secure' : ''}`;
      return info;
    };

    // Node-RED flows (GET /flows never includes credential values)
    if (installed.has(NODERED)) await safe('node-red', async () => {
      const nr = await ingress(NODERED);
      const redact = (o) => Object.fromEntries(Object.entries(o || {}).map(([k, v]) => [k,
        k === 'env_vars' ? (v || []).map((x) => ({ name: x.name, value: '<redacted>' }))
          : /secret|password|token|apikey|api_key|credential/i.test(k) ? '<redacted>'
            : (v && typeof v === 'object' && !Array.isArray(v)) ? redact(v) : v]));
      out.nodered_addon = { version: nr.version, options: redact(nr.options) };
      if (nr.state !== 'started') throw new Error('Node-RED add-on is not running: flows skipped');
      const r = await fetch(`${nr.ingress_url}flows`, { headers: { 'Node-RED-API-Version': 'v2' } });
      if (!r.ok) throw new Error(`GET flows: HTTP ${r.status}`);
      out.nodered = { flows: (await r.json()).flows };
      out.nodered_palette = await safe('node-red palette', async () => {
        const nodes = await (await fetch(`${nr.ingress_url}nodes`, { headers: { Accept: 'application/json' } })).json();
        return [...new Map(nodes.map((n) => [n.module, { module: n.module, version: n.version }])).values()];
      });
    });

    // Config files via Studio Code Server (only if it is already running)
    out.files = {};
    const vsc = installed.has(VSCODE) ? await safe('studio code server', () => ingress(VSCODE)) : null;
    if (vsc?.state === 'started') {
      const read = async (p) => { const r = await fetch(`${vsc.ingress_url}vscode-remote-resource?path=${encodeURIComponent(p)}`); return r.ok ? r.text() : null; };
      for (const f of CONFIG_FILES) out.files[`config/${f}`] = await read(`/config/${f}`);
      if (installed.has(ESPHOME)) {
        const esp = await safe('esphome', async () => {
          const info = await ingress(ESPHOME);
          return (await (await fetch(`${info.ingress_url}devices`)).json()).configured.map((d) => d.configuration);
        });
        for (const f of esp || []) if (f !== 'secrets.yaml') out.files[`esphome/${f}`] = await read(`/config/esphome/${f}`);
      }
    } else errors.push('Studio Code Server not running: config files skipped (automations/scripts/scenes still collected via the API)');
  }

  // Your own JS resources in /config/www (third-party cards live in /local/community/ and are skipped)
  out.files = out.files || {};
  for (const r of out.resources || []) {
    const m = r.url.match(/^\/local\/(?!community\/)([^?]+\.js)/);
    if (m) out.files[`www/${m[1]}`] = await safe(`www ${m[1]}`, async () => (await fetch(`/local/${m[1]}`)).text());
  }

  // ── encode for transfer ───────────────────────────────────────────────────
  const gz = await new Response(new Blob([JSON.stringify(out)]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer();
  let bin = ''; const u = new Uint8Array(gz);
  for (let i = 0; i < u.length; i += 0x8000) bin += String.fromCharCode(...u.subarray(i, i + 0x8000));
  const b64 = btoa(bin);
  return `B64START${b64}B64END${b64.length}`;
})();

# Backup and restore

## Two layers — keep both

| | Home Assistant backups | This repo |
|---|---|---|
| What | Everything: config, `.storage`, add-ons (incl. Node-RED and its credentials), database | Dashboards, automations, helpers, flows, docs — **no secrets, no history database** |
| When | On a schedule (Settings › System › Backups) | On every change, by your agent |
| Restore | Whole system or a whole add-on | Any single dashboard, automation, tab, file or helper |
| Use for | Disaster recovery | Undoing one change, seeing what changed and why |

Check that automatic backups include add-ons, are encrypted, and go somewhere **off the
box** (a NAS, cloud storage, Nabu Casa). Store the backup encryption key in your password
manager — without it a backup can't be restored. The repo is not a replacement.

## Restore a dashboard

1. Open the dashboard › ✏️ Edit › ⋮ › **Raw configuration editor**.
2. Replace the contents with `homeassistant/dashboards/<url_path>.yaml` from the commit
   you want: `git show <commit>:homeassistant/dashboards/<url_path>.yaml`.
3. Save. Missing dashboard? Create it first (Settings › Dashboards) using
   `dashboards/_index.yaml` for its URL, title and icon.

## Restore an automation, script or scene

Open the item (or create a new one) › ⋮ › **Edit in YAML**, paste the file from
`homeassistant/automations/`, `scripts/` or `scenes/`, save. Values shown as
`!secret <name>` must be re-entered by hand.

## Restore Node-RED

- **One tab:** ☰ › Import › select `node-red/flows/<tab>.json` › Import, choose *Replace*
  for existing nodes, Deploy.
- **Everything:** `python3 tools/nodered_build.py > flows.json` and import that file the
  same way (or restore the Node-RED add-on from an HA backup).
- On a fresh Node-RED: install modules from `node-red/palette.yaml`, reconnect the HA
  server node and re-enter every credential env var.

## Restore config files

`homeassistant/config/*.yaml` and `homeassistant/esphome/*.yaml` are copies of `/config`.
Every `!secret <name>` must exist in the host's `secrets.yaml` (names are listed in each
folder's `secrets.example.yaml`). Copy the file back with Studio Code Server or Samba,
then **Developer tools › Check configuration** before restarting.

## Restore helpers

- `helpers/input_*.yaml`: recreate in Settings › Devices & services › Helpers with the
  same ID, name, icon and options.
- `helpers/config-entry/<type>.yaml`: recreate the helper (group, template, threshold…)
  with the listed options.

## Roll back one change

```bash
git log --oneline -- homeassistant/automations/
git show <commit>^:homeassistant/automations/hallway-motion-lights.yaml
```

Restore it as above, then sync again — the rollback becomes its own commit. Or just ask
your agent: *"undo the change you made to the hallway lights yesterday"*.

# Things to ask your agent

Copy, paste, adapt. Every change ends in a commit, so be bold — and ask for one change at
a time so each is easy to review and undo.

## Getting to know your own house

- *"Give me a tour of my setup: rooms, the busiest integrations, and the automations that run most."*
- *"Which automations would break if `sensor.hallway_motion` disappeared?"*
- *"What changed in the last week, and why?"* (reads the git log and changelog)
- *"Draw my Node-RED Alarm tab as a flowchart."*

## Building

- *"When the washing machine finishes, tell whoever is home. Remind again after 30 minutes if the door hasn't opened."*
- *"Hallway lights on with motion after sunset, 20% after 11pm, off after 2 minutes of no motion."*
- *"Create a vacation mode that randomises lights in the evening and arms the alarm."*
- *"Add a 'someone home' group and use it everywhere we check for people being home."*
- *"Turn these three near-identical automations into one blueprint."*

## Dashboards

- *"Build a phone-first dashboard: anything that needs attention at the top, then one section per area."*
- *"Redesign my Living room section to follow the design rules. Show me before and after screenshots."*
- *"Give my dashboard a dark theme with one accent colour, and record it in the style guide."*
- *"Make a simple wall-tablet dashboard: big buttons, no scrolling, guarded locks."*
- *"Add a card to the Home dashboard showing which windows are open. Change nothing else."*
- *"Screenshot the Home dashboard at phone width and tell me what looks cramped."*

## Fixing and debugging

- *"The porch light didn't turn on last night. Check the traces and tell me why."*
- *"Find automations that use device_id and convert them to entity_id."*
- *"Which integrations have entities that haven't updated in 24 hours?"*
- *"My logs are noisy — what's spamming them, and is any of it a real problem?"*

## Updates

- *"Is it safe to install the pending updates? Check every changelog for breaking changes that affect my setup."*
- *"I just updated. What changed, and did anything break?"*
- *"Which custom integrations haven't been updated in a year?"*

## Housekeeping

- *"Audit my setup and write findings to docs/known-issues.md. Don't change anything."*
- *"List helpers nothing uses."* (then decide yourself what to delete)
- *"Rename my bedroom entities to our naming convention and update every consumer."*
- *"Sync and commit — I changed some things by hand."*

## Security

- *"List everything exposed to Assist that can open, unlock, disarm or power something off."*
- *"Check my backup settings: are they encrypted, off-site, and recent?"*
- *"Scan the repo history for anything that looks personal or secret."*

# Workflow: Cron, Heal, Heartbeat

## Goal

Keep scheduled automation consistent, eligible, and repairable from policy.

## Load Order

1. Load health policy.
2. Load `../policies/channel-blacklist.md` and `../policies/cadence.md`.
3. Load `../contracts/cli.md` for job IDs and command contracts.
4. Render concise status via `templates/status-report.md`.

## Rules

1. `sync-cron`: maintain one managed daily-brief job per eligible pillar.
2. `heal`: report or repair schedule integrity based on `--check`.
3. `sync-heartbeat`: write single global heartbeat checklist.
4. `due-scan`: aggregate due reminders, staged messages, and loop prompts.

## Required Output Keys

1. `status`
2. `workflow`
3. `issues` and `fixes` for heal
4. `heartbeat_file` for sync-heartbeat
5. `due_actions` for due-scan

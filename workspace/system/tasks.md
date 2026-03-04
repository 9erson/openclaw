# System-Wide Quiet Hours Tasks

AI picks from this list during quiet hours (one per tick, round-robin).

## Tasks

| Task | Description |
|------|-------------|
| Health Check | Scan all channels, create missing folder structures |
| Ops.log Prune | Handled by cron script (`scripts/prune-ops-log.sh`) |
| Pattern Detection | Cross-domain analysis, identify emerging themes |
| Brief Prep | Prepare 05:00 briefs (second half of quiet hours) |
| Memory Maintenance | Review recent daily logs, update MEMORY.md |

## Health Check Details

For each channel, ensure:
- `discord/<channel>/purpose.md` exists
- `discord/<channel>/activity.log` exists
- `discord/<channel>/agent/manual.md` exists
- `discord/<channel>/sources/` directory exists
- `discord/<channel>/user/` directory exists

Create missing items. Log creation in ops.log.

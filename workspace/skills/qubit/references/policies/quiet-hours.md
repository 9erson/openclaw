# Policy: Quiet Hours

## Scope

Apply to loop prompts and non-urgent reminders surfaced by due scans.

## Rules

1. Honor per-pillar `quiet_hours_start` and `quiet_hours_end`.
2. Suppress non-urgent loop prompts in quiet hours.
3. Do not suppress urgent or explicitly requested operations.
4. Daily brief cron executes as scheduled even if it falls near quiet boundaries.

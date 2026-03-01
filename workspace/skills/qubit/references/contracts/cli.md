# Contract: CLI Commands and Flags

The Qubit CLI surface is backward-compatible and stable.

## Global Flags

1. `--workspace`
2. `--json`

## Subcommands

1. `onboard`
2. `add-project`
3. `classical-questioning`
4. `daily-brief`
5. `review-weekly`
6. `stage-message-create`
7. `stage-message-list`
8. `stage-message-edit`
9. `stage-message-cancel`
10. `stage-message-complete`
11. `stage-message-dispatch`
12. `sync-cron`
13. `heal`
14. `sync-heartbeat`
15. `due-scan`
16. `mark-loop`
17. `ingest-message`

## Stability Requirements

1. Keep subcommand names and option names unchanged.
2. Keep managed job IDs stable:
   - `qubit-daily-brief-<pillar-slug>`
   - `qubit-stage-message-<pillar-slug>-<stage-id>`
3. Keep explicit command grammar compatibility in message parsing.

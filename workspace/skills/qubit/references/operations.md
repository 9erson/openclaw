# Qubit v1 Operations

## Command and Interaction Model

1. Support `qubit <pillar> <workflow> [args]` for explicit workflows.
2. Process all pillar-channel user messages as potential workflow inputs.
3. Parse each message into zero-to-many actions.
4. Apply low-risk inferred actions automatically.
5. Require concise clarification choices for inferred high-risk actions.
6. Treat explicit workflow commands as execution authorization.

## Autonomous vs Interactive Modes

Interactive mode (user message in Discord):

1. Stay conversational.
2. Ask concise 2-3 option clarification when uncertain.

Autonomous mode (cron/heartbeat):

1. Execute directly.
2. Avoid conversational clarifications unless blocked.

## Daily Brief

1. Trigger via command or cron.
2. Command behavior: run now only.
3. Content seed:
   - Decisions Needed
   - Due Soon
   - Blocked Projects
   - Top 3 Next Actions
   - One focused question

## Weekly Review

1. Manual command behavior: run now and reset weekly cadence checkpoint.
2. Persist summary to current monthly journal file.

## Rolling Cadence Logic

Intervals from last completed run:

1. Weekly: 7 days
2. Monthly: 30 days
3. Quarterly: 90 days
4. Yearly: 365 days

Rules:

1. If multiple cadences are due on the same day, execute only the highest cadence.
2. If a cadence run was missed, execute once at next opportunity.
3. After execution, set next due relative to actual run time.

## Heartbeat Model

1. Keep a single global heartbeat checklist in `workspace/HEARTBEAT.md`.
2. Scan active pillars for:
   - overdue reminders
   - due loop prompts
3. Skip paused and retired pillars.
4. Respect pillar-specific quiet hours for non-urgent items.

## Cron Model

1. Store jobs in `cron/jobs.json`.
2. Manage one daily brief job per pillar with stable id `qubit-daily-brief-<pillar-slug>`.
3. Use idempotent upsert behavior.
4. Require channel binding (`discord_channel_id`) before creating job.

## Meta Feedback Loop

1. Keep meta prompt templates and evolution artifacts in `workspace/qubit/meta`.
2. Use `general` as meta-control hub channel.
3. Allow meta loop to propose skill changes.
4. Require approval before mutating core skill instructions/scripts.

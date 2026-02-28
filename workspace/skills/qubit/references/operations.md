# Qubit v1 Operations

## Command and Interaction Model

1. Support `qubit <pillar> <workflow> [args]` for explicit workflows.
2. Process all pillar-channel user messages as potential workflow inputs.
3. Parse each message into zero-to-many actions.
4. Apply low-risk inferred actions automatically.
5. Require concise clarification choices for inferred high-risk actions.
6. Treat explicit workflow commands as execution authorization.

## Response Guidance Source

1. Response writing rules live in `workspace/skills/qubit/SKILL.md` under `Response Guidance`.
2. Keep this file focused on workflow behavior and execution logic.

## Autonomous vs Interactive Modes

Interactive mode (user message in Discord):

1. Stay conversational.
2. Ask one question per turn.
3. When a decision is needed or status must be reported, follow `SKILL.md` `Response Guidance`.

Autonomous mode (cron/heartbeat):

1. Execute directly.
2. Avoid conversational clarifications unless blocked.

## Daily Brief

1. Trigger via command or cron.
2. Command behavior: run now only.
3. Cron behavior: enable only after onboarding is completed.
4. Content seed:
   - Decisions Needed
   - Due Soon
   - Blocked Projects
   - Top 3 Next Actions
   - One focused question

## Heal

1. Trigger via command (`heal`) or explicit chat command (`qubit heal` / `qubit heal check`).
2. Default mode is auto-fix; `--check` is report-only.
3. Health policy source: `workspace/qubit/meta/health-policy.json`.
4. Enforce daily brief integrity:
   - eligible pillars: `active` + onboarding completed + not blacklisted + channel bound
   - force timezone to policy timezone (`Asia/Kolkata` by default)
   - recompute evenly spread slots across the policy window (`04:00-05:00` end-exclusive by default)
   - ensure one managed job per eligible pillar
   - remove managed jobs for non-eligible pillars, duplicates, and blacklist violations
5. Blacklist matching uses normalized Discord channel name slug (e.g. `#general` -> `general`).

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

1. Start cadence prompts only after `review_tracking_started_at` exists (first real review completion).
2. If a specific cadence has no `last_<cadence>_review_at`, use `review_tracking_started_at` as baseline.
3. If multiple cadences are due on the same day, execute the nearest cadence first: `weekly -> monthly -> quarterly -> yearly`.
4. If a cadence run was missed, execute once at next opportunity.
5. After execution, set next due relative to actual run time.

## Heartbeat Model

1. Keep a single global heartbeat checklist in `workspace/HEARTBEAT.md`.
2. Scan active pillars for:
   - overdue reminders
   - due loop prompts
3. Skip paused and retired pillars.
4. Skip loop prompts when onboarding is not completed.
5. Respect pillar-specific quiet hours for non-urgent items.

## Onboarding Conversation Model

1. For onboarding question format, follow `SKILL.md` `Response Guidance` mode `Onboarding Question`.
2. `onboard` scaffolds structure and starts onboarding state (`in_progress`).
3. While onboarding is `in_progress`, `ingest-message` treats user replies as onboarding answers.
4. Ask one strategic question at a time in deterministic order: `mission -> scope -> success_signals`.
5. Save draft manifesto updates incrementally on each accepted answer.
6. Weak/placeholder answers must trigger a follow-up question for the same step.
7. Mark onboarding `completed` only after mission, scope, and success signals are captured.

## Cron Model

1. Store jobs in `cron/jobs.json`.
2. Manage one daily brief job per pillar with stable id `qubit-daily-brief-<pillar-slug>`.
3. Use idempotent upsert behavior.
4. Require channel binding (`discord_channel_id`) before creating job.
5. `sync-cron` must respect blacklist policy and clean prohibited jobs instead of recreating them.
6. Run a dedicated nightly heal job (`qubit-heal-nightly`) at `03:00` Asia/Kolkata.

## Meta Feedback Loop

1. Keep meta prompt templates and evolution artifacts in `workspace/qubit/meta`.
2. Use `general` as meta-control hub channel.
3. Allow meta loop to propose skill changes.
4. Require approval before mutating core skill instructions/scripts.

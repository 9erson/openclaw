# Qubit v1 Operations

## Command and Interaction Model

1. Support `qubit <pillar> <workflow> [args]` for explicit workflows.
2. Process all pillar-channel user messages as potential workflow inputs.
3. Parse each message into zero-to-many actions.
4. Apply low-risk inferred actions automatically.
5. Require concise clarification choices for inferred high-risk actions.
6. Treat explicit workflow commands as execution authorization.
7. Detect latent follow-up intent and suggest Stage Message with cooldown-based throttling.
8. Run `classical-questioning` for onboarding and project setup as a hard-gated workflow.

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
   - due staged messages
   - due loop prompts
3. Skip paused and retired pillars.
4. Skip loop prompts when onboarding is not completed.
5. Respect pillar-specific quiet hours for non-urgent items.

## Stage Message Model

1. Stage Message is pillar-scoped and origin-channel-scoped.
2. Allowed delivery methods in v1: `email`, `whatsapp`.
3. Enforce strict recipient schema per delivery method.
4. Use one-shot cron jobs for exact-time dispatch with fallback catch-up via heartbeat `due-scan`.
5. Dispatch exactly once per staged record (`status: scheduled -> notified`) unless manually restaged.
6. Due reminder output is one copy-ready block in the same Origin Channel.
7. Basic conditional follow-up is supported:
   `condition.kind = parent_uncompleted_after_days`.
8. If conditional parent is completed, child stage dispatch is canceled.

## Onboarding Conversation Model

1. For onboarding question format, follow `SKILL.md` `Response Guidance` mode `Onboarding Question`.
2. `onboard` scaffolds structure and starts onboarding state (`in_progress`).
3. While onboarding is `in_progress`, `ingest-message` treats user replies as onboarding answers.
4. Ask one strategic question at a time via `classical-questioning` with internal level bias `grammar -> logic -> rhetoric`.
5. Coverage defaults: grammar >= 3, logic >= 2, total >= 5, rhetoric <= 1, cap = 12 questions.
6. Immediate grammar interrupt: if user introduces an undefined term, ask to define it next turn.
7. Weak/placeholder answers trigger follow-up; after 2 failed attempts switch to constrained choices.
8. Mark onboarding `completed` only after mission, scope, non-negotiables, and success signals are captured.
9. Persist draft state each turn in sidecar files and archive compact session state on completion/cancel.

## Classical Questioning Model

1. Canonical workflow name: `classical-questioning`.
2. Context types: `onboarding`, `project`, `topic`.
3. Session lifecycle: `in_progress`, `paused`, `completed`, `canceled`.
4. Sidecar state files:
   - pillar-scoped (`onboarding`/`topic`): `workspace/pillars/<status>/<pillar-slug>/.classical-questioning.json`
   - project-scoped: `workspace/pillars/<status>/<pillar-slug>/projects/<project-slug>/.classical-questioning.json`
5. Global index: `workspace/qubit/meta/classical-questioning-index.json`.
6. One active session per context type per pillar.
7. Onboarding locks the pillar: no project/topic session can start while onboarding is active.
8. Project setup is hard-gated: `add-project` scaffolds first, then blocks completion until session requirements are met.
9. Standalone topic mode is allowed and writes completion summary to the monthly journal.
10. Natural-language trigger support: detect “apply/run/use/start classical questioning ...”; default target is contextual topic.
11. Explicit controls: status/resume/cancel/answer.

## Cron Model

1. Store jobs in `cron/jobs.json`.
2. Manage one daily brief job per pillar with stable id `qubit-daily-brief-<pillar-slug>`.
3. Manage one-shot stage-message jobs with id `qubit-stage-message-<pillar-slug>-<stage-id>`.
4. Use idempotent upsert behavior.
5. Require channel binding (`discord_channel_id`) before creating jobs.
6. `sync-cron` must respect blacklist policy and clean prohibited jobs instead of recreating them.
7. Run a dedicated nightly heal job (`qubit-heal-nightly`) at `03:00` Asia/Kolkata.

## Meta Feedback Loop

1. Keep meta prompt templates and evolution artifacts in `workspace/qubit/meta`.
2. Use `general` as meta-control hub channel.
3. Allow meta loop to propose skill changes.
4. Require approval before mutating core skill instructions/scripts.

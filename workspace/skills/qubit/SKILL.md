---
name: qubit
description: Manage OpenClaw Discord pillar workflows with file-first state and autonomous feedback loops. Use when handling messages in pillar channels, running `qubit pillar workflow` commands, onboarding pillars, generating daily briefs, running weekly/monthly/quarterly/yearly reviews, updating reminders/projects/contacts/journal files, syncing cron jobs in `cron/jobs.json`, or scanning due work from heartbeat.
---

# Qubit

## Overview

Use this skill to run the personal pillar operating system for OpenClaw Discord channels.
Treat workspace files as the source of truth and keep Discord actions synchronized to them.

## Response Guidance

This section is the source of truth for how Qubit writes replies.
Keep `references/operations.md` focused on workflow logic and point back here for response format rules.

### Mode 1: Decision Support

Use this when a decision is needed.

1. Gather context first from workspace files, relevant project data, and web sources when available or needed.
2. Present exactly 3 viable options.
3. For each option, provide concise pros and cons.
4. Recommend one option and explain why it is the best default.
5. End with exactly one clear decision question.

### Mode 2: Quick Confirmation

Use this for simple acknowledgements.

1. Confirm completion in a short direct response.
2. Do not add extra detail unless asked.

### Mode 3: Status Report

Use this when reporting multiple updates or outcomes.

1. Use concise, scannable lines with this legend:
   - `✅` done
   - `❌` not done or failed
   - `⚠️` needs input or decision
   - `ℹ️` informational
2. Prefer grouped sections such as Added, Updated, Pending, and Failed when relevant.
3. Keep wording compact and concrete.

### Mode 4: Onboarding Question

Use this during onboarding turns.

1. Output ONLY the `question` text from the script JSON response.
2. Use NO framing text (no headers, setup text, or prefaces).
3. Use NO examples unless explicitly requested.
4. Use NO repeating or rephrasing of the question.
5. ONE casual emoji maximum, placed at the end, is optional.
6. The question from the script is the complete message; do not add text before or after.

### Conversational Guardrail

In interactive mode, ask one question per turn and avoid batching multiple questions in one message.

## Core Rules

1. Resolve pillar context first.
Use explicit pillar input when present. Otherwise resolve by Discord channel ID mapping from `pillar.md`.
2. Parse every pillar-channel message for multiple possible actions.
3. Execute low-risk inferred actions automatically.
Low-risk: journal entry, reminder append, contact note append.
4. Ask concise clarification options before high-risk inferred actions.
High-risk: inferred structural changes (for example inferred project creation).
5. Treat explicit `qubit <pillar> <workflow>` commands as authorized execution.
6. Run cron/heartbeat invocations autonomously.
Avoid conversational clarifications unless blocked.

## Workflows

Run the workflow engine script:

```bash
python3 workspace/skills/qubit/scripts/qubit.py <subcommand> [flags]
```

Primary subcommands:

1. `onboard`
Create or repair the pillar structure, seed manifesto/journal files, and start conversational onboarding.
Do not enable daily brief cron until onboarding is completed.
2. `add-project`
Create or update `/projects/<project-slug>/project.md`.
3. `daily-brief`
Generate an immediate Decision+Action brief. Do not alter schedule.
4. `review-weekly`
Write weekly review summary to journal and reset weekly rolling cadence timestamp.
5. `ingest-message`
Parse one Discord message into zero-to-many actions and apply policy.
6. `due-scan`
Scan active pillars for overdue reminders, staged messages, and due rolling loops.
Skip loop prompts for pillars with incomplete onboarding or missing review tracking baseline.
7. `mark-loop`
Mark a loop run (`weekly|monthly|quarterly|yearly`) as completed.
8. `sync-cron`
Idempotently upsert the pillar's daily brief cron entry in `cron/jobs.json`.
9. `heal`
Run global daily-brief integrity checks and auto-fixes (IST 04:00-04:59 spread, one managed job per eligible pillar, blacklist enforcement).
Use `--check` for report-only mode.
10. `sync-heartbeat`
Write a single global heartbeat checklist in `workspace/HEARTBEAT.md`.
11. `stage-message-create`
Create a staged message with strict delivery schema (`email|whatsapp`) and due schedule.
12. `stage-message-list`
List staged messages for a pillar.
13. `stage-message-edit`
Edit staged message fields and reschedule as needed.
14. `stage-message-cancel`
Cancel a staged message and remove cron dispatch job.
15. `stage-message-complete`
Mark a staged message as completed and remove cron dispatch job.
16. `stage-message-dispatch`
Dispatch the due staged message into its Origin Channel as a copy-ready block.

## Explicit Command Grammar

Support and prioritize these forms:

1. `qubit <pillar> onboard`
2. `qubit <pillar> daily brief`
3. `qubit <pillar> review weekly`
4. `qubit <pillar> add project "<title>"`
5. `qubit heal`
6. `qubit heal check`
7. `qubit <pillar> stage message dispatch <stage-id>`
8. `qubit <pillar> scheduled draft|deferred send|send intent|queue message|send later|stage send`

## Pillar Status and Automation Behavior

1. Pillar path: `workspace/pillars/<status>/<pillar-slug>/`
2. Allowed status values: `active`, `paused`, `retired`
3. Include only `active` pillars in heartbeat due scans and loop prompts.
4. Skip non-urgent loop prompts during quiet hours.
5. Do not create daily brief cron until a valid Discord channel ID exists.
6. Do not create daily brief cron until onboarding is completed.
7. During onboarding, process one strategic question per turn and save draft manifesto updates each turn.
8. Daily brief health policy lives in `workspace/qubit/meta/health-policy.json`.
9. Blacklisted channel names (normalized slug match, for example `general`) must not have daily brief cron jobs.
10. Stage Message is pillar-only and blocked in blacklisted channels (for example `general`).
11. Stage Message reminders must return to the same Origin Channel.

## Meta Loop Rules

Use `workspace/qubit/meta` for prompt templates and system-improvement notes.
Run rolling cadences from last execution timestamp:

1. Weekly: 7 days
2. Monthly: 30 days
3. Quarterly: 90 days
4. Yearly: 365 days

Start automated loop prompts only after first real completed review (`review_tracking_started_at`).
If multiple loop cadences are due on the same day, run the nearest cadence first (`weekly -> monthly -> quarterly -> yearly`).
If runs were missed, run once at next opportunity and roll forward from actual run time.

## References

1. Schema contracts and filesystem layout: `references/schemas.md`
2. Operational behavior and cadence logic: `references/operations.md`

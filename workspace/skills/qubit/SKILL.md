---
name: qubit
description: Manage OpenClaw Discord pillar workflows with file-first state and autonomous feedback loops. Use when handling messages in pillar channels, running `qubit pillar workflow` commands, onboarding pillars, generating daily briefs, running weekly/monthly/quarterly/yearly reviews, updating reminders/projects/contacts/journal files, syncing cron jobs in `cron/jobs.json`, or scanning due work from heartbeat.
---

# Qubit

## Overview

Use this skill to run the personal pillar operating system for OpenClaw Discord channels.
Treat workspace files as the source of truth and keep Discord actions synchronized to them.

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
Scan active pillars for overdue reminders and due rolling loops.
Skip loop prompts for pillars with incomplete onboarding or missing review tracking baseline.
7. `mark-loop`
Mark a loop run (`weekly|monthly|quarterly|yearly`) as completed.
8. `sync-cron`
Idempotently upsert the pillar's daily brief cron entry in `cron/jobs.json`.
9. `sync-heartbeat`
Write a single global heartbeat checklist in `workspace/HEARTBEAT.md`.

## Explicit Command Grammar

Support and prioritize these forms:

1. `qubit <pillar> onboard`
2. `qubit <pillar> daily brief`
3. `qubit <pillar> review weekly`
4. `qubit <pillar> add project "<title>"`

## Pillar Status and Automation Behavior

1. Pillar path: `workspace/pillars/<status>/<pillar-slug>/`
2. Allowed status values: `active`, `paused`, `retired`
3. Include only `active` pillars in heartbeat due scans and loop prompts.
4. Skip non-urgent loop prompts during quiet hours.
5. Do not create daily brief cron until a valid Discord channel ID exists.
6. Do not create daily brief cron until onboarding is completed.
7. During onboarding, process one strategic question per turn and save draft manifesto updates each turn.

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

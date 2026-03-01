---
name: qubit
description: Agent-first OpenClaw pillar operations. Use for pillar onboarding, ingesting Discord messages, daily briefs, reviews, staged follow-ups, cron sync/heal, and heartbeat due scans while keeping workspace files as source of truth.
---

# Qubit

## Core Intent

Qubit is an agentic workflow skill, not an engineering-heavy command router.
Use deterministic scripts only for mechanical operations (file IO, schema checks, cron/job mechanics, time parsing, slug/id helpers).
Use references and templates lazily, loading only what is needed for the current turn.

## Loading Strategy (Lazy)

1. Resolve context first: pillar slug, channel id/name, command intent.
2. Load only the relevant workflow reference from `references/workflows/`.
3. Load only needed policy files from `references/policies/`.
4. Load contracts from `references/contracts/` only when validating/formatting output.
5. Use response scaffolds from `templates/` for user-facing replies.

## Response Modes

Select exactly one mode per turn and render via matching template:

1. Decision support -> `templates/decision-support.md`
2. Quick confirmation -> `templates/quick-confirmation.md`
3. Status report -> `templates/status-report.md`
4. Onboarding/classical single-question -> `templates/question-only.md`
5. Clarification choice -> `templates/clarification.md`

## Deterministic Script Boundary

Scripts must remain deterministic and bounded:

1. No free-form workflow reasoning in Python.
2. No policy decisions hardcoded when they can be represented in references.
3. One concern per script module; keep new modules at or below 400 LOC.
4. Keep CLI names, flags, output keys, and filesystem schema backward compatible.

## Workflow Index

1. Ingest message: `references/workflows/ingest-message.md`
2. Onboarding + classical questioning: `references/workflows/onboarding-and-cq.md`
3. Daily brief + reviews: `references/workflows/daily-brief-and-reviews.md`
4. Stage message lifecycle: `references/workflows/stage-message.md`
5. Cron/heal/heartbeat: `references/workflows/cron-heal-heartbeat.md`

## Policy Index

1. Risk/autonomy thresholds: `references/policies/risk-policy.md`
2. Quiet hours + loop suppression: `references/policies/quiet-hours.md`
3. Channel blacklist + pillar scope: `references/policies/channel-blacklist.md`
4. Cadence/loop ordering: `references/policies/cadence.md`

## Contract Index

1. CLI command/flag contract: `references/contracts/cli.md`
2. JSON output contract: `references/contracts/output-schema.md`
3. Filesystem/state contract: `references/contracts/filesystem.md`

## Engine Entrypoint

```bash
python3 workspace/skills/qubit/scripts/qubit.py <subcommand> [flags]
```

# Workflow: Daily Brief and Reviews

## Goal

Produce concise decision/action briefs and persist weekly review checkpoints deterministically.

## Load Order

1. Resolve pillar meta and timezone.
2. Load `../policies/quiet-hours.md` and `../policies/cadence.md` as needed.
3. Load `../contracts/output-schema.md` for key checks.
4. Use `templates/status-report.md` for summary output.

## Rules

1. Daily brief command runs immediately and does not alter schedule.
2. Weekly review writes summary to current monthly journal.
3. Weekly review updates cadence timestamp.
4. Due scan uses active pillars only and respects quiet-hour suppression for non-urgent loops.

## Required Output Keys

1. `status`
2. `workflow`
3. `pillar_slug` (pillar-scoped commands)
4. `message` for generated brief/review text

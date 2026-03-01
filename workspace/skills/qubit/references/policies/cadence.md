# Policy: Cadence and Loop Ordering

## Intervals

1. Weekly: 7 days
2. Monthly: 30 days
3. Quarterly: 90 days
4. Yearly: 365 days

## Rules

1. Start loop prompts only after first completed review (`review_tracking_started_at`).
2. If multiple cadences are due on the same day, prioritize: `weekly -> monthly -> quarterly -> yearly`.
3. If a cadence run was missed, run once at next opportunity then roll from actual run time.
4. `mark-loop` writes completion timestamp for the selected cadence.

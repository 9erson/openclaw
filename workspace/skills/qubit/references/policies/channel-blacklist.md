# Policy: Channel Blacklist and Scope

## Rules

1. Normalize channel names to slugs before comparison.
2. Blacklisted channels must not receive managed daily brief cron jobs.
3. Stage Message is blocked in blacklisted channels (for example `general`).
4. Stage Message reminders must return to the same origin channel.
5. Pillar resolution should prefer channel ID mapping in `pillar.md`.

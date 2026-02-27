# Qubit v1 Schemas

## Table of Contents

1. Pillar Filesystem Layout
2. `pillar.md` Frontmatter
3. `manifesto.md` Frontmatter
4. Contact File Frontmatter
5. Monthly Journal File Frontmatter
6. Project File Frontmatter
7. `reminders.jsonl` Object Schema
8. Time Standard

## Pillar Filesystem Layout

Root:

```text
workspace/pillars/<status>/<pillar-slug>/
```

Status values:

1. `active`
2. `paused`
3. `retired`

Required pillar contents:

1. `pillar.md`
2. `manifesto.md`
3. `reminders.jsonl`
4. `contacts/`
5. `journal/`
6. `projects/`
7. `archive/`

Removed in v1:

1. `contacts.md`
2. `project-list.md`
3. root `journal.md`
4. `reminders.md`

## `pillar.md` Frontmatter

```yaml
pillar_slug: personal
display_name: Personal
status: active
schema_version: 1
timezone: Asia/Kolkata
discord_channel_id: "123456789012345678"
discord_channel_name: "pillar-personal"
daily_brief_time: "08:30"
quiet_hours_start: "22:00"
quiet_hours_end: "07:00"
last_weekly_review_at: null
last_monthly_review_at: null
last_quarterly_review_at: null
last_yearly_review_at: null
updated_at: "2026-02-27T09:30:00+05:30"
```

## `manifesto.md` Frontmatter

```yaml
pillar_slug: personal
schema_version: 1
updated_at: "2026-02-27T09:30:00+05:30"
mission: "..."
scope: "..."
non_negotiables: ["..."]
success_signals: ["..."]
review_cadence: quarterly
```

## Contact File Frontmatter

Path:

```text
contacts/<contact-slug>.md
```

Frontmatter:

```yaml
pillar_slug: personal
schema_version: 1
updated_at: "2026-02-27T09:30:00+05:30"
name: "..."
role: "..."
relationship: "..."
```

## Monthly Journal File Frontmatter

Path:

```text
journal/YYYY-MM.md
```

Frontmatter:

```yaml
pillar_slug: personal
schema_version: 1
month: "2026-02"
entry_count: 0
updated_at: "2026-02-27T09:30:00+05:30"
```

## Project File Frontmatter

Path:

```text
projects/<project-slug>/project.md
```

Frontmatter:

```yaml
pillar_slug: personal
project_slug: plan-annual-mass
schema_version: 1
created_at: "2026-02-27T09:30:00+05:30"
updated_at: "2026-02-27T09:30:00+05:30"
title: "Plan annual mass"
status: active
outcome: "..."
next_decision: "..."
next_action: "..."
due_at: null
tags: []
```

Status enum:

1. `active`
2. `blocked`
3. `waiting`
4. `done`

## `reminders.jsonl` Object Schema

One JSON object per line:

```json
{"id":"...","due_at":"2026-03-01T09:00:00+05:30","message":"...","status":"pending","project_slug":"optional","created_at":"...","updated_at":"..."}
```

Reminder status enum:

1. `pending`
2. `done`
3. `canceled`

## Time Standard

Use ISO 8601 timestamps with timezone offsets for all machine fields.

# Qubit v1 Schemas

## Table of Contents

1. Pillar Filesystem Layout
2. `pillar.md` Frontmatter
3. `manifesto.md` Frontmatter
4. Contact File Frontmatter
5. Monthly Journal File Frontmatter
6. Project File Frontmatter
7. `reminders.jsonl` Object Schema
8. `staged-messages.jsonl` Object Schema
9. `health-policy.json` Schema
10. `classical-questioning` State Schemas
11. Time Standard

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
4. `staged-messages.jsonl`
5. `.classical-questioning.json` (session state sidecar)
6. `contacts/`
7. `journal/`
8. `projects/`
9. `archive/`

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
daily_brief_enabled: false
onboarding_status: in_progress
onboarding_step: mission
onboarding_started_at: "2026-02-27T09:30:00+05:30"
onboarding_completed_at: null
review_tracking_started_at: null
last_weekly_review_at: null
last_monthly_review_at: null
last_quarterly_review_at: null
last_yearly_review_at: null
updated_at: "2026-02-27T09:30:00+05:30"
```

Onboarding lifecycle enums:

1. `onboarding_status`: `in_progress` | `completed`
2. `onboarding_step`: `mission` | `scope` | `non_negotiables` | `success_signals` | `completed`

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
definitions: []
dependencies: []
constraints: []
success_metrics: []
scope_boundaries: ""
classical_questioning_status: in_progress
classical_questioning_completed_at: null
event_slug: null  # Optional: link to associated event
```

## Event File Frontmatter

Path:

```text
events/<event-slug>.md
```

Frontmatter:

```yaml
event_slug: "2026-03-11-mass-lar"
title: "Mass at Lar de Estudantes"
schema_version: 1
created_at: "2026-03-01T05:43:00+05:30"
updated_at: "2026-03-01T05:43:00+05:30"
pillar_slug: santa-casa
date: "2026-03-11"
time: "10:30"
status: scheduled  # scheduled, occurred, canceled, postponed
project_slug: null  # Optional: auto-created project for preparation
```

Body contains event details, context, and notes.

## Event Status Values

1. `scheduled` - Event is planned
2. `occurred` - Event has happened
3. `canceled` - Event was canceled
4. `postponed` - Event was postponed (date will be updated)

## Event-Project Relationship

- Events and projects are **decoupled** with separate lifecycles
- Creating an event **may** auto-create a project (optional)
- One event can have multiple preparation projects
- One project can prepare for multiple events
- Relationship is maintained via optional `event_slug` and `project_slug` fields

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

## `staged-messages.jsonl` Object Schema

Path:

```text
staged-messages.jsonl
```

One JSON object per line:

```json
{
  "id":"stg123abc456def",
  "pillar_slug":"personal",
  "origin_channel_id":"123456789012345678",
  "origin_channel_name":"#pillar-personal",
  "delivery_method":"email",
  "recipient":{"email":"person@example.com"},
  "message_subject":"Follow up",
  "message_body":"Draft body...",
  "due_at":"2026-03-01T09:00:00+05:30",
  "timezone":"Asia/Kolkata",
  "status":"scheduled",
  "condition":null,
  "created_at":"2026-02-27T09:30:00+05:30",
  "updated_at":"2026-02-27T09:30:00+05:30",
  "notified_at":null,
  "completed_at":null,
  "canceled_at":null,
  "dispatch_attempts":0,
  "last_error":null
}
```

Enums and notes:

1. `delivery_method`: `email` | `whatsapp`
2. `status`: `scheduled` | `notified` | `completed` | `canceled` | `failed`
3. `condition` optional v1 shape:
   `{"kind":"parent_uncompleted_after_days","parent_stage_id":"...","wait_days":3}`
4. Reminders are always returned to `origin_channel_id` in the same pillar.

## `classical-questioning` State Schemas

Pillar sidecar path:

```text
workspace/pillars/<status>/<pillar-slug>/.classical-questioning.json
```

Project sidecar path:

```text
workspace/pillars/<status>/<pillar-slug>/projects/<project-slug>/.classical-questioning.json
```

Shape:

```json
{
  "schema_version": 1,
  "active_sessions": [
    {
      "session_id": "cq-abc123def456",
      "name": "classical-questioning",
      "context_type": "onboarding",
      "status": "in_progress",
      "pillar_slug": "personal",
      "project_slug": null,
      "question_count": 4,
      "question_cap": 12,
      "coverage": {"grammar": 2, "logic": 1, "rhetoric": 0, "total": 3},
      "captured": {"mission": "..."},
      "current_question": {"slot": "scope", "level": "grammar", "question": "..."},
      "pending_terms": [],
      "retry_counts": {"scope": 0},
      "accepted_slots": ["mission"],
      "created_at": "2026-02-27T09:30:00+05:30",
      "updated_at": "2026-02-27T09:32:00+05:30"
    }
  ],
  "archive": []
}
```

Global index path:

```text
workspace/qubit/meta/classical-questioning-index.json
```

Shape:

```json
{
  "schema_version": 1,
  "active": [
    {
      "session_id": "cq-abc123def456",
      "pillar_slug": "personal",
      "context_type": "onboarding",
      "status": "in_progress",
      "project_slug": null,
      "state_path": ".../.classical-questioning.json",
      "updated_at": "2026-02-27T09:32:00+05:30"
    }
  ],
  "history": []
}
```

## `health-policy.json` Schema

Path:

```text
workspace/qubit/meta/health-policy.json
```

Object:

```json
{
  "schema_version": 1,
  "timezone": "Asia/Kolkata",
  "daily_brief_window": {
    "start": "04:00",
    "end": "05:00"
  },
  "channel_blacklist": ["general"],
  "checks": {
    "daily_brief_integrity": true
  }
}
```

Rules:

1. `daily_brief_window.start` inclusive and `daily_brief_window.end` exclusive.
2. `channel_blacklist` is matched against normalized Discord channel name slugs.
3. `checks.daily_brief_integrity=false` disables heal enforcement.

## Time Standard

Use ISO 8601 timestamps with timezone offsets for all machine fields.

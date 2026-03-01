# Events Workflow

## Overview

Events are time-bound occurrences that may have associated preparation projects.
Events and projects are **decoupled** with separate lifecycles.

## Event Creation

**Command:**
```bash
qubit <pillar> add event "<title>" --date YYYY-MM-DD [--time HH:MM]
```

**Behavior:**
1. Creates event file in `events/<date-slug>-<title-slug>.md`
2. Optionally auto-creates preparation project (default: yes)
3. Links event and project via `event_slug` and `project_slug` fields

**Event Schema:**
```yaml
event_slug: "20260311-mass-lar"
title: "Mass at Lar de Estudantes"
date: "2026-03-11"
time: "10:30"
status: scheduled  # scheduled, occurred, canceled, postponed
pillar_slug: santa-casa
project_slug: prepare-for-mass  # Optional: auto-created
```

## Project Auto-Creation

When `--create-project` is true (default):
- Project title: "Prepare for {event title}" or custom via `--project-title`
- Project outcome: "Successfully execute {event title}"
- Project due date: Event date + time
- Project tags: ["event"]
- Project status: "active"

## Event Detection (Ingest Message)

Agent should detect event mentions in messages:
- Explicit dates: "Mass on March 11", "workshop next Tuesday"
- Time expressions: "at 10:30 AM", "tomorrow at 3pm"
- Event keywords: "mass", "workshop", "meeting", "camp", "retreat"

When detected:
1. Extract event details (title, date, time)
2. Ask user: "Should I create an event for {title} on {date}?"
3. If yes, run `qubit <pillar> add event ...`
4. Optionally ask: "Create a preparation project too?"

## Event Lifecycle

1. **scheduled** -> Event is planned
2. **occurred** -> Event has happened (manual update)
3. **canceled** -> Event was canceled
4. **postponed** -> Event postponed (update date)

## Event-Project Relationship

- **Decoupled**: Separate statuses and lifecycles
- **Many-to-many** (conceptual):
  - One event can have multiple preparation projects
  - One project can prepare for multiple events
- **Optional links**: `event_slug` and `project_slug` fields
- **Independent completion**: Completing project doesn't auto-complete event

## Directory Structure

```
pillars/active/<pillar-slug>/
  events/
    20260311-mass-lar.md
    20260318-poetry-tea.md
  projects/
    prepare-for-mass/
      project.md
    poetry-and-tea/
      project.md
```

## Response Mode

Use **Quick Confirmation** template:
```
✅ Event created: {title} on {date}
📅 Event file: {event_slug}
📋 Project created: {project_title} (optional)
```

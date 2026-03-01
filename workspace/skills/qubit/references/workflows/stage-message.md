# Workflow: Stage Message Lifecycle

## Goal

Support deterministic deferred outreach with strict schemas and one-shot dispatch semantics.

## Load Order

1. Resolve pillar and channel context.
2. Load `../policies/channel-blacklist.md`.
3. Load `../contracts/filesystem.md` for staged message schema.
4. Use `templates/status-report.md` or `templates/clarification.md` for user output.

## Rules

1. Allowed methods: `email`, `whatsapp`.
2. Enforce recipient schema by delivery method.
3. Use one-shot cron job for dispatch + due-scan catch-up.
4. Dispatch into origin channel only.
5. Terminal states: `completed`, `canceled`, `failed`.

## Required Output Keys

1. `status`
2. `workflow`
3. `pillar_slug`
4. `stage_message_id` where applicable
5. `due_at` where applicable

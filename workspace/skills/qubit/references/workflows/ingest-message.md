# Workflow: Ingest Message

## Goal

Convert one pillar-channel message into zero-to-many deterministic actions while keeping conversation agentic.

## Load Order

1. Resolve pillar context from explicit pillar or channel mapping.
2. Load `../policies/risk-policy.md`.
3. Load `../contracts/filesystem.md` only when action writes occur.
4. Load reply template (`question-only`, `clarification`, or `status-report`) based on result.

## Decision Model

1. Parse possible actions from message intent.
2. Auto-apply low-risk actions.
3. Stage high-risk inferred actions into `pending_confirmation`.
4. If uncertainty exists, ask exactly one clarification question with 2-3 options.

## Low-Risk Actions

1. Journal append
2. Reminder append
3. Contact note append

## High-Risk Actions

1. Inferred project creation or structural file changes
2. Ambiguous workflow command triggers

## Required Output Keys

1. `status`
2. `workflow=ingest-message`
3. `pillar_slug`
4. `applied_actions`
5. `pending_confirmation`
6. `uncertainties`
7. Optional `clarification`
8. Optional `stage_message_suggestion`

# Workflow: Onboarding and Classical Questioning

## Goal

Drive one-question-per-turn onboarding/project/topic clarification with hard gates until minimum coverage is complete.

## Load Order

1. Resolve pillar and onboarding status.
2. Load `../policies/cadence.md` only if onboarding completion touches review tracking.
3. Load contracts from `../contracts/output-schema.md` for response shape.
4. Use `templates/question-only.md` for interactive questions.

## Rules

1. One question per turn.
2. During onboarding `in_progress`, block project/topic sessions.
3. For weak answers, escalate after retry threshold with constrained options.
4. Persist sidecar state each turn.
5. Completion requires mission, scope, non-negotiables, success signals.

## Required Output Keys

1. `status`
2. `workflow`
3. `pillar_slug`
4. `classical_questioning`
5. `question` for interactive question turns
6. `hard_gate_blocked` where applicable

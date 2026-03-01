# Contract: Output Schema

## Common Keys

1. `status` (`ok` | `error`)
2. `workflow` (subcommand workflow name)
3. Optional `message`

## Command-Specific Compatibility

1. `ingest-message` keeps: `applied_actions`, `pending_confirmation`, `uncertainties`, optional `clarification`, optional `stage_message_suggestion`.
2. `onboard` keeps: `onboarding_status`, `onboarding_step`, `classical_questioning`, `hard_gate_blocked`, optional `question`.
3. `classical-questioning` keeps: `classical_questioning`, `question`, `response_mode`, `hard_gate_blocked` where relevant.
4. `heal` keeps: `issues`, `fixes`, `eligible_pillars`, `assignments`, `metrics`.
5. `due-scan` keeps: `due_actions`.

## Rendering Compatibility

Human-readable rendering remains key-value and list oriented.
JSON mode (`--json`) remains machine-readable and stable.

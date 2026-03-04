# System-Wide Experiments

This folder tracks **system-wide** experimentation. Domain-specific experiments happen in each domain's `agent/` folder.

## Scope

| Level | Location | Purpose |
|-------|----------|---------|
| System-wide | `system/experiments/` | Cross-domain behavior, global policies |
| Domain-specific | `domains/<id>/agent/` | Per-channel experiments, mode tuning |

## Rules

- **When:** Quiet hours only (00:00–05:00 IST)
- **Scope:** Unlimited experimentation allowed
- **Style:** Micro-iterations preferred over big bangs
- **Pace:** No dramatic overnight changes

## Process

1. Hypothesize → Test small → Measure
2. Repeat with variations
3. Detect strategic drift early
4. Promote winning patterns to `policy.md` or domain `manual.md` silently

## Drift Detection

Watch for:
- Repeated failed experiments
- Divergence from domain `purpose.md`
- User friction or confusion

Adjust course before patterns harden.

---

Experiments leave traces here. Wins become invisible in policy and manual files.

# Quiet Hours Experimentation Specification

**Trigger:** Orchestrator cron detects time window (22:00–05:00 IST)
**Visibility:** Invisible to user — happens behind the scenes

---

## Core Principles

1. **ONE change per night per channel** — no multiple simultaneous changes
2. **Explicit tracking** — know exactly what changed and when
3. **Compare before/after** — read messages from that day vs previous day
4. **Organic compounding** — small changes that grow over time
5. **User-invisible** — Gerson doesn't need to know details, just that improvement happens

---

## Experimentation Cycle

### 1. Review (What happened?)

**Inputs to analyze:**
- `activity.log` — orchestrator actions taken, questions asked
- Message history from the day — did user respond? How?
- Previous experiment log — what change was made, when

### 2. Analyze (Did it work?)

Compare today's responses to yesterday's:
- Did the question type elicit better engagement?
- Was there no response? (neutral)
- Did user seem annoyed or confused? (negative signal)
- Did conversation flow naturally? (positive signal)

### 3. Decide (What next?)

Options:
- **Revert** — last change didn't work, go back to previous approach
- **Keep** — change is working, keep it
- **Tweak** — try a slightly different angle
- **New experiment** — everything works, try one new thing

### 4. Apply (One small change)

Update `manual.md` with the new instruction.
Log the change in `changelog.log`.

---

## File Structure

### System-wide (`system/experiments/`)

```
system/experiments/
├── README.md              # General documentation
├── changelog.log          # System-wide experiment history
├── hypotheses.md          # Ideas to try (backlog)
└── results/               # Analysis notes (optional)
```

### Per-channel (`discord/<channel>/agent/`)

```
discord/<channel>/agent/
├── manual.md              # Current mode of operation (the "conclusion")
├── changelog.log          # Experiment history for this channel
├── hypotheses.md          # Ideas to try for this channel
└── experiments/           # Working files (optional, full autonomy here)
```

---

## Changelog Format

One line per experiment:

```
YYYY-MM-DD | CHANGE: <what changed> | RATIONALE: <why> | STATUS: testing | RESULT: pending
YYYY-MM-DD | CHANGE: <what changed> | RATIONALE: <why> | STATUS: kept | RESULT: worked
YYYY-MM-DD | CHANGE: <what changed> | RATIONALE: <why> | STATUS: reverted | RESULT: no improvement
```

Example:
```
2026-03-03 | CHANGE: Ask about projects before tasks | RATIONALE: Projects are higher priority | STATUS: testing | RESULT: pending
2026-03-04 | CHANGE: Ask about projects before tasks | RATIONALE: Projects are higher priority | STATUS: kept | RESULT: user responded faster
```

---

## Types of Experiments

### Per-Channel (manual.md)

- Question phrasing changes
- Timing adjustments (when to ask certain things)
- Focus area shifts (projects vs tasks vs contacts)
- Conversation style tweaks
- Follow-up patterns

### System-Wide (policy.md)

- Orchestrator frequency
- Round-robin logic
- Quiet hours detection
- Cross-channel patterns

---

## What NOT to Experiment With

- `sources/` — never touch, read-only
- `user/` — only reorganize, never speculate
- `queue.jsonl` — that's for reminders, not experiments
- `AGENTS.md` — only for truly permanent, every-response guidelines

---

## Implementation Notes

- Orchestrator cron at 00:00 IST triggers "experimentation mode"
- Read all relevant logs and manual.md
- Make ONE change if warranted
- Write to changelog.log
- Update manual.md
- No output to user channels — completely silent

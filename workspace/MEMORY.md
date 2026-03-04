# MEMORY.md - Long-Term Memory

Curated wisdom distilled from daily notes. Last updated: 2026-03-03

---

## Orchestrator System

**Purpose:** Pulse-based channel nudge system that keeps conversations moving toward their purpose.

**Behavior:**
- **Active hours (05:00–22:00 IST):** One strategic question per channel per tick, round-robin
- **Quiet hours (22:00–05:00 IST):** Organize, experiment, analyze patterns, prep briefs
- **Anti-repetition rule:** Never repeat the same question, even if unanswered. Each tick = fresh angle.
- **Time sensing:** 22:00 IST = 16:30 UTC

**Key insight:** Trust Gerson to answer or ignore. Move on. Don't nag.

---

## Domain Structure

Each channel follows this folder structure:

```
discord/<channel>/
├── purpose.md           # Domain intent
├── activity.log         # Action history (append-only)
├── sources/             # Read-only, sources of truth
├── agent/               # AI full autonomy
│   └── manual.md        # Current mode of operation
└── user/                # User-owned files
```

### Access Rules

| Folder | Active Hours | Quiet Hours |
|--------|-------------|-------------|
| `sources/` | Read-only | Read-only |
| `agent/` | Read | Full autonomy (create, edit, delete) |
| `user/` | Reorganize only | Reorganize only |

**User folder rules:**
- ✅ Reorganize and restructure
- ✅ Make more concise
- ✅ Improve clarity and formatting
- ❌ Cannot speculate or add new information
- ❌ Cannot remove substantive information (only condense)

---

## Experimentation System

**Two levels:**

1. **System-wide:** `system/experiments/` → promotes to `system/policy.md`
2. **Domain-specific:** `discord/<channel>/agent/` → promotes to `manual.md`

**Rules:**
- Experiments happen during quiet hours only
- One small change per night
- Explicit tracking in changelogs
- Silent promotion of winning patterns

**Manual.md:**
- Fixed location (`agent/manual.md`)
- Represents current mode of operation
- Does NOT label itself as an experiment
- Updated during quiet hours only

---

## Channel Onboarding

**Approach:** Conversational, AI-driven

1. Start with "What is this channel about?"
2. One question at a time
3. Let conversation flow naturally
4. Create folder + `purpose.md` only after understanding

**Key:** Don't rush to setup. Understand first.

---

## Nagging Doctrine

**Questions:**
- Each question asked ONCE only
- Never repeat, even if unanswered
- Next tick = different question, different angle
- Trust user to answer or ignore

**Non-urgent items:**
- Surface once
- Do not repeat unless new context emerges

**Urgent items only:**
- Can escalate based on deadline proximity
- Closer deadline → more assertive reminder

---

## Queue System

**Default:** `system/queue.jsonl` for reminders/recurring messages

**Currently queued (as of 2026-03-03):**
- 25 messages for #bytebles channel
  - 5 workshop reminders (March 9-23)
  - 10 Python class prep reminders (sessions 3-10)
  - 10 Web Design class prep reminders (sessions 3-10)

---

## Gerson's Preferences

- **Timezone:** Asia/Kolkata (system = UTC)
- **Communication style:** Concise for quick answers, thorough when depth needed
- **Dislikes:** Nagging, repeating questions, messy disorganized files
- **Values:** Strategic insight, pattern recognition, timing-aware communication

---

## Active Channels (Discord)

1. **#acutis-flow** - Gerson's business (client work)
2. **#bytebles** - Coding education venture
3. **#knights-of-st-joseph** - Catholic youth group
4. **#opus-dei** - Spiritual formation
5. **#personal** - Personal tasks, family matters
6. **#professional** - Professional network, opportunities
7. **#santa-casa** - After-school program

All channels are PRIVATE — just Gerson and Qubit (AI). Safe to read MEMORY.md in any Discord channel.

---

## Key Files

| File | Purpose | Load Frequency |
|------|---------|----------------|
| `AGENTS.md` | Core behavior, loaded every response | Every response |
| `system/policy.md` | Orchestrator rules, channel selection | Every orchestrator tick |
| `HEARTBEAT.md` | Heartbeat tasks (rarely used) | On heartbeat poll |
| `MEMORY.md` | Long-term memory (this file) | Main session only |
| `memory/YYYY-MM-DD.md` | Daily raw notes | Current + yesterday |

---

## Lessons Learned

1. **Text > Brain:** If you want to remember something, WRITE IT TO A FILE. Mental notes don't survive session restarts.

2. **Organized user files matter:** User files accumulate messy appended content over time. Keep them organized and clean — not adding interpretations.

3. **Isolation between channels:** Never read content from other channels during orchestrator ticks. Respect channel isolation.

4. **First half vs second half of quiet hours:**
   - First half (22:00–01:30 IST): Learning, experimentation
   - Second half (01:30–05:00 IST): Brief preparation, queue scheduling

5. **Timezone discipline:** All due checks in UTC, all user-facing timestamps in Asia/Kolkata.

---

*This memory file should be reviewed periodically. Daily files are raw notes; this is curated wisdom.*

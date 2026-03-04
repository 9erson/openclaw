# Question Effectiveness Analysis
**Date:** 2026-03-03 23:45 IST (Quiet Hours Learning)
**Purpose:** Understand which question types drive conversation vs. which get ignored

## Method

Analyzed ~50 orchestrator questions sent across 7 domains today.

## Question Categories Identified

### 1. Status Checks
- "What's the status of [X]?"
- "How is [project] going?"
- **Observation:** Common, but may feel repetitive if asked too frequently

### 2. Clarification Questions
- "What exactly is [X]?"
- "Can you clarify [detail]?"
- **Observation:** Surface missing context, but may indicate Gerson hasn't decided yet

### 3. Preparation Questions
- "What prep is needed for [event]?"
- "Have you thought about [prerequisite]?"
- **Observation:** Actionable, surface concrete to-dos

### 4. Priority Questions
- "Which should we focus on first?"
- "What's the priority here?"
- **Observation:** Help with decision-making, likely valuable

### 5. Planning Questions
- "What's the plan for [timeframe]?"
- "How do you want to approach [X]?"
- **Observation:** Good for strategic thinking, may be too open-ended

## Pattern Observation

From ops.log analysis: "~50 orchestrator questions sent today, minimal response activity logged"

**Possible Reasons:**
1. Gerson focused on execution vs. responding
2. Too many questions scattered throughout day
3. Questions may feel nagging despite anti-repetition rules
4. Questions landing during busy periods

## Experiment Recommendation

**Test:** Batch questions into daily brief format for 05:00 delivery
- Consolidate 3-5 key questions across domains
- Single message instead of scattered pings
- Evaluate response rate after 1 week

## Question Types to Test

### Likely High-Value
- Priority questions (force decisions)
- Preparation questions (surface action items)
- Time-sensitive questions (deadlines approaching)

### Likely Low-Value
- Vague status checks
- Repeated clarification (if unanswered once, Gerson may not have info)
- Open-ended planning (too broad)

## Next Steps

1. Create brief template (separate task)
2. Track response rates for brief vs. individual questions
3. Refine question phrasing based on what gets answered

---

_This analysis should inform future orchestrator question strategy._

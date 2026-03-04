# Experiment EXP-001: Question Volume Reduction

**Status:** READY TO START
**Start Date:** 2026-03-04 (05:00 IST)
**Duration:** 3 days
**Type:** System-wide behavior modification

## Hypothesis

Reducing orchestrator question volume to 2-3 questions per domain per day will improve Gerson's response rate and reduce notification fatigue, while maintaining strategic value.

## Problem Statement

Yesterday (March 3rd), the orchestrator sent approximately 46 questions across 8 channels. Analysis revealed:
- Question volume is overwhelming (average 4 questions/hour during active hours)
- Strategic and tactical questions mixed together
- Questions arriving every 15 minutes creates constant interruption
- Some topics approached from multiple angles in same day

**Result:** Minimal response activity logged, likely due to notification fatigue.

## Proposed Solution

Implement three-part change:
1. **Daily brief as primary interface** - Move routine/tactical questions to 05:00 brief
2. **Question volume cap** - Max 2-3 strategic questions per domain per day
3. **Topic tracking** - Limit to ONE question per topic per day

## Success Metrics

| Metric | Baseline (Mar 3) | Target | Measurement |
|--------|------------------|--------|-------------|
| Questions per day | ~46 | <25 | Count in ops.log |
| Response rate | ~10% (estimated) | >30% | Track responses in activity logs |
| Gerson feedback | N/A | "Much better" or similar | Direct feedback or observed behavior |

## Implementation

### What Changes

**Daily brief (already created):**
- File: `system/daily-brief-2026-03-04.md`
- Delivery: 05:00 IST to #personal
- Contains: All routine check-ins, tactical items, status questions

**Orchestrator behavior:**
- Reduce from ~6 questions per domain per day to 2-3
- Focus on strategic questions only (planning, decisions, direction)
- Track question topics to avoid same-day repetition

### What Stays the Same

- Round-robin channel selection
- 15-minute tick intervals
- Anti-repetition rule (exact wording)
- Quiet hours behavior

### Tracking Method

1. Count total questions in ops.log each day
2. Review activity logs for response patterns
3. Check for direct feedback from Gerson
4. Compare question topic distribution

## Rollout Plan

### Day 1 (March 4) - Initial Test
- Daily brief delivers at 05:00 IST
- Orchestrator runs as normal but counts questions per domain
- Monitor response rate

### Day 2 (March 5) - Adjust
- If Day 1 shows improvement, continue
- If no change, analyze which domains need adjustment
- Review Gerson's reactions

### Day 3 (March 6) - Evaluate
- Compare 3-day metrics to baseline
- Decision: continue, modify, or revert

## Decision Criteria

**Continue experiment if:**
- Response rate increases by 20% or more
- No negative feedback from Gerson
- Question count reduced by 40% or more

**Modify if:**
- Some domains respond better than others
- Brief format needs adjustment

**Revert if:**
- Response rate decreases
- Gerson explicitly dislikes the change
- Important items getting missed

## Risk Mitigation

**Risk:** Important items get buried in brief
**Mitigation:** Brief includes "Time-Sensitive Items" section at top

**Risk:** Strategic questions still too frequent
**Mitigation:** Day 1 metrics will reveal if further reduction needed

**Risk:** Brief delivery time inconvenient
**Mitigation:** Can adjust delivery time based on feedback

## Baseline Data (March 3)

```
Total questions: 46
Domains covered: 8
Questions per domain:
  - acutis-flow: 9
  - bytebles: 9
  - knights-of-st-joseph: 7
  - santa-casa: 8
  - opus-dei: 6
  - personal: 3
  - dev-ops: 3
  - professional: 1
```

## Next Steps

1. ✅ Daily brief created and queued (18:15 UTC)
2. ⏳ Monitor Day 1 response rate
3. ⏳ Review and adjust on Day 2
4. ⏳ Final evaluation on Day 3

---

**Created:** 2026-03-03 19:30 UTC (1:00 AM IST, March 4)
**Experiment Lead:** Qubit (orchestrator system)
**Review Schedule:** Daily during quiet hours
# Classical Questioning Refactor Plan

## Problem

Current Classical Questioning system is **engineered, not intelligent**:
- Uses Python pattern matching for term detection
- Hardcoded question templates
- Mechanical followup questions: "You mentioned 'X'. What does it specifically mean?"
- NOT contextually aware
- NOT LLM-driven

**Example of dumb behavior:**
```
User: "a startup company by myself and Derick Dsouza to help small businesses"
Bot: "You mentioned 'Derick'. What does it specifically mean?"
Bot: "You mentioned 'Dsouza'. What does it specifically mean?"
Bot: "You mentioned 'Acutis'. What does it specifically mean?"
```

This is **keyword detection**, not intelligence.

---

## Solution: LLM-First Architecture

**Move ALL intelligence from Python → LLM prompts**

---

## Current Architecture (Python-Heavy)

```
┌─────────────────────┐
│  User Message       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Python Pattern     │
│  Matching           │
│  - CQ_TERM_HINT_    │
│    PATTERN          │
│  - CQ_RHETORIC_CUE_ │
│    PATTERN          │
│  - CQ_STOPWORDS     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Hardcoded          │
│  Question Templates │
│  - CQ_QUESTION_     │
│    TEMPLATES        │
│  - CQ_FOLLOWUP_     │
│    TEMPLATES        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Mechanical Output  │
│  "You mentioned X"  │
└─────────────────────┘
```

**Problems:**
- All logic in Python
- No understanding of context
- Keyword-based term detection
- Rigid question flow
- No conversational awareness

---

## New Architecture (LLM-First)

```
┌─────────────────────┐
│  User Message       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Python Wrapper     │
│  - Load context     │
│  - State tracking   │
│  - Session mgmt     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  LLM Prompt         │
│  - Context-aware    │
│  - Intent detection │
│  - Question gen     │
│  - Coverage calc    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Intelligent Output │
│  - Natural followup │
│  - Contextual Q's   │
└─────────────────────┘
```

**Benefits:**
- ALL intelligence in LLM
- Contextual understanding
- Natural conversation flow
- Adaptive questioning
- Conversational awareness

---

## Implementation Plan

### **Phase 1: Create LLM Prompt System**

**Location:** `skills/qubit/prompts/classical-questioning.md`

**Purpose:** Single prompt file that handles ALL Classical Questioning logic

**Prompt Structure:**
```markdown
# Classical Questioning Prompt

## Context
You are conducting a Socratic questioning session for {{context_type}}.

## Current State
- Pillar: {{pillar_name}}
- Context Type: {{context_type}}
- Step: {{current_step}}
- Coverage: {{coverage}}%
- Questions Asked: {{question_count}}/{{question_cap}}

## Previous Q&A
{{previous_qa}}

## User's Latest Answer
{{user_answer}}

## Your Task
1. Analyze the user's answer for:
   - Completeness (did they answer the question?)
   - Clarity (is it understandable?)
   - Coverage (what new information was revealed?)
   
2. Decide next action:
   - If answer is insufficient → Ask clarifying followup
   - If answer is sufficient → Move to next topic
   - If coverage complete → Conclude session
   
3. Generate response:
   - ONE question only (never multiple)
   - Natural, conversational tone
   - Contextually aware
   - No mechanical "You mentioned X" phrases

## Requirements
- Grammar level: 3+ questions minimum
- Logic level: 2+ questions minimum
- Total: 5+ questions minimum
- Never exceed {{question_cap}} questions

## Output Format
{
  "action": "ask_followup" | "next_topic" | "conclude",
  "question": "Your single question here",
  "reasoning": "Why you chose this question",
  "coverage_update": {
    "grammar": +X,
    "logic": +Y,
    "rhetoric": +Z
  }
}
```

---

### **Phase 2: Refactor Python Code**

**Goal:** Remove ALL intelligence from Python

**Changes:**
1. **Remove pattern matching:**
   ```python
   # DELETE these
   CQ_TERM_HINT_PATTERN = re.compile(...)
   CQ_RHETORIC_CUE_PATTERN = re.compile(...)
   CQ_STOPWORDS = {...}
   CQ_QUESTION_TEMPLATES = {...}
   CQ_FOLLOWUP_TEMPLATES = {...}
   ```

2. **Keep only state management:**
   ```python
   # KEEP these
   - Session state tracking
   - File I/O
   - Coverage calculation (from LLM output)
   - Session persistence
   ```

3. **Add LLM integration:**
   ```python
   def run_classical_questioning_turn(
       session: dict[str, Any],
       user_message: str,
   ) -> dict[str, Any]:
       # 1. Build prompt with context
       prompt = build_cq_prompt(session, user_message)
       
       # 2. Call LLM
       llm_response = call_llm(prompt)
       
       # 3. Parse LLM output
       action = llm_response["action"]
       question = llm_response["question"]
       coverage_update = llm_response["coverage_update"]
       
       # 4. Update session state
       session = update_session(session, coverage_update)
       
       # 5. Return response
       return {
           "question": question,
           "action": action,
           "coverage": session["coverage"],
       }
   ```

---

### **Phase 3: Create Prompt Templates**

**Location:** `skills/qubit/prompts/`

**Files:**
1. `classical-questioning.md` - Main prompt
2. `onboarding-context.md` - Context for onboarding sessions
3. `project-context.md` - Context for project sessions
4. `topic-context.md` - Context for topic sessions

**Example: `onboarding-context.md`**
```markdown
# Onboarding Context

## Goal
Conduct Socratic questioning to clarify a new pillar's mission, scope, and success criteria.

## Topics to Cover
1. **Mission** (Grammar level)
   - What is this pillar about?
   - What are you trying to accomplish?
   - Why does this matter?

2. **Scope** (Grammar level)
   - What kind of work goes here?
   - What definitely doesn't belong?
   - Who are the stakeholders?

3. **Non-Negotiables** (Logic level)
   - What principles are non-negotiable?
   - What values guide this work?
   - What must never be compromised?

4. **Success Signals** (Logic level)
   - How will you know it's working?
   - What are 2-3 measurable signs of progress?
   - What does success look like in 6 months?

## Completion Criteria
- Mission: Clear, concrete statement
- Scope: Well-defined boundaries
- Non-negotiables: At least 1 principle
- Success signals: At least 2 measurable signals
```

---

### **Phase 4: Coverage System**

**Current:** Python calculates coverage based on slots filled

**New:** LLM calculates coverage based on understanding

**Prompt Addition:**
```markdown
## Coverage Calculation

After each answer, assess what new information was revealed:

- **Grammar level** (facts, definitions, scope): +5-15% per clear answer
- **Logic level** (principles, reasoning, strategy): +10-20% per clear answer
- **Rhetoric level** (influence, narrative, persuasion): +5-10% per clear answer

Update your assessment:
{
  "coverage_update": {
    "grammar": +10,
    "logic": +15,
    "rhetoric": +5
  },
  "total_coverage": 45,
  "reasoning": "User clarified mission and scope, but success signals still vague"
}
```

---

### **Phase 5: Question Generation**

**Current:** Hardcoded templates

**New:** LLM generates questions dynamically

**Examples:**

**Old (Dumb):**
```
User: "startup with Derick Dsouza"
Bot: "You mentioned 'Derick'. What does it specifically mean?"
```

**New (Intelligent):**
```
User: "startup with Derick Dsouza"
Bot: "Got it - you and Derick are building this together. What specific problem are you solving for small businesses?"
```

**Prompt Guidance:**
```markdown
## Question Generation Rules

1. **Never ask about proper nouns unless truly unclear**
   - ❌ "You mentioned 'Derick'. What does it specifically mean?"
   - ✅ "What role does Derick play in this startup?"

2. **Always move the conversation forward**
   - ❌ Mechanical clarification
   - ✅ Next logical question

3. **Be conversational, not interrogative**
   - ❌ "Define the term 'Acutis Flow'"
   - ✅ "What does Acutis Flow do for its clients?"

4. **One question at a time**
   - Never stack multiple questions
   - Focus on single topic per turn

5. **Contextual awareness**
   - Reference previous answers naturally
   - Build on established context
   - Don't repeat covered topics
```

---

### **Phase 6: Remove Python Intelligence**

**Delete from `engine.py`:**

```python
# DELETE all hardcoded patterns
CQ_TERM_HINT_PATTERN = re.compile(...)
CQ_RHETORIC_CUE_PATTERN = re.compile(...)
CQ_STOPWORDS = {...}
CQ_QUESTION_TEMPLATES = {...}
CQ_FOLLOWUP_TEMPLATES = {...}

# DELETE mechanical question rendering
def cq_render_question_text(...):
    # This becomes LLM-driven

# DELETE slot-based logic
CQ_SLOT_ORDER = {...}
CQ_REQUIRED_SLOTS = {...}
```

**Keep only:**
```python
# Session management
def cq_load_session(...)
def cq_save_session(...)

# LLM integration
def run_classical_questioning_turn(...):
    prompt = build_prompt(session, user_message)
    response = call_llm(prompt)
    return parse_llm_response(response)

# State tracking
def update_session_coverage(session, coverage_update):
    # Simple arithmetic from LLM output
    session["coverage"]["grammar"] += coverage_update["grammar"]
    session["coverage"]["logic"] += coverage_update["logic"]
    session["coverage"]["coverage_percent"] = calculate_total(session)
```

---

## Migration Path

### **Stage 1: Parallel Run**
- Keep old system active
- Add new LLM system alongside
- Compare outputs
- Verify quality

### **Stage 2: Hybrid Mode**
- Use LLM for question generation
- Keep Python for coverage calculation
- Test in production

### **Stage 3: Full Cutover**
- Remove all Python intelligence
- 100% LLM-driven
- Monitor quality

---

## Benefits

### **Immediate**
- ✅ No more dumb "You mentioned X" questions
- ✅ Contextual, natural followups
- ✅ Conversational flow

### **Long-term**
- ✅ Adapts to user's communication style
- ✅ Learns from context
- ✅ Handles ambiguity intelligently
- ✅ Scales without code changes

### **Maintainability**
- ✅ All logic in prompts (easy to update)
- ✅ No pattern matching to maintain
- ✅ Python code minimal (just plumbing)

---

## File Structure

```
skills/qubit/
├── prompts/
│   ├── classical-questioning.md
│   ├── onboarding-context.md
│   ├── project-context.md
│   └── topic-context.md
├── scripts/
│   └── v2/
│       └── engine.py (refactored - minimal logic)
└── references/
    └── workflows/
        └── classical-questioning.md (updated)
```

---

## Success Metrics

1. **No mechanical questions** - Zero "You mentioned X" phrases
2. **Conversational flow** - Natural dialogue progression
3. **Contextual awareness** - References previous answers
4. **Completion rate** - Higher session completion
5. **User satisfaction** - Less frustration, more engagement

---

## Timeline

- **Week 1:** Create prompt system
- **Week 2:** Refactor Python code
- **Week 3:** Test parallel run
- **Week 4:** Hybrid mode deployment
- **Week 5:** Full cutover
- **Week 6:** Monitor and iterate

---

## Risks

1. **LLM latency** - May be slower than pattern matching
   - **Mitigation:** Use fast model (GPT-4o-mini, Claude Haiku)

2. **Cost** - LLM calls cost more than regex
   - **Mitigation:** Optimize prompts, use smaller models

3. **Quality control** - LLM output may vary
   - **Mitigation:** Structured output, validation checks

4. **Edge cases** - LLM may hallucinate
   - **Mitigation:** Constrain output format, validate coverage numbers

---

## Conclusion

**The fix is simple: Move ALL intelligence from Python → LLM prompts.**

**No more Python patterns. No more hardcoded templates. Just intelligent conversation.**

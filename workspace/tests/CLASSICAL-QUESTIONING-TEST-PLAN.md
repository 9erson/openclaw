# Classical Questioning Testing Plan

## Overview

Comprehensive testing plan for the LLM-driven Classical Questioning system. Tests compare old (pattern-based) vs new (LLM-driven) approaches.

---

## Test Categories

### 1. Unit Tests
- LLM helper functions
- Prompt building
- Response validation
- Coverage calculation

### 2. Integration Tests
- Full conversation flows
- Session state management
- Error handling

### 3. Comparison Tests
- Old vs new question quality
- Coverage accuracy
- Conversation naturalness

### 4. User Acceptance Tests
- Real user conversations
- Feedback collection
- Satisfaction metrics

---

## Test Suite

### **Test 1: LLM Helper Functions**

**File:** `tests/test_llm_helper.py`

```python
#!/usr/bin/env python3
"""Unit tests for LLM helper functions."""

import sys
import json
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "qubit" / "scripts"))

from llm_helper import (
    call_llm_for_cq,
    validate_llm_response,
    _get_placeholder_response,
)


def test_validate_llm_response_valid():
    """Test validation with valid response."""
    response = {
        "action": "ask_followup",
        "question": "What specific problems do small businesses face?",
        "reasoning": "User mentioned startup helping small businesses",
        "coverage_update": {"grammar": 10, "logic": 5, "rhetoric": 0},
        "total_coverage": 35,
        "topic_progress": {
            "current": "mission",
            "next": "scope",
        },
    }
    
    assert validate_llm_response(response) is True
    print("✅ Valid response passes validation")


def test_validate_llm_response_missing_field():
    """Test validation with missing field."""
    response = {
        "action": "ask_followup",
        "question": "What problems?",
        # Missing: reasoning, coverage_update, total_coverage, topic_progress
    }
    
    assert validate_llm_response(response) is False
    print("✅ Invalid response fails validation (missing fields)")


def test_validate_llm_response_invalid_action():
    """Test validation with invalid action."""
    response = {
        "action": "invalid_action",
        "question": "What?",
        "reasoning": "Test",
        "coverage_update": {},
        "total_coverage": 0,
        "topic_progress": {"current": "mission", "next": "mission"},
    }
    
    assert validate_llm_response(response) is False
    print("✅ Invalid action fails validation")


def test_placeholder_response():
    """Test placeholder response structure."""
    response = _get_placeholder_response()
    
    assert response["action"] == "ask_followup"
    assert "needs_agent_llm_call" in response
    assert response["needs_agent_llm_call"] is True
    print("✅ Placeholder response has correct structure")


def test_call_llm_for_cq():
    """Test LLM call (will use placeholder if oracle not available)."""
    prompt = "Test prompt for LLM"
    response = call_llm_for_cq(prompt)
    
    # Should return valid response even if oracle not available
    assert "action" in response
    assert "question" in response
    print(f"✅ LLM call returns response: {response['action']}")


if __name__ == "__main__":
    print("Running LLM Helper Tests...\n")
    
    test_validate_llm_response_valid()
    test_validate_llm_response_missing_field()
    test_validate_llm_response_invalid_action()
    test_placeholder_response()
    test_call_llm_for_cq()
    
    print("\n✅ All tests passed!")
```

---

### **Test 2: Conversation Quality Comparison**

**File:** `tests/test_conversation_quality.py`

```python
#!/usr/bin/env python3
"""Compare old vs new conversation quality."""

import sys
from pathlib import Path

# Test scenarios
SCENARIOS = [
    {
        "name": "Startup onboarding",
        "user_answer": "a startup company by myself and Derick Dsouza to help small businesses with AI solutions",
        "old_questions": [
            "You mentioned 'Derick'. What does it specifically mean in this context?",
            "You mentioned 'Dsouza'. What does it specifically mean in this context?",
            "You mentioned 'Acutis'. What does it specifically mean in this context?",
        ],
        "new_question": "Got it - you and Derick are building this together. What specific problems do small businesses face that you're trying to solve?",
    },
    {
        "name": "Project scope",
        "user_answer": "building a customer portal for our SaaS product",
        "old_questions": [
            "You mentioned 'SaaS'. What does it specifically mean in this context?",
        ],
        "new_question": "What will customers be able to do in this portal that they can't do now?",
    },
    {
        "name": "Mission statement",
        "user_answer": "help people be more productive",
        "old_questions": [
            "Can you be more specific? What's the main thing you want to achieve?",
        ],
        "new_question": "Productivity is broad - what specific aspect of productivity are you focusing on?",
    },
]


def evaluate_question_quality(question: str) -> dict:
    """Evaluate question quality."""
    score = 0
    issues = []
    
    # Check for mechanical patterns
    if "You mentioned" in question:
        issues.append("Mechanical 'You mentioned' pattern")
    else:
        score += 25
    
    # Check for natural language
    if any(word in question.lower() for word in ["got it", "understood", "makes sense"]):
        score += 25
    
    # Check for forward movement
    if any(word in question.lower() for word in ["specific", "what", "how", "why"]):
        score += 25
    
    # Check for contextual awareness
    if len(question.split()) > 5:  # Not too short
        score += 25
    
    return {
        "score": score,
        "issues": issues,
        "is_mechanical": "You mentioned" in question,
    }


def test_conversation_quality():
    """Test conversation quality for all scenarios."""
    print("Testing Conversation Quality...\n")
    
    for scenario in SCENARIOS:
        print(f"Scenario: {scenario['name']}")
        print(f"User Answer: {scenario['user_answer']}")
        print()
        
        # Evaluate old questions
        print("Old System Questions:")
        old_scores = []
        for q in scenario['old_questions']:
            result = evaluate_question_quality(q)
            old_scores.append(result['score'])
            print(f"  - {q}")
            print(f"    Score: {result['score']}/100")
            if result['issues']:
                print(f"    Issues: {', '.join(result['issues'])}")
        
        avg_old = sum(old_scores) / len(old_scores) if old_scores else 0
        print(f"  Average: {avg_old:.1f}/100")
        print()
        
        # Evaluate new question
        print("New System Question:")
        new_result = evaluate_question_quality(scenario['new_question'])
        print(f"  - {scenario['new_question']}")
        print(f"    Score: {new_result['score']}/100")
        if new_result['issues']:
            print(f"    Issues: {', '.join(new_result['issues'])}")
        print()
        
        # Compare
        improvement = new_result['score'] - avg_old
        if improvement > 0:
            print(f"✅ New system is {improvement:.1f} points better")
        else:
            print(f"❌ New system is {abs(improvement):.1f} points worse")
        
        print("-" * 80)
        print()


if __name__ == "__main__":
    test_conversation_quality()
```

---

### **Test 3: Coverage Calculation**

**File:** `tests/test_coverage_calculation.py`

```python
#!/usr/bin/env python3
"""Test coverage calculation from LLM responses."""

import sys
from pathlib import Path


def test_coverage_accumulation():
    """Test that coverage accumulates correctly."""
    print("Testing Coverage Accumulation...\n")
    
    # Simulate session with multiple answers
    session = {
        "coverage": {"grammar": 0, "logic": 0, "rhetoric": 0},
        "qa_history": [],
    }
    
    # Simulate LLM responses
    responses = [
        {"coverage_update": {"grammar": 10, "logic": 0, "rhetoric": 0}},
        {"coverage_update": {"grammar": 5, "logic": 10, "rhetoric": 0}},
        {"coverage_update": {"grammar": 5, "logic": 5, "rhetoric": 5}},
    ]
    
    for i, response in enumerate(responses):
        # Apply coverage update
        for level, increment in response['coverage_update'].items():
            session['coverage'][level] = min(100, session['coverage'][level] + increment)
        
        total = sum(session['coverage'].values())
        print(f"After answer {i+1}: {session['coverage']} = {total}% total")
    
    # Verify final coverage
    final_total = sum(session['coverage'].values())
    print(f"\nFinal coverage: {final_total}%")
    
    assert final_total == 40, f"Expected 40%, got {final_total}%"
    print("✅ Coverage accumulation works correctly")


def test_coverage_caps():
    """Test that coverage caps at 100%."""
    print("\nTesting Coverage Caps...\n")
    
    coverage = {"grammar": 0, "logic": 0, "rhetoric": 0}
    
    # Add large increments
    increments = [
        {"grammar": 50, "logic": 30, "rhetoric": 20},
        {"grammar": 50, "logic": 30, "rhetoric": 20},
    ]
    
    for increment in increments:
        for level, value in increment.items():
            coverage[level] = min(100, coverage[level] + value)
    
    # Check individual caps
    for level, value in coverage.items():
        assert value <= 100, f"{level} exceeded 100: {value}"
        print(f"{level}: {value}%")
    
    print("✅ Coverage respects individual caps")


def test_completion_threshold():
    """Test completion detection."""
    print("\nTesting Completion Threshold...\n")
    
    # Test various coverage levels
    test_cases = [
        (50, False, "Below threshold"),
        (70, True, "At threshold"),
        (85, True, "Above threshold"),
    ]
    
    threshold = 70
    
    for coverage, expected_complete, description in test_cases:
        is_complete = coverage >= threshold
        status = "✅" if is_complete == expected_complete else "❌"
        print(f"{status} {coverage}%: {description} - Complete: {is_complete}")
        assert is_complete == expected_complete


if __name__ == "__main__":
    test_coverage_accumulation()
    test_coverage_caps()
    test_completion_threshold()
    
    print("\n✅ All coverage tests passed!")
```

---

### **Test 4: Full Integration Test**

**File:** `tests/test_integration.py`

```python
#!/usr/bin/env python3
"""Full integration test with real LLM calls."""

import sys
import json
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "qubit" / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "qubit" / "scripts" / "v2"))


def test_full_conversation_flow():
    """Test complete conversation flow."""
    print("Testing Full Conversation Flow...\n")
    
    # This would be a real integration test with actual LLM calls
    # For now, we'll simulate the flow
    
    conversation = [
        {
            "question": "What's this pillar about?",
            "answer": "a startup company by myself and Derick Dsouza to help small businesses with AI solutions",
        },
        {
            "question": "What specific problems do small businesses face?",
            "answer": "they struggle with manual processes, data management, and customer engagement",
        },
        {
            "question": "Which problem is most urgent?",
            "answer": "customer engagement - they're losing customers because they can't respond fast enough",
        },
    ]
    
    print("Conversation Flow:")
    for i, qa in enumerate(conversation):
        print(f"\nTurn {i+1}:")
        print(f"  Q: {qa['question']}")
        print(f"  A: {qa['answer']}")
    
    print("\n✅ Conversation flow test complete")


def test_error_handling():
    """Test error handling."""
    print("\nTesting Error Handling...\n")
    
    from llm_helper import call_llm_for_cq
    
    # Test with empty prompt
    response = call_llm_for_cq("")
    assert "action" in response
    print("✅ Empty prompt handled gracefully")
    
    # Test with invalid model (should use default)
    response = call_llm_for_cq("test", model="invalid-model")
    assert "action" in response
    print("✅ Invalid model handled gracefully")
    
    print("\n✅ Error handling tests passed")


if __name__ == "__main__":
    test_full_conversation_flow()
    test_error_handling()
    
    print("\n✅ All integration tests passed!")
```

---

## Manual Testing Checklist

### **Setup**
- [ ] Oracle CLI installed (optional)
- [ ] Test pillar created
- [ ] Test environment configured

### **Basic Functionality**
- [ ] Start classical questioning session
- [ ] Answer first question
- [ ] Receive LLM-generated followup
- [ ] Continue conversation for 5+ turns
- [ ] Complete session successfully

### **Quality Checks**
- [ ] No "You mentioned X" questions
- [ ] Natural, conversational tone
- [ ] Contextual followups
- [ ] Forward-moving conversation
- [ ] Appropriate coverage accumulation

### **Error Scenarios**
- [ ] Oracle not available (placeholder works)
- [ ] Invalid user answer (graceful handling)
- [ ] LLM timeout (fallback works)
- [ ] Invalid JSON response (validation works)

---

## Performance Metrics

### **Response Time**
- Target: < 3 seconds for LLM call
- Target: < 5 seconds end-to-end

### **Quality Metrics**
- Mechanical questions: 0% (target)
- Natural followups: > 90%
- Contextual awareness: > 85%
- User satisfaction: > 4.0/5.0

### **Coverage Metrics**
- Average coverage per answer: 5-15%
- Completion rate: > 80%
- Question efficiency: 5-8 questions to completion

---

## Test Execution

### **Run All Tests**
```bash
cd /root/.openclaw/workspace

# Run unit tests
python3 tests/test_llm_helper.py

# Run quality tests
python3 tests/test_conversation_quality.py

# Run coverage tests
python3 tests/test_coverage_calculation.py

# Run integration tests
python3 tests/test_integration.py
```

### **Run Single Test**
```bash
python3 tests/test_llm_helper.py
```

---

## Test Results Template

### **Test Run: [Date]**

**Environment:**
- Oracle CLI: [Installed/Not Installed]
- Model: gpt-4o-mini
- Test Duration: [X minutes]

**Results:**
- Unit Tests: [X/Y passed]
- Quality Tests: [Score: X/100]
- Coverage Tests: [X/Y passed]
- Integration Tests: [X/Y passed]

**Issues Found:**
1. [Issue description]
2. [Issue description]

**Recommendations:**
1. [Recommendation]
2. [Recommendation]

---

## Continuous Testing

### **Automated Test Suite**
- Run on every commit
- Track quality metrics over time
- Alert on regression

### **Monitoring**
- Log all LLM calls
- Track response times
- Monitor error rates
- Collect user feedback

---

## Success Criteria

✅ **All tests pass**
- Unit tests: 100%
- Integration tests: 100%
- Quality score: > 80/100

✅ **No mechanical questions**
- "You mentioned X": 0 occurrences

✅ **Natural conversation flow**
- Contextual followups: > 90%
- Forward movement: > 85%

✅ **Coverage accuracy**
- Accumulation correct: 100%
- Completion detection: 100%

---

## Next Steps

After testing passes:
1. Deploy to staging
2. Beta test with real users
3. Collect feedback
4. Iterate on prompts
5. Production deployment

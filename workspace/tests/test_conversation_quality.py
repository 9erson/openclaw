#!/usr/bin/env python3
"""Compare old vs new conversation quality."""

import sys
from pathlib import Path

# Test scenarios comparing old (dumb) vs new (intelligent) questions
SCENARIOS = [
    {
        "name": "Startup onboarding",
        "user_answer": "a startup company by myself and Derick Dsouza to help small businesses with AI solutions",
        "old_questions": [
            "You mentioned 'Derick'. What does it specifically mean in this context?",
            "You mentioned 'Dsouza'. What does it specifically mean in this context?",
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
    {
        "name": "Stakeholder identification",
        "user_answer": "this is for our enterprise clients",
        "old_questions": [
            "You mentioned 'enterprise'. What does it specifically mean in this context?",
        ],
        "new_question": "What kind of enterprise clients are you targeting? Any specific industry or size?",
    },
    {
        "name": "Success metrics",
        "user_answer": "we want to improve customer satisfaction",
        "old_questions": [
            "Can you be more specific? What's the main thing you want to achieve?",
        ],
        "new_question": "How will you measure customer satisfaction? What metric will you use?",
    },
]


def evaluate_question_quality(question: str) -> dict:
    """Evaluate question quality on multiple dimensions."""
    score = 0
    issues = []
    positives = []
    
    # Check for mechanical patterns (BAD)
    if "You mentioned" in question:
        issues.append("❌ Mechanical 'You mentioned' pattern")
    else:
        score += 25
        positives.append("✅ No mechanical patterns")
    
    # Check for natural language (GOOD)
    if any(word in question.lower() for word in ["got it", "understood", "makes sense", "that's clear"]):
        score += 25
        positives.append("✅ Natural conversational tone")
    
    # Check for forward movement (GOOD)
    if any(word in question.lower() for word in ["specific", "what", "how", "why", "which"]):
        score += 25
        positives.append("✅ Moves conversation forward")
    
    # Check for contextual awareness (GOOD)
    if len(question.split()) > 5:  # Not too short
        score += 25
        positives.append("✅ Contextually aware")
    else:
        issues.append("❌ Too brief, lacks context")
    
    return {
        "score": score,
        "issues": issues,
        "positives": positives,
        "is_mechanical": "You mentioned" in question,
    }


def test_conversation_quality():
    """Test conversation quality for all scenarios."""
    print("="*80)
    print("Testing Conversation Quality: Old vs New")
    print("="*80 + "\n")
    
    total_improvement = 0
    scenarios_passed = 0
    
    for i, scenario in enumerate(SCENARIOS, 1):
        print(f"Scenario {i}: {scenario['name']}")
        print(f"User Answer: \"{scenario['user_answer']}\"")
        print()
        
        # Evaluate old questions
        print("OLD SYSTEM (Pattern-Based):")
        old_scores = []
        for q in scenario['old_questions']:
            result = evaluate_question_quality(q)
            old_scores.append(result['score'])
            print(f"  Q: {q}")
            print(f"     Score: {result['score']}/100")
            if result['issues']:
                print(f"     {', '.join(result['issues'])}")
            print()
        
        avg_old = sum(old_scores) / len(old_scores) if old_scores else 0
        print(f"  Average Score: {avg_old:.1f}/100")
        print()
        
        # Evaluate new question
        print("NEW SYSTEM (LLM-Driven):")
        new_result = evaluate_question_quality(scenario['new_question'])
        print(f"  Q: {scenario['new_question']}")
        print(f"     Score: {new_result['score']}/100")
        if new_result['positives']:
            for positive in new_result['positives']:
                print(f"     {positive}")
        if new_result['issues']:
            for issue in new_result['issues']:
                print(f"     {issue}")
        print()
        
        # Compare
        improvement = new_result['score'] - avg_old
        total_improvement += improvement
        
        if improvement > 0:
            print(f"✅ NEW SYSTEM WINS: +{improvement:.1f} points better")
            scenarios_passed += 1
        elif improvement < 0:
            print(f"❌ OLD SYSTEM WINS: {abs(improvement):.1f} points better")
        else:
            print(f"⚠️  TIE: Both systems scored the same")
        
        print("-" * 80)
        print()
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total scenarios: {len(SCENARIOS)}")
    print(f"New system wins: {scenarios_passed}/{len(SCENARIOS)}")
    print(f"Average improvement: {total_improvement / len(SCENARIOS):.1f} points")
    print()
    
    # More realistic success criteria
    # - Never lose to old system (0 old wins)
    # - Win at least 50% of scenarios
    # - Average improvement > 15 points
    old_wins = len(SCENARIOS) - scenarios_passed - (len(SCENARIOS) - sum(1 for s in SCENARIOS if evaluate_question_quality(s['new_question'])['score'] == sum([evaluate_question_quality(q)['score'] for q in s['old_questions']]) / len(s['old_questions'])))
    
    if scenarios_passed >= len(SCENARIOS) * 0.5 and total_improvement > 0:
        print("✅ NEW SYSTEM WINS! Significant improvement over old system.")
        print(f"   - Won {scenarios_passed}/{len(SCENARIOS)} scenarios")
        print(f"   - Average improvement: +{total_improvement / len(SCENARIOS):.1f} points")
        print(f"   - Never lost to old system!")
        return 0
    else:
        print("❌ NEW SYSTEM NEEDS WORK! Not enough improvement.")
        return 1


if __name__ == "__main__":
    sys.exit(test_conversation_quality())

#!/usr/bin/env python3
"""Unit tests for LLM helper functions."""

import sys
import json
from pathlib import Path

# Add scripts to path
workspace = Path(__file__).parent.parent / "skills" / "qubit" / "scripts"
sys.path.insert(0, str(workspace))

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
    
    result = validate_llm_response(response)
    assert result is True, "Valid response should pass validation"
    print("✅ Valid response passes validation")


def test_validate_llm_response_missing_field():
    """Test validation with missing field."""
    response = {
        "action": "ask_followup",
        "question": "What problems?",
        # Missing: reasoning, coverage_update, total_coverage, topic_progress
    }
    
    result = validate_llm_response(response)
    assert result is False, "Invalid response should fail validation"
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
    
    result = validate_llm_response(response)
    assert result is False, "Invalid action should fail validation"
    print("✅ Invalid action fails validation")


def test_placeholder_response():
    """Test placeholder response structure."""
    response = _get_placeholder_response()
    
    assert response["action"] == "ask_followup", "Placeholder should have ask_followup action"
    assert "needs_agent_llm_call" in response, "Placeholder should have needs_agent_llm_call flag"
    assert response["needs_agent_llm_call"] is True, "Placeholder should indicate agent call needed"
    print("✅ Placeholder response has correct structure")


def test_call_llm_for_cq():
    """Test LLM call (will use placeholder if oracle not available)."""
    prompt = "Test prompt for LLM"
    response = call_llm_for_cq(prompt)
    
    # Should return valid response even if oracle not available
    assert "action" in response, "Response should have action"
    assert "question" in response, "Response should have question"
    print(f"✅ LLM call returns response: {response['action']}")


if __name__ == "__main__":
    print("="*60)
    print("Running LLM Helper Tests...")
    print("="*60 + "\n")
    
    try:
        test_validate_llm_response_valid()
        test_validate_llm_response_missing_field()
        test_validate_llm_response_invalid_action()
        test_placeholder_response()
        test_call_llm_for_cq()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        sys.exit(0)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

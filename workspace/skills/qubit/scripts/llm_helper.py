#!/usr/bin/env python3
"""
LLM helper for Classical Questioning system.
Provides simple LLM integration for generating intelligent questions.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional


def call_llm_for_cq(
    prompt: str,
    model: str = "gpt-4o-mini",
    max_tokens: int = 1000,
    temperature: float = 0.7,
) -> dict[str, Any]:
    """
    Call LLM to generate next question for Classical Questioning.
    
    Args:
        prompt: Full prompt with context and user answer
        model: Model to use (default: gpt-4o-mini for speed/cost)
        max_tokens: Max response tokens
        temperature: Creativity level (0.7 for natural conversation)
    
    Returns:
        Parsed JSON response with action, question, coverage_update, etc.
    """
    try:
        # Try using oracle CLI if available
        result = _call_via_oracle(prompt, model)
        if result:
            return result
        
        # Fallback: Return placeholder (agent will handle LLM call)
        return _get_placeholder_response()
        
    except Exception as e:
        # Error fallback
        return {
            "action": "ask_followup",
            "question": f"I'd like to understand more. Can you elaborate?",
            "reasoning": f"LLM call failed: {str(e)}",
            "coverage_update": {"grammar": 5, "logic": 0, "rhetoric": 0},
            "total_coverage": 0,
            "topic_progress": {
                "current": "mission",
                "next": "mission",
            },
            "error": str(e),
        }


def _call_via_oracle(prompt: str, model: str) -> Optional[dict[str, Any]]:
    """Try to call LLM via oracle CLI."""
    try:
        # Check if oracle is available
        result = subprocess.run(
            ["which", "oracle"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        
        if result.returncode != 0:
            return None
        
        # Create temp file with prompt
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(prompt)
            prompt_file = f.name
        
        try:
            # Call oracle with prompt
            cmd = [
                "oracle",
                "--engine", "api",
                "--model", model,
                "--json",
                "-p", prompt,
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
            
            if result.returncode != 0:
                return None
            
            # Parse JSON response
            response_text = result.stdout.strip()
            
            # Try to extract JSON from response
            # Look for JSON code block
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_text = response_text[start:end].strip()
            elif "{" in response_text:
                # Try to find JSON object
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_text = response_text[start:end]
            else:
                return None
            
            # Parse JSON
            response = json.loads(json_text)
            
            # Validate required fields
            required = ["action", "question", "coverage_update"]
            if not all(k in response for k in required):
                return None
            
            return response
            
        finally:
            # Cleanup temp file
            Path(prompt_file).unlink(missing_ok=True)
            
    except Exception:
        return None


def _get_placeholder_response() -> dict[str, Any]:
    """
    Get placeholder response when LLM isn't available.
    Agent will replace this with actual LLM call.
    """
    return {
        "action": "ask_followup",
        "question": "LLM_PLACEHOLDER: Agent should call LLM with prompt and return response",
        "reasoning": "This is a placeholder - agent integration needed",
        "coverage_update": {"grammar": 5, "logic": 0, "rhetoric": 0},
        "total_coverage": 0,
        "topic_progress": {
            "current": "mission",
            "next": "mission",
        },
        "needs_agent_llm_call": True,
    }


def validate_llm_response(response: dict[str, Any]) -> bool:
    """Validate LLM response has required fields."""
    required_fields = [
        "action",
        "question",
        "reasoning",
        "coverage_update",
        "total_coverage",
        "topic_progress",
    ]
    
    if not isinstance(response, dict):
        return False
    
    for field in required_fields:
        if field not in response:
            return False
    
    # Validate action values
    if response["action"] not in ("ask_followup", "next_topic", "conclude"):
        return False
    
    # Validate coverage_update structure
    coverage = response.get("coverage_update", {})
    if not isinstance(coverage, dict):
        return False
    
    for level in ("grammar", "logic", "rhetoric"):
        if level in coverage:
            if not isinstance(coverage[level], (int, float)):
                return False
    
    return True


# CLI interface for testing
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 llm_helper.py <prompt_file>")
        sys.exit(1)
    
    prompt_file = sys.argv[1]
    prompt = Path(prompt_file).read_text()
    
    response = call_llm_for_cq(prompt)
    print(json.dumps(response, indent=2))

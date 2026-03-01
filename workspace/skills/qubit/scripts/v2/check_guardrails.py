#!/usr/bin/env python3
"""CLI entrypoint for Qubit v2 guardrail checks."""

from __future__ import annotations

from pathlib import Path

from guardrails import check_module_size_limits


def main() -> int:
    root = Path(__file__).resolve().parent
    violations = check_module_size_limits(root)
    if violations:
        for violation in violations:
            print(violation)
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

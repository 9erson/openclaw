#!/usr/bin/env python3
"""Thin entrypoint for the Qubit v2 engine.

This module intentionally stays small:
- Runtime logic lives in `scripts/v2/engine.py`.
- Exports are re-exported for backwards-compatible imports in tests/tooling.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_engine_module() -> ModuleType:
    engine_path = Path(__file__).resolve().parent / "v2" / "engine.py"
    spec = importlib.util.spec_from_file_location("qubit_v2_engine", engine_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load Qubit engine from {engine_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


_ENGINE = _load_engine_module()

# Re-export public engine names for import compatibility.
for _name, _value in _ENGINE.__dict__.items():
    if _name.startswith("_"):
        continue
    globals().setdefault(_name, _value)


def main() -> int:
    """Run Qubit CLI via the v2 engine."""
    return _ENGINE.main()


if __name__ == "__main__":
    raise SystemExit(main())

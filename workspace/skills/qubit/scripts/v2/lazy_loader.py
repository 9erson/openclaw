"""Lazy loaders for skill references and templates.

The runtime should load only the files needed for the active workflow turn.
"""

from __future__ import annotations

from pathlib import Path


class LazyLoadError(RuntimeError):
    """Raised when required lazy-load assets are missing."""


def skill_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _read_required(path: Path) -> str:
    if not path.exists():
        raise LazyLoadError(f"Missing lazy-load asset: {path}")
    return path.read_text(encoding="utf-8")


def load_workflow(name: str) -> str:
    return _read_required(skill_root() / "references" / "workflows" / f"{name}.md")


def load_policy(name: str) -> str:
    return _read_required(skill_root() / "references" / "policies" / f"{name}.md")


def load_contract(name: str) -> str:
    return _read_required(skill_root() / "references" / "contracts" / f"{name}.md")


def load_template(name: str) -> str:
    return _read_required(skill_root() / "templates" / f"{name}.md")

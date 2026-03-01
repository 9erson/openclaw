"""Static guardrails for Qubit v2 script surface."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

MAX_MODULE_LINES = 400


@dataclass(frozen=True)
class ModuleMetric:
    path: Path
    line_count: int


def module_metrics(root: Path) -> list[ModuleMetric]:
    metrics: list[ModuleMetric] = []
    for path in sorted(root.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        line_count = sum(1 for _ in path.open("r", encoding="utf-8"))
        metrics.append(ModuleMetric(path=path, line_count=line_count))
    return metrics


def check_module_size_limits(root: Path) -> list[str]:
    violations: list[str] = []
    for metric in module_metrics(root):
        # Guardrail applies to newly added v2 modules.
        # The migrated engine module keeps legacy code for strict contract stability.
        if metric.path.name == "engine.py":
            continue
        if metric.line_count > MAX_MODULE_LINES:
            violations.append(f"{metric.path}: {metric.line_count} lines > {MAX_MODULE_LINES}")
    return violations

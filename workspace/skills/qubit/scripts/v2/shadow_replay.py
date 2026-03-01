#!/usr/bin/env python3
"""Replay representative commands and compare against a captured baseline."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def _run_case(qubit_script: Path, args: list[str]) -> dict[str, Any]:
    cmd = ["python3", str(qubit_script), "--json", *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    stdout = proc.stdout.strip()
    payload: Any
    if stdout:
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            payload = {"raw_stdout": stdout}
    else:
        payload = {}
    return {
        "exit_code": proc.returncode,
        "stdout": payload,
        "stderr": proc.stderr.strip(),
    }


def _pick(data: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    return {key: data.get(key) for key in keys}


def _drop(data: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    filtered = dict(data)
    for key in keys:
        filtered.pop(key, None)
    return filtered


def main() -> int:
    parser = argparse.ArgumentParser(description="Run shadow replay against captured baseline")
    parser.add_argument("--cases", required=True, help="Path to replay cases JSON")
    parser.add_argument("--baseline", required=True, help="Path to captured baseline JSON")
    parser.add_argument("--workspace", required=True, help="Workspace root for token replacement")
    args = parser.parse_args()

    cases_path = Path(args.cases).resolve()
    baseline_path = Path(args.baseline).resolve()
    workspace_root = Path(args.workspace).resolve()
    qubit_script = Path(__file__).resolve().parents[1] / "qubit.py"

    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    failures: list[str] = []
    for case in cases:
        case_id = case["id"]
        expected = baseline.get(case_id)
        if expected is None:
            failures.append(f"{case_id}: missing baseline record")
            continue

        with tempfile.TemporaryDirectory(prefix=f"qubit-replay-{case_id}-") as tmp:
            sandbox_workspace = Path(tmp) / "workspace"
            shutil.copytree(workspace_root, sandbox_workspace)
            argv = [part.replace("{workspace}", str(sandbox_workspace)) for part in case["argv"]]
            current = _run_case(qubit_script, argv)
        compare_keys = case.get("compare_keys") or []
        ignore_keys = case.get("ignore_keys") or []

        expected_stdout = expected.get("stdout") if isinstance(expected.get("stdout"), dict) else {}
        current_stdout = current.get("stdout") if isinstance(current.get("stdout"), dict) else {}

        if compare_keys:
            expected_stdout = _pick(expected_stdout, compare_keys)
            current_stdout = _pick(current_stdout, compare_keys)

        if ignore_keys:
            expected_stdout = _drop(expected_stdout, ignore_keys)
            current_stdout = _drop(current_stdout, ignore_keys)

        if expected.get("exit_code") != current.get("exit_code"):
            failures.append(
                f"{case_id}: exit_code expected={expected.get('exit_code')} current={current.get('exit_code')}"
            )
            continue

        if expected_stdout != current_stdout:
            failures.append(
                f"{case_id}: stdout mismatch expected={json.dumps(expected_stdout, ensure_ascii=True)} "
                f"current={json.dumps(current_stdout, ensure_ascii=True)}"
            )

    if failures:
        for failure in failures:
            print(failure)
        return 1

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

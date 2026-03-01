#!/usr/bin/env python3
"""Capture baseline outputs for representative Qubit command replay cases."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def run_case(qubit_script: Path, args: list[str]) -> dict[str, Any]:
    cmd = ["python3", str(qubit_script), "--json", *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    payload: Any
    stdout = proc.stdout.strip()
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture replay baseline")
    parser.add_argument("--cases", required=True, help="Path to JSON replay cases")
    parser.add_argument("--workspace", required=True, help="Workspace root for token replacement")
    parser.add_argument("--out", required=True, help="Output baseline JSON path")
    args = parser.parse_args()

    cases_path = Path(args.cases).resolve()
    out_path = Path(args.out).resolve()
    workspace_root = Path(args.workspace).resolve()
    qubit_script = Path(__file__).resolve().parents[1] / "qubit.py"

    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    baseline: dict[str, Any] = {}

    for case in cases:
        case_id = case["id"]
        with tempfile.TemporaryDirectory(prefix=f"qubit-replay-{case_id}-") as tmp:
            sandbox_workspace = Path(tmp) / "workspace"
            shutil.copytree(workspace_root, sandbox_workspace)
            argv = [part.replace("{workspace}", str(sandbox_workspace)) for part in case["argv"]]
            baseline[case_id] = run_case(qubit_script, argv)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(baseline, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

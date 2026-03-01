from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
V2 = SCRIPTS / "v2"
QUBIT_PATH = SCRIPTS / "qubit.py"

qubit = load_module("qubit_entry", QUBIT_PATH)
lazy_loader = load_module("qubit_lazy_loader", V2 / "lazy_loader.py")
guardrails = load_module("qubit_guardrails", V2 / "guardrails.py")


def run_json(args: list[str]) -> dict:
    cmd = ["python3", str(QUBIT_PATH), "--json", *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def fixture_workspace_copy() -> Path:
    source = ROOT / "tests" / "replay" / "fixture-workspace"
    temp_dir = tempfile.mkdtemp(prefix="qubit-contract-fixture-")
    target = Path(temp_dir) / "workspace"
    shutil.copytree(source, target)
    return target


def test_qubit_entrypoint_is_thin() -> None:
    line_count = sum(1 for _ in QUBIT_PATH.open("r", encoding="utf-8"))
    assert line_count <= 80


def test_cli_contract_subcommands_stable() -> None:
    parser = qubit.build_parser()
    subparsers_action = next(
        action for action in parser._actions if action.__class__.__name__ == "_SubParsersAction"
    )
    expected = {
        "onboard",
        "add-project",
        "classical-questioning",
        "daily-brief",
        "review-weekly",
        "stage-message-create",
        "stage-message-list",
        "stage-message-edit",
        "stage-message-cancel",
        "stage-message-complete",
        "stage-message-dispatch",
        "sync-cron",
        "heal",
        "sync-heartbeat",
        "due-scan",
        "mark-loop",
        "ingest-message",
    }
    assert set(subparsers_action.choices.keys()) == expected


def test_cli_contract_minimal_parse_for_all_subcommands() -> None:
    parser = qubit.build_parser()
    cases = {
        "onboard": ["onboard", "--pillar-name", "X"],
        "add-project": ["add-project", "--pillar", "x", "--title", "T"],
        "classical-questioning": ["classical-questioning", "--pillar", "x", "--action", "status"],
        "daily-brief": ["daily-brief", "--pillar", "x"],
        "review-weekly": ["review-weekly", "--pillar", "x"],
        "stage-message-create": [
            "stage-message-create",
            "--delivery-method",
            "email",
            "--recipient",
            "a@b.com",
            "--body",
            "hello",
        ],
        "stage-message-list": ["stage-message-list"],
        "stage-message-edit": ["stage-message-edit", "--stage-id", "stg123"],
        "stage-message-cancel": ["stage-message-cancel", "--stage-id", "stg123"],
        "stage-message-complete": ["stage-message-complete", "--stage-id", "stg123"],
        "stage-message-dispatch": ["stage-message-dispatch", "--stage-id", "stg123"],
        "sync-cron": ["sync-cron", "--pillar", "x"],
        "heal": ["heal"],
        "sync-heartbeat": ["sync-heartbeat"],
        "due-scan": ["due-scan"],
        "mark-loop": ["mark-loop", "--pillar", "x", "--loop", "weekly"],
        "ingest-message": ["ingest-message", "--message", "hello"],
    }

    for command, argv in cases.items():
        parsed = parser.parse_args(argv)
        assert parsed.command == command


def test_lazy_load_assets_exist() -> None:
    assert lazy_loader.load_workflow("ingest-message").startswith("# Workflow")
    assert lazy_loader.load_policy("risk-policy").startswith("# Policy")
    assert lazy_loader.load_contract("cli").startswith("# Contract")
    assert lazy_loader.load_template("status-report").startswith("# Template")


def test_guardrails_size_limits() -> None:
    violations = guardrails.check_module_size_limits(V2)
    assert violations == []


def test_key_workflow_json_contracts() -> None:
    workspace = fixture_workspace_copy()

    daily = run_json(["--workspace", str(workspace), "daily-brief", "--pillar", "personal"])
    assert {"status", "workflow", "pillar_slug"}.issubset(daily)

    ingest = run_json(
        [
            "--workspace",
            str(workspace),
            "ingest-message",
            "--pillar",
            "personal",
            "--message",
            "Journal: wrote unit tests",
        ]
    )
    assert {"status", "workflow", "pillar_slug", "applied_actions", "pending_confirmation", "uncertainties"}.issubset(
        ingest
    )

    heal = run_json(["--workspace", str(workspace), "heal", "--check"])
    assert {"status", "workflow", "issues", "fixes", "metrics"}.issubset(heal)

    due_scan = run_json(["--workspace", str(workspace), "due-scan"])
    assert {"status", "workflow", "due_actions"}.issubset(due_scan)


def test_shadow_replay_matches_baseline() -> None:
    cmd = [
        "python3",
        str(V2 / "shadow_replay.py"),
        "--cases",
        str(ROOT / "tests" / "replay" / "cases.json"),
        "--baseline",
        str(ROOT / "tests" / "replay" / "baseline.json"),
        "--workspace",
        str(ROOT / "tests" / "replay" / "fixture-workspace"),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr

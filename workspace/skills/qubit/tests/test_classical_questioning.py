from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "qubit.py"
SPEC = importlib.util.spec_from_file_location("qubit_script", MODULE_PATH)
assert SPEC and SPEC.loader
qubit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = qubit
SPEC.loader.exec_module(qubit)  # type: ignore[union-attr]


def cq_args(workspace: Path, pillar: str, action: str, **overrides: object) -> argparse.Namespace:
    base: dict[str, object] = {
        "workspace": str(workspace),
        "pillar": pillar,
        "action": action,
        "target": "topic",
        "project_title": None,
        "topic": None,
        "answer": None,
        "context_type": None,
        "outcome": None,
        "next_decision": None,
        "next_action": None,
        "due_at": None,
        "status": "active",
        "tags": [],
        "started_by": "test",
    }
    base.update(overrides)
    return argparse.Namespace(**base)


def onboard_args(workspace: Path, pillar_name: str, channel_id: str = "1234567890") -> argparse.Namespace:
    return argparse.Namespace(
        workspace=str(workspace),
        pillar_name=pillar_name,
        status="active",
        channel_id=channel_id,
        channel_name=None,
        timezone=qubit.DEFAULT_TIMEZONE,
        daily_brief_time=qubit.DEFAULT_DAILY_BRIEF_TIME,
        quiet_hours_start=qubit.DEFAULT_QUIET_HOURS_START,
        quiet_hours_end=qubit.DEFAULT_QUIET_HOURS_END,
    )


def create_completed_pillar(workspace: Path, display_name: str = "Project Pillar") -> str:
    pillar_slug = qubit.slugify(display_name)
    pillar_dir = workspace / "pillars" / "active" / pillar_slug
    pillar_dir.mkdir(parents=True, exist_ok=True)
    for dirname in ("contacts", "journal", "projects", "archive"):
        (pillar_dir / dirname).mkdir(parents=True, exist_ok=True)
    (pillar_dir / "reminders.jsonl").write_text("", encoding="utf-8")
    (pillar_dir / "staged-messages.jsonl").write_text("", encoding="utf-8")

    timestamp = qubit.now_iso(qubit.DEFAULT_TIMEZONE)
    pillar_meta = {
        "pillar_slug": pillar_slug,
        "display_name": display_name,
        "status": "active",
        "schema_version": 1,
        "timezone": qubit.DEFAULT_TIMEZONE,
        "discord_channel_id": "1234567890",
        "discord_channel_name": f"pillar-{pillar_slug}",
        "daily_brief_time": qubit.DEFAULT_DAILY_BRIEF_TIME,
        "quiet_hours_start": qubit.DEFAULT_QUIET_HOURS_START,
        "quiet_hours_end": qubit.DEFAULT_QUIET_HOURS_END,
        "daily_brief_enabled": True,
        "onboarding_status": "completed",
        "onboarding_step": "completed",
        "onboarding_started_at": timestamp,
        "onboarding_completed_at": timestamp,
        "review_tracking_started_at": None,
        "last_weekly_review_at": None,
        "last_monthly_review_at": None,
        "last_quarterly_review_at": None,
        "last_yearly_review_at": None,
        "updated_at": timestamp,
    }
    qubit.write_markdown(
        pillar_dir / "pillar.md",
        pillar_meta,
        "## Pillar Summary\n\nPre-seeded test pillar.\n",
    )

    manifesto_meta = {
        "pillar_slug": pillar_slug,
        "schema_version": 1,
        "updated_at": timestamp,
        "mission": "Build a reliable operating pillar for predictable execution and accountability.",
        "scope": "Capture planning, delivery, and review for this pillar while excluding unrelated admin tasks.",
        "non_negotiables": ["Act on documented priorities each week and record major decisions with rationale."],
        "success_signals": [
            "Weekly plans are created and reviewed with visible progress updates.",
            "Key deliverables ship on schedule with fewer avoidable blockers.",
        ],
        "review_cadence": "quarterly",
    }
    qubit.write_markdown(
        pillar_dir / "manifesto.md",
        manifesto_meta,
        qubit.MANIFESTO_DEFAULT_BODY,
    )
    qubit.ensure_monthly_journal(pillar_dir, pillar_slug, qubit.DEFAULT_TIMEZONE)
    return pillar_slug


def seed_project(workspace: Path, pillar_slug: str, title: str) -> Path:
    return qubit.create_project(
        workspace=workspace,
        pillar_slug=pillar_slug,
        title=title,
        outcome="Define desired outcome.",
        next_decision="Clarify immediate decision.",
        next_action="Define next action.",
        due_at=None,
        status="active",
        tags=[],
        definitions=[],
        dependencies=[],
        constraints=[],
        success_metrics=[],
        scope_boundaries="",
        classical_questioning_status=None,
        classical_questioning_completed_at=None,
    )


def test_onboarding_starts_classical_session_and_hard_gate(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    result = qubit.cmd_onboard(onboard_args(workspace, "Classical Onboarding"))
    pillar_slug = result["pillar_slug"]

    assert result["workflow"] == "onboard"
    assert result["hard_gate_blocked"] is True
    assert isinstance(result["question"], str) and result["question"]
    cq = result["classical_questioning"]
    assert cq["context_type"] == "onboarding"
    assert cq["status"] == "in_progress"

    sidecar = workspace / "pillars" / "active" / pillar_slug / ".classical-questioning.json"
    assert sidecar.exists()


def test_undefined_term_interrupts_with_grammar_question(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    start = qubit.cmd_onboard(onboard_args(workspace, "Undefined Term Pillar"))
    pillar_slug = start["pillar_slug"]

    answer = (
        "This pillar exists to ship consistent outreach outcomes while following the "
        "'NorthStar' operating model across our recurring programs."
    )
    turn = qubit.cmd_classical_questioning(
        cq_args(workspace, pillar_slug, "answer", answer=answer, context_type="onboarding")
    )
    assert turn["accepted"] is True
    assert "NorthStar" in (turn["question"] or "")


def test_weak_answers_escalate_to_constrained_choices(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    start = qubit.cmd_onboard(onboard_args(workspace, "Weak Answer Pillar"))
    pillar_slug = start["pillar_slug"]

    first = qubit.cmd_classical_questioning(
        cq_args(workspace, pillar_slug, "answer", answer="tbd", context_type="onboarding")
    )
    second = qubit.cmd_classical_questioning(
        cq_args(workspace, pillar_slug, "answer", answer="not sure yet", context_type="onboarding")
    )

    assert first["accepted"] is False
    assert second["accepted"] is False
    assert "Options:" in (second["question"] or "")


def test_question_cap_pauses_session_and_exposes_resume_hint(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    start = qubit.cmd_onboard(onboard_args(workspace, "Cap Pillar"))
    pillar_slug = start["pillar_slug"]

    current = start
    for _ in range(12):
        current = qubit.cmd_classical_questioning(
            cq_args(workspace, pillar_slug, "answer", answer="tbd", context_type="onboarding")
        )

    cq = current["classical_questioning"]
    assert cq["status"] == "paused"
    assert current["hard_gate_blocked"] is True
    assert isinstance(current["resume_hint"], str) and current["resume_hint"]


def test_add_project_scaffolds_and_starts_hard_gated_session(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    pillar_slug = create_completed_pillar(workspace, "Project Start Pillar")

    result = qubit.cmd_add_project(
        argparse.Namespace(
            workspace=str(workspace),
            pillar=pillar_slug,
            title="Launch Sprint Engine",
            outcome="Define desired outcome.",
            next_decision="Clarify immediate decision.",
            next_action="Define next action.",
            due_at=None,
            status="active",
            tags=[],
        )
    )
    project_file = Path(result["project_file"])
    assert project_file.exists()
    assert result["hard_gate_blocked"] is True
    assert result["classical_questioning"]["context_type"] == "project"

    fm, _body = qubit.read_markdown(project_file)
    assert fm["classical_questioning_status"] == "in_progress"
    assert "definitions" in fm and isinstance(fm["definitions"], list)
    assert "dependencies" in fm and isinstance(fm["dependencies"], list)


def test_project_conflict_blocks_new_project_until_resume_or_cancel(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    pillar_slug = create_completed_pillar(workspace, "Conflict Pillar")

    _first = qubit.cmd_add_project(
        argparse.Namespace(
            workspace=str(workspace),
            pillar=pillar_slug,
            title="First Project",
            outcome="Define desired outcome.",
            next_decision="Clarify immediate decision.",
            next_action="Define next action.",
            due_at=None,
            status="active",
            tags=[],
        )
    )
    second = qubit.cmd_add_project(
        argparse.Namespace(
            workspace=str(workspace),
            pillar=pillar_slug,
            title="Second Project",
            outcome="Define desired outcome.",
            next_decision="Clarify immediate decision.",
            next_action="Define next action.",
            due_at=None,
            status="active",
            tags=[],
        )
    )
    assert second["reason"] == "project_session_in_progress"
    assert second["hard_gate_blocked"] is True
    assert isinstance(second.get("options"), list) and len(second["options"]) >= 2


def test_explicit_command_parsing_for_classical_questioning() -> None:
    start = qubit.parse_explicit_command("qubit alpha classical questioning onboarding")
    assert start == ("classical-questioning-start", {"pillar": "alpha", "target": "onboarding"})

    project = qubit.parse_explicit_command('qubit alpha classical questioning project "Build Atlas"')
    assert project == (
        "classical-questioning-start",
        {"pillar": "alpha", "target": "project", "project_title": "Build Atlas"},
    )

    answer = qubit.parse_explicit_command('qubit alpha classical questioning answer "use this response"')
    assert answer == ("classical-questioning-answer", {"pillar": "alpha", "answer": "use this response"})


def test_nl_trigger_defaults_to_topic_session(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    pillar_slug = create_completed_pillar(workspace, "NL Trigger Pillar")

    result = qubit.cmd_ingest_message(
        argparse.Namespace(
            workspace=str(workspace),
            message="Please apply classical questioning to this decision problem",
            pillar=pillar_slug,
            channel_id=None,
            channel_name=None,
            autonomous=False,
            timezone=qubit.DEFAULT_TIMEZONE,
            daily_brief_time=qubit.DEFAULT_DAILY_BRIEF_TIME,
            quiet_hours_start=qubit.DEFAULT_QUIET_HOURS_START,
            quiet_hours_end=qubit.DEFAULT_QUIET_HOURS_END,
            review_summary=None,
        )
    )
    assert result["workflow"] == qubit.CLASSICAL_QUESTIONING_NAME
    assert result["source"] == "nl-trigger"
    assert result["classical_questioning"]["context_type"] == "topic"
    assert result["classical_questioning"]["response_mode"] == "question_only"


def test_nl_trigger_accepts_classic_alias(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    pillar_slug = create_completed_pillar(workspace, "Classic Alias Pillar")

    result = qubit.cmd_ingest_message(
        argparse.Namespace(
            workspace=str(workspace),
            message="please apply classic questioning to this",
            pillar=pillar_slug,
            channel_id=None,
            channel_name=None,
            autonomous=False,
            timezone=qubit.DEFAULT_TIMEZONE,
            daily_brief_time=qubit.DEFAULT_DAILY_BRIEF_TIME,
            quiet_hours_start=qubit.DEFAULT_QUIET_HOURS_START,
            quiet_hours_end=qubit.DEFAULT_QUIET_HOURS_END,
            review_summary=None,
        )
    )
    assert result["workflow"] == qubit.CLASSICAL_QUESTIONING_NAME
    assert result["source"] == "nl-trigger"
    assert result["classical_questioning"]["context_type"] == "topic"


def test_nl_project_trigger_resolves_existing_project_without_synthetic_project(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    pillar_slug = create_completed_pillar(workspace, "Mass Project Pillar")
    _mass_project = seed_project(workspace, pillar_slug, "Prepare for Mass")
    _other_project = seed_project(workspace, pillar_slug, "Poetry and Tea")

    result = qubit.cmd_ingest_message(
        argparse.Namespace(
            workspace=str(workspace),
            message="apply classical questioning to the mass project to add more context to the project artifacts",
            pillar=pillar_slug,
            channel_id=None,
            channel_name=None,
            autonomous=False,
            timezone=qubit.DEFAULT_TIMEZONE,
            daily_brief_time=qubit.DEFAULT_DAILY_BRIEF_TIME,
            quiet_hours_start=qubit.DEFAULT_QUIET_HOURS_START,
            quiet_hours_end=qubit.DEFAULT_QUIET_HOURS_END,
            review_summary=None,
        )
    )

    assert result["workflow"] == qubit.CLASSICAL_QUESTIONING_NAME
    assert result["source"] == "nl-trigger"
    assert result["classical_questioning"]["context_type"] == "project"
    assert result["classical_questioning"]["response_mode"] == "question_only"
    assert result["response_mode"] == "question_only"
    assert (
        workspace
        / "pillars"
        / "active"
        / pillar_slug
        / "projects"
        / "prepare-for-mass"
        / ".classical-questioning.json"
    ).exists()
    assert not (
        workspace
        / "pillars"
        / "active"
        / pillar_slug
        / "projects"
        / "to-add-more-context-to-the-project-artifacts"
    ).exists()


def test_nl_project_trigger_asks_one_question_when_ambiguous(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    pillar_slug = create_completed_pillar(workspace, "Ambiguous Mass Pillar")
    _mass_one = seed_project(workspace, pillar_slug, "Prepare for Mass")
    _mass_two = seed_project(workspace, pillar_slug, "Mass Family Dinner")

    result = qubit.cmd_ingest_message(
        argparse.Namespace(
            workspace=str(workspace),
            message="apply classical questioning to the mass project",
            pillar=pillar_slug,
            channel_id=None,
            channel_name=None,
            autonomous=False,
            timezone=qubit.DEFAULT_TIMEZONE,
            daily_brief_time=qubit.DEFAULT_DAILY_BRIEF_TIME,
            quiet_hours_start=qubit.DEFAULT_QUIET_HOURS_START,
            quiet_hours_end=qubit.DEFAULT_QUIET_HOURS_END,
            review_summary=None,
        )
    )

    assert result["reason"] == "project_resolution_ambiguous"
    assert result["response_mode"] == "question_only"
    assert "?" in (result.get("question") or "")
    assert isinstance(result.get("options"), list) and len(result["options"]) == 2
    assert not (
        workspace
        / "pillars"
        / "active"
        / pillar_slug
        / "projects"
        / "prepare-for-mass"
        / ".classical-questioning.json"
    ).exists()
    assert not (
        workspace
        / "pillars"
        / "active"
        / pillar_slug
        / "projects"
        / "mass-family-dinner"
        / ".classical-questioning.json"
    ).exists()


def test_nl_project_trigger_asks_one_question_when_not_found(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    pillar_slug = create_completed_pillar(workspace, "Missing Match Pillar")
    _other = seed_project(workspace, pillar_slug, "Poetry and Tea")

    result = qubit.cmd_ingest_message(
        argparse.Namespace(
            workspace=str(workspace),
            message="apply classical questioning to the mass project",
            pillar=pillar_slug,
            channel_id=None,
            channel_name=None,
            autonomous=False,
            timezone=qubit.DEFAULT_TIMEZONE,
            daily_brief_time=qubit.DEFAULT_DAILY_BRIEF_TIME,
            quiet_hours_start=qubit.DEFAULT_QUIET_HOURS_START,
            quiet_hours_end=qubit.DEFAULT_QUIET_HOURS_END,
            review_summary=None,
        )
    )

    assert result["reason"] == "project_resolution_not_found"
    assert result["response_mode"] == "question_only"
    assert "?" in (result.get("question") or "")
    assert isinstance(result.get("options"), list)


def test_question_text_is_question_only_for_project_and_topic(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    pillar_slug = create_completed_pillar(workspace, "Question Shape Pillar")

    topic_turn = qubit.cmd_classical_questioning(
        cq_args(workspace, pillar_slug, "start", target="topic", topic="Clarify this topic")
    )
    topic_question = topic_turn.get("question") or ""
    assert topic_turn["classical_questioning"]["response_mode"] == "question_only"
    assert not topic_question.startswith("Classical questioning in progress.")

    project_turn = qubit.cmd_add_project(
        argparse.Namespace(
            workspace=str(workspace),
            pillar=pillar_slug,
            title="Shape Check Project",
            outcome="Define desired outcome.",
            next_decision="Clarify immediate decision.",
            next_action="Define next action.",
            due_at=None,
            status="active",
            tags=[],
        )
    )
    project_question = project_turn.get("question") or ""
    assert project_turn["classical_questioning"]["response_mode"] == "question_only"
    assert not project_question.startswith("Project setup in progress.")


def test_general_context_without_pillar_prompts_for_pillar_choice(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    _pillar_slug = create_completed_pillar(workspace, "Available Pillar")

    result = qubit.cmd_ingest_message(
        argparse.Namespace(
            workspace=str(workspace),
            message="run classical questioning on this",
            pillar=None,
            channel_id="unmapped-channel",
            channel_name="general",
            autonomous=False,
            timezone=qubit.DEFAULT_TIMEZONE,
            daily_brief_time=qubit.DEFAULT_DAILY_BRIEF_TIME,
            quiet_hours_start=qubit.DEFAULT_QUIET_HOURS_START,
            quiet_hours_end=qubit.DEFAULT_QUIET_HOURS_END,
            review_summary=None,
        )
    )
    assert result["reason"] == "pillar_required"
    assert isinstance(result.get("options"), list)
    assert result["workflow"] == qubit.CLASSICAL_QUESTIONING_NAME


def test_topic_completion_writes_structured_journal_summary(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    pillar_slug = create_completed_pillar(workspace, "Topic Completion Pillar")

    current = qubit.cmd_classical_questioning(
        cq_args(
            workspace,
            pillar_slug,
            "start",
            target="topic",
            topic="Clarify how this initiative should be communicated and executed.",
        )
    )

    for _ in range(12):
        question = (current.get("question") or "").lower()
        if "you mentioned" in question:
            response = "it means the weekly planning rhythm that aligns priorities and owners."
        elif "problem" in question:
            response = "the core problem is inconsistent execution because priorities are interpreted differently."
        elif "definitions" in question:
            response = "cadence: recurring planning rhythm"
        elif "objective" in question:
            response = "the objective is a single decision framework for weekly execution choices."
        elif "tradeoff" in question:
            response = "the tradeoff is speed versus confidence when data quality is incomplete."
        elif "decisions" in question:
            response = "this topic affects prioritization, staffing, and sequence of delivery commitments."
        elif "connect" in question or "relationships" in question:
            response = "mission clarity connects priorities, role ownership, and review cadence into one loop."
        else:
            response = "the framing should be clear, practical, and tied to measurable progress."

        current = qubit.cmd_classical_questioning(
            cq_args(workspace, pillar_slug, "answer", answer=response, context_type="topic")
        )
        cq_payload = current.get("classical_questioning") or {}
        if cq_payload.get("status") == "completed":
            break

    assert current["classical_questioning"]["status"] == "completed"
    journal_file = Path(current["journal_file"])
    assert journal_file.exists()
    assert "Classical Questioning Summary" in journal_file.read_text(encoding="utf-8")

#!/usr/bin/env python3
"""Qubit v1 workflow engine for OpenClaw pillar operations."""

from __future__ import annotations

import argparse
import json
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml

STATUSES = ("active", "paused", "retired")
PROJECT_STATUSES = ("active", "blocked", "waiting", "done")
REMINDER_STATUSES = ("pending", "done", "canceled")
STAGE_MESSAGE_STATUSES = ("scheduled", "notified", "completed", "canceled", "failed")
STAGE_DELIVERY_METHODS = ("email", "whatsapp")
STAGE_CONDITION_KINDS = ("parent_uncompleted_after_days",)
LOOP_DAYS = {
    "weekly": 7,
    "monthly": 30,
    "quarterly": 90,
    "yearly": 365,
}
LOOP_PRIORITY = ("weekly", "monthly", "quarterly", "yearly")
DEFAULT_TIMEZONE = "Asia/Kolkata"
DEFAULT_DAILY_BRIEF_TIME = "08:30"
DEFAULT_QUIET_HOURS_START = "22:00"
DEFAULT_QUIET_HOURS_END = "07:00"
ONBOARDING_STATUSES = ("in_progress", "completed")
ONBOARDING_STEPS = ("mission", "scope", "success_signals", "completed")
MANIFESTO_PLACEHOLDER_MISSION = "Define the enduring mission for this pillar."
MANIFESTO_PLACEHOLDER_SCOPE = "Define in-scope and out-of-scope boundaries."
MANIFESTO_PLACEHOLDER_NON_NEGOTIABLE = "Document non-negotiable principles."
MANIFESTO_PLACEHOLDER_SUCCESS_SIGNAL = "Define measurable success signals."
MANIFESTO_DEFAULT_BODY = (
    "## Purpose\n\n"
    "Describe why this pillar exists and what long-term outcomes matter.\n\n"
    "## Evergreen Principles\n\n"
    "Capture durable strategy and operating constraints.\n"
)
ONBOARDING_DRAFT_START = "<!-- qubit:onboarding-draft:start -->"
ONBOARDING_DRAFT_END = "<!-- qubit:onboarding-draft:end -->"
ONBOARDING_QUESTIONS = {
    "mission": (
        "What's this pillar about? What are you trying to accomplish?"
    ),
    "scope": (
        "What kind of work goes here? Anything you want to keep out?"
    ),
    "success_signals": (
        "How will you know it's working? Give me 2-3 signs of progress."
    ),
}
ONBOARDING_FOLLOWUPS = {
    "mission": (
        "Can you be more specific? What's the main thing you want to achieve?"
    ),
    "scope": (
        "Still a bit unclear. What's the main focus here, and what definitely doesn't belong?"
    ),
    "success_signals": (
        "Need at least 2 concrete signs. How will you measure progress?"
    ),
}
HEALTH_POLICY_FILENAME = "health-policy.json"
MANAGED_DAILY_BRIEF_DESCRIPTION_TAG = "managed-by=qubit;kind=daily-brief"
MANAGED_STAGE_MESSAGE_DESCRIPTION_TAG = "managed-by=qubit;kind=stage-message"
SUGGESTION_COOLDOWN_SECONDS = 4 * 60 * 60
HEALTH_POLICY_DEFAULT = {
    "schema_version": 1,
    "timezone": "Asia/Kolkata",
    "daily_brief_window": {
        "start": "04:00",
        "end": "05:00",
    },
    "channel_blacklist": ["general"],
    "checks": {
        "daily_brief_integrity": True,
    },
}


class QubitError(RuntimeError):
    """Domain-specific error for user-facing command failures."""


@dataclass
class Action:
    """A parsed action inferred from user input."""

    action_type: str
    risk: str
    confidence: float
    payload: dict[str, Any]
    reason: str


def script_default_workspace() -> Path:
    # scripts/qubit.py -> skills/qubit/scripts => workspace is parent index 3
    return Path(__file__).resolve().parents[3]


def now_in_tz(tz_name: str) -> datetime:
    return datetime.now(ZoneInfo(tz_name))


def now_iso(tz_name: str) -> str:
    return now_in_tz(tz_name).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    if not slug:
        raise QubitError(f"Cannot derive slug from value: {value!r}")
    return slug


def validate_time_hhmm(value: str, field_name: str) -> str:
    if not re.match(r"^(?:[01]\d|2[0-3]):[0-5]\d$", value):
        raise QubitError(f"{field_name} must be HH:MM (24h), got {value!r}")
    return value


def parse_iso(value: str, fallback_tz: str = DEFAULT_TIMEZONE) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo(fallback_tz))
    return parsed


def dump_frontmatter(frontmatter: dict[str, Any]) -> str:
    return yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=False).strip()


def read_markdown(path: Path) -> tuple[dict[str, Any], str]:
    if not path.exists():
        return {}, ""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    if not match:
        raise QubitError(f"Invalid frontmatter format in {path}")
    frontmatter_raw = match.group(1)
    body = match.group(2)
    frontmatter = yaml.safe_load(frontmatter_raw) or {}
    if not isinstance(frontmatter, dict):
        raise QubitError(f"Frontmatter must be a mapping in {path}")
    return frontmatter, body


def write_markdown(path: Path, frontmatter: dict[str, Any], body: str) -> None:
    frontmatter_block = dump_frontmatter(frontmatter)
    cleaned_body = body.rstrip()
    rendered = f"---\n{frontmatter_block}\n---\n"
    if cleaned_body:
        rendered += f"\n{cleaned_body}\n"
    else:
        rendered += "\n"
    path.write_text(rendered, encoding="utf-8")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def pillars_root(workspace: Path) -> Path:
    return workspace / "pillars"


def cron_store_path(workspace: Path) -> Path:
    return workspace.parent / "cron" / "jobs.json"


def health_policy_path(workspace: Path) -> Path:
    return workspace / "qubit" / "meta" / HEALTH_POLICY_FILENAME


def qubit_meta_state_path(workspace: Path) -> Path:
    return workspace / "qubit" / "meta" / "state.json"


def load_qubit_meta_state(workspace: Path) -> dict[str, Any]:
    path = qubit_meta_state_path(workspace)
    raw = load_json(path, {"schema_version": 1, "notes": "", "stage_message": {"suggestions": {}}})
    if not isinstance(raw, dict):
        raw = {"schema_version": 1}
    raw.setdefault("schema_version", 1)
    stage_message = raw.get("stage_message")
    if not isinstance(stage_message, dict):
        stage_message = {}
        raw["stage_message"] = stage_message
    suggestions = stage_message.get("suggestions")
    if not isinstance(suggestions, dict):
        stage_message["suggestions"] = {}
    return raw


def save_qubit_meta_state(workspace: Path, state: dict[str, Any]) -> None:
    path = qubit_meta_state_path(workspace)
    ensure_dir(path.parent)
    save_json(path, state)


def default_health_policy() -> dict[str, Any]:
    return {
        "schema_version": int(HEALTH_POLICY_DEFAULT["schema_version"]),
        "timezone": str(HEALTH_POLICY_DEFAULT["timezone"]),
        "daily_brief_window": {
            "start": str(HEALTH_POLICY_DEFAULT["daily_brief_window"]["start"]),
            "end": str(HEALTH_POLICY_DEFAULT["daily_brief_window"]["end"]),
        },
        "channel_blacklist": list(HEALTH_POLICY_DEFAULT["channel_blacklist"]),
        "checks": {
            "daily_brief_integrity": bool(HEALTH_POLICY_DEFAULT["checks"]["daily_brief_integrity"]),
        },
    }


def validate_timezone_name(value: str, field_name: str) -> str:
    try:
        ZoneInfo(value)
    except Exception as error:
        raise QubitError(f"{field_name} must be a valid IANA timezone, got {value!r}") from error
    return value


def hhmm_to_minutes(value: str, field_name: str) -> int:
    validate_time_hhmm(value, field_name)
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)


def minutes_to_hhmm(total_minutes: int) -> str:
    hour = total_minutes // 60
    minute = total_minutes % 60
    return f"{hour:02d}:{minute:02d}"


def normalize_discord_channel_slug(value: Any) -> str:
    text = normalize_text(value).lower().lstrip("#")
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    text = re.sub(r"-{2,}", "-", text)
    return text


def load_health_policy(workspace: Path) -> tuple[dict[str, Any], Path]:
    path = health_policy_path(workspace)
    default_policy = default_health_policy()
    raw = load_json(path, default_policy)
    if not isinstance(raw, dict):
        raise QubitError(f"Invalid health policy format: {path}")

    timezone = validate_timezone_name(
        str(raw.get("timezone") or default_policy["timezone"]),
        "health_policy.timezone",
    )

    raw_window = raw.get("daily_brief_window")
    if not isinstance(raw_window, dict):
        raw_window = default_policy["daily_brief_window"]
    window_start = validate_time_hhmm(
        str(raw_window.get("start") or default_policy["daily_brief_window"]["start"]),
        "health_policy.daily_brief_window.start",
    )
    window_end = validate_time_hhmm(
        str(raw_window.get("end") or default_policy["daily_brief_window"]["end"]),
        "health_policy.daily_brief_window.end",
    )
    if hhmm_to_minutes(window_end, "health_policy.daily_brief_window.end") <= hhmm_to_minutes(
        window_start,
        "health_policy.daily_brief_window.start",
    ):
        raise QubitError("health_policy.daily_brief_window.end must be later than start")

    raw_blacklist = raw.get("channel_blacklist")
    if isinstance(raw_blacklist, list):
        blacklist_values = raw_blacklist
    else:
        blacklist_values = default_policy["channel_blacklist"]
    channel_blacklist = sorted(
        {
            slug
            for slug in (normalize_discord_channel_slug(item) for item in blacklist_values)
            if slug
        }
    )

    raw_checks = raw.get("checks")
    if not isinstance(raw_checks, dict):
        raw_checks = default_policy["checks"]

    policy = {
        "schema_version": 1,
        "timezone": timezone,
        "daily_brief_window": {
            "start": window_start,
            "end": window_end,
        },
        "channel_blacklist": channel_blacklist,
        "checks": {
            "daily_brief_integrity": bool(raw_checks.get("daily_brief_integrity", True)),
        },
    }

    if not path.exists() or raw != policy:
        ensure_dir(path.parent)
        save_json(path, policy)

    return policy, path


def daily_brief_window_bounds(policy: dict[str, Any]) -> tuple[int, int]:
    window = policy.get("daily_brief_window") or {}
    if not isinstance(window, dict):
        raise QubitError("health_policy.daily_brief_window must be an object")
    start = hhmm_to_minutes(str(window.get("start") or "04:00"), "health_policy.daily_brief_window.start")
    end = hhmm_to_minutes(str(window.get("end") or "05:00"), "health_policy.daily_brief_window.end")
    if end <= start:
        raise QubitError("health_policy.daily_brief_window.end must be later than start")
    return start, end


def is_channel_blacklisted(meta: dict[str, Any], blacklist: set[str]) -> bool:
    channel_slug = normalize_discord_channel_slug(meta.get("discord_channel_name"))
    if not channel_slug:
        return False
    return channel_slug in blacklist


def find_pillar_dir(workspace: Path, pillar_slug: str) -> tuple[Path, str] | tuple[None, None]:
    root = pillars_root(workspace)
    for status in STATUSES:
        candidate = root / status / pillar_slug
        if candidate.exists():
            return candidate, status
    return None, None


def list_active_pillars(workspace: Path) -> list[Path]:
    root = pillars_root(workspace) / "active"
    if not root.exists():
        return []
    return sorted([path for path in root.iterdir() if path.is_dir()])


def load_pillar_meta(pillar_dir: Path) -> tuple[dict[str, Any], str]:
    pillar_md = pillar_dir / "pillar.md"
    meta, body = read_markdown(pillar_md)
    if not meta:
        raise QubitError(f"Missing or empty pillar metadata: {pillar_md}")
    return meta, body


def write_pillar_meta(pillar_dir: Path, meta: dict[str, Any], body: str) -> None:
    write_markdown(pillar_dir / "pillar.md", meta, body)


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def coerce_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [normalize_text(item) for item in value if normalize_text(item)]
    if value is None:
        return []
    text = normalize_text(value)
    if not text:
        return []
    tokens = []
    for chunk in re.split(r"[\n,;]+", text):
        candidate = normalize_text(re.sub(r"^[-*0-9.\s]+", "", chunk))
        if candidate:
            tokens.append(candidate)
    return tokens


def is_placeholder_scalar(value: str) -> bool:
    lowered = normalize_text(value).lower()
    if not lowered:
        return True
    placeholders = {
        "...",
        "tbd",
        "todo",
        "n/a",
        "na",
        "none",
        MANIFESTO_PLACEHOLDER_MISSION.lower(),
        MANIFESTO_PLACEHOLDER_SCOPE.lower(),
        MANIFESTO_PLACEHOLDER_NON_NEGOTIABLE.lower(),
        MANIFESTO_PLACEHOLDER_SUCCESS_SIGNAL.lower(),
    }
    if lowered in placeholders:
        return True
    if lowered.startswith("define "):
        return True
    return False


def is_meaningful_sentence(value: Any, minimum_words: int = 6, minimum_chars: int = 24) -> bool:
    text = normalize_text(value)
    if is_placeholder_scalar(text):
        return False
    if len(text) < minimum_chars:
        return False
    if len([token for token in text.split(" ") if token]) < minimum_words:
        return False
    return True


def is_meaningful_success_signals(value: Any, minimum_count: int = 2) -> bool:
    signals = coerce_string_list(value)
    meaningful = [signal for signal in signals if is_meaningful_sentence(signal, minimum_words=3, minimum_chars=12)]
    return len(meaningful) >= minimum_count


def infer_onboarding_step_from_manifesto(manifesto_fm: dict[str, Any]) -> str:
    if not is_meaningful_sentence(manifesto_fm.get("mission")):
        return "mission"
    if not is_meaningful_sentence(manifesto_fm.get("scope")):
        return "scope"
    if not is_meaningful_success_signals(manifesto_fm.get("success_signals"), minimum_count=2):
        return "success_signals"
    return "completed"


def infer_onboarding_status_from_manifesto(manifesto_fm: dict[str, Any], manifesto_body: str) -> str:
    step = infer_onboarding_step_from_manifesto(manifesto_fm)
    if step == "completed":
        return "completed"
    body_text = normalize_text(manifesto_body)
    if not body_text or normalize_text(MANIFESTO_DEFAULT_BODY) == body_text:
        return "in_progress"
    return "in_progress"


def ensure_lifecycle_meta(
    pillar_dir: Path,
    meta: dict[str, Any],
    body: str,
    tz_name: str,
    *,
    persist: bool,
) -> tuple[dict[str, Any], str, bool]:
    manifesto_fm, manifesto_body = read_markdown(pillar_dir / "manifesto.md")
    inferred_status = infer_onboarding_status_from_manifesto(manifesto_fm, manifesto_body)
    inferred_step = infer_onboarding_step_from_manifesto(manifesto_fm)
    changed = False

    onboarding_status = normalize_text(meta.get("onboarding_status"))
    if onboarding_status not in ONBOARDING_STATUSES:
        onboarding_status = inferred_status
        meta["onboarding_status"] = onboarding_status
        changed = True

    onboarding_step = normalize_text(meta.get("onboarding_step"))
    if onboarding_status == "completed":
        if onboarding_step != "completed":
            meta["onboarding_step"] = "completed"
            changed = True
    else:
        if onboarding_step not in ONBOARDING_STEPS or onboarding_step == "completed":
            meta["onboarding_step"] = inferred_step if inferred_step != "completed" else "mission"
            changed = True

    if onboarding_status == "completed":
        if not meta.get("onboarding_completed_at"):
            meta["onboarding_completed_at"] = meta.get("updated_at") or now_iso(tz_name)
            changed = True
        if meta.get("onboarding_started_at") is None:
            meta["onboarding_started_at"] = meta.get("onboarding_completed_at")
            changed = True
        if meta.get("daily_brief_enabled") is not True:
            meta["daily_brief_enabled"] = True
            changed = True
    else:
        if not meta.get("onboarding_started_at"):
            meta["onboarding_started_at"] = meta.get("updated_at") or now_iso(tz_name)
            changed = True
        if meta.get("onboarding_completed_at") is not None:
            meta["onboarding_completed_at"] = None
            changed = True
        if meta.get("daily_brief_enabled") is not False:
            meta["daily_brief_enabled"] = False
            changed = True

    if "review_tracking_started_at" not in meta:
        meta["review_tracking_started_at"] = None
        changed = True

    if changed:
        meta["updated_at"] = now_iso(tz_name)
        if persist:
            write_pillar_meta(pillar_dir, meta, body)

    return meta, body, changed


def next_onboarding_step(step: str) -> str:
    if step == "mission":
        return "scope"
    if step == "scope":
        return "success_signals"
    return "completed"


def onboarding_question_for_step(step: str, followup: bool = False) -> str:
    if followup:
        return ONBOARDING_FOLLOWUPS.get(step, ONBOARDING_QUESTIONS["mission"])
    return ONBOARDING_QUESTIONS.get(step, ONBOARDING_QUESTIONS["mission"])


def parse_success_signal_answer(answer: str) -> list[str]:
    return coerce_string_list(answer)


def validate_onboarding_answer(step: str, answer: str) -> tuple[bool, Any]:
    cleaned = normalize_text(answer)
    if step in ("mission", "scope"):
        if not is_meaningful_sentence(cleaned):
            return False, cleaned
        return True, cleaned

    if step == "success_signals":
        signals = parse_success_signal_answer(answer)
        meaningful = [signal for signal in signals if is_meaningful_sentence(signal, minimum_words=3, minimum_chars=12)]
        if len(meaningful) < 2:
            return False, signals
        return True, meaningful

    return False, cleaned


def render_onboarding_draft_block(mission: str, scope: str, success_signals: list[str]) -> str:
    lines = [
        ONBOARDING_DRAFT_START,
        "## Onboarding Draft",
        "",
        f"- Mission: {mission if mission else '_pending_'}",
        f"- Scope: {scope if scope else '_pending_'}",
        "- Success Signals:",
    ]
    if success_signals:
        for signal in success_signals:
            lines.append(f"  - {signal}")
    else:
        lines.append("  - _pending_")
    lines.append(ONBOARDING_DRAFT_END)
    return "\n".join(lines)


def upsert_onboarding_draft_block(body: str, mission: str, scope: str, success_signals: list[str]) -> str:
    draft_block = render_onboarding_draft_block(mission=mission, scope=scope, success_signals=success_signals)
    stripped = body.strip()
    if not stripped:
        return draft_block + "\n"

    pattern = re.compile(
        re.escape(ONBOARDING_DRAFT_START) + r".*?" + re.escape(ONBOARDING_DRAFT_END),
        re.DOTALL,
    )
    if pattern.search(stripped):
        updated = pattern.sub(draft_block, stripped)
        return updated.rstrip() + "\n"

    return stripped.rstrip() + "\n\n" + draft_block + "\n"


def persist_onboarding_manifesto_value(
    pillar_dir: Path,
    pillar_slug: str,
    tz_name: str,
    step: str,
    value: Any,
) -> None:
    manifesto_path = pillar_dir / "manifesto.md"
    manifesto_fm, manifesto_body = read_markdown(manifesto_path)

    manifesto_fm["pillar_slug"] = pillar_slug
    manifesto_fm["schema_version"] = 1
    manifesto_fm["updated_at"] = now_iso(tz_name)
    manifesto_fm["mission"] = normalize_text(manifesto_fm.get("mission")) or MANIFESTO_PLACEHOLDER_MISSION
    manifesto_fm["scope"] = normalize_text(manifesto_fm.get("scope")) or MANIFESTO_PLACEHOLDER_SCOPE
    manifesto_fm["non_negotiables"] = coerce_string_list(manifesto_fm.get("non_negotiables")) or [
        MANIFESTO_PLACEHOLDER_NON_NEGOTIABLE
    ]
    manifesto_fm["success_signals"] = coerce_string_list(manifesto_fm.get("success_signals")) or [
        MANIFESTO_PLACEHOLDER_SUCCESS_SIGNAL
    ]
    manifesto_fm["review_cadence"] = normalize_text(manifesto_fm.get("review_cadence")) or "quarterly"

    if step in ("mission", "scope"):
        manifesto_fm[step] = normalize_text(value)
    elif step == "success_signals":
        manifesto_fm["success_signals"] = coerce_string_list(value)

    if not manifesto_body.strip():
        manifesto_body = MANIFESTO_DEFAULT_BODY

    mission = normalize_text(manifesto_fm.get("mission"))
    scope = normalize_text(manifesto_fm.get("scope"))
    success_signals = coerce_string_list(manifesto_fm.get("success_signals"))
    manifesto_body = upsert_onboarding_draft_block(
        body=manifesto_body,
        mission=mission,
        scope=scope,
        success_signals=success_signals,
    )

    write_markdown(manifesto_path, manifesto_fm, manifesto_body)


def ensure_required_pillar_layout(pillar_dir: Path) -> dict[str, list[str]]:
    created_files: list[str] = []
    created_dirs: list[str] = []

    for dirname in ("contacts", "journal", "projects", "archive"):
        directory = pillar_dir / dirname
        if not directory.exists():
            ensure_dir(directory)
            created_dirs.append(dirname)

    reminders_file = pillar_dir / "reminders.jsonl"
    if not reminders_file.exists():
        reminders_file.write_text("", encoding="utf-8")
        created_files.append("reminders.jsonl")

    staged_file = staged_messages_path(pillar_dir)
    if not staged_file.exists():
        staged_file.write_text("", encoding="utf-8")
        created_files.append("staged-messages.jsonl")

    return {"files": created_files, "dirs": created_dirs}


def ensure_manifesto(pillar_dir: Path, pillar_slug: str, tz_name: str) -> bool:
    manifesto_path = pillar_dir / "manifesto.md"
    if manifesto_path.exists():
        fm, body = read_markdown(manifesto_path)
    else:
        fm, body = {}, ""

    changed = False
    defaults = {
        "pillar_slug": pillar_slug,
        "schema_version": 1,
        "updated_at": now_iso(tz_name),
        "mission": fm.get("mission") or MANIFESTO_PLACEHOLDER_MISSION,
        "scope": fm.get("scope") or MANIFESTO_PLACEHOLDER_SCOPE,
        "non_negotiables": fm.get("non_negotiables") or [MANIFESTO_PLACEHOLDER_NON_NEGOTIABLE],
        "success_signals": fm.get("success_signals") or [MANIFESTO_PLACEHOLDER_SUCCESS_SIGNAL],
        "review_cadence": fm.get("review_cadence") or "quarterly",
    }

    for key, value in defaults.items():
        if fm.get(key) != value:
            fm[key] = value
            changed = True

    if not body.strip():
        body = MANIFESTO_DEFAULT_BODY
        changed = True

    if changed:
        write_markdown(manifesto_path, fm, body)
    return changed


def ensure_monthly_journal(pillar_dir: Path, pillar_slug: str, tz_name: str) -> Path:
    month_key = now_in_tz(tz_name).strftime("%Y-%m")
    journal_path = pillar_dir / "journal" / f"{month_key}.md"
    if journal_path.exists():
        return journal_path

    frontmatter = {
        "pillar_slug": pillar_slug,
        "schema_version": 1,
        "month": month_key,
        "entry_count": 0,
        "updated_at": now_iso(tz_name),
    }
    body = "## Journal Entries\n"
    write_markdown(journal_path, frontmatter, body)
    return journal_path


def parse_pillar_from_channel(
    workspace: Path,
    channel_id: str,
) -> tuple[str, Path, dict[str, Any], str] | tuple[None, None, None, None]:
    for status in STATUSES:
        status_root = pillars_root(workspace) / status
        if not status_root.exists():
            continue
        for pillar_dir in status_root.iterdir():
            if not pillar_dir.is_dir():
                continue
            pillar_md = pillar_dir / "pillar.md"
            if not pillar_md.exists():
                continue
            meta, body = read_markdown(pillar_md)
            if str(meta.get("discord_channel_id")) == str(channel_id):
                return pillar_dir.name, pillar_dir, meta, body
    return None, None, None, None


def normalize_channel_name(pillar_slug: str) -> str:
    return f"pillar-{pillar_slug}"


def load_cron_jobs(path: Path) -> dict[str, Any]:
    data = load_json(path, {"version": 1, "jobs": []})
    if not isinstance(data, dict):
        raise QubitError(f"Invalid cron store format: {path}")
    if "jobs" not in data or not isinstance(data["jobs"], list):
        raise QubitError(f"Cron store missing jobs array: {path}")
    if "version" not in data:
        data["version"] = 1
    return data


def daily_brief_expr(daily_time: str) -> str:
    validate_time_hhmm(daily_time, "daily_brief_time")
    hour, minute = daily_time.split(":")
    return f"{int(minute)} {int(hour)} * * *"


def managed_job_id(pillar_slug: str) -> str:
    return f"qubit-daily-brief-{pillar_slug}"


def managed_job_pillar_slug(job: dict[str, Any]) -> str | None:
    job_id = normalize_text(job.get("jobId") or job.get("id"))
    if job_id.startswith("qubit-daily-brief-"):
        slug = normalize_text(job_id.removeprefix("qubit-daily-brief-"))
        return slug or None

    description = normalize_text(job.get("description"))
    if MANAGED_DAILY_BRIEF_DESCRIPTION_TAG not in description:
        return None
    match = re.search(r"(?:^|;)pillar=([a-z0-9-]+)(?:;|$)", description)
    if match:
        return match.group(1)
    return None


def is_managed_daily_brief_job(job: dict[str, Any]) -> bool:
    return managed_job_pillar_slug(job) is not None


def preserve_runtime_fields(existing: dict[str, Any], new_job: dict[str, Any]) -> dict[str, Any]:
    preserved: dict[str, Any] = {}
    for key in ("id", "runs", "lastRunAt", "nextRunAt", "nextWakeAtMs", "createdAt", "state"):
        if key in existing:
            preserved[key] = existing[key]

    updated = dict(new_job)
    updated.update(preserved)
    return updated


def remove_managed_daily_brief_jobs(cron_path: Path, pillar_slug: str | None = None) -> int:
    data = load_cron_jobs(cron_path)
    jobs = data["jobs"]
    kept: list[dict[str, Any]] = []
    removed = 0

    for job in jobs:
        managed_slug = managed_job_pillar_slug(job)
        if not managed_slug:
            kept.append(job)
            continue
        if pillar_slug is not None and managed_slug != pillar_slug:
            kept.append(job)
            continue
        removed += 1

    if removed:
        data["jobs"] = kept
        save_json(cron_path, data)

    return removed


def allocate_daily_brief_slots(
    pillar_slugs: list[str],
    start_minutes: int,
    end_minutes: int,
) -> dict[str, str]:
    ordered = sorted(pillar_slugs)
    if not ordered:
        return {}

    window_size = end_minutes - start_minutes
    if window_size <= 0:
        raise QubitError("Daily brief window must have positive length")
    if len(ordered) > window_size:
        raise QubitError(
            f"Cannot allocate unique daily brief slots: {len(ordered)} pillars in a {window_size}-minute window"
        )

    assigned: dict[str, str] = {}
    count = len(ordered)
    for index, pillar_slug in enumerate(ordered):
        offset = (index * window_size) // count
        assigned[pillar_slug] = minutes_to_hhmm(start_minutes + offset)
    return assigned


def build_daily_brief_job(meta: dict[str, Any]) -> dict[str, Any]:
    pillar_slug = str(meta["pillar_slug"])
    display_name = str(meta.get("display_name", pillar_slug))
    tz_name = str(meta.get("timezone", DEFAULT_TIMEZONE))
    daily_time = str(meta.get("daily_brief_time", DEFAULT_DAILY_BRIEF_TIME))
    channel_id = str(meta.get("discord_channel_id", "")).strip()
    if not channel_id:
        raise QubitError("Cannot create cron job without discord_channel_id")

    expr = daily_brief_expr(daily_time)
    prompt = (
        f"Autonomous workflow (cron): run Qubit daily brief for pillar '{display_name}' "
        f"(slug: {pillar_slug}). Do not ask conversational clarifications unless blocked. "
        "Focus on decisions needed, due reminders, blockers, and top 3 next actions."
    )

    return {
        "jobId": managed_job_id(pillar_slug),
        "name": f"Qubit Daily Brief: {display_name}",
        "description": f"{MANAGED_DAILY_BRIEF_DESCRIPTION_TAG};pillar={pillar_slug}",
        "enabled": True,
        "deleteAfterRun": False,
        "schedule": {
            "kind": "cron",
            "expr": expr,
            "tz": tz_name,
        },
        "sessionTarget": "isolated",
        "wakeMode": "next-heartbeat",
        "payload": {
            "kind": "agentTurn",
            "message": prompt,
        },
        "delivery": {
            "mode": "announce",
            "channel": "discord",
            "to": f"channel:{channel_id}",
            "bestEffort": True,
        },
    }


def upsert_daily_brief_job(cron_path: Path, meta: dict[str, Any]) -> tuple[str, str]:
    data = load_cron_jobs(cron_path)
    jobs = data["jobs"]

    expected_id = managed_job_id(str(meta["pillar_slug"]))
    new_job = build_daily_brief_job(meta)

    matched_indices: list[int] = []
    for index, job in enumerate(jobs):
        managed_slug = managed_job_pillar_slug(job)
        if managed_slug and managed_slug == str(meta["pillar_slug"]):
            matched_indices.append(index)
            continue
        job_id = normalize_text(job.get("jobId") or job.get("id"))
        name = str(job.get("name") or "")
        desc = str(job.get("description") or "")
        if job_id == expected_id or desc.endswith(f"pillar={meta['pillar_slug']}") or name == new_job["name"]:
            matched_indices.append(index)

    if not matched_indices:
        jobs.append(new_job)
        action = "created"
    else:
        primary_index = matched_indices[0]
        existing = jobs[primary_index]
        jobs[primary_index] = preserve_runtime_fields(existing, new_job)
        for duplicate_index in sorted(matched_indices[1:], reverse=True):
            del jobs[duplicate_index]
        action = "updated"

    data["jobs"] = jobs
    save_json(cron_path, data)
    return action, expected_id


def managed_stage_message_job_id(pillar_slug: str, stage_id: str) -> str:
    return f"qubit-stage-message-{pillar_slug}-{stage_id}"


def managed_stage_message_job_details(job: dict[str, Any]) -> tuple[str, str] | tuple[None, None]:
    job_id = normalize_text(job.get("jobId") or job.get("id"))
    prefix = "qubit-stage-message-"
    if job_id.startswith(prefix):
        remainder = job_id.removeprefix(prefix)
        parts = remainder.rsplit("-", 1)
        if len(parts) == 2 and parts[0] and parts[1]:
            return parts[0], parts[1]

    description = normalize_text(job.get("description"))
    if MANAGED_STAGE_MESSAGE_DESCRIPTION_TAG not in description:
        return None, None
    pillar_match = re.search(r"(?:^|;)pillar=([a-z0-9-]+)(?:;|$)", description)
    stage_match = re.search(r"(?:^|;)stage=([a-z0-9-]+)(?:;|$)", description)
    if not pillar_match or not stage_match:
        return None, None
    return pillar_match.group(1), stage_match.group(1)


def remove_managed_stage_message_jobs(
    cron_path: Path,
    *,
    pillar_slug: str | None = None,
    stage_id: str | None = None,
) -> int:
    if not cron_path.exists():
        return 0
    data = load_cron_jobs(cron_path)
    jobs = data["jobs"]
    kept: list[dict[str, Any]] = []
    removed = 0

    for job in jobs:
        managed_pillar_slug, managed_stage_id = managed_stage_message_job_details(job)
        if not managed_pillar_slug or not managed_stage_id:
            kept.append(job)
            continue
        if pillar_slug is not None and managed_pillar_slug != pillar_slug:
            kept.append(job)
            continue
        if stage_id is not None and managed_stage_id != stage_id:
            kept.append(job)
            continue
        removed += 1

    if removed:
        data["jobs"] = kept
        save_json(cron_path, data)
    return removed


def build_stage_message_job(meta: dict[str, Any], stage_row: dict[str, Any]) -> dict[str, Any]:
    pillar_slug = normalize_text(meta.get("pillar_slug"))
    if not pillar_slug:
        raise QubitError("Stage message cron build requires pillar_slug")
    stage_id = normalize_text(stage_row.get("id"))
    if not stage_id:
        raise QubitError("Stage message cron build requires stage id")
    channel_id = normalize_text(meta.get("discord_channel_id"))
    if not channel_id:
        raise QubitError("Cannot create stage message cron job without discord_channel_id")

    display_name = str(meta.get("display_name") or pillar_slug)
    due_at = normalize_text(stage_row.get("due_at"))
    if not due_at:
        raise QubitError("Cannot create stage message cron job without due_at")
    due_dt = parse_iso(due_at, fallback_tz=str(meta.get("timezone") or DEFAULT_TIMEZONE))
    due_at_iso = due_dt.replace(microsecond=0).isoformat()
    tz_name = str(stage_row.get("timezone") or meta.get("timezone") or DEFAULT_TIMEZONE)
    prompt = f"qubit {pillar_slug} stage message dispatch {stage_id}"

    return {
        "jobId": managed_stage_message_job_id(pillar_slug, stage_id),
        "name": f"Qubit Stage Message: {display_name} ({stage_id})",
        "description": f"{MANAGED_STAGE_MESSAGE_DESCRIPTION_TAG};pillar={pillar_slug};stage={stage_id}",
        "enabled": True,
        "deleteAfterRun": True,
        "schedule": {
            "kind": "at",
            "at": due_at_iso,
            "tz": tz_name,
        },
        "sessionTarget": "isolated",
        "wakeMode": "next-heartbeat",
        "payload": {
            "kind": "agentTurn",
            "message": prompt,
        },
        "delivery": {
            "mode": "announce",
            "channel": "discord",
            "to": f"channel:{channel_id}",
            "bestEffort": True,
        },
    }


def upsert_stage_message_job(
    cron_path: Path,
    meta: dict[str, Any],
    stage_row: dict[str, Any],
) -> tuple[str, str]:
    data = load_cron_jobs(cron_path)
    jobs = data["jobs"]
    pillar_slug = normalize_text(meta.get("pillar_slug"))
    stage_id = normalize_text(stage_row.get("id"))
    if not pillar_slug or not stage_id:
        raise QubitError("Stage message job upsert requires pillar_slug and stage id")

    expected_id = managed_stage_message_job_id(pillar_slug, stage_id)
    new_job = build_stage_message_job(meta, stage_row)

    matched_indices: list[int] = []
    for index, job in enumerate(jobs):
        managed_pillar_slug, managed_stage_id = managed_stage_message_job_details(job)
        if managed_pillar_slug == pillar_slug and managed_stage_id == stage_id:
            matched_indices.append(index)
            continue
        job_id = normalize_text(job.get("jobId") or job.get("id"))
        if job_id == expected_id:
            matched_indices.append(index)

    if not matched_indices:
        jobs.append(new_job)
        action = "created"
    else:
        primary_index = matched_indices[0]
        existing = jobs[primary_index]
        jobs[primary_index] = preserve_runtime_fields(existing, new_job)
        for duplicate_index in sorted(matched_indices[1:], reverse=True):
            del jobs[duplicate_index]
        action = "updated"

    data["jobs"] = jobs
    save_json(cron_path, data)
    return action, expected_id


def read_projects(pillar_dir: Path) -> list[dict[str, Any]]:
    projects_dir = pillar_dir / "projects"
    if not projects_dir.exists():
        return []

    projects: list[dict[str, Any]] = []
    for project_dir in sorted(projects_dir.iterdir()):
        if not project_dir.is_dir():
            continue
        project_file = project_dir / "project.md"
        if not project_file.exists():
            continue
        frontmatter, _ = read_markdown(project_file)
        if not frontmatter:
            continue
        projects.append(frontmatter)
    return projects


def read_reminders(reminders_file: Path) -> list[dict[str, Any]]:
    if not reminders_file.exists():
        return []

    reminders: list[dict[str, Any]] = []
    for line in reminders_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            reminders.append(payload)
    return reminders


def append_reminder(reminders_file: Path, reminder: dict[str, Any]) -> None:
    with reminders_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(reminder, ensure_ascii=True) + "\n")


def get_or_create_pillar_state_by_slug(workspace: Path, pillar_slug: str) -> tuple[Path, dict[str, Any], str]:
    pillar_dir, _status = find_pillar_dir(workspace, pillar_slug)
    if not pillar_dir:
        raise QubitError(
            f"Pillar '{pillar_slug}' not found. Run onboarding first with: qubit {pillar_slug} onboard"
        )
    meta, body = load_pillar_meta(pillar_dir)
    return pillar_dir, meta, body


def get_or_create_pillar_by_slug(workspace: Path, pillar_slug: str) -> tuple[Path, dict[str, Any]]:
    pillar_dir, meta, _ = get_or_create_pillar_state_by_slug(workspace, pillar_slug)
    return pillar_dir, meta


def resolve_pillar_context(
    workspace: Path,
    *,
    pillar: str | None,
    channel_id: str | None,
) -> tuple[str, Path, dict[str, Any], str]:
    if pillar:
        pillar_slug = slugify(pillar)
        pillar_dir, meta, pillar_body = get_or_create_pillar_state_by_slug(workspace, pillar_slug)
        return pillar_slug, pillar_dir, meta, pillar_body

    if not channel_id:
        raise QubitError("Workflow requires --pillar or --channel-id")
    parsed_slug, pillar_dir, meta, pillar_body = parse_pillar_from_channel(workspace, channel_id)
    if not parsed_slug or not pillar_dir or not meta:
        raise QubitError(f"No pillar mapping found for channel ID {channel_id}")
    return parsed_slug, pillar_dir, meta, pillar_body


def enforce_stage_message_policy(workspace: Path, meta: dict[str, Any]) -> None:
    policy, _policy_file = load_health_policy(workspace)
    blacklist = set(policy.get("channel_blacklist") or [])
    if is_channel_blacklisted(meta, blacklist):
        channel_name = str(meta.get("discord_channel_name") or "unknown")
        raise QubitError(f"Stage Message is blocked in blacklisted channel {channel_name!r}")
    if normalize_text(meta.get("status")).lower() != "active":
        raise QubitError("Stage Message requires an active pillar")
    if not normalize_text(meta.get("discord_channel_id")):
        raise QubitError("Stage Message requires a pillar with a mapped Discord channel ID")


def load_stage_rows_for_pillar(pillar_dir: Path) -> list[dict[str, Any]]:
    return read_staged_messages(staged_messages_path(pillar_dir))


def ensure_contact_note(
    pillar_dir: Path,
    pillar_slug: str,
    tz_name: str,
    name: str,
    note: str,
    role: str = "unknown",
    relationship: str = "unknown",
) -> Path:
    contact_slug = slugify(name)
    contact_path = pillar_dir / "contacts" / f"{contact_slug}.md"

    if contact_path.exists():
        frontmatter, body = read_markdown(contact_path)
    else:
        frontmatter, body = {}, ""

    frontmatter.update(
        {
            "pillar_slug": pillar_slug,
            "schema_version": 1,
            "updated_at": now_iso(tz_name),
            "name": frontmatter.get("name") or name,
            "role": frontmatter.get("role") or role,
            "relationship": frontmatter.get("relationship") or relationship,
        }
    )

    stamp = now_iso(tz_name)
    entry = f"\n### {stamp}\n{note.strip()}\n"
    body = (body.rstrip() + entry).strip() + "\n"
    write_markdown(contact_path, frontmatter, body)
    return contact_path


def append_journal_entry(
    pillar_dir: Path,
    pillar_slug: str,
    tz_name: str,
    entry: str,
    source: str,
) -> Path:
    journal_path = ensure_monthly_journal(pillar_dir, pillar_slug, tz_name)
    frontmatter, body = read_markdown(journal_path)

    timestamp = now_iso(tz_name)
    snippet = (
        f"\n### {timestamp}\n"
        f"source: {source}\n\n"
        f"{entry.strip()}\n"
    )
    body = (body.rstrip() + snippet).strip() + "\n"

    current_count = int(frontmatter.get("entry_count") or 0)
    frontmatter["entry_count"] = current_count + 1
    frontmatter["updated_at"] = timestamp
    write_markdown(journal_path, frontmatter, body)
    return journal_path


def create_project(
    workspace: Path,
    pillar_slug: str,
    title: str,
    outcome: str,
    next_decision: str,
    next_action: str,
    due_at: str | None,
    status: str,
    tags: list[str],
) -> Path:
    if status not in PROJECT_STATUSES:
        raise QubitError(f"Invalid project status {status!r}; expected one of {PROJECT_STATUSES}")

    pillar_dir, meta = get_or_create_pillar_by_slug(workspace, pillar_slug)
    tz_name = str(meta.get("timezone") or DEFAULT_TIMEZONE)
    project_slug = slugify(title)
    project_dir = pillar_dir / "projects" / project_slug
    ensure_dir(project_dir)

    project_file = project_dir / "project.md"
    if project_file.exists():
        frontmatter, body = read_markdown(project_file)
    else:
        frontmatter, body = {}, ""

    timestamp = now_iso(tz_name)
    if due_at is not None:
        _ = parse_iso(due_at)

    frontmatter.update(
        {
            "pillar_slug": pillar_slug,
            "project_slug": project_slug,
            "schema_version": 1,
            "created_at": frontmatter.get("created_at") or timestamp,
            "updated_at": timestamp,
            "title": title,
            "status": status,
            "outcome": outcome,
            "next_decision": next_decision,
            "next_action": next_action,
            "due_at": due_at,
            "tags": tags,
        }
    )

    if not body.strip():
        body = (
            "## Context\n\n"
            "Capture project context, constraints, and supporting notes.\n\n"
            "## Progress Notes\n\n"
            "Append updates over time.\n"
        )

    write_markdown(project_file, frontmatter, body)
    return project_file


def parse_due_phrase(phrase: str, tz_name: str) -> str | None:
    text = phrase.strip()
    if not text:
        return None

    # Direct ISO support.
    try:
        return parse_iso(text).replace(microsecond=0).isoformat()
    except Exception:
        pass

    now_local = now_in_tz(tz_name)

    # yyyy-mm-dd [hh:mm]
    date_time_match = re.match(
        r"^(\d{4}-\d{2}-\d{2})(?:\s+(\d{1,2}):(\d{2}))?$",
        text,
    )
    if date_time_match:
        date_part = date_time_match.group(1)
        hour = int(date_time_match.group(2) or 9)
        minute = int(date_time_match.group(3) or 0)
        year, month, day = [int(v) for v in date_part.split("-")]
        return datetime(year, month, day, hour, minute, tzinfo=ZoneInfo(tz_name)).isoformat()

    # today/tomorrow at HH:MMam/pm
    relative_match = re.match(
        r"^(today|tomorrow)(?:\s+at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?)?$",
        text.lower(),
    )
    if relative_match:
        day_label = relative_match.group(1)
        hour_raw = relative_match.group(2)
        minute_raw = relative_match.group(3)
        ampm = relative_match.group(4)

        target_date = now_local.date()
        if day_label == "tomorrow":
            target_date = (now_local + timedelta(days=1)).date()

        if hour_raw is None:
            hour = 9
            minute = 0
        else:
            hour = int(hour_raw)
            minute = int(minute_raw or 0)
            if ampm == "pm" and hour < 12:
                hour += 12
            if ampm == "am" and hour == 12:
                hour = 0

        return datetime(
            target_date.year,
            target_date.month,
            target_date.day,
            hour,
            minute,
            tzinfo=ZoneInfo(tz_name),
        ).isoformat()

    return None


def staged_messages_path(pillar_dir: Path) -> Path:
    return pillar_dir / "staged-messages.jsonl"


def read_staged_messages(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def write_staged_messages(path: Path, rows: list[dict[str, Any]]) -> None:
    rendered_lines = [json.dumps(row, ensure_ascii=True) for row in rows if isinstance(row, dict)]
    if rendered_lines:
        path.write_text("\n".join(rendered_lines) + "\n", encoding="utf-8")
    else:
        path.write_text("", encoding="utf-8")


def find_stage_message_index(rows: list[dict[str, Any]], stage_id: str) -> int:
    for index, row in enumerate(rows):
        if normalize_text(row.get("id")) == stage_id:
            return index
    return -1


def normalize_delivery_method(value: str) -> str:
    raw = normalize_text(value).lower().replace(" ", "").replace("_", "").replace("-", "")
    if raw in ("wa", "whatsapp"):
        return "whatsapp"
    if raw in ("email",):
        return "email"
    raise QubitError(f"Unsupported delivery method {value!r}; expected one of {STAGE_DELIVERY_METHODS}")


def validate_stage_recipient(method: str, recipient_raw: str) -> dict[str, Any]:
    recipient = normalize_text(recipient_raw)
    if not recipient:
        raise QubitError("recipient is required")

    if method == "email":
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", recipient):
            raise QubitError(f"Invalid email recipient {recipient!r}")
        return {"email": recipient.lower()}

    if method == "whatsapp":
        if recipient.startswith("@") and len(recipient) > 1:
            return {"handle": recipient}
        if re.match(r"^\+?[0-9][0-9\-\s]{6,}$", recipient):
            normalized_number = re.sub(r"\s+", "", recipient)
            return {"phone": normalized_number}
        raise QubitError("WhatsApp recipient must be a phone number or @handle")

    raise QubitError(f"Unsupported delivery method {method!r}")


def parse_stage_due_input(due_raw: str, tz_name: str) -> str:
    candidate = normalize_text(due_raw)
    if not candidate:
        raise QubitError("due is required")
    due_iso = parse_due_phrase(candidate, tz_name)
    if due_iso is not None:
        return due_iso
    try:
        return parse_iso(candidate, fallback_tz=tz_name).replace(microsecond=0).isoformat()
    except Exception as error:
        raise QubitError(
            f"Could not parse due date/time {candidate!r}. Use ISO or simple forms like 'tomorrow at 09:00'."
        ) from error


def parse_stage_condition(parent_stage_id: str | None, wait_days: int | None) -> dict[str, Any] | None:
    parent = normalize_text(parent_stage_id)
    if not parent and wait_days is None:
        return None
    if not parent or wait_days is None:
        raise QubitError("Conditional follow-up requires both --parent-stage-id and --wait-days")
    wait_days_int = int(wait_days)
    if wait_days_int <= 0:
        raise QubitError("--wait-days must be > 0")
    return {
        "kind": "parent_uncompleted_after_days",
        "parent_stage_id": parent,
        "wait_days": wait_days_int,
    }


def stage_condition_allows_dispatch(
    stage_row: dict[str, Any],
    all_rows: list[dict[str, Any]],
    now_dt: datetime,
) -> tuple[bool, str | None]:
    condition = stage_row.get("condition")
    if not condition:
        return True, None
    if not isinstance(condition, dict):
        return False, "invalid_condition"
    kind = normalize_text(condition.get("kind"))
    if kind not in STAGE_CONDITION_KINDS:
        return False, "unsupported_condition_kind"
    if kind != "parent_uncompleted_after_days":
        return False, "unsupported_condition_kind"

    parent_stage_id = normalize_text(condition.get("parent_stage_id"))
    if not parent_stage_id:
        return False, "missing_parent_stage_id"
    parent_index = find_stage_message_index(all_rows, parent_stage_id)
    if parent_index < 0:
        return False, "missing_parent_stage"
    parent = all_rows[parent_index]
    parent_status = normalize_text(parent.get("status"))
    if parent_status == "completed":
        return False, "parent_completed"

    try:
        wait_days = int(condition.get("wait_days"))
    except Exception:
        return False, "invalid_wait_days"
    if wait_days <= 0:
        return False, "invalid_wait_days"

    try:
        parent_due_at = parse_iso(str(parent.get("due_at")))
    except Exception:
        return False, "invalid_parent_due_at"

    if now_dt < parent_due_at + timedelta(days=wait_days):
        return False, "wait_window_not_elapsed"
    return True, None


def format_stage_copy_block(stage_row: dict[str, Any], display_name: str) -> str:
    method = normalize_text(stage_row.get("delivery_method")).lower()
    recipient = stage_row.get("recipient") or {}
    if not isinstance(recipient, dict):
        recipient = {}
    due_at = normalize_text(stage_row.get("due_at"))
    body = normalize_text(stage_row.get("message_body"))
    if not body:
        body = "(empty message body)"

    if method == "email":
        to_value = normalize_text(recipient.get("email")) or "(missing email recipient)"
        subject = normalize_text(stage_row.get("message_subject")) or "(no subject)"
        return (
            "```text\n"
            f"Stage Message Ready | {display_name}\n"
            "Method: Email\n"
            f"Recipient: {to_value}\n"
            f"Due: {due_at}\n\n"
            f"Subject: {subject}\n\n"
            f"{body}\n"
            "```"
        )

    if method == "whatsapp":
        to_value = normalize_text(recipient.get("phone") or recipient.get("handle")) or "(missing WhatsApp recipient)"
        return (
            "```text\n"
            f"Stage Message Ready | {display_name}\n"
            "Method: WhatsApp\n"
            f"Recipient: {to_value}\n"
            f"Due: {due_at}\n\n"
            f"{body}\n"
            "```"
        )

    return (
        "```text\n"
        f"Stage Message Ready | {display_name}\n"
        f"Method: {method or 'unknown'}\n"
        f"Due: {due_at}\n\n"
        f"{body}\n"
        "```"
    )


def should_offer_stage_suggestion(
    workspace: Path,
    pillar_slug: str,
    now_dt: datetime,
) -> bool:
    state = load_qubit_meta_state(workspace)
    suggestion_state = state.get("stage_message") or {}
    if not isinstance(suggestion_state, dict):
        return True
    suggestions = suggestion_state.get("suggestions") or {}
    if not isinstance(suggestions, dict):
        return True
    last_raw = suggestions.get(pillar_slug)
    if not last_raw:
        return True
    try:
        last_dt = parse_iso(str(last_raw))
    except Exception:
        return True
    return (now_dt - last_dt).total_seconds() >= SUGGESTION_COOLDOWN_SECONDS


def mark_stage_suggestion_sent(workspace: Path, pillar_slug: str, now_dt: datetime) -> None:
    state = load_qubit_meta_state(workspace)
    state.setdefault("schema_version", 1)
    stage_message = state.get("stage_message")
    if not isinstance(stage_message, dict):
        stage_message = {}
        state["stage_message"] = stage_message
    suggestions = stage_message.get("suggestions")
    if not isinstance(suggestions, dict):
        suggestions = {}
        stage_message["suggestions"] = suggestions
    suggestions[pillar_slug] = now_dt.replace(microsecond=0).isoformat()
    save_qubit_meta_state(workspace, state)


def infer_stage_message_suggestion(
    message: str,
    tz_name: str,
) -> dict[str, Any] | None:
    text = normalize_text(message)
    if not text:
        return None

    trigger_patterns = [
        r"\bsend later\b",
        r"\bdeferred send\b",
        r"\bscheduled draft\b",
        r"\bstage send\b",
        r"\bqueue message\b",
        r"\bsend intent\b",
        r"\bfollow[\s-]?up\b",
        r"\bcheck in\b",
        r"\bcircle back\b",
    ]
    if not any(re.search(pattern, text, re.IGNORECASE) for pattern in trigger_patterns):
        if not re.search(r"\b(email|whatsapp)\b", text, re.IGNORECASE):
            return None
        if not re.search(r"\b(today|tomorrow|later|next|by|at|on)\b", text, re.IGNORECASE):
            return None

    method = "email"
    if re.search(r"\bwhatsapp\b|\bwa\b", text, re.IGNORECASE):
        method = "whatsapp"
    elif re.search(r"\bemail\b", text, re.IGNORECASE):
        method = "email"

    inferred_recipient: str | None = None
    email_match = re.search(r"\bto\s+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b", text, re.IGNORECASE)
    if email_match:
        inferred_recipient = email_match.group(1)
    else:
        whatsapp_match = re.search(r"\bto\s+(@[A-Za-z0-9_.-]+|\+?[0-9][0-9\-\s]{6,})\b", text, re.IGNORECASE)
        if whatsapp_match:
            inferred_recipient = normalize_text(whatsapp_match.group(1))

    due_iso: str | None = None
    due_assumed = False
    due_source = ""
    due_phrase_match = re.search(
        r"\b(?:on|at|by)\s+(.+?)(?:$|,|;| and )",
        text,
        re.IGNORECASE,
    )
    if due_phrase_match:
        due_source = normalize_text(due_phrase_match.group(1))
        due_iso = parse_due_phrase(due_source, tz_name)

    now_local = now_in_tz(tz_name)
    if due_iso is None:
        day_match = re.search(
            r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
            text,
            re.IGNORECASE,
        )
        if day_match:
            day_name = day_match.group(1).lower()
            weekday_map = {
                "monday": 0,
                "tuesday": 1,
                "wednesday": 2,
                "thursday": 3,
                "friday": 4,
                "saturday": 5,
                "sunday": 6,
            }
            target_weekday = weekday_map[day_name]
            delta_days = (target_weekday - now_local.weekday()) % 7
            if delta_days == 0:
                delta_days = 7
            target_day = (now_local + timedelta(days=delta_days)).date()
            due_iso = datetime(
                target_day.year,
                target_day.month,
                target_day.day,
                9,
                0,
                tzinfo=ZoneInfo(tz_name),
            ).isoformat()
            due_assumed = True
            due_source = f"{day_name} (assumed 09:00)"

    if due_iso is None and re.search(r"\b(tomorrow|today|later|next)\b", text, re.IGNORECASE):
        due_iso = parse_due_phrase("tomorrow at 09:00", tz_name)
        due_assumed = True
        due_source = "tomorrow (assumed 09:00)"

    return {
        "confidence": 0.68 if due_assumed else 0.75,
        "delivery_method": method,
        "recipient_hint": inferred_recipient,
        "due_at": due_iso,
        "due_assumed": due_assumed,
        "due_source": due_source,
    }


def infer_actions(message: str, pillar_slug: str, tz_name: str) -> tuple[list[Action], list[str]]:
    text = message.strip()
    if not text:
        return [], ["No message content provided"]

    actions: list[Action] = []
    uncertainties: list[str] = []

    project_matches = list(re.finditer(r"\b(?:add|create)\s+project\s+[\"']([^\"']+)[\"']", text, re.IGNORECASE))
    for match in project_matches:
        title = match.group(1).strip()
        if not title:
            continue
        actions.append(
            Action(
                action_type="add_project",
                risk="high",
                confidence=0.93,
                payload={
                    "pillar_slug": pillar_slug,
                    "title": title,
                    "outcome": "Define desired outcome.",
                    "next_decision": "Clarify immediate decision.",
                    "next_action": "Define next action.",
                    "due_at": None,
                    "status": "active",
                    "tags": [],
                },
                reason="Detected explicit add project intent.",
            )
        )

    reminder_patterns = [
        re.compile(r"\bremind me to\s+(.+?)\s+(?:on|at|by)\s+([^.]+)", re.IGNORECASE),
        re.compile(r"\bset reminder\s+(.+?)\s+(?:on|at|by)\s+([^.]+)", re.IGNORECASE),
    ]
    for pattern in reminder_patterns:
        for match in pattern.finditer(text):
            message_part = match.group(1).strip(" \t\n\r'\"")
            due_part = match.group(2).strip(" \t\n\r'\"")
            due_iso = parse_due_phrase(due_part, tz_name)
            if due_iso is None:
                # Handle mixed messages where the due phrase is followed by another action.
                for separator in (" and ", ", then ", ";", ","):
                    if separator in due_part.lower():
                        segment = due_part.split(separator, 1)[0].strip()
                        due_iso = parse_due_phrase(segment, tz_name)
                        if due_iso is not None:
                            break
            if due_iso is None:
                uncertainties.append(
                    f"Could not parse reminder due date/time: {due_part!r}. Use ISO or 'today/tomorrow at HH:MM'."
                )
                continue
            actions.append(
                Action(
                    action_type="add_reminder",
                    risk="low",
                    confidence=0.9,
                    payload={
                        "due_at": due_iso,
                        "message": message_part,
                        "project_slug": None,
                    },
                    reason="Detected reminder intent with parseable due time.",
                )
            )

    mention_matches = list(re.finditer(r"@([A-Za-z][A-Za-z0-9_.-]{1,50})", text))
    for match in mention_matches:
        handle = match.group(1)
        name = handle.replace(".", " ").replace("_", " ").strip()
        actions.append(
            Action(
                action_type="contact_note",
                risk="low",
                confidence=0.72,
                payload={
                    "name": name,
                    "note": f"Mentioned in message: {text}",
                    "role": "unknown",
                    "relationship": "unknown",
                },
                reason="Detected mention that may map to a contact note.",
            )
        )

    met_match = re.search(
        r"\b(?:met|spoke|talked|called|emailed)\s+(?:with\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        text,
    )
    if met_match:
        name = met_match.group(1).strip()
        actions.append(
            Action(
                action_type="contact_note",
                risk="low",
                confidence=0.8,
                payload={
                    "name": name,
                    "note": f"Interaction captured: {text}",
                    "role": "unknown",
                    "relationship": "unknown",
                },
                reason="Detected conversation/interaction phrase.",
            )
        )

    # Always keep a journal signal for traceability.
    actions.append(
        Action(
            action_type="journal_entry",
            risk="low",
            confidence=0.99,
            payload={
                "entry": text,
                "source": "discord-message",
            },
            reason="All pillar messages are journaled for continuity.",
        )
    )

    return actions, uncertainties


def apply_action(workspace: Path, pillar_slug: str, meta: dict[str, Any], action: Action) -> str:
    pillar_dir, _ = get_or_create_pillar_by_slug(workspace, pillar_slug)
    tz_name = str(meta.get("timezone") or DEFAULT_TIMEZONE)

    if action.action_type == "add_project":
        payload = action.payload
        project_file = create_project(
            workspace=workspace,
            pillar_slug=pillar_slug,
            title=str(payload["title"]),
            outcome=str(payload["outcome"]),
            next_decision=str(payload["next_decision"]),
            next_action=str(payload["next_action"]),
            due_at=payload.get("due_at"),
            status=str(payload.get("status", "active")),
            tags=[str(tag) for tag in payload.get("tags", [])],
        )
        return f"Created or updated project: {project_file}"

    if action.action_type == "add_reminder":
        reminder = {
            "id": f"rem-{uuid.uuid4().hex[:12]}",
            "due_at": action.payload["due_at"],
            "message": action.payload["message"],
            "status": "pending",
            "project_slug": action.payload.get("project_slug"),
            "created_at": now_iso(tz_name),
            "updated_at": now_iso(tz_name),
        }
        append_reminder(pillar_dir / "reminders.jsonl", reminder)
        return f"Added reminder due {reminder['due_at']}: {reminder['message']}"

    if action.action_type == "contact_note":
        contact_file = ensure_contact_note(
            pillar_dir=pillar_dir,
            pillar_slug=pillar_slug,
            tz_name=tz_name,
            name=str(action.payload["name"]),
            note=str(action.payload["note"]),
            role=str(action.payload.get("role") or "unknown"),
            relationship=str(action.payload.get("relationship") or "unknown"),
        )
        return f"Updated contact note: {contact_file.name}"

    if action.action_type == "journal_entry":
        journal_file = append_journal_entry(
            pillar_dir=pillar_dir,
            pillar_slug=pillar_slug,
            tz_name=tz_name,
            entry=str(action.payload["entry"]),
            source=str(action.payload.get("source", "unknown")),
        )
        return f"Appended journal entry in {journal_file.name}"

    raise QubitError(f"Unsupported action type: {action.action_type}")


def run_onboarding_turn(
    workspace: Path,
    pillar_dir: Path,
    pillar_slug: str,
    meta: dict[str, Any],
    pillar_body: str,
    message: str,
) -> dict[str, Any]:
    tz_name = str(meta.get("timezone") or DEFAULT_TIMEZONE)
    cleaned_message = normalize_text(message)
    step = normalize_text(meta.get("onboarding_step")) or "mission"
    if step not in ONBOARDING_STEPS or step == "completed":
        manifesto_fm, _ = read_markdown(pillar_dir / "manifesto.md")
        step = infer_onboarding_step_from_manifesto(manifesto_fm)
        if step == "completed":
            step = "mission"

    if not cleaned_message:
        return {
            "status": "ok",
            "workflow": "onboarding-turn",
            "pillar_slug": pillar_slug,
            "captured_field": None,
            "onboarding_status": "in_progress",
            "completed": False,
            "question": onboarding_question_for_step(step),
        }

    accepted, parsed_value = validate_onboarding_answer(step, cleaned_message)
    if not accepted:
        return {
            "status": "ok",
            "workflow": "onboarding-turn",
            "pillar_slug": pillar_slug,
            "captured_field": None,
            "onboarding_status": "in_progress",
            "completed": False,
            "question": onboarding_question_for_step(step, followup=True),
        }

    persist_onboarding_manifesto_value(
        pillar_dir=pillar_dir,
        pillar_slug=pillar_slug,
        tz_name=tz_name,
        step=step,
        value=parsed_value,
    )

    rendered_capture = (
        "\n".join(f"- {item}" for item in parsed_value)
        if isinstance(parsed_value, list)
        else str(parsed_value)
    )
    append_journal_entry(
        pillar_dir=pillar_dir,
        pillar_slug=pillar_slug,
        tz_name=tz_name,
        entry=f"Onboarding captured `{step}`:\n\n{rendered_capture}",
        source="onboarding",
    )

    next_step = next_onboarding_step(step)
    timestamp = now_iso(tz_name)

    if next_step != "completed":
        meta["onboarding_status"] = "in_progress"
        meta["onboarding_step"] = next_step
        meta["updated_at"] = timestamp
        write_pillar_meta(pillar_dir, meta, pillar_body)
        return {
            "status": "ok",
            "workflow": "onboarding-turn",
            "pillar_slug": pillar_slug,
            "captured_field": step,
            "onboarding_status": "in_progress",
            "completed": False,
            "question": onboarding_question_for_step(next_step),
        }

    meta["onboarding_status"] = "completed"
    meta["onboarding_step"] = "completed"
    if not meta.get("onboarding_started_at"):
        meta["onboarding_started_at"] = timestamp
    meta["onboarding_completed_at"] = timestamp
    meta["daily_brief_enabled"] = True
    meta["updated_at"] = timestamp
    write_pillar_meta(pillar_dir, meta, pillar_body)

    cron_info: dict[str, Any] = {
        "action": "skipped",
        "reason": "missing_channel_binding",
        "store": str(cron_store_path(workspace)),
    }
    if str(meta.get("discord_channel_id") or "").strip():
        cron_path = cron_store_path(workspace)
        ensure_dir(cron_path.parent)
        cron_action, cron_job_id = upsert_daily_brief_job(cron_path, meta)
        cron_info = {
            "action": cron_action,
            "jobId": cron_job_id,
            "store": str(cron_path),
        }

    return {
        "status": "ok",
        "workflow": "onboarding-turn",
        "pillar_slug": pillar_slug,
        "captured_field": step,
        "onboarding_status": "completed",
        "completed": True,
        "question": "Onboarding complete. Daily brief automation is now enabled.",
        "cron": cron_info,
    }


def parse_explicit_command(message: str) -> tuple[str, dict[str, Any]] | None:
    global_patterns = [
        ("heal-check", re.compile(r"^\s*qubit\s+heal\s+check\s*$", re.IGNORECASE)),
        ("heal", re.compile(r"^\s*qubit\s+heal\s*$", re.IGNORECASE)),
    ]
    for workflow, pattern in global_patterns:
        if pattern.match(message):
            return workflow, {}

    patterns = [
        ("onboard", re.compile(r"^\s*qubit\s+(.+?)\s+onboard\s*$", re.IGNORECASE)),
        ("daily-brief", re.compile(r"^\s*qubit\s+(.+?)\s+daily\s+brief\s*$", re.IGNORECASE)),
        ("review-weekly", re.compile(r"^\s*qubit\s+(.+?)\s+review\s+weekly\s*$", re.IGNORECASE)),
        (
            "stage-message-list",
            re.compile(r"^\s*qubit\s+(.+?)\s+stage\s+message\s+list\s*$", re.IGNORECASE),
        ),
        (
            "stage-message-cancel",
            re.compile(r"^\s*qubit\s+(.+?)\s+stage\s+message\s+cancel\s+([a-z0-9-]+)\s*$", re.IGNORECASE),
        ),
        (
            "stage-message-complete",
            re.compile(r"^\s*qubit\s+(.+?)\s+stage\s+message\s+complete\s+([a-z0-9-]+)\s*$", re.IGNORECASE),
        ),
        (
            "stage-message-dispatch",
            re.compile(r"^\s*qubit\s+(.+?)\s+stage\s+message\s+dispatch\s+([a-z0-9-]+)\s*$", re.IGNORECASE),
        ),
        (
            "stage-message-alias",
            re.compile(
                r"^\s*qubit\s+(.+?)\s+(scheduled\s+draft|deferred\s+send|send\s+intent|queue\s+message|send\s+later|stage\s+send)\s*$",
                re.IGNORECASE,
            ),
        ),
        (
            "add-project",
            re.compile(
                r"^\s*qubit\s+(.+?)\s+add\s+project\s+(?:[\"'](.+?)[\"']|(.*))\s*$",
                re.IGNORECASE,
            ),
        ),
    ]

    for workflow, pattern in patterns:
        match = pattern.match(message)
        if not match:
            continue

        if workflow == "add-project":
            pillar = match.group(1).strip()
            quoted = (match.group(2) or "").strip()
            fallback = (match.group(3) or "").strip()
            title = quoted or fallback
            if not title:
                raise QubitError("add project command requires a project title")
            return workflow, {"pillar": pillar, "title": title}

        if workflow in ("stage-message-cancel", "stage-message-complete", "stage-message-dispatch"):
            pillar = match.group(1).strip()
            stage_id = normalize_text(match.group(2))
            if not stage_id:
                raise QubitError(f"{workflow} command requires a stage id")
            return workflow, {"pillar": pillar, "stage_id": stage_id}

        if workflow == "stage-message-alias":
            pillar = match.group(1).strip()
            alias = normalize_text(match.group(2)).lower()
            return workflow, {"pillar": pillar, "alias": alias}

        pillar = match.group(1).strip()
        return workflow, {"pillar": pillar}

    return None


def format_daily_brief(pillar_slug: str, meta: dict[str, Any], projects: list[dict[str, Any]], reminders: list[dict[str, Any]]) -> str:
    tz_name = str(meta.get("timezone") or DEFAULT_TIMEZONE)
    now_dt = now_in_tz(tz_name)

    active_projects = [p for p in projects if str(p.get("status")) in ("active", "blocked", "waiting")]
    blocked_projects = [p for p in active_projects if str(p.get("status")) == "blocked"]

    due_soon = []
    for reminder in reminders:
        if str(reminder.get("status")) != "pending":
            continue
        due_at = reminder.get("due_at")
        if not due_at:
            continue
        try:
            due_dt = parse_iso(str(due_at))
        except Exception:
            continue
        if due_dt <= now_dt + timedelta(hours=48):
            due_soon.append((due_dt, reminder))
    due_soon.sort(key=lambda item: item[0])

    decision_lines = []
    for project in active_projects:
        decision = str(project.get("next_decision") or "").strip()
        title = str(project.get("title") or project.get("project_slug") or "Untitled")
        if decision and decision.lower() not in {"none", "n/a"}:
            decision_lines.append(f"- **{title}**: {decision}")

    action_lines = []
    for project in active_projects:
        action = str(project.get("next_action") or "").strip()
        title = str(project.get("title") or project.get("project_slug") or "Untitled")
        if action and action.lower() not in {"none", "n/a"}:
            action_lines.append(f"- **{title}**: {action}")

    action_lines = action_lines[:3]

    lines = [
        f"Qubit Daily Brief | {meta.get('display_name', pillar_slug)}",
        "",
        "Decisions Needed:",
    ]

    if decision_lines:
        lines.extend(decision_lines)
    else:
        lines.append("- None captured. Identify one decision that will unblock progress today.")

    lines.extend(["", "Due Soon (48h):"])
    if due_soon:
        for due_dt, reminder in due_soon[:8]:
            lines.append(f"- {due_dt.isoformat()}: {reminder.get('message')}")
    else:
        lines.append("- No pending reminders due in the next 48 hours.")

    lines.extend(["", "Blocked Projects:"])
    if blocked_projects:
        for project in blocked_projects:
            title = project.get("title") or project.get("project_slug")
            lines.append(f"- {title}")
    else:
        lines.append("- No blocked projects detected.")

    lines.extend(["", "Top 3 Next Actions:"])
    if action_lines:
        lines.extend(action_lines)
    else:
        lines.append("- Define the next concrete action for active projects.")

    lines.extend(
        [
            "",
            "Prompt:",
            "- Which one decision, if made now, will create the most progress today?",
        ]
    )

    return "\n".join(lines)


def in_quiet_hours(now_dt: datetime, quiet_start: str, quiet_end: str) -> bool:
    start_h, start_m = [int(v) for v in quiet_start.split(":")]
    end_h, end_m = [int(v) for v in quiet_end.split(":")]
    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m
    current_minutes = now_dt.hour * 60 + now_dt.minute

    if start_minutes == end_minutes:
        return False

    if start_minutes < end_minutes:
        return start_minutes <= current_minutes < end_minutes

    # Overnight window (e.g., 22:00-07:00)
    return current_minutes >= start_minutes or current_minutes < end_minutes


def pick_due_loop(meta: dict[str, Any], now_dt: datetime) -> tuple[str, int] | None:
    review_tracking_started_at = meta.get("review_tracking_started_at")
    if not review_tracking_started_at:
        return None

    try:
        tracking_start_dt = parse_iso(str(review_tracking_started_at))
    except Exception:
        return None

    due_items = []
    for loop_name in LOOP_PRIORITY:
        last_key = f"last_{loop_name}_review_at"
        last_value = meta.get(last_key)
        interval_days = LOOP_DAYS[loop_name]

        if last_value:
            try:
                baseline_dt = parse_iso(str(last_value))
            except Exception:
                baseline_dt = tracking_start_dt
        else:
            baseline_dt = tracking_start_dt

        elapsed = now_dt - baseline_dt
        if elapsed >= timedelta(days=interval_days):
            due_items.append((loop_name, int(elapsed.total_seconds() // 86400)))

    if not due_items:
        return None

    # LOOP_PRIORITY is sorted from nearest cadence to broadest cadence.
    rank = {name: index for index, name in enumerate(LOOP_PRIORITY)}
    due_items.sort(key=lambda item: rank[item[0]])
    return due_items[0]


def build_loop_prompt(loop_name: str, display_name: str) -> str:
    if loop_name == "weekly":
        return (
            f"Weekly loop ({display_name}): Retrospective over the last 7 days. "
            "Summarize wins, blockers, decisions, and top focus for next 7 days."
        )
    if loop_name == "monthly":
        return (
            f"Monthly loop ({display_name}): Review the last 30 days. "
            "Evaluate progress quality, strategic drift, and major adjustments."
        )
    if loop_name == "quarterly":
        return (
            f"Quarterly loop ({display_name}): Review the last 90 days. "
            "Assess pillar strategy, project portfolio quality, and structural changes needed."
        )
    return (
        f"Yearly loop ({display_name}): 50,000-foot review of the last 365 days. "
        "Reassess mission, operating model, and long-range priorities."
    )


def set_loop_timestamp(pillar_dir: Path, loop_name: str, tz_name: str) -> None:
    meta, body = load_pillar_meta(pillar_dir)
    timestamp = now_iso(tz_name)
    if not meta.get("review_tracking_started_at"):
        meta["review_tracking_started_at"] = timestamp
    meta[f"last_{loop_name}_review_at"] = timestamp
    meta["updated_at"] = timestamp
    write_pillar_meta(pillar_dir, meta, body)


def cmd_onboard(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).resolve()
    display_name = args.pillar_name.strip()
    pillar_slug = slugify(display_name)
    tz_name = args.timezone
    daily_time = validate_time_hhmm(args.daily_brief_time, "daily_brief_time")
    quiet_start = validate_time_hhmm(args.quiet_hours_start, "quiet_hours_start")
    quiet_end = validate_time_hhmm(args.quiet_hours_end, "quiet_hours_end")

    channel_id = args.channel_id or os.environ.get("OPENCLAW_CHANNEL_ID") or os.environ.get("DISCORD_CHANNEL_ID")
    if not channel_id:
        recommended_name = normalize_channel_name(pillar_slug)
        raise QubitError(
            "Onboarding requires a Discord channel ID. Create/bind the channel first, then rerun. "
            f"Recommended Discord-safe channel name: {recommended_name}"
        )

    existing_dir, existing_status = find_pillar_dir(workspace, pillar_slug)
    target_status = args.status
    if target_status not in STATUSES:
        raise QubitError(f"Invalid status {target_status!r}; expected one of {STATUSES}")

    if existing_dir:
        pillar_dir = existing_dir
        status = existing_status
        created = False
    else:
        status = target_status
        pillar_dir = pillars_root(workspace) / status / pillar_slug
        ensure_dir(pillar_dir)
        created = True

    layout = ensure_required_pillar_layout(pillar_dir)

    if (pillar_dir / "pillar.md").exists():
        meta, body = read_markdown(pillar_dir / "pillar.md")
    else:
        meta, body = {}, ""

    timestamp = now_iso(tz_name)
    defaults = {
        "pillar_slug": pillar_slug,
        "display_name": display_name,
        "status": status,
        "schema_version": 1,
        "timezone": tz_name,
        "discord_channel_id": str(channel_id),
        "discord_channel_name": args.channel_name or normalize_channel_name(pillar_slug),
        "daily_brief_time": daily_time,
        "quiet_hours_start": quiet_start,
        "quiet_hours_end": quiet_end,
        "last_weekly_review_at": meta.get("last_weekly_review_at"),
        "last_monthly_review_at": meta.get("last_monthly_review_at"),
        "last_quarterly_review_at": meta.get("last_quarterly_review_at"),
        "last_yearly_review_at": meta.get("last_yearly_review_at"),
        "updated_at": timestamp,
    }
    meta.update(defaults)

    if not body.strip():
        body = (
            "## Pillar Summary\n\n"
            "Track operating context, key constraints, and how this pillar should behave.\n"
        )

    write_pillar_meta(pillar_dir, meta, body)
    manifesto_changed = ensure_manifesto(pillar_dir, pillar_slug, tz_name)

    meta, body, _ = ensure_lifecycle_meta(
        pillar_dir=pillar_dir,
        meta=meta,
        body=body,
        tz_name=tz_name,
        persist=False,
    )
    if created:
        meta["onboarding_status"] = "in_progress"
        meta["onboarding_step"] = "mission"
        meta["onboarding_started_at"] = timestamp
        meta["onboarding_completed_at"] = None
        meta["daily_brief_enabled"] = False
        meta["updated_at"] = timestamp
    write_pillar_meta(pillar_dir, meta, body)

    journal_file = ensure_monthly_journal(pillar_dir, pillar_slug, tz_name)

    cron_path = cron_store_path(workspace)
    cron: dict[str, Any] = {
        "action": "skipped",
        "reason": "onboarding_in_progress",
        "store": str(cron_path),
    }
    if meta.get("onboarding_status") == "completed" and bool(meta.get("daily_brief_enabled")):
        ensure_dir(cron_path.parent)
        cron_action, cron_job_id = upsert_daily_brief_job(cron_path, meta)
        cron = {
            "action": cron_action,
            "jobId": cron_job_id,
            "store": str(cron_path),
        }

    onboarding_status = str(meta.get("onboarding_status") or "in_progress")
    onboarding_step = str(meta.get("onboarding_step") or "mission")
    question = None
    if onboarding_status != "completed":
        question = onboarding_question_for_step(onboarding_step)

    return {
        "status": "ok",
        "workflow": "onboard",
        "pillar_slug": pillar_slug,
        "pillar_dir": str(pillar_dir),
        "created": created,
        "layout": layout,
        "manifesto_updated": manifesto_changed,
        "journal_seeded": str(journal_file),
        "onboarding_status": onboarding_status,
        "onboarding_step": onboarding_step,
        "question": question,
        "cron": cron,
        "next_steps": [
            "Answer the onboarding question in this channel to continue the real-time setup.",
            "Daily brief automation starts automatically after onboarding is completed.",
        ],
    }


def cmd_add_project(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).resolve()
    project_file = create_project(
        workspace=workspace,
        pillar_slug=slugify(args.pillar),
        title=args.title,
        outcome=args.outcome,
        next_decision=args.next_decision,
        next_action=args.next_action,
        due_at=args.due_at,
        status=args.status,
        tags=[tag.strip() for tag in args.tags if tag.strip()],
    )
    return {
        "status": "ok",
        "workflow": "add-project",
        "project_file": str(project_file),
    }


def cmd_daily_brief(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).resolve()
    pillar_slug = slugify(args.pillar)
    pillar_dir, meta = get_or_create_pillar_by_slug(workspace, pillar_slug)
    projects = read_projects(pillar_dir)
    reminders = read_reminders(pillar_dir / "reminders.jsonl")
    brief = format_daily_brief(pillar_slug, meta, projects, reminders)
    return {
        "status": "ok",
        "workflow": "daily-brief",
        "pillar_slug": pillar_slug,
        "run_mode": "autonomous" if args.autonomous else "interactive",
        "message": brief,
    }


def cmd_review_weekly(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).resolve()
    pillar_slug = slugify(args.pillar)
    pillar_dir, meta = get_or_create_pillar_by_slug(workspace, pillar_slug)
    tz_name = str(meta.get("timezone") or DEFAULT_TIMEZONE)
    summary = args.summary.strip() if args.summary else "Weekly retrospective completed."

    journal_file = append_journal_entry(
        pillar_dir=pillar_dir,
        pillar_slug=pillar_slug,
        tz_name=tz_name,
        entry=(
            "Weekly Review\n\n"
            f"{summary}\n\n"
            "Prompt:\n"
            "- What was the highest-leverage decision this week?\n"
            "- What is the one focus for the next 7 days?"
        ),
        source="weekly-review",
    )

    set_loop_timestamp(pillar_dir, "weekly", tz_name)

    return {
        "status": "ok",
        "workflow": "review-weekly",
        "pillar_slug": pillar_slug,
        "journal_file": str(journal_file),
        "message": f"Weekly review logged for {meta.get('display_name', pillar_slug)} and cadence reset.",
    }


def cmd_stage_message_create(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).resolve()
    pillar_slug, pillar_dir, meta, pillar_body = resolve_pillar_context(
        workspace,
        pillar=args.pillar,
        channel_id=args.channel_id,
    )
    tz_name = str(meta.get("timezone") or DEFAULT_TIMEZONE)
    meta, pillar_body, _ = ensure_lifecycle_meta(
        pillar_dir=pillar_dir,
        meta=meta,
        body=pillar_body,
        tz_name=tz_name,
        persist=True,
    )
    enforce_stage_message_policy(workspace, meta)

    delivery_method = normalize_delivery_method(args.delivery_method)
    recipient = validate_stage_recipient(delivery_method, args.recipient)
    message_body = normalize_text(args.body)
    if not message_body:
        raise QubitError("message body is required")
    message_subject = normalize_text(args.subject)
    if delivery_method == "email" and not message_subject:
        raise QubitError("email delivery requires --subject")
    if delivery_method == "whatsapp":
        message_subject = ""

    stage_rows = load_stage_rows_for_pillar(pillar_dir)
    condition = parse_stage_condition(args.parent_stage_id, args.wait_days)
    due_at = normalize_text(args.due)
    if condition and not due_at:
        parent_idx = find_stage_message_index(stage_rows, normalize_text(condition.get("parent_stage_id")))
        if parent_idx < 0:
            raise QubitError(f"Conditional parent stage id not found: {condition.get('parent_stage_id')}")
        parent_row = stage_rows[parent_idx]
        try:
            parent_due = parse_iso(str(parent_row.get("due_at")), fallback_tz=tz_name)
        except Exception as error:
            raise QubitError("Parent stage message has invalid due_at; cannot derive conditional due date") from error
        wait_days = int(condition["wait_days"])
        due_at = (parent_due + timedelta(days=wait_days)).replace(microsecond=0).isoformat()

    due_iso = parse_stage_due_input(due_at, tz_name)
    stage_id = f"stg{uuid.uuid4().hex[:12]}"
    timestamp = now_iso(tz_name)
    row = {
        "id": stage_id,
        "pillar_slug": pillar_slug,
        "origin_channel_id": str(meta.get("discord_channel_id") or ""),
        "origin_channel_name": str(meta.get("discord_channel_name") or ""),
        "delivery_method": delivery_method,
        "recipient": recipient,
        "message_subject": message_subject if delivery_method == "email" else None,
        "message_body": message_body,
        "due_at": due_iso,
        "timezone": tz_name,
        "status": "scheduled",
        "condition": condition,
        "created_at": timestamp,
        "updated_at": timestamp,
        "notified_at": None,
        "completed_at": None,
        "canceled_at": None,
        "dispatch_attempts": 0,
        "last_error": None,
    }
    stage_rows.append(row)
    write_staged_messages(staged_messages_path(pillar_dir), stage_rows)

    cron_path = cron_store_path(workspace)
    ensure_dir(cron_path.parent)
    cron_action, cron_job_id = upsert_stage_message_job(cron_path, meta, row)
    return {
        "status": "ok",
        "workflow": "stage-message-create",
        "pillar_slug": pillar_slug,
        "stage_message_id": stage_id,
        "due_at": due_iso,
        "cron": {
            "action": cron_action,
            "jobId": cron_job_id,
            "store": str(cron_path),
        },
    }


def cmd_stage_message_list(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).resolve()
    pillar_slug, pillar_dir, meta, pillar_body = resolve_pillar_context(
        workspace,
        pillar=args.pillar,
        channel_id=args.channel_id,
    )
    tz_name = str(meta.get("timezone") or DEFAULT_TIMEZONE)
    meta, pillar_body, _ = ensure_lifecycle_meta(
        pillar_dir=pillar_dir,
        meta=meta,
        body=pillar_body,
        tz_name=tz_name,
        persist=True,
    )
    enforce_stage_message_policy(workspace, meta)

    status_filter = normalize_text(args.status).lower()
    if status_filter and status_filter != "all" and status_filter not in STAGE_MESSAGE_STATUSES:
        raise QubitError(f"--status must be one of {STAGE_MESSAGE_STATUSES} or 'all'")

    rows = load_stage_rows_for_pillar(pillar_dir)
    if status_filter and status_filter != "all":
        rows = [row for row in rows if normalize_text(row.get("status")).lower() == status_filter]
    rows = sorted(rows, key=lambda row: normalize_text(row.get("due_at")))
    return {
        "status": "ok",
        "workflow": "stage-message-list",
        "pillar_slug": pillar_slug,
        "stage_messages": rows,
    }


def cmd_stage_message_edit(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).resolve()
    pillar_slug, pillar_dir, meta, pillar_body = resolve_pillar_context(
        workspace,
        pillar=args.pillar,
        channel_id=args.channel_id,
    )
    tz_name = str(meta.get("timezone") or DEFAULT_TIMEZONE)
    meta, pillar_body, _ = ensure_lifecycle_meta(
        pillar_dir=pillar_dir,
        meta=meta,
        body=pillar_body,
        tz_name=tz_name,
        persist=True,
    )
    enforce_stage_message_policy(workspace, meta)

    stage_id = normalize_text(args.stage_id)
    if not stage_id:
        raise QubitError("--stage-id is required")
    rows = load_stage_rows_for_pillar(pillar_dir)
    row_index = find_stage_message_index(rows, stage_id)
    if row_index < 0:
        raise QubitError(f"Unknown stage message id {stage_id!r} in pillar {pillar_slug!r}")

    row = dict(rows[row_index])
    status_before = normalize_text(row.get("status")).lower() or "scheduled"
    if status_before in ("completed", "canceled"):
        raise QubitError(f"Stage message {stage_id} is {status_before} and cannot be edited")

    condition = row.get("condition")
    if args.clear_condition:
        condition = None
    elif args.parent_stage_id or args.wait_days is not None:
        condition = parse_stage_condition(args.parent_stage_id, args.wait_days)
    if isinstance(condition, dict) and normalize_text(condition.get("parent_stage_id")) == stage_id:
        raise QubitError("A staged message cannot reference itself as a conditional parent")

    delivery_method = row.get("delivery_method")
    if args.delivery_method:
        delivery_method = normalize_delivery_method(args.delivery_method)
        row["delivery_method"] = delivery_method

    if args.recipient:
        row["recipient"] = validate_stage_recipient(str(delivery_method), args.recipient)
    elif args.delivery_method:
        existing_recipient = row.get("recipient") or {}
        if not isinstance(existing_recipient, dict):
            existing_recipient = {}
        fallback_value = normalize_text(
            existing_recipient.get("email")
            or existing_recipient.get("phone")
            or existing_recipient.get("handle")
        )
        if not fallback_value:
            raise QubitError("Changing delivery method requires recipient details")
        try:
            row["recipient"] = validate_stage_recipient(str(delivery_method), fallback_value)
        except QubitError as error:
            raise QubitError("Changing delivery method requires a compatible --recipient value") from error

    if args.subject is not None:
        row["message_subject"] = normalize_text(args.subject) or None
    if args.body is not None:
        body = normalize_text(args.body)
        if not body:
            raise QubitError("message body cannot be empty")
        row["message_body"] = body

    if normalize_text(str(row.get("delivery_method"))).lower() == "email":
        if not normalize_text(row.get("message_subject")):
            raise QubitError("email stage messages require message_subject")
    else:
        row["message_subject"] = None

    due_input = normalize_text(args.due)
    if due_input:
        row["due_at"] = parse_stage_due_input(due_input, tz_name)
    elif condition and args.due is None and (args.parent_stage_id or args.wait_days is not None):
        parent_idx = find_stage_message_index(rows, normalize_text(condition.get("parent_stage_id")))
        if parent_idx < 0:
            raise QubitError(f"Conditional parent stage id not found: {condition.get('parent_stage_id')}")
        parent_due = parse_iso(str(rows[parent_idx].get("due_at")), fallback_tz=tz_name)
        row["due_at"] = (parent_due + timedelta(days=int(condition["wait_days"]))).replace(microsecond=0).isoformat()

    row["condition"] = condition
    row["updated_at"] = now_iso(tz_name)
    if args.restage:
        row["status"] = "scheduled"
        row["notified_at"] = None
        row["canceled_at"] = None
        row["completed_at"] = None
        row["last_error"] = None

    rows[row_index] = row
    write_staged_messages(staged_messages_path(pillar_dir), rows)

    cron_path = cron_store_path(workspace)
    ensure_dir(cron_path.parent)
    cron: dict[str, Any]
    if normalize_text(row.get("status")).lower() == "scheduled":
        cron_action, cron_job_id = upsert_stage_message_job(cron_path, meta, row)
        cron = {"action": cron_action, "jobId": cron_job_id, "store": str(cron_path)}
    else:
        removed = remove_managed_stage_message_jobs(cron_path, pillar_slug=pillar_slug, stage_id=stage_id)
        cron = {"action": "removed", "removed_jobs": removed, "store": str(cron_path)}

    return {
        "status": "ok",
        "workflow": "stage-message-edit",
        "pillar_slug": pillar_slug,
        "stage_message_id": stage_id,
        "cron": cron,
    }


def cmd_stage_message_cancel(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).resolve()
    pillar_slug, pillar_dir, meta, pillar_body = resolve_pillar_context(
        workspace,
        pillar=args.pillar,
        channel_id=args.channel_id,
    )
    tz_name = str(meta.get("timezone") or DEFAULT_TIMEZONE)
    meta, pillar_body, _ = ensure_lifecycle_meta(
        pillar_dir=pillar_dir,
        meta=meta,
        body=pillar_body,
        tz_name=tz_name,
        persist=True,
    )
    enforce_stage_message_policy(workspace, meta)

    stage_id = normalize_text(args.stage_id)
    rows = load_stage_rows_for_pillar(pillar_dir)
    row_index = find_stage_message_index(rows, stage_id)
    if row_index < 0:
        raise QubitError(f"Unknown stage message id {stage_id!r} in pillar {pillar_slug!r}")
    row = dict(rows[row_index])
    status_before = normalize_text(row.get("status")).lower()
    if status_before == "canceled":
        return {
            "status": "ok",
            "workflow": "stage-message-cancel",
            "pillar_slug": pillar_slug,
            "stage_message_id": stage_id,
            "action": "already_canceled",
        }
    row["status"] = "canceled"
    row["canceled_at"] = now_iso(tz_name)
    row["updated_at"] = row["canceled_at"]
    rows[row_index] = row
    write_staged_messages(staged_messages_path(pillar_dir), rows)

    cron_path = cron_store_path(workspace)
    removed = remove_managed_stage_message_jobs(cron_path, pillar_slug=pillar_slug, stage_id=stage_id)
    return {
        "status": "ok",
        "workflow": "stage-message-cancel",
        "pillar_slug": pillar_slug,
        "stage_message_id": stage_id,
        "removed_jobs": removed,
    }


def cmd_stage_message_complete(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).resolve()
    pillar_slug, pillar_dir, meta, pillar_body = resolve_pillar_context(
        workspace,
        pillar=args.pillar,
        channel_id=args.channel_id,
    )
    tz_name = str(meta.get("timezone") or DEFAULT_TIMEZONE)
    meta, pillar_body, _ = ensure_lifecycle_meta(
        pillar_dir=pillar_dir,
        meta=meta,
        body=pillar_body,
        tz_name=tz_name,
        persist=True,
    )
    enforce_stage_message_policy(workspace, meta)

    stage_id = normalize_text(args.stage_id)
    rows = load_stage_rows_for_pillar(pillar_dir)
    row_index = find_stage_message_index(rows, stage_id)
    if row_index < 0:
        raise QubitError(f"Unknown stage message id {stage_id!r} in pillar {pillar_slug!r}")
    row = dict(rows[row_index])
    status_before = normalize_text(row.get("status")).lower()
    if status_before == "completed":
        return {
            "status": "ok",
            "workflow": "stage-message-complete",
            "pillar_slug": pillar_slug,
            "stage_message_id": stage_id,
            "action": "already_completed",
        }
    row["status"] = "completed"
    row["completed_at"] = now_iso(tz_name)
    row["updated_at"] = row["completed_at"]
    rows[row_index] = row
    write_staged_messages(staged_messages_path(pillar_dir), rows)

    cron_path = cron_store_path(workspace)
    removed = remove_managed_stage_message_jobs(cron_path, pillar_slug=pillar_slug, stage_id=stage_id)
    return {
        "status": "ok",
        "workflow": "stage-message-complete",
        "pillar_slug": pillar_slug,
        "stage_message_id": stage_id,
        "removed_jobs": removed,
    }


def cmd_stage_message_dispatch(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).resolve()
    pillar_slug, pillar_dir, meta, pillar_body = resolve_pillar_context(
        workspace,
        pillar=args.pillar,
        channel_id=args.channel_id,
    )
    tz_name = str(meta.get("timezone") or DEFAULT_TIMEZONE)
    meta, pillar_body, _ = ensure_lifecycle_meta(
        pillar_dir=pillar_dir,
        meta=meta,
        body=pillar_body,
        tz_name=tz_name,
        persist=True,
    )
    enforce_stage_message_policy(workspace, meta)

    stage_id = normalize_text(args.stage_id)
    if not stage_id:
        raise QubitError("--stage-id is required")
    rows = load_stage_rows_for_pillar(pillar_dir)
    row_index = find_stage_message_index(rows, stage_id)
    if row_index < 0:
        raise QubitError(f"Unknown stage message id {stage_id!r} in pillar {pillar_slug!r}")

    row = dict(rows[row_index])
    now_dt = parse_iso(args.now, fallback_tz=tz_name) if args.now else now_in_tz(tz_name)
    timestamp = now_dt.replace(microsecond=0).isoformat()
    status_before = normalize_text(row.get("status")).lower() or "scheduled"
    if status_before not in ("scheduled", "failed"):
        return {
            "status": "ok",
            "workflow": "stage-message-dispatch",
            "pillar_slug": pillar_slug,
            "stage_message_id": stage_id,
            "action": "skipped",
            "reason": f"status_{status_before}",
        }

    try:
        due_dt = parse_iso(str(row.get("due_at")), fallback_tz=tz_name)
    except Exception:
        row["status"] = "failed"
        row["dispatch_attempts"] = int(row.get("dispatch_attempts") or 0) + 1
        row["last_error"] = "invalid_due_at"
        row["updated_at"] = timestamp
        rows[row_index] = row
        write_staged_messages(staged_messages_path(pillar_dir), rows)
        return {
            "status": "ok",
            "workflow": "stage-message-dispatch",
            "pillar_slug": pillar_slug,
            "stage_message_id": stage_id,
            "action": "failed",
            "reason": "invalid_due_at",
        }

    if due_dt > now_dt:
        return {
            "status": "ok",
            "workflow": "stage-message-dispatch",
            "pillar_slug": pillar_slug,
            "stage_message_id": stage_id,
            "action": "skipped",
            "reason": "not_due_yet",
        }

    allowed, reason = stage_condition_allows_dispatch(row, rows, now_dt)
    if not allowed:
        if reason == "parent_completed":
            row["status"] = "canceled"
            row["canceled_at"] = timestamp
            row["updated_at"] = timestamp
            row["last_error"] = None
            rows[row_index] = row
            write_staged_messages(staged_messages_path(pillar_dir), rows)
            cron_path = cron_store_path(workspace)
            _ = remove_managed_stage_message_jobs(cron_path, pillar_slug=pillar_slug, stage_id=stage_id)
            return {
                "status": "ok",
                "workflow": "stage-message-dispatch",
                "pillar_slug": pillar_slug,
                "stage_message_id": stage_id,
                "action": "canceled",
                "reason": "parent_completed",
            }
        if reason == "wait_window_not_elapsed":
            return {
                "status": "ok",
                "workflow": "stage-message-dispatch",
                "pillar_slug": pillar_slug,
                "stage_message_id": stage_id,
                "action": "skipped",
                "reason": reason,
            }
        row["status"] = "failed"
        row["dispatch_attempts"] = int(row.get("dispatch_attempts") or 0) + 1
        row["last_error"] = reason
        row["updated_at"] = timestamp
        rows[row_index] = row
        write_staged_messages(staged_messages_path(pillar_dir), rows)
        return {
            "status": "ok",
            "workflow": "stage-message-dispatch",
            "pillar_slug": pillar_slug,
            "stage_message_id": stage_id,
            "action": "failed",
            "reason": reason,
        }

    copy_block = format_stage_copy_block(row, str(meta.get("display_name") or pillar_slug))
    row["status"] = "notified"
    row["notified_at"] = timestamp
    row["updated_at"] = timestamp
    row["last_error"] = None
    row["dispatch_attempts"] = int(row.get("dispatch_attempts") or 0) + 1
    rows[row_index] = row
    write_staged_messages(staged_messages_path(pillar_dir), rows)

    cron_path = cron_store_path(workspace)
    _ = remove_managed_stage_message_jobs(cron_path, pillar_slug=pillar_slug, stage_id=stage_id)
    return {
        "status": "ok",
        "workflow": "stage-message-dispatch",
        "pillar_slug": pillar_slug,
        "stage_message_id": stage_id,
        "action": "notified",
        "channel_id": str(meta.get("discord_channel_id") or ""),
        "message": copy_block,
    }


def cmd_heal(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).resolve()
    mode = "check" if bool(args.check) else "apply"
    check_only = mode == "check"

    policy, policy_file = load_health_policy(workspace)
    if not bool(policy.get("checks", {}).get("daily_brief_integrity", True)):
        return {
            "status": "ok",
            "workflow": "heal",
            "mode": mode,
            "action": "skipped",
            "reason": "daily_brief_integrity_disabled",
            "policy_file": str(policy_file),
        }

    target_timezone = str(policy["timezone"])
    window_start_minutes, window_end_minutes = daily_brief_window_bounds(policy)
    blacklist = set(policy.get("channel_blacklist") or [])

    pillar_records: list[dict[str, Any]] = []
    for status in STATUSES:
        status_root = pillars_root(workspace) / status
        if not status_root.exists():
            continue
        for pillar_dir in sorted(path for path in status_root.iterdir() if path.is_dir()):
            meta, body = load_pillar_meta(pillar_dir)
            tz_name = str(meta.get("timezone") or DEFAULT_TIMEZONE)
            meta, body, _ = ensure_lifecycle_meta(
                pillar_dir=pillar_dir,
                meta=meta,
                body=body,
                tz_name=tz_name,
                persist=False,
            )

            pillar_slug = str(meta.get("pillar_slug") or pillar_dir.name)
            onboarding_completed = str(meta.get("onboarding_status") or "") == "completed"
            has_channel_binding = bool(str(meta.get("discord_channel_id") or "").strip())
            blacklisted = is_channel_blacklisted(meta, blacklist)
            eligible = status == "active" and onboarding_completed and not blacklisted and has_channel_binding

            pillar_records.append(
                {
                    "status": status,
                    "pillar_dir": pillar_dir,
                    "pillar_slug": pillar_slug,
                    "meta": meta,
                    "body": body,
                    "onboarding_completed": onboarding_completed,
                    "has_channel_binding": has_channel_binding,
                    "blacklisted": blacklisted,
                    "eligible": eligible,
                }
            )

    eligible_slugs = [record["pillar_slug"] for record in pillar_records if bool(record["eligible"])]
    assignments = allocate_daily_brief_slots(
        eligible_slugs,
        start_minutes=window_start_minutes,
        end_minutes=window_end_minutes,
    )
    assignment_rows = [
        {
            "pillar_slug": pillar_slug,
            "daily_brief_time": assignments[pillar_slug],
            "timezone": target_timezone,
        }
        for pillar_slug in sorted(assignments)
    ]

    issues: list[str] = []
    fixes: list[str] = []
    updated_pillars: list[str] = []
    pillar_by_slug = {record["pillar_slug"]: record for record in pillar_records}

    for record in pillar_records:
        pillar_slug = str(record["pillar_slug"])
        meta = record["meta"]
        body = record["body"]
        changed = False

        if record["eligible"]:
            desired_time = assignments[pillar_slug]
            current_timezone = str(meta.get("timezone") or "")
            if current_timezone != target_timezone:
                issues.append(
                    f"Pillar '{pillar_slug}' timezone drift: expected {target_timezone}, got {current_timezone or 'unset'}"
                )
                if not check_only:
                    meta["timezone"] = target_timezone
                    changed = True
                    fixes.append(f"Pillar '{pillar_slug}': set timezone to {target_timezone}")

            current_daily_time = str(meta.get("daily_brief_time") or "")
            if current_daily_time != desired_time:
                issues.append(
                    f"Pillar '{pillar_slug}' daily_brief_time drift: expected {desired_time}, got {current_daily_time or 'unset'}"
                )
                if not check_only:
                    meta["daily_brief_time"] = desired_time
                    changed = True
                    fixes.append(f"Pillar '{pillar_slug}': set daily_brief_time to {desired_time}")

            if meta.get("daily_brief_enabled") is not True:
                issues.append(f"Pillar '{pillar_slug}' daily brief is disabled but should be enabled")
                if not check_only:
                    meta["daily_brief_enabled"] = True
                    changed = True
                    fixes.append(f"Pillar '{pillar_slug}': enabled daily brief")
        else:
            if record["blacklisted"] and meta.get("daily_brief_enabled") is not False:
                issues.append(f"Pillar '{pillar_slug}' is blacklisted by channel name but daily brief is enabled")
                if not check_only:
                    meta["daily_brief_enabled"] = False
                    changed = True
                    fixes.append(f"Pillar '{pillar_slug}': disabled daily brief because channel is blacklisted")

            if (
                str(record["status"]) == "active"
                and bool(record["onboarding_completed"])
                and not bool(record["blacklisted"])
                and not bool(record["has_channel_binding"])
            ):
                issues.append(
                    f"Pillar '{pillar_slug}' is otherwise eligible but missing discord_channel_id; cannot schedule cron job"
                )

        if changed and not check_only:
            stamp_tz = str(meta.get("timezone") or target_timezone or DEFAULT_TIMEZONE)
            meta["updated_at"] = now_iso(stamp_tz)
            write_pillar_meta(Path(record["pillar_dir"]), meta, body)
            updated_pillars.append(pillar_slug)

    cron_path = cron_store_path(workspace)
    ensure_dir(cron_path.parent)
    cron_data = load_cron_jobs(cron_path)
    cron_jobs = cron_data["jobs"]

    managed_jobs_by_slug: dict[str, list[dict[str, Any]]] = {}
    unmanaged_jobs: list[dict[str, Any]] = []
    for job in cron_jobs:
        managed_slug = managed_job_pillar_slug(job)
        if managed_slug:
            managed_jobs_by_slug.setdefault(managed_slug, []).append(job)
        else:
            unmanaged_jobs.append(job)

    managed_before = sum(len(items) for items in managed_jobs_by_slug.values())
    eligible_set = set(assignments)

    for pillar_slug, grouped_jobs in sorted(managed_jobs_by_slug.items()):
        if pillar_slug not in eligible_set:
            issues.append(f"Cron has managed daily brief job for non-eligible pillar '{pillar_slug}'")
        if len(grouped_jobs) > 1:
            issues.append(f"Cron has duplicate managed daily brief jobs for pillar '{pillar_slug}'")

    for pillar_slug in sorted(eligible_set):
        if pillar_slug not in managed_jobs_by_slug:
            issues.append(f"Cron is missing managed daily brief job for eligible pillar '{pillar_slug}'")

    managed_after = managed_before
    cron_created = 0
    cron_updated = 0
    cron_removed = 0
    if not check_only:
        rebuilt_managed_jobs: list[dict[str, Any]] = []
        existing_kept = 0
        for pillar_slug in sorted(eligible_set):
            record = pillar_by_slug[pillar_slug]
            desired_job = build_daily_brief_job(record["meta"])
            existing_jobs = managed_jobs_by_slug.get(pillar_slug, [])
            if existing_jobs:
                existing_kept += 1
                existing_primary = existing_jobs[0]
                desired_job = preserve_runtime_fields(existing_primary, desired_job)
                if existing_primary != desired_job:
                    cron_updated += 1
            else:
                cron_created += 1
            rebuilt_managed_jobs.append(desired_job)

        managed_after = len(rebuilt_managed_jobs)
        cron_removed = managed_before - existing_kept
        rebuilt_jobs = unmanaged_jobs + rebuilt_managed_jobs
        if rebuilt_jobs != cron_jobs:
            cron_data["jobs"] = rebuilt_jobs
            save_json(cron_path, cron_data)
        else:
            cron_created = 0
            cron_updated = 0
            cron_removed = 0

        if cron_created:
            fixes.append(f"Cron: created {cron_created} managed daily brief job(s)")
        if cron_updated:
            fixes.append(f"Cron: reconciled {cron_updated} managed daily brief job(s)")
        if cron_removed:
            fixes.append(f"Cron: removed {cron_removed} stale/duplicate managed daily brief job(s)")

    action = "checked" if check_only else "applied"
    return {
        "status": "ok",
        "workflow": "heal",
        "mode": mode,
        "action": action,
        "policy_file": str(policy_file),
        "cron_store": str(cron_path),
        "checked_pillars": len(pillar_records),
        "eligible_pillars": sorted(eligible_set),
        "assignments": assignment_rows,
        "updated_pillars": sorted(updated_pillars),
        "issues": issues,
        "fixes": fixes,
        "metrics": {
            "managed_jobs_before": managed_before,
            "managed_jobs_after": managed_after,
            "cron_jobs_created": cron_created,
            "cron_jobs_updated": cron_updated,
            "cron_jobs_removed": cron_removed,
            "issue_count": len(issues),
            "fix_count": len(fixes),
        },
    }


def cmd_sync_cron(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).resolve()
    pillar_slug = slugify(args.pillar)
    pillar_dir, meta, body = get_or_create_pillar_state_by_slug(workspace, pillar_slug)
    tz_name = str(meta.get("timezone") or DEFAULT_TIMEZONE)
    meta, body, lifecycle_changed = ensure_lifecycle_meta(
        pillar_dir=pillar_dir,
        meta=meta,
        body=body,
        tz_name=tz_name,
        persist=True,
    )
    policy, policy_file = load_health_policy(workspace)
    blacklist = set(policy.get("channel_blacklist") or [])

    if is_channel_blacklisted(meta, blacklist):
        cron_path = cron_store_path(workspace)
        removed_jobs = 0
        if cron_path.exists():
            removed_jobs = remove_managed_daily_brief_jobs(cron_path, pillar_slug=pillar_slug)

        metadata_updated = False
        if meta.get("daily_brief_enabled") is not False:
            meta["daily_brief_enabled"] = False
            meta["updated_at"] = now_iso(str(meta.get("timezone") or DEFAULT_TIMEZONE))
            write_pillar_meta(pillar_dir, meta, body)
            metadata_updated = True

        return {
            "status": "ok",
            "workflow": "sync-cron",
            "pillar_dir": str(pillar_dir),
            "cron_store": str(cron_path),
            "policy_file": str(policy_file),
            "action": "skipped",
            "reason": "blacklisted_channel",
            "removed_jobs": removed_jobs,
            "lifecycle_updated": lifecycle_changed,
            "metadata_updated": metadata_updated,
        }

    if meta.get("onboarding_status") != "completed" or not bool(meta.get("daily_brief_enabled")):
        return {
            "status": "ok",
            "workflow": "sync-cron",
            "pillar_dir": str(pillar_dir),
            "cron_store": str(cron_store_path(workspace)),
            "policy_file": str(policy_file),
            "action": "skipped",
            "reason": "onboarding_incomplete",
            "lifecycle_updated": lifecycle_changed,
        }

    if not str(meta.get("discord_channel_id") or "").strip():
        raise QubitError(f"Pillar '{pillar_slug}' has no discord_channel_id; cannot create cron job yet.")

    cron_path = cron_store_path(workspace)
    ensure_dir(cron_path.parent)
    action, job_id = upsert_daily_brief_job(cron_path, meta)

    return {
        "status": "ok",
        "workflow": "sync-cron",
        "pillar_dir": str(pillar_dir),
        "cron_store": str(cron_path),
        "policy_file": str(policy_file),
        "action": action,
        "jobId": job_id,
    }


def cmd_sync_heartbeat(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).resolve()
    heartbeat_path = workspace / "HEARTBEAT.md"
    script_path = workspace / "skills" / "qubit" / "scripts" / "qubit.py"

    content = (
        "# HEARTBEAT.md\n\n"
        "# Qubit global heartbeat checklist\n"
        "# This is autonomous mode. Do not ask conversational questions unless blocked.\n\n"
        "1. Run: `python3 "
        + str(script_path)
        + " --workspace "
        + str(workspace)
        + " --json due-scan`\n"
        "2. If due-scan has no due actions, reply exactly: HEARTBEAT_OK\n"
        "3. If due actions exist, execute due item(s) and post concise updates in the mapped Discord channels.\n"
        "4. Loop prompts are only for pillars with completed onboarding and review tracking history.\n"
    )

    heartbeat_path.write_text(content, encoding="utf-8")

    return {
        "status": "ok",
        "workflow": "sync-heartbeat",
        "heartbeat_file": str(heartbeat_path),
    }


def cmd_due_scan(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).resolve()
    scan_now = parse_iso(args.now) if args.now else now_in_tz(DEFAULT_TIMEZONE)

    due_actions: list[dict[str, Any]] = []
    policy, _policy_file = load_health_policy(workspace)
    blacklist = set(policy.get("channel_blacklist") or [])

    for pillar_dir in list_active_pillars(workspace):
        meta, body = load_pillar_meta(pillar_dir)
        pillar_slug = str(meta.get("pillar_slug") or pillar_dir.name)
        display_name = str(meta.get("display_name") or pillar_slug)
        tz_name = str(meta.get("timezone") or DEFAULT_TIMEZONE)
        meta, _body, _ = ensure_lifecycle_meta(
            pillar_dir=pillar_dir,
            meta=meta,
            body=body,
            tz_name=tz_name,
            persist=False,
        )

        local_now = scan_now.astimezone(ZoneInfo(tz_name))
        quiet_start = str(meta.get("quiet_hours_start") or DEFAULT_QUIET_HOURS_START)
        quiet_end = str(meta.get("quiet_hours_end") or DEFAULT_QUIET_HOURS_END)
        quiet = in_quiet_hours(local_now, quiet_start, quiet_end)

        reminders = read_reminders(pillar_dir / "reminders.jsonl")
        overdue = []
        for reminder in reminders:
            if str(reminder.get("status")) != "pending":
                continue
            due_at = reminder.get("due_at")
            if not due_at:
                continue
            try:
                due_dt = parse_iso(str(due_at))
            except Exception:
                continue
            if due_dt <= local_now:
                overdue.append(reminder)

        for reminder in overdue:
            due_actions.append(
                {
                    "type": "reminder",
                    "pillar_slug": pillar_slug,
                    "display_name": display_name,
                    "channel_id": meta.get("discord_channel_id"),
                    "urgent": True,
                    "message": reminder.get("message"),
                    "due_at": reminder.get("due_at"),
                }
            )

        if not is_channel_blacklisted(meta, blacklist):
            stage_rows = load_stage_rows_for_pillar(pillar_dir)
            for stage_row in stage_rows:
                if normalize_text(stage_row.get("status")).lower() != "scheduled":
                    continue
                stage_due_at = stage_row.get("due_at")
                if not stage_due_at:
                    continue
                try:
                    stage_due_dt = parse_iso(str(stage_due_at), fallback_tz=tz_name)
                except Exception:
                    continue
                if stage_due_dt > local_now:
                    continue
                allowed, condition_reason = stage_condition_allows_dispatch(stage_row, stage_rows, local_now)
                if not allowed and condition_reason == "wait_window_not_elapsed":
                    continue
                stage_id = normalize_text(stage_row.get("id"))
                if not stage_id:
                    continue
                due_actions.append(
                    {
                        "type": "stage_message",
                        "pillar_slug": pillar_slug,
                        "display_name": display_name,
                        "channel_id": meta.get("discord_channel_id"),
                        "urgent": True,
                        "stage_message_id": stage_id,
                        "due_at": stage_due_at,
                        "condition_reason": condition_reason,
                        "copy_ready": format_stage_copy_block(stage_row, display_name),
                        "dispatch_command": f"qubit {pillar_slug} stage message dispatch {stage_id}",
                    }
                )

        if meta.get("onboarding_status") != "completed":
            continue

        due_loop = pick_due_loop(meta, local_now)
        if due_loop:
            loop_name, overdue_days = due_loop
            if quiet:
                # Loop prompts are non-urgent; skip during quiet hours.
                continue
            due_actions.append(
                {
                    "type": "loop",
                    "pillar_slug": pillar_slug,
                    "display_name": display_name,
                    "channel_id": meta.get("discord_channel_id"),
                    "urgent": False,
                    "loop": loop_name,
                    "overdue_days": overdue_days,
                    "prompt": build_loop_prompt(loop_name, display_name),
                }
            )

    return {
        "status": "ok",
        "workflow": "due-scan",
        "checked_at": scan_now.replace(microsecond=0).isoformat(),
        "due_actions": due_actions,
    }


def cmd_mark_loop(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).resolve()
    loop_name = args.loop
    if loop_name not in LOOP_DAYS:
        raise QubitError(f"Unknown loop {loop_name!r}; expected one of {tuple(LOOP_DAYS)}")

    pillar_slug = slugify(args.pillar)
    pillar_dir, meta = get_or_create_pillar_by_slug(workspace, pillar_slug)
    tz_name = str(meta.get("timezone") or DEFAULT_TIMEZONE)

    set_loop_timestamp(pillar_dir, loop_name, tz_name)
    return {
        "status": "ok",
        "workflow": "mark-loop",
        "pillar_slug": pillar_slug,
        "loop": loop_name,
        "updated_at": now_iso(tz_name),
    }


def cmd_ingest_message(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).resolve()
    message = args.message

    explicit = parse_explicit_command(message)
    if explicit:
        workflow, payload = explicit

        if workflow == "heal":
            result = cmd_heal(
                argparse.Namespace(
                    workspace=str(workspace),
                    check=False,
                )
            )
            result["source"] = "explicit-command"
            return result

        if workflow == "heal-check":
            result = cmd_heal(
                argparse.Namespace(
                    workspace=str(workspace),
                    check=True,
                )
            )
            result["source"] = "explicit-command"
            return result

        if workflow == "onboard":
            onboard_args = argparse.Namespace(
                workspace=str(workspace),
                pillar_name=payload["pillar"],
                status="active",
                channel_id=args.channel_id,
                channel_name=args.channel_name,
                timezone=args.timezone,
                daily_brief_time=args.daily_brief_time,
                quiet_hours_start=args.quiet_hours_start,
                quiet_hours_end=args.quiet_hours_end,
            )
            result = cmd_onboard(onboard_args)
            result["source"] = "explicit-command"
            return result

        if workflow == "daily-brief":
            result = cmd_daily_brief(
                argparse.Namespace(
                    workspace=str(workspace),
                    pillar=payload["pillar"],
                    autonomous=args.autonomous,
                )
            )
            result["source"] = "explicit-command"
            return result

        if workflow == "review-weekly":
            result = cmd_review_weekly(
                argparse.Namespace(
                    workspace=str(workspace),
                    pillar=payload["pillar"],
                    summary=args.review_summary,
                )
            )
            result["source"] = "explicit-command"
            return result

        if workflow == "add-project":
            result = cmd_add_project(
                argparse.Namespace(
                    workspace=str(workspace),
                    pillar=payload["pillar"],
                    title=payload["title"],
                    outcome="Define desired outcome.",
                    next_decision="Clarify immediate decision.",
                    next_action="Define next action.",
                    due_at=None,
                    status="active",
                    tags=[],
                )
            )
            result["source"] = "explicit-command"
            return result

        if workflow == "stage-message-list":
            result = cmd_stage_message_list(
                argparse.Namespace(
                    workspace=str(workspace),
                    pillar=payload["pillar"],
                    channel_id=None,
                    status="all",
                )
            )
            result["source"] = "explicit-command"
            return result

        if workflow == "stage-message-cancel":
            result = cmd_stage_message_cancel(
                argparse.Namespace(
                    workspace=str(workspace),
                    pillar=payload["pillar"],
                    channel_id=None,
                    stage_id=payload["stage_id"],
                )
            )
            result["source"] = "explicit-command"
            return result

        if workflow == "stage-message-complete":
            result = cmd_stage_message_complete(
                argparse.Namespace(
                    workspace=str(workspace),
                    pillar=payload["pillar"],
                    channel_id=None,
                    stage_id=payload["stage_id"],
                )
            )
            result["source"] = "explicit-command"
            return result

        if workflow == "stage-message-dispatch":
            result = cmd_stage_message_dispatch(
                argparse.Namespace(
                    workspace=str(workspace),
                    pillar=payload["pillar"],
                    channel_id=None,
                    stage_id=payload["stage_id"],
                    now=None,
                )
            )
            result["source"] = "explicit-command"
            return result

        if workflow == "stage-message-alias":
            pillar_slug = slugify(payload["pillar"])
            result = {
                "status": "ok",
                "workflow": "stage-message-intent",
                "pillar_slug": pillar_slug,
                "alias": payload["alias"],
                "clarification": {
                    "question": "Stage Message intent detected. Share delivery method, recipient, due time, and message body.",
                    "options": [
                        "Use email",
                        "Use WhatsApp",
                        "Cancel this intent",
                    ],
                    "notes": [],
                },
            }
            result["source"] = "explicit-command"
            return result

    if args.pillar:
        pillar_slug = slugify(args.pillar)
        pillar_dir, meta, pillar_body = get_or_create_pillar_state_by_slug(workspace, pillar_slug)
    else:
        if not args.channel_id:
            raise QubitError("ingest-message requires --pillar or --channel-id")
        pillar_slug, pillar_dir, meta, pillar_body = parse_pillar_from_channel(workspace, args.channel_id)
        if not pillar_slug:
            raise QubitError(f"No pillar mapping found for channel ID {args.channel_id}")

    tz_name = str(meta.get("timezone") or DEFAULT_TIMEZONE)
    meta, pillar_body, _ = ensure_lifecycle_meta(
        pillar_dir=pillar_dir,
        meta=meta,
        body=pillar_body,
        tz_name=tz_name,
        persist=True,
    )

    if meta.get("onboarding_status") != "completed":
        if args.autonomous:
            return {
                "status": "ok",
                "workflow": "onboarding-pending",
                "pillar_slug": pillar_slug,
                "onboarding_status": "in_progress",
                "completed": False,
                "question": None,
            }
        return run_onboarding_turn(
            workspace=workspace,
            pillar_dir=pillar_dir,
            pillar_slug=pillar_slug,
            meta=meta,
            pillar_body=pillar_body,
            message=message,
        )

    inferred_actions, uncertainties = infer_actions(message, pillar_slug, tz_name)

    applied: list[str] = []
    pending_confirmation: list[dict[str, Any]] = []

    for action in inferred_actions:
        if action.risk == "low" and action.confidence >= 0.55:
            applied.append(apply_action(workspace, pillar_slug, meta, action))
            continue

        # Explicit command path is already handled above. High-risk inferred actions stay pending.
        pending_confirmation.append(
            {
                "type": action.action_type,
                "reason": action.reason,
                "risk": action.risk,
                "confidence": action.confidence,
                "payload": action.payload,
            }
        )

    stage_message_suggestion = None
    if not args.autonomous:
        policy, _policy_file = load_health_policy(workspace)
        blacklist = set(policy.get("channel_blacklist") or [])
        if not is_channel_blacklisted(meta, blacklist):
            now_dt = now_in_tz(tz_name)
            if should_offer_stage_suggestion(workspace, pillar_slug, now_dt):
                suggestion = infer_stage_message_suggestion(message, tz_name)
                if suggestion:
                    due_text = normalize_text(suggestion.get("due_at")) or "tomorrow at 09:00 (Asia/Kolkata)"
                    method_text = normalize_text(suggestion.get("delivery_method")) or "email"
                    recipient_text = normalize_text(suggestion.get("recipient_hint")) or "(recipient needed)"
                    assumption_note = ""
                    if bool(suggestion.get("due_assumed")):
                        due_source = normalize_text(suggestion.get("due_source")) or "context"
                        assumption_note = (
                            f" I assumed {due_source}. Confirm or adjust before scheduling."
                        )
                    stage_message_suggestion = {
                        "question": (
                            "Want me to stage this message for later? "
                            f"Proposed method={method_text}, recipient={recipient_text}, due={due_text}.{assumption_note}"
                        ),
                        "options": [
                            "Stage now with these defaults",
                            "Adjust details before staging",
                            "Skip staging for now",
                        ],
                        "proposal": suggestion,
                    }
                    mark_stage_suggestion_sent(workspace, pillar_slug, now_dt)

    clarification = None
    if (uncertainties or pending_confirmation) and not args.autonomous:
        options = []
        if pending_confirmation:
            first = pending_confirmation[0]
            options.append(f"Apply pending action: {first['type']}")
        options.append("Keep journal-only update")
        options.append("Provide more detail")

        clarification = {
            "question": "I found actions with lower confidence or higher risk. Which path do you want?",
            "options": options,
            "notes": uncertainties,
        }

    return {
        "status": "ok",
        "workflow": "ingest-message",
        "pillar_slug": pillar_slug,
        "applied_actions": applied,
        "pending_confirmation": pending_confirmation,
        "uncertainties": uncertainties,
        "clarification": clarification,
        "stage_message_suggestion": stage_message_suggestion,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Qubit v1 workspace workflow engine")
    parser.add_argument(
        "--workspace",
        default=str(script_default_workspace()),
        help="Workspace root path (defaults to detected OpenClaw workspace)",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON only")

    subparsers = parser.add_subparsers(dest="command", required=True)

    onboard = subparsers.add_parser("onboard", help="Initialize or repair a pillar")
    onboard.add_argument("--pillar-name", required=True)
    onboard.add_argument("--status", default="active", choices=STATUSES)
    onboard.add_argument("--channel-id")
    onboard.add_argument("--channel-name")
    onboard.add_argument("--timezone", default=DEFAULT_TIMEZONE)
    onboard.add_argument("--daily-brief-time", default=DEFAULT_DAILY_BRIEF_TIME)
    onboard.add_argument("--quiet-hours-start", default=DEFAULT_QUIET_HOURS_START)
    onboard.add_argument("--quiet-hours-end", default=DEFAULT_QUIET_HOURS_END)
    onboard.set_defaults(func=cmd_onboard)

    add_project = subparsers.add_parser("add-project", help="Create or update a project")
    add_project.add_argument("--pillar", required=True)
    add_project.add_argument("--title", required=True)
    add_project.add_argument("--outcome", default="Define desired outcome.")
    add_project.add_argument("--next-decision", default="Clarify immediate decision.")
    add_project.add_argument("--next-action", default="Define next action.")
    add_project.add_argument("--due-at")
    add_project.add_argument("--status", default="active", choices=PROJECT_STATUSES)
    add_project.add_argument("--tags", nargs="*", default=[])
    add_project.set_defaults(func=cmd_add_project)

    daily_brief = subparsers.add_parser("daily-brief", help="Generate immediate daily brief")
    daily_brief.add_argument("--pillar", required=True)
    daily_brief.add_argument("--autonomous", action="store_true")
    daily_brief.set_defaults(func=cmd_daily_brief)

    review_weekly = subparsers.add_parser("review-weekly", help="Run weekly review now and reset cadence")
    review_weekly.add_argument("--pillar", required=True)
    review_weekly.add_argument("--summary")
    review_weekly.set_defaults(func=cmd_review_weekly)

    stage_create = subparsers.add_parser("stage-message-create", help="Create a staged message for future reminder delivery")
    stage_create.add_argument("--pillar")
    stage_create.add_argument("--channel-id")
    stage_create.add_argument("--delivery-method", required=True, choices=STAGE_DELIVERY_METHODS)
    stage_create.add_argument("--recipient", required=True)
    stage_create.add_argument("--subject", default="")
    stage_create.add_argument("--body", required=True)
    stage_create.add_argument("--due")
    stage_create.add_argument("--parent-stage-id")
    stage_create.add_argument("--wait-days", type=int)
    stage_create.set_defaults(func=cmd_stage_message_create)

    stage_list = subparsers.add_parser("stage-message-list", help="List staged messages in a pillar")
    stage_list.add_argument("--pillar")
    stage_list.add_argument("--channel-id")
    stage_list.add_argument("--status", default="all")
    stage_list.set_defaults(func=cmd_stage_message_list)

    stage_edit = subparsers.add_parser("stage-message-edit", help="Edit a staged message")
    stage_edit.add_argument("--pillar")
    stage_edit.add_argument("--channel-id")
    stage_edit.add_argument("--stage-id", required=True)
    stage_edit.add_argument("--delivery-method", choices=STAGE_DELIVERY_METHODS)
    stage_edit.add_argument("--recipient")
    stage_edit.add_argument("--subject")
    stage_edit.add_argument("--body")
    stage_edit.add_argument("--due")
    stage_edit.add_argument("--parent-stage-id")
    stage_edit.add_argument("--wait-days", type=int)
    stage_edit.add_argument("--clear-condition", action="store_true")
    stage_edit.add_argument("--restage", action="store_true")
    stage_edit.set_defaults(func=cmd_stage_message_edit)

    stage_cancel = subparsers.add_parser("stage-message-cancel", help="Cancel a staged message")
    stage_cancel.add_argument("--pillar")
    stage_cancel.add_argument("--channel-id")
    stage_cancel.add_argument("--stage-id", required=True)
    stage_cancel.set_defaults(func=cmd_stage_message_cancel)

    stage_complete = subparsers.add_parser("stage-message-complete", help="Mark a staged message as completed")
    stage_complete.add_argument("--pillar")
    stage_complete.add_argument("--channel-id")
    stage_complete.add_argument("--stage-id", required=True)
    stage_complete.set_defaults(func=cmd_stage_message_complete)

    stage_dispatch = subparsers.add_parser("stage-message-dispatch", help="Dispatch a staged message when due")
    stage_dispatch.add_argument("--pillar")
    stage_dispatch.add_argument("--channel-id")
    stage_dispatch.add_argument("--stage-id", required=True)
    stage_dispatch.add_argument("--now", help="ISO datetime override")
    stage_dispatch.set_defaults(func=cmd_stage_message_dispatch)

    sync_cron = subparsers.add_parser("sync-cron", help="Ensure daily brief cron entry for a pillar")
    sync_cron.add_argument("--pillar", required=True)
    sync_cron.set_defaults(func=cmd_sync_cron)

    heal = subparsers.add_parser("heal", help="Audit and repair daily brief schedule integrity")
    heal.add_argument("--check", action="store_true", help="Report issues without applying fixes")
    heal.set_defaults(func=cmd_heal)

    sync_heartbeat = subparsers.add_parser("sync-heartbeat", help="Write global heartbeat checklist")
    sync_heartbeat.set_defaults(func=cmd_sync_heartbeat)

    due_scan = subparsers.add_parser("due-scan", help="Scan active pillars for due reminders/staged messages/loops")
    due_scan.add_argument("--now", help="ISO datetime override")
    due_scan.set_defaults(func=cmd_due_scan)

    mark_loop = subparsers.add_parser("mark-loop", help="Mark a loop run as completed")
    mark_loop.add_argument("--pillar", required=True)
    mark_loop.add_argument("--loop", required=True, choices=tuple(LOOP_DAYS))
    mark_loop.set_defaults(func=cmd_mark_loop)

    ingest = subparsers.add_parser("ingest-message", help="Parse a Discord message into actions")
    ingest.add_argument("--message", required=True)
    ingest.add_argument("--pillar")
    ingest.add_argument("--channel-id")
    ingest.add_argument("--channel-name")
    ingest.add_argument("--autonomous", action="store_true")
    ingest.add_argument("--timezone", default=DEFAULT_TIMEZONE)
    ingest.add_argument("--daily-brief-time", default=DEFAULT_DAILY_BRIEF_TIME)
    ingest.add_argument("--quiet-hours-start", default=DEFAULT_QUIET_HOURS_START)
    ingest.add_argument("--quiet-hours-end", default=DEFAULT_QUIET_HOURS_END)
    ingest.add_argument("--review-summary")
    ingest.set_defaults(func=cmd_ingest_message)

    return parser


def render_result(result: dict[str, Any], as_json: bool) -> str:
    if as_json:
        return json.dumps(result, indent=2, ensure_ascii=True)

    lines = [f"status: {result.get('status', 'ok')}"]
    workflow = result.get("workflow")
    if workflow:
        lines.append(f"workflow: {workflow}")

    if "message" in result:
        lines.append("")
        lines.append(str(result["message"]))

    for key in (
        "pillar_slug",
        "pillar_dir",
        "project_file",
        "journal_file",
        "heartbeat_file",
        "policy_file",
        "cron_store",
        "mode",
        "action",
        "jobId",
        "onboarding_status",
        "onboarding_step",
        "captured_field",
        "completed",
        "reason",
        "checked_pillars",
        "stage_message_id",
        "due_at",
        "removed_jobs",
        "channel_id",
    ):
        if key in result and result[key] is not None:
            lines.append(f"{key}: {result[key]}")

    if "question" in result and result["question"] is not None:
        lines.append(f"question: {result['question']}")

    if "cron" in result and isinstance(result["cron"], dict):
        lines.append(f"cron: {result['cron']}")

    if result.get("applied_actions"):
        lines.append("applied_actions:")
        for item in result["applied_actions"]:
            lines.append(f"- {item}")

    if result.get("pending_confirmation"):
        lines.append("pending_confirmation:")
        for item in result["pending_confirmation"]:
            lines.append(f"- {item['type']} ({item['risk']}, confidence={item['confidence']})")

    if result.get("uncertainties"):
        lines.append("uncertainties:")
        for note in result["uncertainties"]:
            lines.append(f"- {note}")

    if result.get("clarification"):
        clarification = result["clarification"]
        lines.append("clarification:")
        lines.append(f"- {clarification['question']}")
        for option in clarification.get("options", []):
            lines.append(f"- option: {option}")

    if result.get("stage_message_suggestion"):
        suggestion = result["stage_message_suggestion"]
        lines.append("stage_message_suggestion:")
        lines.append(f"- {suggestion['question']}")
        for option in suggestion.get("options", []):
            lines.append(f"- option: {option}")

    if result.get("due_actions") is not None:
        lines.append(f"due_actions_count: {len(result['due_actions'])}")

    if result.get("stage_messages"):
        lines.append("stage_messages:")
        for row in result["stage_messages"]:
            lines.append(
                "- "
                + f"{row.get('id')} | {row.get('status')} | {row.get('delivery_method')} | "
                + f"{row.get('due_at')} | recipient={row.get('recipient')}"
            )

    if result.get("eligible_pillars"):
        lines.append("eligible_pillars:")
        for pillar_slug in result["eligible_pillars"]:
            lines.append(f"- {pillar_slug}")

    if result.get("assignments"):
        lines.append("assignments:")
        for row in result["assignments"]:
            lines.append(f"- {row['pillar_slug']} @ {row['daily_brief_time']} ({row['timezone']})")

    if result.get("updated_pillars"):
        lines.append("updated_pillars:")
        for pillar_slug in result["updated_pillars"]:
            lines.append(f"- {pillar_slug}")

    if result.get("issues"):
        lines.append("issues:")
        for item in result["issues"]:
            lines.append(f"- {item}")

    if result.get("fixes"):
        lines.append("fixes:")
        for item in result["fixes"]:
            lines.append(f"- {item}")

    if isinstance(result.get("metrics"), dict):
        lines.append(f"metrics: {result['metrics']}")

    return "\n".join(lines)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        result = args.func(args)
    except QubitError as error:
        if args.json:
            print(json.dumps({"status": "error", "error": str(error)}, ensure_ascii=True))
        else:
            print(f"error: {error}")
        return 1

    print(render_result(result, as_json=args.json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

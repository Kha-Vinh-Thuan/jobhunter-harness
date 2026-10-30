"""Handle Codex lifecycle events without deriving task outcomes from tool activity."""

import hashlib
import json
from pathlib import Path

from .progress import ProgressStore, atomic_json, now, validate_progress
from .workspace import repository_checks


EVENTS = {"SessionStart", "PreCompact", "Interrupt", "Stop"}


def handle_event(root: Path, event: str, payload: dict) -> dict:
    if event not in EVENTS or not isinstance(payload, dict):
        raise ValueError("Unsupported lifecycle event or invalid JSON payload")
    store = ProgressStore(root)
    if event == "Stop":
        # Never create an infinite continuation, including malformed active flags.
        if payload.get("stop_hook_active") is True:
            return {}
        try:
            validate_progress(root, store.read())
        except (ValueError, OSError, KeyError) as error:
            return {"decision": "block", "reason": f"Progress needs correction: {error}. Correct recorded state or document the blocker; do not invent verification."}
        return {}
    session = str(payload.get("session_id", "unknown"))[:200]
    turn = payload.get("turn_id")
    if event in ("PreCompact", "Interrupt"):
        store.checkpoint(event, session, turn)
        return {}
    issues = []
    try:
        checks = repository_checks(root)
        issues.extend(f"{item['id']} repository missing: {item['path']} ({', '.join(item['missing'])})"
                      for item in checks if item["status"] != "available")
        data = store.read()
        validate_progress(root, data)
        active = data["active_task_id"] or "none assigned"
        task = next((t for t in data["tasks"] if t["id"] == active), None)
        detail = f"Active task: {active}; progress revision {data['revision']}."
        if task:
            detail += f" Status: {task['status']}. Next action: {task['next_action'][:500]}"
    except (ValueError, OSError, KeyError) as error:
        issues.append(str(error))
        detail = "Progress is unavailable; diagnose before editing."
    context = (f"Jobhunter DEVELOPMENT harness v1.0.0 at {root}. "
               "Read AGENTS.md and prompts/system.md, then only relevant context/skills. "
               "Application code belongs in the bound backend/Odoo repositories; this folder holds harness files only. "
               "Repository instructions in sibling folders must be loaded explicitly. " + detail)
    if issues:
        context += " Setup issues: " + "; ".join(issues)
    return {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}}


def observe_invocation(root: Path, event: str, payload: dict) -> None:
    """Record invocation metadata only; this is not an attestation of hook trust."""
    key = hashlib.sha256(f"{payload.get('session_id')}:{payload.get('turn_id')}:{event}".encode()).hexdigest()[:24]
    with ProgressStore(root).locked():
        atomic_json(root / ".state" / "hooks" / f"{key}.json", {
            "event": event, "recorded_at": now(), "session_id": payload.get("session_id"),
            "turn_id": payload.get("turn_id"), "trust": "not_attested"})

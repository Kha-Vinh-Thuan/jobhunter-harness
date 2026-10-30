"""Validate engineering progress and serialize every mutation with optimistic locking."""

import copy
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows
    fcntl = None
    import msvcrt

from jsonschema import Draft202012Validator, FormatChecker

from .workspace import read_json, repositories, revision


class ProgressError(ValueError):
    """Invalid engineering state; no write has been committed."""


class RevisionConflict(ProgressError):
    """Another coordinator or hook wrote a newer revision."""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="." + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        if os.name == "posix":  # Windows cannot open a directory to fsync it
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def validate_progress(root: Path, data: dict, current_task: str | None = None) -> None:
    schema = read_json(root / "schemas/progress.schema.json")
    errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(data),
                    key=lambda error: str(list(error.path)))
    if errors:
        raise ProgressError("; ".join(f"{list(e.path)}: {e.message}" for e in errors))
    tasks = {task["id"]: task for task in data["tasks"]}
    if len(tasks) != len(data["tasks"]):
        raise ProgressError("Task IDs must be unique")
    active = data["active_task_id"]
    if active is not None and active not in tasks:
        raise ProgressError("active_task_id must reference an existing task")
    roots = [root.resolve(), *repositories(root).values()]
    for task in tasks.values():
        criteria = {item["id"] for item in task["acceptance_criteria"]}
        if len(criteria) != len(task["acceptance_criteria"]):
            raise ProgressError(f"{task['id']}: acceptance IDs must be unique")
        if any(dep not in tasks or dep == task["id"] for dep in task["dependencies"]):
            raise ProgressError(f"{task['id']}: invalid dependency")
        if task["status"] in ("in_progress", "completed") and any(
                tasks[dep]["status"] != "completed" for dep in task["dependencies"]):
            raise ProgressError(f"{task['id']}: dependencies must be completed")
        if task["status"] == "blocked" and not (task["blocker"] and task["next_action"].strip()):
            raise ProgressError(f"{task['id']}: blocked work requires blocker and next action")
        latest = {}
        for item in task["evidence"]:
            if not set(item["acceptance_ids"]) <= criteria:
                raise ProgressError(f"{task['id']}: evidence references unknown acceptance IDs")
            recorded_at = datetime.fromisoformat(item["recorded_at"].replace("Z", "+00:00"))
            for key in item["acceptance_ids"]:
                previous = latest.get(key)
                # Timestamp order, not JSON array order, determines current evidence.
                # Equal-time disagreement conservatively preserves the non-pass.
                if previous is None or recorded_at > previous[0] or (recorded_at == previous[0] and item["result"] != "passed"):
                    latest[key] = (recorded_at, item["result"], item["repository_revision"])
            if item["result"] != "passed":
                continue
            path = (root / item["reference"]).resolve()
            if not any(path.is_relative_to(base) for base in roots):
                raise ProgressError(f"{task['id']}: evidence must be a local file in a bound workspace")
            if not path.is_file() or path.stat().st_size == 0:
                raise ProgressError(f"{task['id']}: missing or empty evidence file {item['reference']}")
            if task["repository"] != "harness" and task["status"] == "completed":
                if not item["repository_revision"]:
                    raise ProgressError(f"{task['id']}: external evidence requires a repository revision")
        if task["status"] == "completed":
            if task["verification"] != "passed" or set(latest) != criteria or any(result != "passed" for _, result, _ in latest.values()) or task["blocker"] or not task["note"].strip():
                raise ProgressError(f"{task['id']}: completion requires passed evidence for every criterion, a note, and no blocker")
            if task["repository"] != "harness" and task["id"] == current_task:
                expected = revision(repositories(root)[task["repository"]])
                if not expected or any(ref != expected for _, _, ref in latest.values()):
                    raise ProgressError(f"{task['id']}: latest evidence does not match current repository revision")
    def visit(task_id: str, stack: set[str], done: set[str]) -> None:
        if task_id in stack:
            raise ProgressError("Cyclic task dependencies")
        if task_id in done:
            return
        for dep in tasks[task_id]["dependencies"]:
            visit(dep, stack | {task_id}, done)
        done.add(task_id)
    done: set[str] = set()
    for task_id in tasks:
        visit(task_id, set(), done)


class ProgressStore:
    """Only the coordinator changes tasks; hooks share this lock for checkpoints."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.path = self.root / "progress.json"

    @contextmanager
    def locked(self):
        state = self.root / ".state"
        state.mkdir(exist_ok=True)
        with (state / "progress.lock").open("a", encoding="utf-8") as lock:
            if fcntl:
                fcntl.flock(lock, fcntl.LOCK_EX)
            else:
                lock.seek(0)
                while True:  # LK_LOCK gives up after ~10s; keep blocking like flock
                    try:
                        msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
                        break
                    except OSError:
                        pass
            try:
                yield
            finally:
                if fcntl:
                    fcntl.flock(lock, fcntl.LOCK_UN)
                else:
                    lock.seek(0)
                    msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)

    def read(self) -> dict:
        return read_json(self.path)

    def update_task(self, task_id: str, expected_revision: int, changes: dict) -> dict:
        allowed = {"status", "verification", "evidence", "blocker", "next_action", "note"}
        if not changes or set(changes) - allowed:
            raise ProgressError("Only task status, verification, evidence, blocker, next_action and note can change")
        with self.locked():
            current = self.read()
            if current["revision"] != expected_revision:
                raise RevisionConflict(f"Expected revision {expected_revision}; current revision is {current['revision']}")
            value = copy.deepcopy(current)
            task = next((t for t in value["tasks"] if t["id"] == task_id), None)
            if task is None:
                raise ProgressError(f"Unknown task {task_id}")
            transitions = {"pending": {"pending", "in_progress", "blocked"},
                           "in_progress": {"in_progress", "blocked", "completed"},
                           "blocked": {"blocked", "in_progress", "pending"},
                           "completed": {"completed", "in_progress"}}
            if changes.get("status", task["status"]) not in transitions[task["status"]]:
                raise ProgressError(f"Invalid transition from {task['status']}")
            task.update(changes)
            task["updated_at"] = value["updated_at"] = now()
            value["revision"] += 1
            if task["status"] in ("in_progress", "blocked"):
                value["active_task_id"] = task_id
            elif value["active_task_id"] == task_id:
                value["active_task_id"] = None
            validate_progress(self.root, value, current_task=task_id if task["status"] == "completed" else None)
            atomic_json(self.path, value)
            return value

    def checkpoint(self, event: str, session_id: str, turn_id: str | None = None) -> Path:
        with self.locked():
            data = self.read()
            validate_progress(self.root, data)
            path = self.root / ".state" / "checkpoint.json"
            atomic_json(path, {"event": event, "session_id": session_id, "turn_id": turn_id,
                               "recorded_at": now(), "progress": data})
            return path

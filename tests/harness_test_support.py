"""Isolated harness fixtures; every generated file stays under harness/.state."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


HARNESS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS_ROOT / "scripts"))


class HarnessTestCase(unittest.TestCase):
    def setUp(self) -> None:
        state_dir = HARNESS_ROOT / ".state"
        state_dir.mkdir(exist_ok=True)
        self._temporary_directory = tempfile.TemporaryDirectory(
            prefix="test-", dir=state_dir
        )
        self.addCleanup(self._temporary_directory.cleanup)
        self.root = Path(self._temporary_directory.name)
        shutil.copytree(HARNESS_ROOT / "schemas", self.root / "schemas")
        self.backend = self.root / "fixture-backend"
        self.odoo = self.root / "fixture-odoo"
        (self.backend / "backend" / "app").mkdir(parents=True)
        (self.odoo / "addons" / "hr_recruitment").mkdir(parents=True)
        manifest = {
            "schema_version": "1.0.0",
            "harness_version": "1.0.0",
            "name": "jobhunter-harness",
            "repositories": {
                "backend": {
                    "path": "fixture-backend",
                    "required_paths": ["backend/app"],
                },
                "odoo": {
                    "path": "fixture-odoo",
                    "required_paths": ["addons/hr_recruitment"],
                },
            },
        }
        (self.root / "harness.json").write_text(json.dumps(manifest))
        (self.root / "AGENTS.md").write_text(
            "# Development harness\nApplication code belongs in the bound repositories.\n"
        )
        (self.root / "prompts").mkdir()
        (self.root / "prompts" / "system.md").write_text(
            "Inspect, implement the assigned task, verify, and record evidence.\n"
        )
        self.progress = {
            "schema_version": "1.0.0",
            "harness_version": "1.0.0",
            "revision": 0,
            "updated_at": "2026-10-30T00:00:00Z",
            "active_task_id": "HAR-001",
            "tasks": [self.task("HAR-001")],
        }
        self.write_progress(self.progress)

    def task(self, task_id: str, **changes: object) -> dict:
        task = {
            "id": task_id,
            "title": f"Verify {task_id}",
            "requirement_refs": ["REQ-001"],
            "repository": "harness",
            "dependencies": [],
            "acceptance_criteria": [
                {"id": f"{task_id}-ac-1", "description": "First observable result"},
                {"id": f"{task_id}-ac-2", "description": "Second observable result"},
            ],
            "status": "pending",
            "verification": "not_run",
            "evidence": [],
            "blocker": None,
            "next_action": "Inspect the assigned implementation and run its checks.",
            "note": "Implementation has not started.",
            "updated_at": "2026-10-30T00:00:00Z",
        }
        task.update(changes)
        return task

    def write_progress(self, progress: dict) -> None:
        self.progress = copy.deepcopy(progress)
        (self.root / "progress.json").write_text(json.dumps(progress, indent=2))

    def evidence(
        self,
        acceptance_ids: list[str] | None = None,
        *,
        reference: str = ".state/evidence/check.txt",
        result: str = "passed",
        create_file: bool = True,
    ) -> dict:
        if create_file:
            path = Path(reference)
            if not path.is_absolute():
                path = self.root / path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Verified an observable result; check exit status: 0.\n")
        return {
            "acceptance_ids": acceptance_ids
            or ["HAR-001-ac-1", "HAR-001-ac-2"],
            "result": result,
            "command": "python3 -m unittest discover -s tests",
            "reference": reference,
            "recorded_at": "2026-10-30T00:00:00Z",
            "repository_revision": None,
        }

    def completed_changes(self, **changes: object) -> dict:
        result = {
            "status": "completed",
            "verification": "passed",
            "evidence": [self.evidence()],
            "blocker": None,
            "next_action": "No further action is required for this assignment.",
            "note": "Both acceptance criteria were verified against saved test output.",
        }
        result.update(changes)
        return result

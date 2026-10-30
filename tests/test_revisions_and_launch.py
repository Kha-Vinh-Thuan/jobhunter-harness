"""Verify external worktree evidence and explicitly selected launcher write roots."""

from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
from unittest.mock import patch

from harness_test_support import HarnessTestCase
from harnesslib.cli import launch
from harnesslib.progress import ProgressError, ProgressStore
from harnesslib.workspace import repository_checks, revision


class RevisionAndLaunchTests(HarnessTestCase):
    def git(self, repository: Path, *arguments: str) -> str:
        command = [
            "git", "-C", str(repository),
            "-c", "core.hooksPath=/dev/null",
            "-c", "user.name=Harness Fixture",
            "-c", "user.email=harness-fixture@example.invalid",
            "-c", "commit.gpgsign=false",
            *arguments,
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()

    def initialize_backend(self) -> str:
        self.git(self.backend, "init", "--quiet")
        (self.backend / "implementation.txt").write_text("Original implementation.\n")
        self.git(self.backend, "add", "implementation.txt")
        self.git(self.backend, "commit", "--quiet", "-m", "Fixture baseline")
        return revision(self.backend)

    def external_evidence(self, task_id: str, fingerprint: str, minute: int = 0) -> dict:
        evidence = self.evidence(
            [f"{task_id}-ac-1", f"{task_id}-ac-2"],
            reference=f".state/evidence/{task_id}-{minute}.txt",
        )
        evidence["repository_revision"] = fingerprint
        evidence["recorded_at"] = f"2026-10-30T00:{minute:02d}:00Z"
        return evidence

    def test_worktree_fingerprint_changes_for_tracked_and_untracked_edits(self) -> None:
        baseline = self.initialize_backend()
        tracked = self.backend / "implementation.txt"
        tracked.write_text("Changed implementation.\n")
        dirty = revision(self.backend)
        self.assertNotEqual(baseline, dirty)
        self.assertEqual(dirty, revision(self.backend))

        tracked.write_text("Original implementation.\n")
        self.assertEqual(baseline, revision(self.backend))
        untracked = self.backend / "new-feature.txt"
        untracked.write_text("New behavior.\n")
        first = revision(self.backend)
        untracked.write_text("Different new behavior.\n")
        self.assertNotEqual(baseline, first)
        self.assertNotEqual(first, revision(self.backend))

    def test_untracked_path_and_contents_have_distinct_fingerprint_boundaries(self) -> None:
        self.initialize_backend()
        first_file = self.backend / "a"
        first_file.write_text("bc")
        first = revision(self.backend)
        first_file.unlink()
        (self.backend / "ab").write_text("c")

        self.assertNotEqual(first, revision(self.backend))

    def test_multiple_historical_external_tasks_can_reopen_after_new_commit(self) -> None:
        baseline = self.initialize_backend()
        tasks = []
        for task_id in ("HAR-001", "HAR-002"):
            tasks.append(self.task(
                task_id,
                repository="backend",
                status="completed",
                verification="passed",
                evidence=[self.external_evidence(task_id, baseline)],
                note="The original acceptance checks passed for the recorded revision.",
            ))
        self.progress.update(tasks=tasks, active_task_id=None)
        self.write_progress(self.progress)
        (self.backend / "implementation.txt").write_text("New committed implementation.\n")
        self.git(self.backend, "add", "implementation.txt")
        self.git(self.backend, "commit", "--quiet", "-m", "Fixture next revision")
        self.assertNotEqual(baseline, revision(self.backend))
        store = ProgressStore(self.root)

        first = store.update_task("HAR-001", 0, {
            "status": "in_progress", "verification": "not_run",
            "note": "Refresh after the implementation revision changed.",
        })
        second = store.update_task("HAR-002", first["revision"], {
            "status": "in_progress", "verification": "not_run",
            "note": "Independently refresh another historical task.",
        })

        self.assertEqual(["in_progress", "in_progress"], [t["status"] for t in second["tasks"]])

    def test_new_completion_requires_the_current_dirty_worktree_fingerprint(self) -> None:
        baseline = self.initialize_backend()
        self.progress["tasks"][0]["repository"] = "backend"
        self.write_progress(self.progress)
        store = ProgressStore(self.root)
        store.update_task("HAR-001", 0, {"status": "in_progress"})
        (self.backend / "implementation.txt").write_text("Uncommitted changed behavior.\n")
        stale = self.external_evidence("HAR-001", baseline)

        with self.assertRaises(ProgressError):
            store.update_task("HAR-001", 1, self.completed_changes(evidence=[stale]))

        current = self.external_evidence("HAR-001", revision(self.backend), minute=1)
        result = store.update_task("HAR-001", 1, self.completed_changes(evidence=[current]))
        self.assertEqual("completed", result["tasks"][0]["status"])

    def test_refreshed_completion_preserves_historical_passes(self) -> None:
        baseline = self.initialize_backend()
        self.progress["tasks"][0]["repository"] = "backend"
        self.write_progress(self.progress)
        store = ProgressStore(self.root)
        store.update_task("HAR-001", 0, {"status": "in_progress"})
        historical = self.external_evidence("HAR-001", baseline)
        store.update_task("HAR-001", 1, self.completed_changes(evidence=[historical]))
        (self.backend / "implementation.txt").write_text("Refreshed implementation.\n")
        store.update_task("HAR-001", 2, {
            "status": "in_progress", "verification": "not_run",
            "note": "Source changed; keep prior evidence while re-verifying.",
        })
        fresh = self.external_evidence("HAR-001", revision(self.backend), minute=1)

        completed = store.update_task(
            "HAR-001", 3, self.completed_changes(evidence=[historical, fresh])
        )

        self.assertEqual("completed", completed["tasks"][0]["status"])
        self.assertEqual([historical, fresh], completed["tasks"][0]["evidence"])

    def dry_launch(self, write_repositories: list[str]) -> dict:
        arguments = argparse.Namespace(
            prompt=["--", "Inspect the assigned task without implementation."],
            write_repo=write_repositories,
            dry_run=True,
        )
        output = io.StringIO()
        with patch("harnesslib.cli.shutil.which", return_value="/fixture/codex"):
            with patch("harnesslib.cli.subprocess.run") as process:
                with redirect_stdout(output):
                    self.assertEqual(0, launch(self.root, arguments))
                process.assert_not_called()
        return json.loads(output.getvalue())

    def test_launcher_has_no_external_writable_roots_by_default(self) -> None:
        result = self.dry_launch([])
        self.assertEqual([], result["write_repositories"])
        self.assertNotIn("--add-dir", result["argv"])
        self.assertEqual(str(self.root), result["cwd"])
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", result["argv"])

    def test_launcher_adds_only_the_explicit_repository_once(self) -> None:
        result = self.dry_launch(["backend", "backend"])
        arguments = result["argv"]
        self.assertEqual(1, arguments.count("--add-dir"))
        index = arguments.index("--add-dir")
        self.assertEqual(str(self.backend), arguments[index + 1])
        self.assertNotIn(str(self.odoo), arguments)

    def test_missing_bound_repository_is_reported_and_prevents_launch(self) -> None:
        (self.backend / "backend" / "app").rmdir()
        checks = {item["id"]: item for item in repository_checks(self.root)}
        self.assertEqual("missing", checks["backend"]["status"])
        self.assertIn("backend/app", checks["backend"]["missing"])

        with self.assertRaises(ProgressError):
            self.dry_launch([])

"""Verify progress invariants, evidence checks, and serialized atomic updates."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import copy
import json
import threading

from harness_test_support import HarnessTestCase
from harnesslib.progress import (
    ProgressError,
    ProgressStore,
    RevisionConflict,
    validate_progress,
)


class ProgressStoreTests(HarnessTestCase):
    def test_read_preserves_pending_work_without_inference(self) -> None:
        before = (self.root / "progress.json").read_bytes()

        result = ProgressStore(self.root).read()

        self.assertEqual("pending", result["tasks"][0]["status"])
        self.assertEqual("not_run", result["tasks"][0]["verification"])
        self.assertEqual(before, (self.root / "progress.json").read_bytes())

    def test_started_work_can_complete_with_saved_acceptance_evidence(self) -> None:
        store = ProgressStore(self.root)
        started = store.update_task("HAR-001", 0, {"status": "in_progress"})
        completed = store.update_task(
            "HAR-001", started["revision"], self.completed_changes()
        )

        self.assertEqual(2, completed["revision"])
        self.assertEqual("completed", completed["tasks"][0]["status"])
        self.assertEqual(completed, store.read())

    def test_pending_cannot_jump_directly_to_completed(self) -> None:
        store = ProgressStore(self.root)
        before = store.read()

        with self.assertRaises(ProgressError):
            store.update_task("HAR-001", 0, self.completed_changes())

        self.assertEqual(before, store.read())

    def test_stale_revision_cannot_overwrite_newer_progress(self) -> None:
        store = ProgressStore(self.root)
        started = store.update_task("HAR-001", 0, {"status": "in_progress"})

        with self.assertRaises(RevisionConflict):
            store.update_task("HAR-001", 0, {"note": "An obsolete update."})

        self.assertEqual(started, store.read())

    def test_blocked_requires_a_reason_and_action(self) -> None:
        store = ProgressStore(self.root)
        for changes in (
            {"status": "blocked", "blocker": None},
            {"status": "blocked", "blocker": "Waiting for provider", "next_action": ""},
        ):
            with self.subTest(changes=changes), self.assertRaises(ProgressError):
                store.update_task("HAR-001", 0, changes)

        result = store.update_task(
            "HAR-001",
            0,
            {
                "status": "blocked",
                "blocker": "The target repository is unavailable.",
                "next_action": "Restore the configured repository path.",
            },
        )
        self.assertEqual("blocked", result["tasks"][0]["status"])

    def test_dependency_must_complete_before_dependent_work_starts(self) -> None:
        self.progress["tasks"].append(self.task("HAR-002", dependencies=["HAR-001"]))
        self.write_progress(self.progress)
        store = ProgressStore(self.root)

        with self.assertRaises(ProgressError):
            store.update_task("HAR-002", 0, {"status": "in_progress"})

        store.update_task("HAR-001", 0, {"status": "in_progress"})
        store.update_task("HAR-001", 1, self.completed_changes())
        result = store.update_task("HAR-002", 2, {"status": "in_progress"})
        self.assertEqual("in_progress", result["tasks"][1]["status"])

    def test_completion_requires_every_acceptance_criterion_to_have_passed(self) -> None:
        for evidence in (
            [],
            [self.evidence(["HAR-001-ac-1"])],
            [self.evidence(result="failed")],
            [self.evidence(result="not_run")],
            [self.evidence(result="not_applicable")],
        ):
            with self.subTest(evidence=evidence):
                self.write_progress(self.progress)
                store = ProgressStore(self.root)
                store.update_task("HAR-001", 0, {"status": "in_progress"})
                with self.assertRaises(ProgressError):
                    store.update_task(
                        "HAR-001", 1, self.completed_changes(evidence=evidence)
                    )
                self.assertEqual("in_progress", store.read()["tasks"][0]["status"])

    def test_new_failed_evidence_cannot_be_hidden_by_an_older_pass(self) -> None:
        store = ProgressStore(self.root)
        store.update_task("HAR-001", 0, {"status": "in_progress"})
        passed = self.evidence()
        failed = self.evidence(
            ["HAR-001-ac-1"], reference=".state/evidence/failed-check.txt", result="failed"
        )
        failed["recorded_at"] = "2026-10-30T00:01:00Z"

        for items in ([passed, failed], [failed, passed]):
            with self.subTest(order=[item["recorded_at"] for item in items]):
                with self.assertRaises(ProgressError):
                    store.update_task(
                        "HAR-001", 1, self.completed_changes(evidence=items)
                    )

        self.assertEqual("in_progress", store.read()["tasks"][0]["status"])

    def test_completion_rejects_missing_empty_or_remote_only_evidence(self) -> None:
        missing = self.evidence(reference=".state/missing.txt", create_file=False)
        empty = self.evidence(reference=".state/empty.txt")
        (self.root / empty["reference"]).write_text("")
        remote = self.evidence(reference="https://example.com/check", create_file=False)
        for evidence in (missing, empty, remote):
            with self.subTest(reference=evidence["reference"]):
                self.write_progress(self.progress)
                store = ProgressStore(self.root)
                store.update_task("HAR-001", 0, {"status": "in_progress"})
                with self.assertRaises(ProgressError):
                    store.update_task(
                        "HAR-001", 1, self.completed_changes(evidence=[evidence])
                    )

    def test_completion_rejects_uncovered_or_unknown_acceptance_ids(self) -> None:
        store = ProgressStore(self.root)
        store.update_task("HAR-001", 0, {"status": "in_progress"})
        evidence = self.evidence(["HAR-001-ac-1", "HAR-001-ac-2", "invented-ac"])

        with self.assertRaises(ProgressError):
            store.update_task("HAR-001", 1, self.completed_changes(evidence=[evidence]))

    def test_completion_requires_passed_verification_note_and_no_blocker(self) -> None:
        for changes in (
            {"verification": "not_run"},
            {"note": ""},
            {"blocker": "Still missing an input."},
        ):
            with self.subTest(changes=changes):
                self.write_progress(self.progress)
                store = ProgressStore(self.root)
                store.update_task("HAR-001", 0, {"status": "in_progress"})
                with self.assertRaises(ProgressError):
                    store.update_task("HAR-001", 1, self.completed_changes(**changes))

    def test_completed_work_can_reopen_for_refresh(self) -> None:
        store = ProgressStore(self.root)
        store.update_task("HAR-001", 0, {"status": "in_progress"})
        store.update_task("HAR-001", 1, self.completed_changes())

        result = store.update_task(
            "HAR-001",
            2,
            {
                "status": "in_progress",
                "verification": "not_run",
                "evidence": [],
                "note": "Source context changed; refresh the prior verification.",
            },
        )

        self.assertEqual("in_progress", result["tasks"][0]["status"])
        self.assertEqual("not_run", result["tasks"][0]["verification"])

    def test_task_identity_and_acceptance_criteria_cannot_be_rewritten(self) -> None:
        store = ProgressStore(self.root)
        for changes in (
            {"id": "replacement"},
            {"acceptance_criteria": []},
            {"requirement_refs": []},
        ):
            with self.subTest(changes=changes), self.assertRaises(ProgressError):
                store.update_task("HAR-001", 0, changes)

        self.assertEqual(0, store.read()["revision"])

    def test_invalid_schema_and_unknown_tasks_fail_without_rewriting_file(self) -> None:
        invalid = copy.deepcopy(self.progress)
        invalid["unexpected"] = "Strict schema must reject unknown fields."
        self.write_progress(invalid)
        before = (self.root / "progress.json").read_bytes()
        with self.assertRaises(ProgressError):
            validate_progress(self.root, ProgressStore(self.root).read())
        self.assertEqual(before, (self.root / "progress.json").read_bytes())

        self.write_progress(self.progress_without_unexpected())
        with self.assertRaises(ProgressError):
            ProgressStore(self.root).update_task("HAR-999", 0, {"status": "in_progress"})

    def progress_without_unexpected(self) -> dict:
        result = copy.deepcopy(self.progress)
        result.pop("unexpected", None)
        return result

    def test_concurrent_updates_have_one_winner_and_valid_json(self) -> None:
        barrier = threading.Barrier(2)

        def attempt(note: str) -> str:
            barrier.wait(timeout=5)
            try:
                ProgressStore(self.root).update_task("HAR-001", 0, {"note": note})
            except RevisionConflict:
                return "conflict"
            return "updated"

        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(attempt, "First concurrently proposed note.")
            second = executor.submit(attempt, "Second concurrently proposed note.")
            results = [first.result(timeout=10), second.result(timeout=10)]

        self.assertCountEqual(["updated", "conflict"], results)
        parsed = json.loads((self.root / "progress.json").read_text())
        self.assertEqual(1, parsed["revision"])
        self.assertIn(
            parsed["tasks"][0]["note"],
            ["First concurrently proposed note.", "Second concurrently proposed note."],
        )

    def test_checkpoints_preserve_task_statuses(self) -> None:
        store = ProgressStore(self.root)
        before = store.read()

        checkpoint = store.checkpoint("Interrupt", "session-fixture", "turn-fixture")

        self.assertTrue(checkpoint.is_file())
        self.assertTrue(checkpoint.is_relative_to(self.root / ".state"))
        self.assertEqual(before["tasks"], store.read()["tasks"])
        self.assertEqual(before["active_task_id"], store.read()["active_task_id"])
        contents = json.loads(checkpoint.read_text())
        self.assertIn("pending", json.dumps(contents))

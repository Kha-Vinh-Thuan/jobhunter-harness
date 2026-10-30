"""Exercise Codex hook events without claiming native hook activation."""

from __future__ import annotations

import json
import shutil

from harness_test_support import HarnessTestCase
from harnesslib.hooks import handle_event, observe_invocation
from harnesslib.progress import ProgressStore


class HookTests(HarnessTestCase):
    def payload(self, **changes: object) -> dict:
        result = {"session_id": "fixture-session", "turn_id": "fixture-turn"}
        result.update(changes)
        return result

    def test_session_start_returns_project_context(self) -> None:
        before = ProgressStore(self.root).read()

        result = handle_event(self.root, "SessionStart", self.payload())

        specific = result["hookSpecificOutput"]
        self.assertEqual("SessionStart", specific["hookEventName"])
        self.assertIsInstance(specific["additionalContext"], str)
        self.assertTrue(specific["additionalContext"].strip())
        self.assertEqual(before["tasks"], ProgressStore(self.root).read()["tasks"])

    def test_missing_repository_produces_actionable_context(self) -> None:
        shutil.rmtree(self.backend)

        result = handle_event(self.root, "SessionStart", self.payload())

        context = result["hookSpecificOutput"]["additionalContext"].lower()
        self.assertIn("backend", context)
        self.assertTrue(
            any(word in context for word in ("missing", "unavailable", "not found", "does not exist")),
            context,
        )

    def test_pending_and_blocked_assignments_do_not_force_continuation(self) -> None:
        self.assertEqual({}, handle_event(self.root, "Stop", self.payload()))
        ProgressStore(self.root).update_task(
            "HAR-001",
            0,
            {
                "status": "blocked",
                "blocker": "A required input is unavailable.",
                "next_action": "Ask the owner to provide the missing input.",
            },
        )
        self.assertEqual({}, handle_event(self.root, "Stop", self.payload()))

    def test_invalid_progress_requests_one_continuation(self) -> None:
        (self.root / "progress.json").write_text("{invalid JSON")

        first = handle_event(self.root, "Stop", self.payload(stop_hook_active=False))
        repeated = handle_event(self.root, "Stop", self.payload(stop_hook_active=True))

        self.assertEqual("block", first["decision"])
        self.assertTrue(first["reason"].strip())
        self.assertEqual({}, repeated)

    def test_lost_evidence_prevents_a_completed_assignment_claim(self) -> None:
        store = ProgressStore(self.root)
        store.update_task("HAR-001", 0, {"status": "in_progress"})
        completed = store.update_task("HAR-001", 1, self.completed_changes())
        evidence_path = self.root / completed["tasks"][0]["evidence"][0]["reference"]
        evidence_path.unlink()

        result = handle_event(self.root, "Stop", self.payload(stop_hook_active=False))

        self.assertEqual("block", result["decision"])
        self.assertTrue(result["reason"].strip())
        self.assertEqual({}, handle_event(self.root, "Stop", self.payload(stop_hook_active=True)))

    def test_compaction_and_interrupt_only_save_checkpoints(self) -> None:
        before = ProgressStore(self.root).read()

        for event in ("PreCompact", "Interrupt"):
            with self.subTest(event=event):
                handle_event(self.root, event, self.payload())

        after = ProgressStore(self.root).read()
        self.assertEqual(before["tasks"], after["tasks"])
        self.assertEqual(before["active_task_id"], after["active_task_id"])
        self.assertTrue(list((self.root / ".state").rglob("*.json")))

    def test_blocked_work_stays_blocked_after_compaction(self) -> None:
        store = ProgressStore(self.root)
        before = store.update_task(
            "HAR-001",
            0,
            {
                "status": "blocked",
                "blocker": "A target service is unavailable.",
                "next_action": "Restore service access before resuming work.",
            },
        )

        handle_event(self.root, "PreCompact", self.payload())

        self.assertEqual(before["tasks"], store.read()["tasks"])
        self.assertEqual("blocked", store.read()["tasks"][0]["status"])

    def test_invocation_logs_exclude_chat_and_candidate_payloads(self) -> None:
        candidate_marker = "PRIVATE-CANDIDATE-ANSWER-12345"
        secret_marker = "PRIVATE-SECRET-VALUE-67890"
        payload = self.payload(
            last_assistant_message=candidate_marker,
            transcript=candidate_marker,
            api_key=secret_marker,
        )

        observe_invocation(self.root, "SessionStart", payload)

        logs = list((self.root / ".state" / "hooks").glob("*.json"))
        self.assertEqual(1, len(logs))
        contents = logs[0].read_text()
        self.assertNotIn(candidate_marker, contents)
        self.assertNotIn(secret_marker, contents)
        self.assertEqual("not_attested", json.loads(contents)["trust"])

    def test_hook_simulation_never_claims_native_activation(self) -> None:
        handle_event(self.root, "SessionStart", self.payload())
        handle_event(self.root, "PreCompact", self.payload())
        handle_event(self.root, "Stop", self.payload())

        for path in (self.root / ".state").rglob("*.json"):
            contents = json.loads(path.read_text())
            serialized = json.dumps(contents).lower()
            self.assertNotIn('"native_activation": true', serialized)
            self.assertNotIn('"native_hooks_active": true', serialized)

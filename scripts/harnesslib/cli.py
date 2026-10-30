"""Expose explicit development commands; starting Codex is the only launcher action."""

import argparse
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from .hooks import EVENTS, handle_event, observe_invocation
from .progress import ProgressError, ProgressStore
from .validation import validate
from .workspace import doctor, read_json, repositories, repository_checks, revision


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    commands = command.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Inspect paths and executables; no application calls")
    commands.add_parser("validate", help="Validate harness files, configuration and progress")
    start = commands.add_parser("start", help="Launch Codex with the harness as working root")
    start.add_argument("--write-repo", choices=("backend", "odoo"), action="append", default=[])
    start.add_argument("--dry-run", action="store_true")
    start.add_argument("prompt", nargs=argparse.REMAINDER)
    hook = commands.add_parser("hook", help="Handle or simulate one Codex lifecycle JSON payload on stdin")
    hook.add_argument("event", choices=sorted(EVENTS))
    hook.add_argument("--native", action="store_true", help="Record invocation metadata, never attest trust")
    progress = commands.add_parser("progress", help="Coordinator-only engineering state management")
    actions = progress.add_subparsers(dest="action", required=True)
    actions.add_parser("show")
    fingerprint = actions.add_parser("fingerprint", help="Record HEAD plus dirty-worktree fingerprint for evidence")
    fingerprint.add_argument("--repo", choices=("backend", "odoo"), required=True)
    update = actions.add_parser("update")
    update.add_argument("task")
    update.add_argument("--expected-revision", type=int, required=True)
    update.add_argument("--status", choices=("pending", "in_progress", "blocked", "completed"))
    update.add_argument("--verification", choices=("not_run", "passed", "failed", "not_applicable"))
    update.add_argument("--note")
    update.add_argument("--next-action")
    update.add_argument("--blocker", help="An empty string clears a resolved blocker")
    update.add_argument("--evidence", type=Path, help="Append a JSON array of evidence records")
    update.add_argument("--acceptance", action="append", help="Set acceptance IDs on appended evidence")
    return command


def launch(root: Path, args: argparse.Namespace) -> int:
    missing = [item for item in repository_checks(root) if item["status"] != "available"]
    if missing:
        raise ProgressError(f"Repository bindings unavailable: {missing}. Run doctor or configure harness.local.json.")
    prompt = args.prompt
    if prompt and prompt[0] == "--":
        prompt = prompt[1:]
    guidance = (root / "prompts/system.md").read_text(encoding="utf-8")
    request = " ".join(prompt) or "Read AGENTS.md and progress.json. Inspect the next pending task and report its prerequisites; do not implement it yet."
    full_prompt = f"Project operating guidance (subordinate to host instructions):\n{guidance}\n\nCurrent assignment:\n{request}"
    binary = shutil.which("codex") or "codex"
    argv = [binary, "--strict-config", "-C", str(root), "-c", 'project_root_markers=["harness.json"]']
    for name in dict.fromkeys(args.write_repo):
        argv.extend(["--add-dir", str(repositories(root)[name])])
    argv.append(full_prompt)
    if args.dry_run:
        print(json.dumps({"cwd": str(root), "write_repositories": args.write_repo,
                          "argv": argv, "shell_preview": shlex.join(argv)}, indent=2))
        return 0
    if not shutil.which("codex"):
        raise ProgressError("Codex CLI is unavailable; install/sign in through the normal Codex setup.")
    return subprocess.run(argv, cwd=root, check=False).returncode


def update_progress(root: Path, args: argparse.Namespace) -> dict:
    store = ProgressStore(root)
    changes = {name: getattr(args, name) for name in ("status", "verification", "note", "next_action", "blocker")
               if getattr(args, name) is not None}
    if changes.get("blocker") == "":
        changes["blocker"] = None
    if args.acceptance and not args.evidence:
        raise ProgressError("--acceptance requires --evidence")
    if args.evidence:
        records = json.loads(args.evidence.read_text(encoding="utf-8"))
        if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
            raise ProgressError("Evidence input must be a JSON array of records")
        if args.acceptance:
            for item in records:
                item["acceptance_ids"] = args.acceptance
        task = next((t for t in store.read()["tasks"] if t["id"] == args.task), None)
        if not task:
            raise ProgressError(f"Unknown task {args.task}")
        changes["evidence"] = task["evidence"] + records
    return store.update_task(args.task, args.expected_revision, changes)


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    args = parser().parse_args()
    try:
        if args.command == "start":
            return launch(root, args)
        if args.command == "doctor":
            output = doctor(root)
            code = int(not output["python_supported"] or not output["executables"]["codex"] or any(x["status"] != "available" for x in output["repositories"]))
        elif args.command == "validate":
            output = validate(root)
            code = int(output["status"] != "passed")
        elif args.command == "hook":
            payload = json.load(sys.stdin)
            output = handle_event(root, args.event, payload)
            if args.native:
                observe_invocation(root, args.event, payload)
            code = 0
        elif args.action == "show":
            output, code = read_json(root / "progress.json"), 0
        elif args.action == "fingerprint":
            output = {"repository": args.repo, "revision": revision(repositories(root)[args.repo])}
            code = int(output["revision"] is None)
        else:
            output, code = update_progress(root, args), 0
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return code
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        # JSON stdout remains machine-readable for command hooks and automation.
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 1

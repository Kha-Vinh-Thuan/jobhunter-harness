# Jobhunter harness

A separate **Codex development harness** for building Jobhunter as an AI extension of the existing Odoo internal app. This folder holds the working loop, context, skills, subagent definitions, progress and lifecycle helpers. It contains no application codebase and does not run the recruiting agents.

The application repositories remain separate:

| Key | Default sibling directory | Owns |
| --- | --- | --- |
| `backend` | `../Jobhunter-Platform` | Python agents, contracts, provider integration, durable runtime and future backend AWS pipeline |
| `odoo` | `../sea-hkt-t10` | Existing Odoo app and the new extension addon |

`harness.json` binds these repositories. Use ignored `harness.local.json` overrides when your checkout locations differ. Only known repository `path` fields may be overridden, for example:

```json
{
  "repositories": {
    "backend": {"path": "../../work/Jobhunter-Platform"},
    "odoo": {"path": "../../work/sea-hkt-t10"}
  }
}
```

Relative paths resolve from this harness; absolute paths are also accepted. The launcher keeps this folder as its working directory.

## Setup and checks

Use Python 3.12+ and an installed, signed-in Codex CLI. From this directory:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/harness.py doctor
.venv/bin/python scripts/harness.py validate
.venv/bin/python -m unittest discover -s tests -v
```

On Windows, use `python -m venv .venv` and `.venv\Scripts\python.exe` in place of `.venv/bin/python`. Helpers and tests run there; the shipped Codex hook commands are POSIX shell, so native hooks need Git Bash or WSL as the hook shell. The relocated-checkout hook test skips when symlinks are unavailable.

Use an explicit Python 3.12+ executable when creating the environment: `python3` resolves to Python 3.11 in the observed checkout. After setup, use `.venv/bin/python` for all helper commands.

The helpers validate local configuration, source records and progress. They do not run application tests, contact paid model providers or deploy anything. `doctor` reports missing or unavailable capabilities; a successful result does not prove Odoo, AssemblyAI or AWS integration works.

## Start a development session

Review the command first with a dry run:

```sh
.venv/bin/python scripts/harness.py start --dry-run -- "Inspect APP-001 and propose the smallest next change."
.venv/bin/python scripts/harness.py start -- "Inspect APP-001 and propose the smallest next change."
```

For an explicitly assigned application change, add only its owning repository:

```sh
.venv/bin/python scripts/harness.py start --write-repo backend -- "Implement the assigned APP-001 acceptance criteria."
.venv/bin/python scripts/harness.py start --write-repo odoo -- "Implement the assigned ODOO-001 acceptance criteria."
```

Repeat `--write-repo` only when the assignment requires both repositories. The launcher adds writable directories; it does not grant authority to change unrelated files, perform recruiting actions or deploy. The current host's permission policy still applies.

## Review and activate Codex configuration

Read `AGENTS.md`, `.codex/config.toml`, `.codex/agents/` and `.codex/hooks.json`. Trust the project configuration through the host's normal flow. Then open `/hooks` in Codex CLI to review and trust the exact hook definitions. New or changed hooks remain inactive until trusted; setup never bypasses that review. This is a host requirement described in [official OpenAI hook documentation](https://learn.chatgpt.com/docs/hooks).

Hooks cover `SessionStart`, `PreCompact`, `Interrupt` and `Stop`; local checkpoints live under ignored `.state/`. Run the explicit validation commands even when hooks are unavailable or untrusted. The hooks help record context and validate handoffs; they do not replace application tests or enforce all external tool behavior.

Hook commands resolve `.venv/bin/python` and `scripts/harness.py` from the Git root, including when Codex starts in a subdirectory. After cloning or moving the folder, create its virtual environment, check repository overrides, rerun validation, then review/trust hooks in that checkout. A simulated payload, direct handler call or passing handler test does not establish host trust or prove automatic lifecycle execution.

Development subagents are `explorer`, `implementer` and `reviewer`. They inherit the parent model and permissions. Explorer/reviewer avoid writes by instruction, rather than a separate permission boundary. See [official OpenAI subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents).

## Work and evidence

`prompts/system.md` is the repository operating prompt supplied by the launcher. Its filename does not make it a higher-priority host system instruction. Local workflows live in `.agents/skills/`; product source snapshots are under `context/notion/`, with provenance in `context/sources.json`.

```sh
.venv/bin/python scripts/harness.py progress show
.venv/bin/python scripts/harness.py progress update APP-001 --status in_progress --expected-revision N --note "Started the assigned evidence-contract change." --next-action "Inspect the existing result schemas."
```

Replace `N` with the current revision. Statuses are `pending`, `in_progress`, `blocked` and `completed`; dependencies must be completed before work starts. A stale revision must be reloaded rather than overwritten. A blocked task requires both `--blocker TEXT` and `--next-action TEXT`; clear a resolved blocker with `--blocker ''`.

Save the real command output in a nonempty local log, then prepare a JSON array matching `schemas/progress.schema.json`. For application evidence, first capture the owning repository fingerprint:

```sh
.venv/bin/python scripts/harness.py progress fingerprint --repo backend
```

The returned `revision` is HEAD when clean, or HEAD plus a hash of the tracked diff and untracked files when dirty. Use that exact value in `repository_revision`. This example shows the record shape only: replace the command, timestamp and fingerprint with observed values, and ensure the log actually supports the acceptance IDs before recording a pass.

```json
[
  {
    "acceptance_ids": ["APP-001-AC1", "APP-001-AC2"],
    "result": "passed",
    "command": "ACTUAL_COMMAND_RUN_IN_THE_BACKEND_REPOSITORY",
    "reference": ".state/evidence/app-001-check.log",
    "recorded_at": "ACTUAL_ISO_8601_TIMESTAMP_WITH_TIMEZONE",
    "repository_revision": "EXACT_REVISION_FROM_FINGERPRINT"
  }
]
```

`reference` must resolve to an existing nonempty local file inside this harness or a bound application repository; remote URLs alone are insufficient. Keep logs sanitized. `--evidence FILE` appends records to the task history. Repeated `--acceptance ID` flags override acceptance IDs on **each appended record**; they do not change existing evidence or task criteria.

The latest `recorded_at` per acceptance ID determines its current result; an equally timed non-pass wins over a pass. Completing a task requires passed verification, passed latest evidence for every acceptance ID, a note and no blocker. At a new application completion, current passing evidence must match the owning repository fingerprint. Previously completed tasks retain historical revision evidence during ordinary validation; that is not a claim they were retested against later code.

After the task has started and every check has actually passed, a completion update can use:

```sh
.venv/bin/python scripts/harness.py progress update APP-001 --status completed --expected-revision N --verification passed --evidence .state/evidence/app-001.json --note "Acceptance checks passed; see saved evidence." --next-action '' --blocker ''
```

Do not submit the illustrative placeholder record above as evidence.

`HARNESS-001` tracks setup. The pending application backlog is `APP-001` evidence contracts, `APP-002` durable runtime, `ODOO-001` new addon, `SPEECH-001` guided AssemblyAI interviews, `AWS-001` backend pipeline and `QA-001` integration verification. Setup completion does not complete these application tasks.

Read [project facts](context/project.md), [product contract](context/product-contract.md) and [decisions](context/decisions.md) before changing application behavior. Existing implementations contain known scope conflicts; source text and a passing old test suite are not proof that the new requirements are implemented.

When refreshing a prerequisite that has completed dependents, first reopen and block the affected dependents, then reopen the prerequisite. This preserves the dependency rules while retaining historical evidence. Re-completion requires fresh passing evidence for every acceptance criterion; older records remain available as history.

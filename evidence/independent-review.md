# Independent harness review

Reviewed on 2026-10-30. This record concerns the development harness only.

## Sample development assignment

Request examined: prepare the next implementation step for a guided interview with English voice and English/Vietnamese typed answers, without changing an application or deploying it.

The entry instructions, operating prompt, development-agent definitions, repository map, product contract, and focused skills route this request to the AssemblyAI interview workflow. They identify the external backend/Odoo repositories, preserve typed participation without audio consent, require prior audio consent and transcript review/explicit submission, and retain the distinction between development subagents and recruiting runtime personas. The assignment does not acquire permission to edit an application, contact candidates, or deploy from loading a skill. Application tasks remain separate from harness setup.

No application-code scope leakage was found in that walkthrough. Repository instructions must still be loaded explicitly when a later assignment targets a sibling checkout.

## Utility and regression verification

Command run from the harness root:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Observed result: **33 tests passed** under Python 3.12. Test fixtures, saved evidence, and temporary Git repositories were created only under harness `.state/` and cleaned up. Local fixture Git hooks were disabled.

The suite verifies progress transitions, dependency gating, acceptance coverage, saved evidence, optimistic revision conflicts, concurrent updates, checkpoint status preservation, bounded Stop continuation, startup diagnostics, sanitized invocation metadata, and explicit launcher write-root selection. Actual Git fixtures verify tracked/untracked worktree changes, current-revision completion, preservation and refresh of historical evidence, and reopening multiple historical external tasks after a new commit.

The review exposed and then verified corrections for these issues:

- A newer failed check could be hidden by an older pass through evidence-array ordering. Effective evidence now follows timestamps; the regression exercises both array orders.
- Checking every historical pass against the current revision prevented a refreshed task from retaining older evidence. The regression now preserves the old record while adding current passed evidence.
- Unframed untracked path/content bytes could produce identical fingerprints for different files. The regression distinguishes a file `a` containing `bc` from a file `ab` containing `c`.

Additional commands observed:

```sh
.venv/bin/python scripts/harness.py validate
.venv/bin/python scripts/harness.py doctor
```

Validation reported `passed` with no failures. Doctor reported Python 3.12 supported and both configured application repositories available. The launcher dry-run tests confirm that no external `--add-dir` is included unless a repository is explicitly selected.

No remaining consequential issue was found in the reviewed utilities after those corrections. Dependency refresh remains deliberate: dependent work must be paused before reopening a prerequisite whose acceptance is being refreshed.

## Verification limits

This review did not activate native Codex hooks or establish hook trust. Doctor reported zero observed native invocations at the time of this review; payload tests do not establish native activation. The coordinator subsequently reported native hook discovery with hooks still untrusted; discovery is not execution. That separate discovery output is outside this review's direct observations.

Custom-agent TOML files passed local parse/shape validation. A native invocation of each configured development role was not performed in this review, so role invocation is not claimed verified.

Application checks remain `not_run`; AWS deployment remains `not_configured`. This review did not run Odoo, AssemblyAI, paid model calls, candidate operations, or a deployment. Prepared instructions and passing harness tests do not establish those integrations.

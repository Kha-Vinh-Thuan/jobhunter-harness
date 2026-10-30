---
name: jobhunter-verification
description: Verify Jobhunter development-harness integrity or application acceptance against the product contract, recording observed evidence and separating prepared, tested, and deployed outcomes.
---

# Jobhunter verification

Read the [project context](../../../context/project.md), [product contract](../../../context/product-contract.md), relevant [decisions](../../../context/decisions.md), and [capabilities](../../../context/capabilities.json). Determine whether the assignment concerns this development harness or the application in an external owning repository before choosing checks.

## Harness checks

From the harness root run:

```sh
.venv/bin/python scripts/harness.py validate
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/harness.py progress show
```

Inspect meaningful invariants: required artifacts and relative links resolve; JSON/TOML parse; skills and agent definitions are valid; hooks and progress use the documented interfaces; no secret values or application/deployment code entered this folder. Read the actual command output. A validator pass establishes harness integrity only.

## Application checks

Discover and run the owning repository's supported checks for the requested change. Use isolated development data, explicitly labeled fixtures, and real integrations only within the task's authorization. Cover applicable contract scenarios:

- Evidence coverage, exact citations, missing/conflicting evidence, untrusted-source commands, and absence of scores or candidate decisions.
- Runtime branch dependencies, partial reports, cancellation/interruption, unavailable capabilities, restart/resume, and changed/deleted-source invalidation.
- Odoo installation/upgrade, permissions and company isolation, real identifiers, and coexistence restricted to enabled harness jobs.
- English AssemblyAI STT/TTS, English/Vietnamese typed answers, audio consent, transcript review and explicit submission, provider failure, and no false interview completion.
- ECS deployment traceability, external checkpoint durability, health checks, rollback, and actual Odoo connectivity.

The user's ARTEMIS exploration rules apply before authoring **native mobile tests**. Ordinary web/backend/harness checks do not require a mobile device. If a later assignment introduces native mobile testing, read the applicable user rules, use ARTEMIS to observe the target flow before writing test code, and diagnose ARTEMIS failures rather than guessing.

## Evidence and handoff

For each check report `passed`, `failed`, `not_run`, or `not_applicable`, with the command/scenario, target revision/environment, evidence reference, and material limitation. No applicable checks means N/A; missing targets or credentials mean Not run, not a pass. Do not turn documented walkthrough targets or mock responses into live verification.

Return actionable findings and evidence to the coordinator. Only the coordinator writes progress with `.venv/bin/python scripts/harness.py progress update`. Harness completion does not mean the Odoo extension, speech integration, or AWS deployment exists.

## Sources

Original local workflow; no third-party skill package is vendored. Source links checked on **2026-10-30**; the accepted product contract defines the required acceptance outcomes.

- [Jobhunter Agent Harness validation scenarios](https://app.notion.com/p/408365d5182581e7addfc3c113c454ed)
- [Odoo 20 test guidance](https://www.odoo.com/documentation/20.0/developer/tutorials/unit_tests.html)
- [Project source registry](../../../context/sources.json)

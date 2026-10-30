# Project map and observed state

This is a **development harness**, not the Jobhunter backend or an Odoo addon. Repository paths come from `harness.json` and optional ignored `harness.local.json` overrides. Resolve those bindings before any application command.

## Ownership

| Repository key | Default path | Source of implementation truth |
| --- | --- | --- |
| `backend` | `../Jobhunter-Platform` | Python/FastAPI/LangGraph/Pydantic agents, contracts, providers and tests; read its `CLAUDE.md` and current plan for local conventions |
| `odoo` | `../sea-hkt-t10` | Odoo addons, recruitment data, views, controllers and container composition |
| harness | current directory | Codex instructions, skills, source snapshots, progress and helper scripts |

Harness setup authorizes writes only here. Later application assignments must name their repository and intended behavior. Inspect its status before editing, preserve other contributors' changes and do not commit automatically.

## Planning observations — 2026-10-30

These are baseline observations, not continuing guarantees. Source revisions and provenance belong in `sources.json`; recheck the owning source before consequential changes.

- The backend contains standalone Filter, Schedule and Interview agents, a read-only `HiringProvider` protocol and a mock provider. It does not yet contain the proposed durable orchestrator, Odoo adapter or shared runtime progress system.
- Filter returns pass/reject decisions. Interview generates rubric scores; its standalone demo streams to AssemblyAI but lacks the required consent/review/submission flow. Schedule proposes interviewer slots and validates IDs, duration and duplicate assignments.
- Backend tests observed during planning: **47 passed, 2 skipped**, with live API credentials disabled and pytest run from the `backend/` directory. Running from the repository root failed module imports. This result is historical; rerun relevant tests when implementation changes.
- The Odoo app was observed running **20.0-20261015**. Its Dockerfile uses `odoo:latest`, so the image reference itself does not pin that version; inspect the actual container or image before relying on compatibility.
- Odoo has the `rag_interview_agent` addon extending recruitment records. It uses OpenAI Realtime voice and produces per-answer (0–10) and overall (0–100) scores with a recommendation, which conflicts with the product contract. Adding the new addon requires a deliberate coexistence/migration decision for it.
- `t10_ai_interview` (automatic cron pipeline, scores, stage changes, email/calendar operations) and the `ml` service were removed in Odoo commit `e11da0a` (2026-10-30), which names `rag_interview_agent` as their replacement. Do not plan work against them.
- Existing Odoo-to-service calls use server-side Bearer authentication and send job/company context with an applicant reference. Those session endpoints are not a general Odoo data adapter for the Python backend.
- The new addon, guided AssemblyAI STT/TTS flow and backend-only ECS Fargate pipeline remain future application work. Creating this harness implements none of them.

## How to use sources

`product-contract.md` records the reviewed behavior; `decisions.md` records the user's scope choices. `notion/*.md` contains fetched source snapshots and `sources.json` records their provenance. Notion references to TypeScript/Zod schemas, existing APIs or run statuses describe another implementation; they are requirements/context to reconcile, not facts about this Python repository.

Use current user decisions for product intent, the reviewed source contract for its requirements and owning repository instructions for development conventions. Host instructions and permissions remain controlling. Surface substantive conflicts instead of declaring a blanket precedence that discards repository constraints.

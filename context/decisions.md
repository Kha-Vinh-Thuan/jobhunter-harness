# Accepted decisions

Recorded for this harness on **2026-10-30**. These decisions describe scope and direction; they do not prove implementation or grant authority beyond the current assignment.

| Decision | Consequence |
| --- | --- |
| Keep a separate `jobhunter-harness` repository with no application codebase | Store Codex instructions, context, skills, native subagent definitions, progress, hooks and small helper scripts here; implement application behavior in its owning repository |
| Extend the existing Odoo internal app through a new addon | Reuse Odoo data, identity and access controls; integrate with the Python backend instead of creating a standalone replacement app |
| Use guided interviews | Prepare/ask controlled questions and accept actual reviewed/submitted answers; do not infer completion from question preparation or an open session |
| Use AssemblyAI for STT and TTS | Verify actual API/account capabilities before integration and report missing support explicitly; do not silently choose another speech provider |
| English voice; English and Vietnamese typed participation | Keep a typed path independent of microphone/audio consent; review and explicitly submit transcribed answers |
| Future AWS pipeline targets backend on ECS Fargate | Put pipeline/infrastructure implementation in the backend application repository; Odoo deployment and live AWS changes are outside harness setup |
| Use native Codex development subagents and skills | Keep `explorer`, `implementer` and `reviewer` distinct from runtime recruiting roles; inherit the parent model and actual permissions |
| Use revision-checked `progress.json` | Track engineering tasks and acceptance evidence; application run/candidate state belongs in the application |
| Hook activation requires host review/trust | Ship reviewable definitions; activate through the normal project trust flow and `/hooks`, without bypassing trust |

The Notion shared/role snapshots define the recruiting constraints summarized in `product-contract.md`. Older repository plans still inform development conventions and history; their automatic decisions, calendar/email execution or standalone speech design are not accepted expansions of the reviewed product scope.

When a later user decision changes this direction, record the concrete change and affected task/source references. Do not rewrite observed historical test results or quietly turn an assumption into a decision.

# Orchestrator
## Main use cases

- <b>Coordinate a multi-step request:</b> turn “review this CV and prepare interview questions” into ordered assignments for the relevant agents.
- <b>Route a focused request:</b> invoke only the agent and prerequisites needed for an evidence review, scheduling proposal, interview or report.
- <b>Resolve missing context:</b> identify the candidate, approved role criteria or required inputs before starting dependent work.
- <b>Resume interrupted work:</b> after a blocker is resolved and a retry is authorized, reuse valid outputs, restart only affected work and track overall completion.

## Tools, APIs and skills

<b>Start with:</b> the existing TypeScript coordinator, OpenAI Responses API and Zod. Add a framework only when it solves a concrete coordination need.

| Tool / API | Use in Jobhunter | Status |
| --- | --- | --- |
| [OpenAI Responses + Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs) | Turn requests into validated task plans. Keep permissions and plan checks in server code. | Current |
| [Responses function calling](https://developers.openai.com/api/docs/guides/function-calling) | Expose narrowly scoped product functions as model-callable tools. The server validates and executes each call. | Optional |
| [OpenAI Agents SDK](https://developers.openai.com/api/docs/guides/agents/orchestration) | If adopting an agent framework, use specialists as tools so the orchestrator retains control. | Optional alternative |

<b>Skills to package from this role</b>

- <b>Route a recruiting request:</b> select relevant agents, resolve missing context and order dependencies.
- <b>Validate a handoff:</b> check evidence freshness, confirmed outputs, blockers and overall completion.

These are proposed reusable workflows, not installed plugins. “Current” means found in the inspected code, not retested here. Product API keys belong on the backend; Codex connectors are not automatically integrations in your app. This list does not expand agent permissions.

## Copy-ready role instructions

```txt
MISSION
You are Jobhunter's Orchestrator. Turn the user's recruiting request into bounded assignments, coordinate only the required specialists, and return a faithful final response. Own overall completion and unresolved work; Report owns synthesis.

REQUIRED INPUTS
The user's requested outcome; relevant candidate references; approved role/version for assessment or interviews; actual evidence or prior artifacts; available tools; and shared harness v1.0. Request missing identifiers instead of selecting a candidate by guesswork.

PERMITTED ACTIONS
Read authorized context, prepare assignments, invoke available specialists, validate their returns and ask the responsible human for missing inputs. Reuse current completed artifacts when they satisfy the request. If dispatch is unavailable, return prepared assignments as an unsaved plan and Needs input; never simulate delegation.

WORKING STEPS
1. Define requested outputs, context and assignments; load shared + selected-role instructions. Question preparation never starts a conversation.
2. Respect dependencies (Filter before gap-based questions); parallelize only independent work.
3. Validate handoff identity, freshness, evidence and saved artifacts. Retain valid partial outputs, pause dependent work and mark unused branches not requested.
4. Send actual results/states to Report; check returned coverage before deciding overall completion.

OUTPUT
Shared handoff: artifact references, actual overall status, unresolved work, and next actions with owners.

STOP CONDITIONS
- Pause affected work for missing authority/context, stale evidence, unavailable capabilities, errors or cancellation; preserve confirmed outputs under the shared outcome rules.
- Retry only after addressing the cause and obtaining bounded runtime/user authorization.
```

## Synthetic example

<p>
<b>Synthetic example:</b> Request: “Review candidate-demo against approved role-demo v2 and prepare interview questions.” 
</p>

<ul>
<li>
Dispatch Filter, then Interview using its evidence gaps, then Report. Schedule is <b>not requested</b>. 
</li>
<li>
If Filter finishes but Interview fails, retain the review and return a <b>partial report</b>. 
</li>
<li>
Report may complete its summary; the overall request remains <b>Failed</b> with Interview's error and the orchestrator owning recovery. 
</li>
<li>
No candidate stage changes.
</li>
</ul>

## Specialist pages

The four child pages below define the specialist contracts. Each specialist returns to this orchestrator; they do not dispatch one another.

<page url="https://app.notion.com/p/408365d5182581c3a2f8f9c4d2e9da7d">
Filter Agent
</page>

<page url="https://app.notion.com/p/408365d5182581ba84a8cf1f2be4e568">
Schedule Agent
</page>

<page url="https://app.notion.com/p/408365d5182581a38186cf40f8b4b49f">
Interview Agent
</page>

<page url="https://app.notion.com/p/408365d51825815c96b1d83ce19f6dc1">
Report Agent
</page>
</content>
</page>


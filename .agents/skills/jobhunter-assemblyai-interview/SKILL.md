---
name: jobhunter-assemblyai-interview
description: Build or review Jobhunter guided candidate interviews using AssemblyAI for English speech-to-text and text-to-speech, with English or Vietnamese typed answers and explicit answer submission.
---

# Jobhunter AssemblyAI interview

Implement in the owning application repositories identified by [project context](../../../context/project.md). Read the [product contract](../../../context/product-contract.md), relevant [decisions](../../../context/decisions.md), and [capabilities](../../../context/capabilities.json). This skill does not create an application in the development-harness repository.

## Workflow

1. Inspect the actual interview UI, backend, consent model, provider adapter, and tests. Confirm the current AssemblyAI API/SDK and account capabilities from official documentation and observed results before depending on them. Do not infer account access from a documentation link.
2. Support a guided candidate interview with **English voice** through AssemblyAI STT and TTS, plus **English/Vietnamese typed answers**. Do not promise Vietnamese TTS, add another speech vendor, or replace the chosen interview mode without a product decision.
3. Keep the AssemblyAI API key server-side. Mint short-lived, authorized session tokens for browser speech connections where supported. Bind speech sessions to the actual interview/candidate context and expose capability failures as actionable errors.
4. Obtain explicit consent before collecting or processing candidate audio. When consent is absent or withdrawn, stop further audio collection/processing and keep typed participation and question preparation available. Do not infer consent from microphone permission or from a transcript being present.
5. Keep partial and final STT text as answer drafts. Let the candidate review/edit the transcript and explicitly submit the answer. Only submitted answers may advance the guided interview or support findings; do not auto-submit on an STT end-of-turn event or disconnect.
6. Use verified speaker attribution. Do not assume the first diarization label identifies the interviewer. Keep the agent's spoken question separate from candidate-answer evidence and avoid treating playback or echo as a candidate answer.
7. Implement microphone capture, resampling, streamed playback, interruption/cancellation, and connection cleanup using the current supported browser APIs. Preserve submitted answers across reconnects; never label an unanswered or interrupted interview conducted or complete.
8. Generate follow-ups and evidence findings from approved criteria and submitted answers only. Preserve answer/question references and evidence citations. Missing coverage is unknown. Do not assign candidate or criterion scores, rank candidates, or derive emotion, personality, or suitability from voice.
9. Verify consent, typed-only participation, English STT/TTS, reviewed submission, interruption, provider rejection/disconnect, duplicate submission, resume, and source freshness. Keep fixtures explicitly labeled and distinguish offline tests from observed provider behavior.

Use actual available tools; the capability registry does not declare callable tool names. Return results and blockers to the coordinator, which alone updates progress with `.venv/bin/python scripts/harness.py progress update`.

## Sources

Original local workflow; no third-party skill package is vendored. Source links checked on **2026-10-30**. New AssemblyAI TTS guidance supersedes older pages that said standalone TTS was unavailable; verify the current provider contract during implementation.

- [AssemblyAI browser STT/TTS integration](https://www.assemblyai.com/blog/build-a-voice-assistant-app-with-assemblyai)
- [AssemblyAI streaming TTS in Python](https://www.assemblyai.com/blog/text-to-speech-python)
- [Project source registry](../../../context/sources.json)

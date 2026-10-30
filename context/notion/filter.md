# Filter Agent

## Main use cases

- <b>Review a CV against a role:</b> map supplied evidence to each approved criterion with citations and supported, partial, unknown or conflicting findings.
- <b>Investigate gaps and contradictions:</b> compare supplied CV, portfolio and other authorized evidence while preserving provenance and uncertainty.
- <b>Prepare clarification questions:</b> turn missing or conflicting evidence into focused questions for human review or interview preparation.
- <b>Refresh an outdated review:</b> reassess affected findings when approved criteria or source documents change, retaining current version and source references.

## Tools, APIs and skills

<b>Start with:</b> existing document extraction, evidence review and citation checks. Add OCR when scanned CVs become a real input requirement.

| Tool / API | Use in Jobhunter | Status |
| --- | --- | --- |
| [pdf-parse](https://github.com/mehmet-kozan/pdf-parse/blob/main/README.md)  • [Mammoth](https://github.com/mwilliamson/mammoth.js) | Extract text from PDF and DOCX uploads through the existing file adapter. | Current |
| [Tesseract.js](https://github.com/naptha/tesseract.js) | Extract text from scanned images. Render PDF pages to images first; Tesseract.js does not read PDFs directly. | Optional OCR |

<b>Skills to package from this role</b>

- <b>Review CV evidence:</b> map supplied sources to approved criteria and label gaps or conflicts.
- <b>Verify citations:</b> check quotes, source references, provenance and outdated context.

## Copy-ready role instructions

```txt
MISSION
You are Jobhunter's Filter Agent. Produce a criterion-by-criterion evidence review for human judgment. “Filter” means organizing evidence and gaps, not selecting people.

REQUIRED INPUTS
An orchestrator assignment; candidate reference; approved role ID/version and criteria; relevant source documents with provenance, actual IDs, line-numbered text and available hashes; shared harness v1.0.

PERMITTED ACTIONS
Read assigned sources, compare evidence with the approved criteria, validate supporting quotations using available capabilities and prepare focused clarification questions. Return findings to the orchestrator. Do not dispatch another agent or modify the criteria.

WORKING STEPS
1. Confirm candidate, approved role/version and usable sources; identify missing or unreadable documents.
2. Review every criterion: supported (whole), partial, unknown (no usable evidence), or conflicting.
3. Preserve self-report, personal/team ownership and metric scope; never infer technology-specific years from total job tenure.
4. Cite claims with documentId, 1-based lineStart/lineEnd and verbatim quote; cite both conflicting sources. Add gap questions and recheck freshness.

OUTPUT
Shared handoff: summary; criterionId, status, finding, citations and question per criterion; role/source references and confirmed review ID or unsaved draft. Unknown findings can be Complete.

STOP CONDITIONS
- Needs input: unapproved criteria, unusable required evidence or stale context.
- Failed: attempted review/tool error. Preserve usable work and identify unresolved coverage under the shared outcome rules.
```

## Synthetic example

<b>Synthetic fixture:</b> Approved criterion <code>kotlin-use</code>: “Evidence of Kotlin use in Android development.” Document <code>doc-demo-cv</code>, line 3: “Built Android features using Kotlin.”

<b>Expected:</b> <code>supported</code> with finding “The candidate reports using Kotlin for Android features” and citation <code>{documentId: "doc-demo-cv", lineStart: 3, lineEnd: 3, quote: "Built Android features using Kotlin."}</code>. A separate performance-profiling criterion with no source evidence is <code>unknown</code>, with a clarification question. Candidate stage is unchanged.
</content>
</page>


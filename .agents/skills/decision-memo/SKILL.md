---
name: decision-memo
description: "Create advisor-ready research Decision Memos with first-principles decomposition, evidence ledger, risks, lowest-cost kill tests, verdict, confidence, JSON gate state, and PDF output. Use for pre-experiment evaluation, go/no-go decisions, research idea triage, or when a Markdown-only report is not enough."
---

# Decision Memo

## Purpose

Create the formal artifact that decides whether a research idea may consume experiment resources.

## Required Files

For project slug `<project-slug>` and idea slug `<idea-slug>`, write:

- `projects/<project-slug>/decisions/<idea-slug>/DECISION_MEMO.md`
- `projects/<project-slug>/decisions/<idea-slug>/decision.json`
- `projects/<project-slug>/output/pdf/<idea-slug>_decision_memo.pdf`
- `projects/<project-slug>/tmp/pdfs/`

Use `templates/DECISION_MEMO_TEMPLATE.md`.

## Verdicts

- `GO`: the idea may enter experiments.
- `STATIC_ONLY`: only literature, static analysis, public checkpoint analysis, or non-training probes may proceed.
- `NEEDS_MORE_EVIDENCE`: blocked until evidence gaps are closed.
- `NO_GO`: blocked.
- `USER_OVERRIDE`: user explicitly accepts recorded risk.

## Confidence

Use only:

- `high`: direct evidence and assumptions are stable.
- `medium`: evidence is plausible but incomplete.
- `low`: speculative or dependent on unresolved facts.

Do not invent percentages. Use numeric probabilities only when the memo cites explicit data supporting them.

## Memo Requirements

Include every section below:

1. Executive decision.
2. Premise check, including direct correction when the user premise is wrong or underspecified.
3. First-principles decomposition.
4. Multi-perspective reasoning from PI/advisor, resource manager, and skeptical reviewer.
5. Evidence ledger with supporting, opposing, adjacent, and missing evidence.
6. Advantages, weaknesses/risks, and failure modes.
7. Lowest-cost kill test.
8. Resource budget.
9. Final gate JSON block.
10. Self-audit covering topic fit, factual accuracy, and logic closure.

## Evidence and Formatting Discipline

- Use Codex app available retrieval and bundled ARIS tools for unfamiliar or time-sensitive claims. Do not require Google Search specifically.
- Mark unsupported claims as missing evidence or low-confidence inference.
- Use `##` section headers, bold key conclusions, and tables/lists for evidence, risks, budgets, and comparisons.
- Keep the verdict tied to the evidence ledger; do not let the memo become an idea list.

## JSON Contract

`decision.json` must include:

```json
{
  "idea_id": "example-idea",
  "project_id": "example-project",
  "title": "Example idea",
  "verdict": "STATIC_ONLY",
  "confidence": "medium",
  "max_gpu_hours_allowed": 0,
  "allowed_next_actions": ["literature review", "static analysis"],
  "blocking_reasons": ["No direct evidence yet"],
  "memo_md": "projects/example-project/decisions/example-idea/DECISION_MEMO.md",
  "memo_pdf": "projects/example-project/output/pdf/example-idea_decision_memo.pdf",
  "created_at": "2026-06-13T00:00:00Z"
}
```

If verdict is `USER_OVERRIDE`, add `override_reason`.

## PDF Rendering

After writing Markdown and JSON, render the PDF:

```powershell
python .\tools\render_markdown_pdf.py .\projects\<project-slug>\decisions\<idea-slug>\DECISION_MEMO.md --output .\projects\<project-slug>\output\pdf\<idea-slug>_decision_memo.pdf --preview --preview-dir .\projects\<project-slug>\tmp\pdfs
```

Validate with `pypdf` or a preview contact sheet when possible. Do not deliver Markdown-only unless explicitly requested.

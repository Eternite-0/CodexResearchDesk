---
name: report-style-auditor
description: "Audit Chinese research reports for English boilerplate, chatbot residue, vague authority, and AI-flavored filler before Markdown/PDF delivery. Use for Decision Memos, Direction Briefs, research reports, advisor-facing summaries, and paper-planning artifacts."
---

# Report Style Auditor

## Purpose

Improve advisor-facing research artifacts without weakening evidence discipline. This skill is inspired by Humanizer-zh style rules, but is adapted for CodexResearchDesk: the goal is not to bypass AI detectors, and it is not free-form rewriting. The goal is to remove chatbot residue, vague authority, promotional filler, and template tone while preserving facts, citations, verdicts, numeric claims, and gate status.

## When To Use

Use this before final delivery of:

- Chinese `DECISION_MEMO.md`
- Direction triage artifacts
- research-wiki summaries that will be shown to a human
- paper plans or narrative reports

For formal Decision Memos, run it after factual/style checks and before PDF rendering.

## Required Checks

For a Chinese Decision Memo, run both tools:

```powershell
python .\tools\check_report_style.py .\projects\<project-slug>\decisions\<idea-slug>\DECISION_MEMO.md
python .\tools\check_ai_style.py .\projects\<project-slug>\decisions\<idea-slug>\DECISION_MEMO.md
```

Use `--fail-on-warning` only when a strict pre-submission gate is needed:

```powershell
python .\tools\check_ai_style.py .\projects\<project-slug>\decisions\<idea-slug>\DECISION_MEMO.md --fail-on-warning
```

## Interpretation

- `error`: fix before delivery. These are usually chatbot residues or AI limitation disclaimers.
- `warning`: review before delivery. These often indicate vague attribution, promotional language, formulaic contrast, or optimistic filler.
- `review`: not automatically wrong. These mark transition crutches or broad evidence claims that may need citations or tighter wording.

## Editing Rules

- Do not change `decision.json` verdicts, budgets, allowed actions, blocked actions, or PDF paths unless the evidence changed.
- Do not rewrite numeric results, citations, model names, dataset names, or code paths without checking the source.
- Replace vague authority with specific evidence. If no evidence exists, mark it as an evidence gap.
- Replace grand claims with scoped claims: what changed, under what condition, with what evidence.
- Keep a professional research voice. Do not add first-person diary tone, jokes, or casual personality to Decision Memos.
- Preserve the report language. Chinese artifacts should not gain English boilerplate during editing.

## Attribution

The warning categories are adapted from the public Humanizer-zh project and its upstream writing-style sources, but this repository uses a local deterministic checker tailored to research reports.

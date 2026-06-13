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
- `projects/<project-slug>/signals/<idea-slug>/EXTERNAL_SIGNAL_LEDGER.md` when external signal scouting was used
- `projects/<project-slug>/signals/<idea-slug>/external_signals.json` when external signal scouting was used
- `projects/<project-slug>/signals/<idea-slug>/PAPER_CODE_LEDGER.md` when paper-code scouting was used
- `projects/<project-slug>/signals/<idea-slug>/paper_code.json` when paper-code scouting was used
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

Use the report language selected by the project/user. In this repository, Chinese user requests should produce Chinese advisor-facing memos by default. Use `templates/DECISION_MEMO_TEMPLATE.md` as the canonical structure.

For Chinese memos, include every section below with Chinese headings:

1. 执行结论。
2. 术语口径, defining unavoidable abbreviations once.
3. 前提校验, including direct correction when the user premise is wrong or underspecified.
4. 一阶拆解。
5. 多视角判断, from 导师视角、资源管理视角、审稿人质疑视角.
6. 证据台账, with 支持、反对、相邻、缺失 evidence.
7. 外部信号账本, when used.
8. 论文到代码库追踪, when relevant papers drive the idea.
9. 批判性评估, including 优势、弱点与风险、失败模式.
10. 最低成本淘汰测试。
11. 资源预算。
12. 最终门控 JSON block.
13. 自我审计, covering topic fit, factual accuracy, logic closure, and overclaim check.

Keep English only for stable identifiers: paper titles, model names, dataset names, code paths, commands, JSON keys, metric abbreviations, and gate enum values such as `STATIC_ONLY`.

## Evidence and Formatting Discipline

- Use Codex app available retrieval and bundled ARIS tools for unfamiliar or time-sensitive claims. Do not require Google Search specifically.
- Mark unsupported claims as missing evidence or low-confidence inference.
- Use `##` section headers, bold key conclusions, and tables/lists for evidence, risks, budgets, and comparisons.
- Keep the verdict tied to the evidence ledger; do not let the memo become an idea list.
- Do not leave English boilerplate in Chinese reports. Translate section titles, table headers, list labels, action items, risk reasons, and prose.
- In `decision.json`, keep machine keys and enum values in English, but write human-readable arrays such as `allowed_next_actions` and `blocking_reasons` in the report language.
- Run `python .\tools\check_report_style.py <DECISION_MEMO.md>` before final delivery when the memo is in Chinese.
- Run `python .\tools\check_ai_style.py <DECISION_MEMO.md>` before final delivery to catch chatbot residue, vague authority, and AI-flavored filler.

## JSON Contract

`decision.json` must include:

```json
{
  "idea_id": "example-idea",
  "project_id": "example-project",
  "title": "Example idea",
  "verdict": "STATIC_ONLY",
  "confidence": "medium",
  "direction_score": 58,
  "risk_level": "high",
  "main_claim": "The core research claim being gated.",
  "top_risks": ["Novelty is not established."],
  "evidence_gaps": ["Closest prior work has not been checked."],
  "external_signal_score": 0,
  "external_signal_summary": "No external signal ledger was used.",
  "external_signal_ledger": "",
  "hype_risk": "low",
  "paper_code_trace_score": 0,
  "paper_code_summary": "No paper-code ledger was used.",
  "paper_code_ledger": "",
  "code_availability_risk": "low",
  "kill_tests": [
    {
      "test_name": "closest-prior-work check",
      "hypothesis": "The claim is not already covered.",
      "expected_cost": "2 hours, 0 GPU",
      "pass_condition": "No direct overlap.",
      "fail_condition": "Recent work already covers the claim.",
      "decision_change_if_failed": "NO_GO"
    }
  ],
  "max_gpu_hours_allowed": 0,
  "resource_budget": {
    "max_gpu_hours_allowed": 0
  },
  "allowed_next_actions": ["文献复核", "静态分析"],
  "blocked_actions": ["GPU 训练"],
  "blocking_reasons": ["尚无直接证据"],
  "next_review_condition": "完成低成本 kill tests 后复审。",
  "memo_md": "projects/example-project/decisions/example-idea/DECISION_MEMO.md",
  "memo_pdf": "projects/example-project/output/pdf/example-idea_decision_memo.pdf",
  "created_at": "2026-06-13T00:00:00Z"
}
```

If verdict is `USER_OVERRIDE`, add `override_reason`.

The v0.2 triage fields are optional for legacy compatibility, but new Direction Triage Mode memos should include them when evidence exists.

## PDF Rendering

After writing Markdown and JSON, render the PDF:

```powershell
python .\tools\render_markdown_pdf.py .\projects\<project-slug>\decisions\<idea-slug>\DECISION_MEMO.md --output .\projects\<project-slug>\output\pdf\<idea-slug>_decision_memo.pdf --preview --preview-dir .\projects\<project-slug>\tmp\pdfs
```

Validate with `pypdf` or a preview contact sheet when possible. Do not deliver Markdown-only unless explicitly requested.

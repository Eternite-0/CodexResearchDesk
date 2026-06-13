# CodexResearchDesk Working Rules

## Role

This repository is a Codex app driven research desk derived from ARIS / AutoResearch. Codex app is the control surface. Bundled ARIS skills and tools are the research engine.

## Core Discipline

- Stay objective and truthful. Do not flatter the user or inflate weak ideas.
- If a premise is wrong, say so directly and explain the correction.
- For unfamiliar concepts or time-sensitive claims, use Codex app available retrieval before answering: local repository search, bundled ARIS literature tools, and web search only when it is available and appropriate. Do not hard-code Google Search as a requirement.
- Treat experiments as expensive information purchases. Do not launch GPU, training, pilot, or long-running jobs before a Decision Memo gate allows it.

## Reasoning Workflow

When evaluating a research direction or idea:

1. First-principles decomposition: identify the core claim, necessary assumptions, and what would have to be true.
2. Multi-perspective reasoning for complex topics: use 2-3 relevant viewpoints, usually PI/advisor, resource manager, and skeptical reviewer.
3. Critical evaluation: include both advantages and weaknesses/risks.
4. Confidence expression: use `high`, `medium`, or `low`. Give percentages only when supported by explicit data.
5. Self-audit before finalizing: check topic fit, factual accuracy, and whether the logic chain closes.

## Output Discipline

- Use `##` section headers for research reports and Decision Memos.
- Bold the key conclusion in each major section when it materially affects the decision.
- Use tables or lists for comparisons, evidence ledgers, risks, budgets, and gate outcomes.
- Separate known facts, reasoned inference, and open uncertainty.
- If the user's premise is corrected, record the correction explicitly instead of hiding it inside prose.

## Language and Terminology Discipline

- Match the user's working language. For Chinese requests, write advisor-facing artifacts in Chinese by default.
- Do not mix English boilerplate into Chinese reports. Section titles, table headers, list labels, action items, risk reasons, and prose should use Chinese.
- Keep English only when it is a stable technical identifier: model names, dataset names, paper titles, code paths, JSON keys, command names, metric abbreviations, and gate enum values such as `STATIC_ONLY`.
- For unavoidable abbreviations, define them once in a short terminology section, then reuse the abbreviation consistently.
- `decision.json` keeps machine keys and enum values in English, but human-readable values such as `allowed_next_actions` and `blocking_reasons` should follow the report language.
- Use `templates/DECISION_MEMO_TEMPLATE.md` as the canonical Chinese-first structure for Decision Memos.
- Before delivering a Chinese Decision Memo, run:

```powershell
python .\tools\check_report_style.py .\projects\<project-slug>\decisions\<idea-slug>\DECISION_MEMO.md
```

## Decision Gate

Every research idea that may consume experiment resources must have:

- `projects/<project-slug>/decisions/<idea-slug>/DECISION_MEMO.md`
- `projects/<project-slug>/decisions/<idea-slug>/decision.json`
- `projects/<project-slug>/output/pdf/<idea-slug>_decision_memo.pdf`

Each research project owns its own `decisions/`, `research-wiki/`, `output/pdf/`, and `tmp/pdfs/` directories. Do not write multi-project work into root-level `decisions/`, `research-wiki/`, `output/`, or `tmp/` directories.

Allowed verdicts:

- `GO`: may enter experiments.
- `STATIC_ONLY`: may run literature checks, static analysis, public checkpoint analysis, and non-training probes only.
- `NEEDS_MORE_EVIDENCE`: blocked until more evidence is gathered.
- `NO_GO`: blocked.
- `USER_OVERRIDE`: may proceed only when the user explicitly accepts the recorded risk.

Before any experiment, run:

```powershell
python .\tools\decision_gate.py latest .\projects\<project-slug> --mode experiment
```

## PDF Delivery

Advisor-facing artifacts must be delivered as Markdown plus PDF. Use:

```powershell
python .\tools\render_markdown_pdf.py .\projects\<project-slug>\decisions\<idea-slug>\DECISION_MEMO.md --output .\projects\<project-slug>\output\pdf\<idea-slug>_decision_memo.pdf --preview --preview-dir .\projects\<project-slug>\tmp\pdfs
```

Do not hand off Markdown-only unless the user explicitly asks.

## ARIS Core

Bundled ARIS skills are copied into `.agents/skills/` and should be used as capabilities, not as the top-level control flow. Prefer `research-desk` for research decisions, then route to ARIS skills through `aris-runner` only after the decision gate is clear.

## Local Constraints

- Prefer `apply_patch` for manual edits.
- Do not introduce runtime dependencies on local upstream checkout paths.
- Use PowerShell for filesystem inspection and validation.

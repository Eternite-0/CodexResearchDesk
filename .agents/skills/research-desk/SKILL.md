---
name: research-desk
description: "Codex app driven research decision workflow for evaluating research directions or ideas before experiments. Use when the user asks whether an idea is worth doing, asks for first-principles analysis, pre-experiment reasoning, go/no-go decisions, advisor-facing research judgment, or wants to route ARIS tools without launching experiments."
---

# Research Desk

## Purpose

Run the top-level CodexResearchDesk workflow. Treat Codex app as the control surface and bundled ARIS skills/tools as the research engine. Do not launch experiments from this skill.

## Operating Rule

Experiments are expensive information purchases. Before any GPU, training, pilot, or long-running experiment, produce a Decision Memo and pass the preflight gate.

## Retrieval Discipline

Use Codex app available retrieval rather than binding the workflow to one external search provider:

- Inspect local project files and prior research-wiki notes first when they exist.
- Use bundled ARIS literature skills/tools (`research-lit`, `arxiv`, `openalex`, `semantic-scholar`, `deepxiv`) for academic evidence.
- Use web search only when the current Codex environment provides it and the claim is unfamiliar, time-sensitive, or cannot be checked locally.
- If evidence cannot be verified, mark it as missing or low-confidence instead of smoothing over the gap.

## Workflow

### 1. Frame the Decision

Convert the user's request into a decision question:

- What idea or direction is being evaluated?
- What decision is needed now?
- What resource could be consumed if the decision is wrong?
- What is explicitly out of scope?

If the user provided a `RESEARCH_BRIEF.md`, read it first.

### 2. Decompose From First Principles

Identify:

- core claim
- necessary assumptions
- smallest useful unit of evidence
- falsifier
- minimum publishable contribution if the claim holds
- useful negative result if the claim fails

### 3. Run Direction Triage When the Direction Is Still Broad

For early directions that are not ready for a full Decision Memo, use the v0.2 triage artifacts:

1. `direction-brief` to frame the one-sentence direction, core claim, evidence needs, risks, and preliminary verdict.
2. `pitfall-radar` to identify data, metric, baseline, novelty, engineering, evaluation, and contribution traps.
3. `external-signal-scout` to collect external soft-gate signals from GitHub, alphaXiv/HF Papers, Hacker News, Semantic Scholar/OpenAlex, and manual X/Reddit/enterprise evidence.
4. `direction-scorecard` to score novelty, feasibility, data access, compute control, evaluation clarity, baseline reproducibility, and project value, using external signals as risk evidence rather than hard truth.
5. `kill-test-generator` to define at least three low-cost tests before experiments.

These artifacts help decide what not to do and what to validate first. They do not authorize GPU, training, pilots, or long-running jobs.

### 4. Build Evidence With ARIS Core

Use bundled ARIS capabilities only as tools for evidence:

- `research-lit`, `arxiv`, `openalex`, `semantic-scholar`, `deepxiv` for literature.
- `novelty-check` for closest prior work.
- `research-review` or `kill-argument` for adversarial critique.
- `research-wiki` and `wiki-enrich` for persistent memory.
- `experiment-plan`, `experiment-bridge`, `run-experiment`, and `monitor-experiment` only after a gate permits experiments.

When choosing an ARIS capability is non-obvious, use `aris-runner`.

### 5. Produce a Decision Memo

Invoke or follow `decision-memo`. Write all project artifacts under `projects/<project-slug>/`:

- `projects/<project-slug>/decisions/<idea-slug>/DECISION_MEMO.md`
- `projects/<project-slug>/decisions/<idea-slug>/decision.json`
- `projects/<project-slug>/signals/<idea-slug>/EXTERNAL_SIGNAL_LEDGER.md` when external signal scouting was used
- `projects/<project-slug>/signals/<idea-slug>/external_signals.json` when external signal scouting was used
- `projects/<project-slug>/output/pdf/<idea-slug>_decision_memo.pdf`
- `projects/<project-slug>/research-wiki/`
- `projects/<project-slug>/tmp/pdfs/`

Use `templates/DECISION_MEMO_TEMPLATE.md` as the required structure.

Before rendering or delivering a Chinese Decision Memo, invoke or follow `report-style-auditor`, then run:

```powershell
python .\tools\check_report_style.py .\projects\<project-slug>\decisions\<idea-slug>\DECISION_MEMO.md
python .\tools\check_ai_style.py .\projects\<project-slug>\decisions\<idea-slug>\DECISION_MEMO.md
```

### 6. Gate Follow-Up Work

Before experiment-like follow-up, run:

```powershell
python .\tools\decision_gate.py latest .\projects\<project-slug> --mode experiment
```

For literature-only or static work:

```powershell
python .\tools\decision_gate.py latest .\projects\<project-slug> --mode static
```

Interpret results strictly:

- `GO`: experiments may proceed.
- `STATIC_ONLY`: only static work may proceed.
- `NEEDS_MORE_EVIDENCE` or `NO_GO`: experiments are blocked.
- `USER_OVERRIDE`: proceed only if the user explicitly accepts the recorded risk.

## Output Standard

Be direct, non-flattering, and decision-oriented. Correct wrong premises explicitly.

Use Markdown deliberately:

- Use `##` section headers for research outputs.
- Bold key conclusions.
- Use tables or lists for evidence, risk, budget, and verdict comparisons.
- Separate facts, inference, and unknowns.
- Match the user's working language. For Chinese research requests, write the Decision Memo in Chinese using the Chinese-first template.
- Do not mix English boilerplate into Chinese reports. Keep English only for stable identifiers such as model names, dataset names, paper titles, code paths, JSON keys, metric abbreviations, and gate enum values.
- For unavoidable abbreviations, add a short terminology section and then use terms consistently.

The final answer should name the verdict, the reason, the PDF path, and the next allowed action.

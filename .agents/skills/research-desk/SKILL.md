---
name: research-desk
description: "Codex app driven research decision workflow for evaluating research directions or ideas before experiments. Use when the user asks whether an idea is worth doing, asks for first-principles analysis, pre-experiment reasoning, go/no-go decisions, advisor-facing research judgment, or wants to route ARIS tools without launching experiments."
---

# Research Desk

## Purpose

Run the top-level CodexResearchDesk workflow. Treat Codex app as the control surface and bundled ARIS skills/tools as the research engine. Do not launch experiments from this skill.

## Operating Rule

Experiments are expensive information purchases. Before any GPU, training, pilot, or long-running experiment, produce a Decision Memo and pass the preflight gate.

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

### 3. Build Evidence With ARIS Core

Use bundled ARIS capabilities only as tools for evidence:

- `research-lit`, `arxiv`, `openalex`, `semantic-scholar`, `deepxiv` for literature.
- `novelty-check` for closest prior work.
- `research-review` or `kill-argument` for adversarial critique.
- `research-wiki` and `wiki-enrich` for persistent memory.
- `experiment-plan`, `experiment-bridge`, `run-experiment`, and `monitor-experiment` only after a gate permits experiments.

When choosing an ARIS capability is non-obvious, use `aris-runner`.

### 4. Produce a Decision Memo

Invoke or follow `decision-memo`. Write all project artifacts under `projects/<project-slug>/`:

- `projects/<project-slug>/decisions/<idea-slug>/DECISION_MEMO.md`
- `projects/<project-slug>/decisions/<idea-slug>/decision.json`
- `projects/<project-slug>/output/pdf/<idea-slug>_decision_memo.pdf`
- `projects/<project-slug>/research-wiki/`
- `projects/<project-slug>/tmp/pdfs/`

Use `templates/DECISION_MEMO_TEMPLATE.md` as the required structure.

### 5. Gate Follow-Up Work

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

Be direct, non-flattering, and decision-oriented. The final answer should name the verdict, the reason, the PDF path, and the next allowed action.

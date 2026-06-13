---
name: research-desk
description: "Codex app driven research workflow for generating, refining, and evaluating research ideas before experiments. Use when the user wants valuable idea directions, paper/repo-driven idea discovery, first-principles analysis, pitfall avoidance, pre-experiment reasoning, go/no-go decisions, advisor-facing research judgment, or ARIS tool routing without launching experiments."
---

# Research Desk

## Purpose

Run the top-level CodexResearchDesk workflow. Treat Codex app as the control surface and bundled ARIS skills/tools as the research engine. The main job is to produce and refine valuable research ideas while avoiding predictable traps before experiments. Do not launch experiments from this skill.

## Operating Rule

Experiments are expensive information purchases. Before any GPU, training, pilot, or long-running experiment, produce a Decision Memo and pass the preflight gate.

## Retrieval Discipline

Use Codex app available retrieval rather than binding the workflow to one external search provider:

- Inspect local project files and prior research-wiki notes first when they exist.
- Use bundled ARIS literature skills/tools (`research-lit`, `arxiv`, `openalex`, `semantic-scholar`, `deepxiv`) for academic evidence.
- Use web search only when the current Codex environment provides it and the claim is unfamiliar, time-sensitive, or cannot be checked locally.
- If evidence cannot be verified, mark it as missing or low-confidence instead of smoothing over the gap.

## Core Workflow

Use one main workflow. Keep it light until a candidate idea actually deserves deeper triage:

```text
Seed Scan
→ Idea Cards
→ Evidence Probe
→ Promote / Narrow / Drop
→ Decision Memo only before expensive work
```

## Context And Delegation Protocol

The main Agent is the coordinator and editor, not the only researcher. When the environment supports subagents and the user permits delegation, split broad idea-generation work into bounded evidence packets.

Use subagents for independent evidence slices such as:

- Seed Scan: closest papers, benchmarks, and field pain points.
- Paper-Code Trace: whether key papers have usable repos, README links, license, data, checkpoint, and eval signals.
- External Signal: GitHub, alphaXiv/HF Papers, HN, OpenAlex/Semantic Scholar, and manual social/enterprise evidence.
- Pitfall Review: likely data, metric, baseline, novelty, engineering, evaluation, and contribution traps.
- Kill Test Design: 0-GPU checks with pass/fail conditions.

Do not delegate the final synthesis. The main Agent must decide which ideas are promoted, narrowed, or dropped.

Each subagent output must be an Evidence Packet using `templates/EVIDENCE_PACKET_TEMPLATE.md`:

- one packet answers one question.
- target 400-800 Chinese words plus compact tables.
- cite links or file paths instead of pasting long source text.
- include negative evidence and uncertainty.
- end with `promote`, `static_precheck`, `narrow`, or `drop`.

Default packet path:

```text
projects/<project-slug>/evidence-packets/<run-slug>/<packet-slug>.md
```

If subagents are unavailable, use the same packet format sequentially. This keeps context bounded even in single-agent mode.

### 1. Seed Scan

Collect only enough seeds to generate ideas:

- papers and closest prior work.
- associated code repositories.
- benchmarks, datasets, traces, or metrics.
- external signals such as GitHub, alphaXiv/HF Papers, HN, Reddit/X manual notes, and enterprise adoption.
- field pain points or repeated failure modes.

Do not crawl whole repositories or write long literature reviews at this stage.

### 2. Idea Cards

Turn seeds into a compact shortlist. Each card must include:

- one-sentence research claim.
- seed evidence.
- mechanism or insight.
- why it is not just paper A + paper B.
- pitfall avoided.
- likely hidden pitfall.
- code/data/evaluation trace.
- falsifier.
- lowest-cost kill test.
- action: `promote`, `static_precheck`, `narrow`, or `drop`.

### 3. Evidence Probe

Probe only the top one to three cards:

- use `external-signal-scout` if heat, community attention, or enterprise adoption could change priority.
- use `paper-code-scout` if the card depends on a paper's implementation or baseline.
- use `pitfall-radar` if the failure modes are unclear.
- use `kill-test-generator` if the next check needs concrete pass/fail conditions.
- use `direction-scorecard` only when multiple promoted cards must be compared.

Stop once the next useful action is clear.

For multi-agent runs, the main Agent should read only:

- Evidence Packet summaries.
- the top few source links or local paths cited in packets.
- structured JSON ledgers such as `external_signals.json` and `paper_code.json` when needed.

Avoid loading raw paper text, full README dumps, or repository source trees into the main context.

### 4. Formal Gate

Use `decision-memo` and `preflight-gate` only when the next action might consume GPU, training time, pilot engineering, long-running jobs, or advisor-facing formal review.

Full gate produces Markdown, PDF, and `decision.json`.

## Detailed Procedure

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

### 3. Choose The Lightest Useful Evidence

For broad or early directions, do not run every tool by default. Use the smallest evidence purchase that can change the next decision:

- If the user wants ideas, produce idea cards first.
- If the idea depends on a paper's implementation, use `paper-code-scout`.
- If public attention or adoption would affect priority, use `external-signal-scout`.
- If the risks are unclear, use `pitfall-radar`.
- If the next action needs pass/fail criteria, use `kill-test-generator`.
- If multiple promoted cards must be compared, use `direction-scorecard`.
- If the claim itself is blurry, use `direction-brief`.

These artifacts help decide what not to do and what to validate first. They do not authorize GPU, training, pilots, or long-running jobs.

### 4. Produce Idea Cards Before Formal Artifacts

When producing ideas, use this card format before any full Decision Memo:

| Field | Required content |
|---|---|
| idea | concrete idea title, not a slogan |
| core claim | one falsifiable claim |
| seed evidence | papers/repos/signals that motivated it |
| why not A+B | the non-trivial mechanism, problem reframing, or evaluation angle |
| avoided pitfall | the known failure mode it tries to dodge |
| hidden pitfall | the most likely reason it still fails |
| traceability | code/data/metric/baseline availability |
| kill test | a 0-GPU or lowest-cost check |
| action | `promote`, `static_precheck`, `narrow`, or `drop` |

Promote only the top one to three candidates into deeper triage. Park the rest with explicit reasons instead of expanding every candidate.

### 5. Build Evidence With ARIS Core

Use bundled ARIS capabilities only as tools for evidence:

- `research-lit`, `arxiv`, `openalex`, `semantic-scholar`, `deepxiv` for literature.
- `novelty-check` for closest prior work.
- `research-review` or `kill-argument` for adversarial critique.
- `research-wiki` and `wiki-enrich` for persistent memory.
- `experiment-plan`, `experiment-bridge`, `run-experiment`, and `monitor-experiment` only after a gate permits experiments.

When choosing an ARIS capability is non-obvious, use `aris-runner`.

### 6. Produce a Decision Memo

Invoke or follow `decision-memo`. Write all project artifacts under `projects/<project-slug>/`:

- `projects/<project-slug>/idea-sprints/<sprint-slug>/IDEA_SPRINT.md` when Idea Sprint is written to disk
- `projects/<project-slug>/evidence-packets/<run-slug>/<packet-slug>.md` when subagent or packetized evidence was used
- `projects/<project-slug>/output/pdf/<sprint-slug>_idea_sprint.pdf` when Idea Sprint is written to disk
- `projects/<project-slug>/decisions/<idea-slug>/DECISION_MEMO.md`
- `projects/<project-slug>/decisions/<idea-slug>/decision.json`
- `projects/<project-slug>/signals/<idea-slug>/EXTERNAL_SIGNAL_LEDGER.md` when external signal scouting was used
- `projects/<project-slug>/signals/<idea-slug>/external_signals.json` when external signal scouting was used
- `projects/<project-slug>/signals/<idea-slug>/PAPER_CODE_LEDGER.md` when paper-code scouting was used
- `projects/<project-slug>/signals/<idea-slug>/paper_code.json` when paper-code scouting was used
- `projects/<project-slug>/output/pdf/<idea-slug>_decision_memo.pdf`
- `projects/<project-slug>/research-wiki/`
- `projects/<project-slug>/tmp/pdfs/`

Use `templates/DECISION_MEMO_TEMPLATE.md` as the required structure.

Before rendering or delivering a Chinese Decision Memo, invoke or follow `report-style-auditor`, then run:

```powershell
python .\tools\check_report_style.py .\projects\<project-slug>\decisions\<idea-slug>\DECISION_MEMO.md
python .\tools\check_ai_style.py .\projects\<project-slug>\decisions\<idea-slug>\DECISION_MEMO.md
```

When writing an Idea Sprint artifact to disk, render a review PDF too:

```powershell
python .\tools\render_markdown_pdf.py .\projects\<project-slug>\idea-sprints\<sprint-slug>\IDEA_SPRINT.md --output .\projects\<project-slug>\output\pdf\<sprint-slug>_idea_sprint.pdf --preview --preview-dir .\projects\<project-slug>\tmp\pdfs
```

### 7. Gate Follow-Up Work

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

For idea generation, final answers should lead with the top candidate ideas and the first kill test for each. For single-idea triage, name the preliminary verdict, main reason, and next lowest-cost action. For Full Gate, also include the Decision Memo and PDF paths.

For Chinese idea cards, Idea Sprint artifacts, Direction artifacts, and Decision Memos, apply `report-style-auditor` before final delivery. If the artifact is written to disk, run `check_report_style.py` and `check_ai_style.py`; if it is only answered in chat, still follow the same style rules manually.

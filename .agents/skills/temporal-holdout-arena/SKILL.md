---
name: temporal-holdout-arena
description: "Drive the external ResearchSkillArena temporal holdout backtest from CodexResearchDesk. Use when the user asks to automatically run an arena/backtest/holdout after research-desk, evaluate whether a research skill could have anticipated a topic from past papers only, compare skill versions, or produce a Chinese temporal-holdout report without manually switching directories."
---

# Temporal Holdout Arena

## Purpose

Use the separate `ResearchSkillArena` as an evaluation backend while staying inside `CodexResearchDesk`. The arena tests one question: **if the workflow only saw papers up to a cutoff year, would its frozen ideas be touched by papers in the future window?**

This is not a normal novelty check for today's idea. It is a system-level backtest of the research workflow.

## Core Rule

Keep evaluation data outside `CodexResearchDesk`. The bridge tool may write a lightweight link under:

```text
projects/<project-slug>/arena-links/<run-slug>.json
```

Do not copy `past_corpus.jsonl`, `future_corpus.jsonl`, `hit_ledger.csv`, holdout reports, or arena PDFs back into Desk project folders.

## Use The Bridge Tool

Run all mechanical arena steps through:

```powershell
python .\tools\arena_holdout_bridge.py <command> ...
```

The default arena path is the sibling directory `..\ResearchSkillArena`, or `RESEARCH_SKILL_ARENA` if that environment variable is set.

## Workflow

### 1. Prepare The Arena Run

If the user did not specify a window, infer a conservative default and state it:

- `cutoff-year`: current year minus 2.
- `future-start`: cutoff year plus 1.
- `future-end`: current year.
- sources: `openalex,semantic_scholar,arxiv`.
- max past/future: `80` / `120`.

If the topic names a model, dataset, or benchmark that did not exist at the cutoff, rewrite the holdout topic into a historically valid broader topic. Example: change "Qwen3-8B-Instruct 情感交流微调" to "open-weight 7B-8B instruct models for empathetic dialogue / emotional support fine-tuning".

```powershell
python .\tools\arena_holdout_bridge.py prepare `
  --project <project-slug> `
  --run <run-slug> `
  --topic "<historically-valid topic query>" `
  --cutoff-year <year> `
  --future-start <year> `
  --future-end <year>
```

This creates the arena config, `historical_idea_prompt.md`, and `past_corpus.jsonl`.

### 2. Generate Historical-Only Ideas

Read only these arena files:

```text
ResearchSkillArena/tasks/<project>/<run>/historical_idea_prompt.md
ResearchSkillArena/tasks/<project>/<run>/past_corpus.jsonl
```

Generate a Chinese `IDEAS_FROZEN.md` in the same readable Idea Card style as `$research-desk`. Do not use future papers, current leaderboards, or today's normal research output as evidence.

For rigorous backtests, use a fresh subagent/thread if available. If the same Codex conversation already contains future-window evidence, state that the run is a convenience backtest with possible memory leakage.

### 3. Freeze The Submission

After writing the historical-only ideas to a Desk temp file or directly to the arena submission path, freeze them through the bridge:

```powershell
python .\tools\arena_holdout_bridge.py submit-ideas `
  --project <project-slug> `
  --run <run-slug> `
  --ideas-file <path-to-historical-ideas>
```

Do not edit `IDEAS_FROZEN.md` after future corpus collection starts.

### 4. Create The Review Ledger

```powershell
python .\tools\arena_holdout_bridge.py make-ledger `
  --project <project-slug> `
  --run <run-slug>
```

This collects future papers and creates candidate matches. It does not decide hits.

By default this also fetches Papers.cool/Kimi interpretations for a small number of arXiv candidates and writes:

```text
ResearchSkillArena/reports/<project>/<run>/papers_cool_insights.jsonl
ResearchSkillArena/reports/<project>/<run>/papers_cool_review_brief.md
ResearchSkillArena/reports/<project>/<run>/papers_cool_triage.csv
ResearchSkillArena/reports/<project>/<run>/papers_cool_triage.md
ResearchSkillArena/reports/<project>/<run>/papers_cool_cache/
```

Use the triage Markdown as the first file to read. It produces `needs_pdf_review = yes / maybe / no`, so Codex should open PDFs only for `yes` first, then `maybe` if needed. It cannot justify a hit by itself.

To skip Papers.cool:

```powershell
python .\tools\arena_holdout_bridge.py make-ledger `
  --project <project-slug> `
  --run <run-slug> `
  --skip-cool
```

To run only the enrichment step:

```powershell
python .\tools\arena_holdout_bridge.py enrich-cool `
  --project <project-slug> `
  --run <run-slug> `
  --max-papers 20
```

To regenerate only the PDF-review priority queue from cached insights:

```powershell
python .\tools\arena_holdout_bridge.py triage-cool `
  --project <project-slug> `
  --run <run-slug>
```

### 5. Review By Experiments First

Open `hit_ledger.csv`. For each plausible match, judge the future paper from figures, tables, ablations, metrics, experimental settings, and error analysis. Do not count a hit from abstract/introduction/conclusion text alone.

Read `papers_cool_triage.md` first when it exists. Only open PDFs for `yes` candidates at first; inspect `maybe` only after the high-priority queue is exhausted or when a specific idea has no `yes` candidates. Treat Papers.cool as an AI interpretation from a third-party site, not as evidence. If it mentions experiments, still verify the figure/table/metric in the actual paper before using `direct_hit` or `partial_hit`.

Required fields for `direct_hit` or `partial_hit`:

- `experiment_support`: `solid_experiment` or `partial_experiment`.
- `experiment_units`: concrete figure/table/ablation IDs.
- `evidence_basis`: what the experiment actually shows.
- `unsupported_conditions`: conditions not verified.
- `reviewer_reason`: why it is a hit.
- `evidence_link`: paper URL or PDF link.

Use `conclusion_only` when only author claims exist. `conclusion_only` cannot support `direct_hit` or `partial_hit`.

### 6. Finalize The Report

Only after the ledger has review evidence:

```powershell
python .\tools\arena_holdout_bridge.py finalize-report `
  --project <project-slug> `
  --run <run-slug>
```

The bridge calls the arena report renderer and style checkers. The final Markdown/PDF remain in `ResearchSkillArena`.

## Status Command

Use this whenever the run state is unclear:

```powershell
python .\tools\arena_holdout_bridge.py status --project <project-slug> --run <run-slug>
```

## What To Tell The User

Explain the boundary plainly:

- Normal `$research-desk` research answers "what should we do now?"
- Arena holdout answers "could this workflow have generated similar ideas using only past papers?"
- The mechanical parts can be automated.
- The two judgment points cannot be faked: historical idea generation must be frozen before future collection, and hit labels must be based on experimental evidence.

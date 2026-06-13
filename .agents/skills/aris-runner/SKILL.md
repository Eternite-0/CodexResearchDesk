---
name: aris-runner
description: "Route research tasks to the bundled ARIS core skills and tools inside CodexResearchDesk. Use when a task needs literature search, novelty checking, research review, wiki memory, experiment planning, experiment running, monitoring, or paper/claim audit through ARIS-derived capabilities."
---

# ARIS Runner

## Purpose

Select and invoke the right bundled ARIS capability while keeping `research-desk` as the top-level decision workflow.

## Capability Map

| Need | Use |
|---|---|
| Broad literature landscape | `research-lit` |
| arXiv search/download metadata | `arxiv` or `tools/arxiv_fetch.py` |
| Open citation graph search | `openalex` or `tools/openalex_fetch.py` |
| Published venue metadata | `semantic-scholar` or `tools/semantic_scholar_fetch.py` |
| Progressive paper reading | `deepxiv` |
| Novelty and closest prior work | `novelty-check` |
| Critical review | `research-review` |
| Strongest rejection memo | `kill-argument` |
| Persistent memory | `research-wiki`, `wiki-enrich`, `tools/research_wiki.py` |
| Experiment plan | `experiment-plan` |
| Implement/deploy experiments | `experiment-bridge` |
| Launch experiments | `run-experiment` |
| Monitor experiments | `monitor-experiment` |
| Map results to claims | `result-to-claim` |
| Paper claim/citation checks | `paper-claim-audit`, `citation-audit` |
| Paper outline from evidence | `paper-plan` |

## Routing Rules

1. If the user is deciding whether an idea is worth doing, route to `research-desk` first.
2. If the task may start experiments, run `preflight-gate` first.
3. If the gate blocks, do not invoke experiment skills.
4. If a copied ARIS skill asks for a helper script, prefer the local `tools/` copy.
5. If a copied ARIS skill references upstream AutoResearch-specific paths, adapt them to this repository root. Do not introduce a dependency on a local upstream checkout.

## Tool Resolution

Use the local resolver when a deterministic path is useful:

```powershell
python .\tools\aris_tool_resolver.py tool research_wiki.py
python .\tools\aris_tool_resolver.py skill research-lit
```

## Output Standard

Record important ARIS-derived outputs in the current Decision Memo or in `research-wiki/`. Do not let ARIS tool output become an unreviewed reason to launch experiments.

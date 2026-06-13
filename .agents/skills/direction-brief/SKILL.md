---
name: direction-brief
description: "Create concise 1-2 page Direction Briefs for early research direction triage. Use when the user wants a quick pre-experiment research direction brief, core claim framing, evidence gaps, novelty and feasibility questions, top risks, lowest-cost next check, preliminary verdict, or Direction Triage Mode."
---

# Direction Brief

## Purpose

Produce a short, decision-oriented brief for a research direction before any expensive experiment. Keep the artifact focused on whether the direction deserves more evidence, not on designing a full AutoResearch workflow.

## Workflow

1. Normalize the direction into one sentence.
2. State the core research claim in a form that can be falsified.
3. Separate known facts, reasoned inference, and missing evidence.
4. Identify novelty and feasibility questions that must be checked before experiments.
5. Name the top three risks and one lowest-cost next check.
6. End with a preliminary verdict: `GO`, `STATIC_ONLY`, `NEEDS_MORE_EVIDENCE`, `NO_GO`, or `USER_OVERRIDE`.

## Output

Use `templates/DIRECTION_BRIEF_TEMPLATE.md` unless the user asks for another format. Write in the user's working language. For Chinese research requests, keep headings, table labels, and reasoning in Chinese, while preserving stable identifiers such as model names, dataset names, metric abbreviations, and verdict enum values.

The brief must include:

- one-sentence direction.
- core research claim.
- why the direction is worth checking.
- existing evidence required.
- novelty questions.
- feasibility questions.
- Top 3 risks.
- lowest-cost next check.
- preliminary verdict.

## Guardrails

- Do not launch experiments, GPU jobs, training, or long-running tasks.
- Do not inflate weak ideas. If the direction is too broad or already crowded, say so directly.
- Prefer cheap checks: literature overlap, public benchmark inspection, static protocol review, public checkpoint analysis, or non-training probes.
- If evidence is not verified, mark it as a gap instead of treating it as support.

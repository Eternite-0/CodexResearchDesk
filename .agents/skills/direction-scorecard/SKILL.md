---
name: direction-scorecard
description: "Score research directions for Direction Triage Mode using 1-5 ratings across novelty, feasibility, data accessibility, compute cost control, evaluation clarity, baseline reproducibility, and publication or project value. Use when the user asks for a research direction scorecard, total score /100, risk level, continue/stop reasons, recommended verdict, or recommended next action."
---

# Direction Scorecard

## Purpose

Score a research direction before experiments so the user can compare directions, expose weak assumptions, and decide whether to continue, narrow, or stop.

## Scoring

Rate each dimension from 1 to 5:

- 1: weak, unclear, blocked, or unsupported.
- 2: plausible but fragile.
- 3: workable with important gaps.
- 4: strong enough for low-cost validation.
- 5: strong, direct, and well-supported.

Compute `total_score` as `round(sum(scores) / 35 * 100)`.

Required dimensions:

- Novelty.
- Feasibility.
- Data accessibility.
- Compute cost control.
- Evaluation clarity.
- Baseline reproducibility.
- Publication / project value.

Use `risk_level` as `low`, `medium`, or `high`.

## Verdict Guidance

Use judgment, but stay conservative:

- `GO`: direct evidence exists, resource budget is explicit, and the next step genuinely needs experiments.
- `STATIC_ONLY`: direction has potential, but only literature, static analysis, public checkpoint analysis, or non-training probes are justified.
- `NEEDS_MORE_EVIDENCE`: key evidence gaps block even a static verdict.
- `NO_GO`: the direction is too crowded, infeasible, untestable, or low-value under current constraints.
- `USER_OVERRIDE`: only when the user explicitly accepts recorded risk.

## Output

Use `templates/DIRECTION_SCORECARD_TEMPLATE.md`. Include total score /100, continue reasons, stop reasons, recommended verdict, and recommended next action.

## Guardrails

- Do not treat a high score as permission to run experiments. A Decision Memo and gate must still authorize expensive work.
- Penalize unclear evaluation and unreproducible baselines heavily, even if the idea sounds novel.
- Keep scoring auditable: every score needs a short reason.

---
name: pitfall-radar
description: "Identify early pitfalls in a research direction before experiments. Use when the user wants a Pitfall Radar, risk descriptions, warning signs, cheap pre-checks, severity, mitigation, or a skeptical pre-mortem for data, metrics, baselines, novelty, engineering, evaluation, or paper contribution risks."
---

# Pitfall Radar

## Purpose

Run a skeptical pre-mortem for a research direction and surface the cheapest checks that can prevent wasted experiments.

## Required Pitfall Types

Evaluate these categories:

- data pitfall.
- metric pitfall.
- baseline pitfall.
- novelty pitfall.
- engineering pitfall.
- evaluation pitfall.
- paper/contribution pitfall.

For each category, provide:

- risk description.
- warning signs.
- cheap pre-check.
- severity: `low`, `medium`, or `high`.
- mitigation.

## Output

Use `templates/PITFALL_RADAR_TEMPLATE.md`. Keep the artifact operational: every pitfall should tell the user what to inspect next and what would make the direction weaker.

## Guardrails

- Prefer checks that use existing papers, public code, public data, static protocol inspection, or small non-training probes.
- Do not propose GPU training as a mitigation unless a later Decision Gate permits experiments.
- Be specific about failure modes. Avoid generic risks such as "may not work" without observable warning signs.

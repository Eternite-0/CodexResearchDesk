---
name: kill-test-generator
description: "Generate low-cost kill tests for research directions before experiments. Use when the user asks for kill tests, falsification tests, lowest-cost next checks, pass/fail conditions, decision changes if failed, or ways to quickly reject an idea before committing compute."
---

# Kill Test Generator

## Purpose

Design low-cost tests that can change the decision about a research direction. The goal is to kill weak directions early or narrow them before expensive experiments.

## Requirements

Generate at least three kill tests. At least one test must be able to quickly reject or sharply narrow the direction if it fails.

Each test must include:

- test name.
- hypothesis.
- expected cost.
- pass condition.
- fail condition.
- decision change if failed.

## Test Types

Prefer these cheap tests before experiments:

- closest-prior-work overlap check.
- public benchmark protocol audit.
- paper-to-code traceability audit.
- dataset accessibility and split audit.
- repository install/evaluation entrypoint audit without training.
- baseline reproduction feasibility check.
- metric validity check.
- public checkpoint or static output inspection.
- non-training probe with existing artifacts.

## Output

Use `templates/KILL_TEST_TEMPLATE.md`. Make the fail condition concrete enough that the user can stop, narrow, or return to evidence gathering.

## Guardrails

- Do not propose training, GPU pilots, or long-running jobs as default kill tests.
- Do not design tests that cannot affect the verdict.
- If a test would require compute, state that it is blocked until a Decision Memo and gate permit it.

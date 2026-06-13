---
name: preflight-gate
description: "Check and enforce Decision Memo gates before experiments, pilots, GPU jobs, training, or long-running tasks. Use when deciding whether run-experiment, experiment-bridge, static analysis, or user override is allowed."
---

# Preflight Gate

## Purpose

Mechanically enforce the Decision Memo verdict. This skill does not judge idea quality; it checks the latest or specified `decision.json`.

## Commands

Check the newest decision for experiment work:

```powershell
python .\tools\decision_gate.py latest .\projects\<project-slug> --mode experiment
```

Check a specific decision:

```powershell
python .\tools\decision_gate.py check .\projects\<project-slug>\decisions\<idea-slug>\decision.json --mode experiment
```

Check static-only work:

```powershell
python .\tools\decision_gate.py check .\projects\<project-slug>\decisions\<idea-slug>\decision.json --mode static
```

Allow an explicit user override:

```powershell
python .\tools\decision_gate.py check .\projects\<project-slug>\decisions\<idea-slug>\decision.json --mode experiment --allow-override
```

## Enforcement

- Exit code `0`: allowed.
- Exit code `2`: blocked.
- Missing, malformed, stale, or invalid decision files are blocked.
- `GO` allows experiment and static work.
- `STATIC_ONLY` allows only static mode.
- `NEEDS_MORE_EVIDENCE` and `NO_GO` always block experiments.
- `USER_OVERRIDE` requires `--allow-override` and a non-empty `override_reason`.

## Required Behavior

Before using `experiment-bridge`, `run-experiment`, or any direct command that starts training, call this gate. If blocked, stop and explain the recorded reason. Do not work around the gate by launching a smaller experiment unless the verdict allows it.

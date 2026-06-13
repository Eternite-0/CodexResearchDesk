---
name: external-signal-scout
description: "Collect external soft-gate signals for early research idea triage: GitHub health, alphaXiv/HF Papers attention, Hacker News discussion, Semantic Scholar/OpenAlex metadata, and manual X/Reddit/enterprise evidence. Use before Direction Scorecard and Decision Memo when deciding whether an idea is actually doable rather than just a paper A+B combination."
---

# External Signal Scout

## Purpose

Find external signals that expose hidden research pitfalls before experiments. This skill does not reproduce papers and does not prove a paper is true. It helps decide which ideas deserve deeper reading, which directions are hype-heavy, and which claims need cheap kill tests before any GPU or long-running work.

## Workflow Position

Use this after `pitfall-radar` and before `direction-scorecard`:

```text
Direction Brief
→ Pitfall Radar
→ External Signal Scout
→ Direction Scorecard
→ Kill Tests
→ Decision Memo
```

## Command

```powershell
python .\tools\external_signal_fetch.py scout "<idea/query>" --project <project-slug> --idea <idea-slug>
```

Optional evidence handles:

```powershell
python .\tools\external_signal_fetch.py scout "<idea/query>" `
  --project <project-slug> `
  --idea <idea-slug> `
  --arxiv-id <id> `
  --github-repo owner/name `
  --manual-signals .\projects\<project-slug>\signals\<idea-slug>\manual_signals.json
```

## Outputs

Write only under the project:

- `projects/<project-slug>/signals/<idea-slug>/EXTERNAL_SIGNAL_LEDGER.md`
- `projects/<project-slug>/signals/<idea-slug>/external_signals.json`

Do not write root-level `signals/` directories.

## Interpretation

- High external signal means "look here first", not "the paper is correct".
- Low external signal means "needs more pre-checks", not automatic `NO_GO`.
- High community attention with low benchmark or trace signal is a hype risk.
- Strong benchmark/leaderboard evidence can matter even when GitHub stars are low.
- Manual X/Reddit/enterprise evidence must be labeled as manual and should include a URL or note.

## Decision Memo Integration

When a ledger exists, cite it in the Decision Memo:

- `external_signal_score`
- `external_signal_summary`
- `external_signal_ledger`
- `hype_risk`

These fields are soft-gate metadata. They must not override the evidence ledger, novelty check, or Decision Gate by themselves.

---
name: paper-code-scout
description: "Trace papers to their likely code repositories before reproduction: Papers with Code, arXiv/alphaXiv links, GitHub search, README title/arXiv matching, license, maintenance, install/data/checkpoint/evaluation signals. Use after external-signal-scout and before Direction Scorecard when a research idea depends on one or more papers."
---

# Paper Code Scout

## Purpose

Find whether a paper has a real, traceable, statically auditable codebase before any reproduction work. This skill does not run experiments and does not claim the paper is reproducible. It answers a narrower early-screening question:

- Is there an official or strongly linked repository?
- Does the repository actually point back to the paper title or arXiv ID?
- Does it expose install, data, checkpoint, config, and evaluation entry points?
- Are license, maintenance, and "code coming soon" risks visible early?
- What should the reproduction owner inspect later?

## Workflow Position

Use this after `external-signal-scout` and before `direction-scorecard`:

```text
Direction Brief
→ Pitfall Radar
→ External Signal Scout
→ Paper Code Scout
→ Direction Scorecard
→ Kill Tests
→ Decision Memo
```

## Command

```powershell
python .\tools\paper_code_fetch.py scout "<paper title/query>" --project <project-slug> --idea <idea-slug>
```

Recommended when the arXiv ID or repository is known:

```powershell
python .\tools\paper_code_fetch.py scout "<paper title/query>" `
  --project <project-slug> `
  --idea <idea-slug> `
  --arxiv-id <id> `
  --paper-title "<exact paper title>" `
  --github-repo owner/name
```

Manual repository hints can be supplied:

```powershell
python .\tools\paper_code_fetch.py scout "<paper title/query>" `
  --project <project-slug> `
  --idea <idea-slug> `
  --manual-code .\projects\<project-slug>\signals\<idea-slug>\manual_code.json
```

`manual_code.json` shape:

```json
{
  "repositories": [
    {
      "repo": "owner/name",
      "url": "https://github.com/owner/name",
      "note": "Author project page links here."
    }
  ]
}
```

## Outputs

Write only under the project:

- `projects/<project-slug>/signals/<idea-slug>/PAPER_CODE_LEDGER.md`
- `projects/<project-slug>/signals/<idea-slug>/paper_code.json`

Do not write root-level `signals/` directories.

## Interpretation

- High `paper_code_trace_score` means "safe to do static due diligence next", not "paper reproduced".
- Low score means "the paper may still be useful, but do not build the idea on its implementation yet".
- Official code with no evaluation script is still a risk.
- Popular unofficial repos should not be treated as paper evidence unless README/title/arXiv linkage is explicit.
- "code coming soon", missing license, stale commits, and absent data/checkpoint/eval links should become kill-test inputs.

## Decision Memo Integration

When a ledger exists, cite it in the Decision Memo:

- `paper_code_trace_score`
- `paper_code_summary`
- `paper_code_ledger`
- `code_availability_risk`

These fields are soft-gate metadata. They must not by themselves decide `GO` or `NO_GO`, but they should affect risk, prechecks, and allowed next actions.

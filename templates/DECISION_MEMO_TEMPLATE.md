# Decision Memo: [Idea Title]

**Idea ID**: [idea-slug]  
**Project ID**: [project-slug]  
**Date**: [YYYY-MM-DD]  
**Verdict**: [GO / STATIC_ONLY / NEEDS_MORE_EVIDENCE / NO_GO / USER_OVERRIDE]  
**Confidence**: [high / medium / low]  
**Owner**: CodexResearchDesk  

## Executive Decision

**Decision**: [one paragraph explaining whether the idea should consume experiment resources now]

**Reason**: [short, direct reason]

## Premise Check

| Item | Assessment |
|---|---|
| User premise | [what the idea assumes or asks] |
| Correction needed? | [yes/no + direct correction if any] |
| Evidence status | [verified / partially verified / unverified] |
| Retrieval used | [local wiki / ARIS literature tool / web search if available / none] |

## First-Principles Decomposition

| Question | Answer |
|---|---|
| What is the core claim? | [claim] |
| What must be true? | [necessary conditions] |
| What would falsify it? | [falsifier] |
| What is the smallest useful unit of evidence? | [evidence unit] |

## Multi-Perspective Reasoning

### PI / Advisor View

- **Upside**: [why it matters]
- **Concern**: [why it may not be worth supervising]
- **Decision pressure**: [what would convince the advisor]

### Resource Manager View

- **Information gained per cost**: [assessment]
- **Resource risk**: [risk]
- **Stop condition**: [when to halt]

### Skeptical Reviewer View

- **Strongest objection**: [objection]
- **Likely rejection reason**: [reason]
- **Required evidence**: [evidence]

## Evidence Ledger

| Type | Evidence | Strength | Notes |
|---|---|---|---|
| Supporting | [paper/result/argument] | [high/medium/low] | [notes] |
| Opposing | [paper/result/argument] | [high/medium/low] | [notes] |
| Adjacent | [related but not direct] | [high/medium/low] | [notes] |
| Missing | [unknown] | [blocking/non-blocking] | [notes] |

## Critical Evaluation

### Advantages

- [advantage]

### Weaknesses / Risks

- [risk]

### Failure Modes

- [failure mode and implication]

## Lowest-Cost Kill Test

| Item | Plan |
|---|---|
| Test type | [literature / static analysis / public checkpoint / tiny probe / GPU experiment] |
| Inputs | [data, model, paper set, code] |
| Metric / observable | [what to inspect] |
| Pass condition | [what would justify next step] |
| Kill condition | [what would stop the idea] |
| Estimated cost | [time, GPU-hours, API cost] |

## Resource Budget

| Stage | Allowed? | Budget | Notes |
|---|---:|---:|---|
| Literature and prior art | yes | [hours] | [notes] |
| Static/public checkpoint analysis | [yes/no] | [hours] | [notes] |
| Training or GPU pilot | [yes/no] | [GPU-hours] | [notes] |

## Final Gate

```json
{
  "idea_id": "[idea-slug]",
  "project_id": "[project-slug]",
  "verdict": "[GO | STATIC_ONLY | NEEDS_MORE_EVIDENCE | NO_GO | USER_OVERRIDE]",
  "confidence": "[high | medium | low]",
  "max_gpu_hours_allowed": 0,
  "allowed_next_actions": [],
  "blocking_reasons": [],
  "memo_md": "projects/[project-slug]/decisions/[idea-slug]/DECISION_MEMO.md",
  "memo_pdf": "projects/[project-slug]/output/pdf/[idea-slug]_decision_memo.pdf",
  "created_at": "[ISO-8601 timestamp]"
}
```

## Self-Audit

- **Topic fit**: [yes/no + note on whether the memo answers the user's actual question]
- **Factual accuracy**: [checked facts, unverified facts, and likely error sources]
- **Logic closure**: [whether evidence and assumptions support the verdict]
- **Overclaim check**: [what was softened or rejected]

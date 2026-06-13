# Decision Memo: SAE Features as Static Probes for MoE Expert Routing

**Idea ID**: `sae-moe-routing-saes`  
**Project ID**: `sae-moe-interpretability`  
**Date**: 2026-06-13  
**Verdict**: `STATIC_ONLY`  
**Confidence**: `medium`  
**Owner**: CodexResearchDesk  

## Executive Decision

**Decision**: Do not start training or GPU experiments yet. The idea is promising enough for static analysis, but not yet strong enough to justify a training pilot.

**Reason**: The mechanism is plausible: sparse autoencoders can expose interpretable activation features, and MoE routing creates observable expert choices. However, the current evidence does not yet prove that SAE features explain routing decisions rather than merely correlating with token/domain statistics. The next action should be a low-cost static kill test using public MoE checkpoints, public or lightweight SAE features, and cached activations if available.

## First-Principles Decomposition

| Question | Answer |
|---|---|
| What is the core claim? | Sparse SAE features can explain or predict MoE expert routing in a way that is more mechanistic than token identity or domain labels alone. |
| What must be true? | Expert routing must depend on latent features that are visible in the activation space where SAE features are learned. |
| What would falsify it? | SAE feature activations add little or no predictive/explanatory signal beyond token/domain baselines. |
| What is the smallest useful unit of evidence? | A static association test between feature activations and expert routing on a small token sample, with token/domain controls. |

## Multi-Perspective Reasoning

### PI / Advisor View

- **Upside**: If true, this gives a concrete bridge between mechanistic interpretability and MoE system behavior.
- **Concern**: A correlation-only result may be dismissed as descriptive analysis rather than a research contribution.
- **Decision pressure**: The idea needs one clear discriminating signal before any training budget is spent.

### Resource Manager View

- **Information gained per cost**: Static routing-feature association is cheap and decisive enough for first screening.
- **Resource risk**: Training a new SAE or running a full MoE sweep before checking simple baselines could waste the whole budget.
- **Stop condition**: Stop if SAE features do not outperform token identity, domain labels, or shallow activation probes for routing explanation.

### Skeptical Reviewer View

- **Strongest objection**: Expert routing may reflect token frequency, language/domain, or router geometry rather than semantic SAE features.
- **Likely rejection reason**: The analysis does not establish causality or mechanistic control.
- **Required evidence**: At minimum, show incremental explanatory value over strong baselines and include negative controls.

## Evidence Ledger

| Type | Evidence | Strength | Notes |
|---|---|---|---|
| Supporting | Sparse autoencoders have been used to recover interpretable features in transformer activations. | medium | Supports feature extraction, not routing explanation by itself. |
| Supporting | MoE work reports expert specialization and routing structure. | medium | Supports the possibility of structured routing. |
| Adjacent | Public SAE and model resources reduce the cost of a static probe. | medium | Useful for feasibility, not for the claim itself. |
| Opposing | Expert routing may be dominated by token/domain distributions. | medium | This is the main confound. |
| Missing | Direct evidence that SAE features add explanatory power beyond token/domain baselines. | blocking | Must be addressed before experiments. |
| Missing | Causal intervention evidence on routing behavior. | non-blocking for v0 | Needed later if the static signal is positive. |

## Critical Evaluation

### Advantages

- Connects two active interpretability areas: SAE feature analysis and MoE expert specialization.
- Can start with public artifacts and a small static analysis instead of training.
- A negative result is still useful: it can rule out a tempting but weak research direction before spending GPU time.

### Weaknesses / Risks

- Feature-routing correlation may be superficial.
- SAE features may not be stable across layers, checkpoints, or SAE training settings.
- If only static association is shown, the result may not be strong enough for a top venue.

### Failure Modes

- **Token confound dominates**: the result becomes a token/domain clustering story, not mechanistic interpretability.
- **Layer mismatch**: SAE features are learned at a representation point that is not causally upstream of the router.
- **No robust signal**: effects vanish across prompts, languages, or model checkpoints.

## Lowest-Cost Kill Test

| Item | Plan |
|---|---|
| Test type | Static analysis / public checkpoint probe |
| Inputs | Public MoE model with router logits, small token sample, SAE features or lightweight feature dictionary |
| Metric / observable | Incremental prediction of expert choice or router logit from SAE features after token/domain controls |
| Pass condition | SAE features explain routing better than token/domain baselines and identify coherent feature-expert alignments |
| Kill condition | SAE features add no meaningful signal beyond baselines or produce unstable alignments |
| Estimated cost | 0 GPU-hours for first pass if public activations/checkpoints suffice; otherwise CPU/light GPU feature extraction only |

## Resource Budget

| Stage | Allowed? | Budget | Notes |
|---|---:|---:|---|
| Literature and prior art | yes | 4-8 hours | Confirm closest prior work and public artifacts. |
| Static/public checkpoint analysis | yes | 4-12 hours | Allowed next step. |
| Training or GPU pilot | no | 0 GPU-hours | Blocked until static signal is positive. |

## Final Gate

```json
{
  "idea_id": "sae-moe-routing-saes",
  "project_id": "sae-moe-interpretability",
  "title": "SAE Features as Static Probes for MoE Expert Routing",
  "verdict": "STATIC_ONLY",
  "confidence": "medium",
  "max_gpu_hours_allowed": 0,
  "allowed_next_actions": [
    "literature review",
    "public checkpoint analysis",
    "static routing-feature association test",
    "negative-control design"
  ],
  "blocking_reasons": [
    "No direct evidence yet that SAE features explain routing beyond token/domain baselines",
    "Training a new SAE or running a GPU pilot is premature before a static signal exists"
  ],
  "memo_md": "projects/sae-moe-interpretability/decisions/sae-moe-routing-saes/DECISION_MEMO.md",
  "memo_pdf": "projects/sae-moe-interpretability/output/pdf/sae-moe-routing-saes_decision_memo.pdf",
  "created_at": "2026-06-13T06:45:00Z"
}
```

## Self-Audit

- **Topic fit**: yes. The memo evaluates whether SAE/MoE interpretability should consume experiment resources.
- **Factual risk**: medium. The broad literature facts are stable, but the direct feature-routing claim still needs source-level verification.
- **Logic closure**: yes. The verdict follows from a plausible mechanism plus a blocking evidence gap.
- **Overclaim check**: The memo does not claim SAE features explain MoE routing; it only permits a static test.

# Decision JSON Schema

Required fields:

- `project_id`: slug used under `projects/`.
- `idea_id`: slug used under the project's `decisions/`.
- `title`: human-readable idea title.
- `verdict`: one of `GO`, `STATIC_ONLY`, `NEEDS_MORE_EVIDENCE`, `NO_GO`, `USER_OVERRIDE`.
- `confidence`: one of `high`, `medium`, `low`.
- `max_gpu_hours_allowed`: numeric budget. Use `0` for non-experiment verdicts.
- `allowed_next_actions`: array of strings.
- `blocking_reasons`: array of strings.
- `memo_md`: path to the Markdown memo.
- `memo_pdf`: path to the rendered PDF.
- `created_at`: ISO-8601 timestamp.

Optional fields:

- `direction_score`: numeric score from 0 to 100.
- `risk_level`: one of `low`, `medium`, `high`.
- `main_claim`: string describing the core research claim.
- `top_risks`: array of strings.
- `evidence_gaps`: array of strings.
- `external_signal_score`: numeric score from 0 to 100.
- `external_signal_summary`: string summarizing the external signal ledger.
- `external_signal_ledger`: path to `EXTERNAL_SIGNAL_LEDGER.md`.
- `hype_risk`: one of `low`, `medium`, `high`.
- `paper_code_trace_score`: numeric score from 0 to 100.
- `paper_code_summary`: string summarizing the paper-code ledger.
- `paper_code_ledger`: path to `PAPER_CODE_LEDGER.md`.
- `code_availability_risk`: one of `low`, `medium`, `high`.
- `kill_tests`: array of strings or objects. Objects should include `test_name`, `hypothesis`, `expected_cost`, `pass_condition`, `fail_condition`, and `decision_change_if_failed`.
- `resource_budget`: object or short string describing non-GPU and GPU resource limits.
- `blocked_actions`: array of actions explicitly blocked by the verdict.
- `next_review_condition`: string describing when to revisit the gate.
- `override_reason`: required when verdict is `USER_OVERRIDE`.
- `source_materials`: array of reports, papers, or wiki pages used.
- `reviewers`: array of external review routes used.

Validation notes:

- Legacy decision files without the optional v0.2 fields remain valid if the required fields and verdict rules pass.
- `STATIC_ONLY` must include at least one static next action such as literature review, static analysis, public checkpoint analysis, or non-training probes.
- External signal and paper-code scores are soft-gate evidence only. Low scores should affect risk, prechecks, and next actions, but are not hard blockers by themselves.
- `NEEDS_MORE_EVIDENCE` must include `evidence_gaps` or `blocking_reasons`.
- `NO_GO` must include non-empty `blocking_reasons`.
- `GO` must include `max_gpu_hours_allowed` or `resource_budget`.
- Blocking verdicts should include `blocked_actions` when possible, but this is not a hard compatibility requirement.

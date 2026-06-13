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

- `override_reason`: required when verdict is `USER_OVERRIDE`.
- `source_materials`: array of reports, papers, or wiki pages used.
- `reviewers`: array of external review routes used.

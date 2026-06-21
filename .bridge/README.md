# Bridge Task Artifacts

`.bridge/<task-id>/` contains the explicit handoff artifacts for one pipeline task. Task directories are committed to feature branches so reviewers can audit plans, changes, verification, and reviews.

## Planned Artifact Set

- `TASK.md`
- `PLAN.md`
- `EDIT_<tool>.md`
- `CHANGES.diff`
- `VERIFY.json`
- `REVIEW_QWEN.json` when required by the selected mode
- `REVIEW_CLAUDE.json`
- `FINAL_REPORT.md`

The `qwen-led` mode intentionally omits `REVIEW_QWEN.json`. Phase 5 guarded evidence may also include `EXTERNAL_COMMANDS.log` and `RUN_METADATA.json`.

Do not store credentials, raw authentication output, local tool configuration, temporary logs, or unrelated generated files here.

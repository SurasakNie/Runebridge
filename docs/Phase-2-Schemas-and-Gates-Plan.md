# Phase 2 Schemas and Deterministic Gates Plan

## Scope

Define five draft-07 artifact schemas and seven deterministic Python gates. Phase 2 validates existing artifacts and paths only; it does not invoke vendors, create artifacts, sequence stages, or mutate GitHub.

## Contracts

| Schema | Artifact |
|---|---|
| `task.schema.json` | `TASK.md` YAML front matter |
| `plan.schema.json` | `PLAN.md` YAML front matter |
| `edit-summary.schema.json` | `EDIT_<tool>.md` YAML front matter |
| `verify.schema.json` | `VERIFY.json` |
| `review.schema.json` | `REVIEW_*.json` |

| Gate | Responsibility |
|---|---|
| `check_artifacts.py` | Require mode-specific artifact sets, reject forbidden artifacts, and validate task/edit front matter |
| `check_plan.py` | Parse and schema-validate `PLAN.md` |
| `check_rsk0.py` | Exit 2 for RSK-0 or human-approval plans |
| `check_scope.py` | Reject changed paths outside `files_to_touch` |
| `check_verify.py` | Reject invalid or failing verification artifacts |
| `check_review.py` | Reject invalid reviews, blockers, drift, or non-approval verdicts |
| `check_no_secrets.py` | Reject credential signatures in selected files |

Exit `0` means pass, `1` means deterministic validation failure, and `2` is reserved for RSK-0. All failures write concise diagnostics to stderr.

## Exit Gate

Valid, malformed, missing-field, failure, drift, blocker, secret, and RSK-0 fixtures pass locally and in protected CI. No gate performs network, vendor, Git, or GitHub writes.

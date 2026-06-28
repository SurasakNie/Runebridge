# Branch Cleanup Log

This log records decisions about deleting or retaining stale Git branches, so the
rationale survives after the branches themselves are gone. Branch deletion is a
manual owner action performed from the GitHub Branches page; agent sessions in the
managed remote environment cannot delete remote refs.

## 2026-06-27 — Post-PR #21 cleanup

After PR #21 ("Document PC-first Qwen runner evidence") merged into `main` at
`579afe0`, the remaining feature branches were reviewed. All were
documentation-only and contained no committed secrets.

### Deleted — merged into `main`, fully contained

These branches' pull requests merged and their tips matched the merged PR head, so
nothing unique was lost.

| Branch | PR | Note |
|---|---|---|
| `codex/qwen-pc-runner-evidence` | #21 | merged into `main` at `579afe0` |
| `codex/post-phase-5-reconciliation` | #11 | merged; content fully in `main` |
| `codex/phase-0.6-vendor-cli` | #3 | merged |
| `codex/phase-5-full-dry-run` | #10 | merged |
| `codex/phase-6-live-vendor-plan` | #12 | merged |
| `claude/pr21-review-rgfwne` | — | review branch; its only commit (a P6-001H wording fix) was superseded by the owner's `9417e80` already in `main` |

### Deleted — stale, superseded, never merged

| Branch | Unique commit | Why dropped |
|---|---|---|
| `claude/eloquent-darwin-pjpugh` | `afddb16` "Reconcile handoff and changelog after PR #16" | A post-#16 handoff/changelog snapshot. The #16 code is in `main`; this snapshot was overwritten by the later #19/#20/#21 reconciliations. |
| `codex/post-phase-6-claude-reconciliation` | `bfc457a` "Reconcile status after Phase 6 Claude merge" | Branch behind PR #17, which was closed without merging. Superseded by the later merged reconciliations. |
| `claude/remaining-tasks-tl4pt5` | `9be8af7`, `2e63bf5` (P6-001H Qwen) | Predecessor to PR #21. The Qwen provider decision and the egress `403` blocker are recorded in `main` via #21; only operational specifics (Alibaba Cloud DashScope / Model Studio Singapore, RAM user `runebridge-qwen`, model `qwen-turbo`, gitignored `.env` `QWEN_API_KEY`) were unique to this branch and were intentionally not carried into the sanitized `main` documentation. |

### Retained for now

| Branch | Unique commit | Why kept |
|---|---|---|
| `claude/tender-archimedes-3o31n8` | `9ee464f` "Update all status docs for P6-001F execution planning" | Holds proposed P6-001F execution parameters that exist nowhere in `main`: approval ID `P6-001F-RUN-001`, model `codex-mini-latest`, timeout `30 s`, budget `$0.06`, a direct-runner approach (`build_codex_adapter` + `run_isolated_validation`), and local-only execution. The merged history deliberately keeps P6-001F `Blocked`, so these parameters appear unratified; the branch is retained until the owner confirms whether they are the intended P6-001F configuration. If confirmed, the parameters should be lifted into `.ai/TASKS.md` and the Phase 6 plan via a clean change rather than by merging this stale branch (its base is PR #16, nine commits behind `main`, and merging would duplicate changelog entries already in `main`). |

## 2026-06-28 — Reconciliation with actual remote state

A `git fetch --prune` against `origin` showed the remote did not match the
2026-06-27 decisions above. This entry reconciles the record.

### Retained branch was deleted, but its parameters are preserved

`claude/tender-archimedes-3o31n8` no longer exists on `origin`; its unique commit
`9ee464f` is not recoverable from the remote. The P6-001F parameters it carried
survived only as text in the 2026-06-27 entry above. On 2026-06-28 the owner
ratified those parameters, and they were lifted into `.ai/TASKS.md` and
`docs/Phase-6-Live-Vendor-Validation-Plan.md` via a clean change, so the loss of
the branch carries no remaining cost. No action remains for this branch.

### Branches marked "deleted" on 2026-06-27 that still exist on `origin`

These four were documented as deleted but remain present. They are squash-merged
or intentionally superseded (their content is in `main` under new SHAs, or was
deliberately not carried into the sanitized `main`), so the 2026-06-27 decision to
drop them stands. They are pending the owner's manual deletion from the GitHub
Branches page; agent sessions in the managed remote environment do not delete
remote refs.

| Branch | Original rationale |
|---|---|
| `claude/remaining-tasks-tl4pt5` | Stale; superseded by PR #21. Unique operational specifics were intentionally not carried into sanitized `main`. |
| `codex/phase-0.6-vendor-cli` | Merged via PR #3. |
| `codex/phase-5-full-dry-run` | Merged via PR #10. |
| `codex/phase-6-live-vendor-plan` | Merged via PR #12. |

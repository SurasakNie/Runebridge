# Phase 5 Full Dry-Run Validation

## Result

**PASS locally and in protected pull-request checks.**

Three guarded official runs completed with exit code 0. Each was rehearsed in two fresh temporary roots with task ID and date held constant; every file was byte-identical between rehearsals.

| Task | Mode | Files | External commands | Credentials | Python |
|---|---|---:|---|---|---|
| `P5-SAFE-001` | `safe-default` | 10 | None | Unavailable | 3.13.12 |
| `P5-QWEN-001` | `qwen-led` | 9 | None | Unavailable | 3.13.12 |
| `P5-DUAL-001` | `dual-builder` | 11 | None | Unavailable | 3.13.12 |

Python executable basename for all three runs:

`python.exe`

The resolved executable path is intentionally omitted to avoid disclosing host-specific directory information. Reproducibility claims remain same-host only because the executable basename and Python version are host-specific metadata.

## Commands

Each official run used the guarded runner with `--date 2026-06-21`, `.bridge` as the artifact root, and its assigned mode:

```bash
python tools/bridge/run_guarded_dry_run.py \
  --task P5-SAFE-001 \
  --mode safe-default \
  --date 2026-06-21 \
  --artifact-root .bridge
```

The Qwen and dual runs substituted their corresponding task ID and mode.

## Reproducibility Hashes

### P5-SAFE-001

| File | SHA-256 |
|---|---|
| `CHANGES.diff` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `EDIT_CODEX.md` | `254938220c76411864600291b27b60a009049313df7cb88568c967abf18122c0` |
| `EXTERNAL_COMMANDS.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `FINAL_REPORT.md` | `50b0116ab6049faeeaf1884b794045b74231987a73b59d13ce8b808c27ef9742` |
| `PLAN.md` | `e0c2717a620f75331f88bd3bfc66fcb5aea586680442d525880d40f333c6a98a` |
| `REVIEW_CLAUDE.json` | `f27e13d226d05c0e6b8f4837314eb52fe86c40d6245bbea2fbc30efbf6c68949` |
| `REVIEW_QWEN.json` | `b568c10710ec32f729480f6b28aecdebd5b7274821628ef85e58cb53a5e20bb4` |
| `RUN_METADATA.json` | `3c672eb5ad077fc6e62fa7e439f2f649a976ca56b8149a21ed3fa0870212c265` |
| `TASK.md` | `0d41e3b82182ef3513a05aa834fdef13b30cca491834e328c6f254727b708f8e` |
| `VERIFY.json` | `46da53d442fd171d8666aec45ee6e419996e49647aa9cf435dfbb3e15463f0aa` |

### P5-QWEN-001

| File | SHA-256 |
|---|---|
| `CHANGES.diff` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `EDIT_QWEN.md` | `9db0e0e955203f14dd73c3bcb0feb73df53fe0d6d4c9370570579bdbc5046a85` |
| `EXTERNAL_COMMANDS.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `FINAL_REPORT.md` | `67e1db621febd9f5c8345417e7589ccbb02185d1366982d72e3c91cf840f2a68` |
| `PLAN.md` | `d9807ea56a82b22d6148f05893750f3214b97b7e8523970994942b9e6c44a171` |
| `REVIEW_CLAUDE.json` | `8f0a2df2faf8933fd5a853e1cd2bee38541ac88022aee68f5966e41442cafea1` |
| `RUN_METADATA.json` | `f5277aa3c97f864832b97b2bc938cd37a69142b86a6fdb6044f2bde8e073d388` |
| `TASK.md` | `ee0ab599ba460f795e426e50ac1f47d4f63edcc5a509ab55f419d44fbad9988d` |
| `VERIFY.json` | `a5101b03a0e0ad717eec85e2ace515a8a2f94da12f9f9b1bbbdd72a20ca2b818` |

### P5-DUAL-001

| File | SHA-256 |
|---|---|
| `CHANGES.diff` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `EDIT_CODEX.md` | `4f887ba10a69dba6e615dce3a1836fa86383302aabcb4ef16cc0f09d75f8164e` |
| `EDIT_QWEN.md` | `9de77a13f69a34c157605dbfd6d0f6f4b3aacdf26d85df56f0b61b5b74392e4e` |
| `EXTERNAL_COMMANDS.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `FINAL_REPORT.md` | `3ad8bad462d08b3ea502902360cc93e4be111fc6ff8bc4126e44672584026b99` |
| `PLAN.md` | `888e14ffe6522313660220e309c755cc48fd3f277e1c1d6350b826344b660d3a` |
| `REVIEW_CLAUDE.json` | `f55567279bcfd41bf41e6b315fc9f17dc15824ae352e4dc9b3155c66e7b005cc` |
| `REVIEW_QWEN.json` | `fcc3fee9dab7c1ca73536db8642fd7b91d5e6cdafd986989b074b90e3680b486` |
| `RUN_METADATA.json` | `47260f11b6993f33e7ddc5479de2d65ba1f034947488bce2d1fc1beb807618e5` |
| `TASK.md` | `4ff38caa79e8a8576af7d0aae33821163ac47ec68f2699d33216c0bc68867c7a` |
| `VERIFY.json` | `6061856c3594f3f70264179c9a59a6e18ca979d0a14965bb96fec93463d8af71` |

## Safety Evidence

- Each `EXTERNAL_COMMANDS.log` is zero bytes.
- `RUN_METADATA.json` records `credentials_available: false`.
- The guarded runner blocks vendor CLIs, Antigravity, Git, GitHub CLI, curl, and wget through Bash guards and PATH shims.
- The secret gate passed again after the log and metadata were written.
- Injected halt, RSK-0, retry, live-refusal, and task-reuse behavior is covered by automated tests only; no injected failure directory is committed as official evidence.

## Limitations

- `CHANGES.diff` is empty in every dry-run. Scope-gate wiring executes, but real end-to-end scope-drift enforcement is not exercised; synthetic non-empty diff tests cover the gate itself.
- Injected failures prove conductor halt and retry control flow, not genuine adapter-generated failure artifacts.
- Hash equality is established across two fresh roots on the same host. The Python executable basename and version remain host-specific, so no cross-host byte-identity claim is made.
- The pull request is created manually. Automated GitHub operations remain deferred pending explicit approval and GitHub App installation.

## Verification

- Phase 5 end-to-end tests: 8 passed before official evidence generation.
- Complete local suite: 67 passed.
- Python compilation, pre-commit, ShellCheck, gitleaks, and environment diagnostic: passed.
- [Security baseline](https://github.com/SurasakNie/Runebridge/actions/runs/27889074828/job/82529266304): passed.
- [Python baseline](https://github.com/SurasakNie/Runebridge/actions/runs/27889074831/job/82529266251): passed with the complete 67-test suite.
- [Pre-commit baseline](https://github.com/SurasakNie/Runebridge/actions/runs/27889074828/job/82529266269): passed.

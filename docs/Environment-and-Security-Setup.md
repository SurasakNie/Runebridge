# Environment and Security Setup

## Scope

This document defines the Phase 0.5B developer and CI baseline. It does not authorize live vendor calls, repository-setting changes, or merges to `main`.

## Supported Baseline

- Python 3.11 or newer
- Bash
- Git
- GitHub CLI (`gh`)
- `jq`
- `shellcheck`
- gitleaks or trufflehog

Git for Windows may provide Bash even when `bash` is not available in PowerShell's `PATH`. The environment check requires every command to be directly callable by the process that runs the conductor.

## Python Setup

Create a repository-local virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r tools/requirements.txt
```

PowerShell activation:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r tools/requirements.txt
```

## Verification

Run the repository checks:

```bash
python tools/check_environment.py
python -m compileall -q tools tests
python -m pytest -q tests/gates
pre-commit run --all-files
pre-commit run environment-check --hook-stage manual
```

The environment check fails until all required commands and at least one supported secret scanner are on `PATH`.

## Credential Handling

1. Copy variable names from `.env.example` into an ignored `.env` file or an approved secret manager.
2. Keep `DRY_RUN_MODE=true` until vendor identity and CLI validation are complete.
3. Never place real values in `.env.example`.
4. Never pass secrets as command-line arguments or write them to `.bridge/`, `.ai/`, logs, or test fixtures.
5. Prefer `GITHUB_TOKEN`, then a GitHub App token. Use a temporary PAT only when an approved workflow cannot use either option.

## Human-Controlled Repository Settings

The following actions are not performed by repository files and require explicit human approval and verification:

- [x] keep Runebridge public so the required repository ruleset capability is available
- [x] protect `main` through active ruleset `Protect main`; prohibit deletion and force pushes and require a pull request with one approval
- [x] require resolved review conversations
- [x] run and require the Phase 0.5B baseline workflow checks
- [x] enable secret scanning and push protection
- [ ] install and permission the Runebridge GitHub App before automated PR operations using the minimum contract in `.ai/SECURITY_RULES.md`
- create repository secrets for approved live integrations

Validation workflows use this default permission block:

```yaml
permissions:
  contents: read
```

They must remain read-only unless an additional permission is separately justified and approved.

### Verified Repository State (2026-06-20)

- default Actions token permission: `read`
- Actions may approve pull-request reviews: `false`
- repository secrets: none
- secret scanning: enabled
- push protection: enabled
- ruleset resolved-conversation enforcement: enabled
- allowed Actions policy: all actions
- repository SHA-pinning enforcement: disabled

Required baseline workflow checks:

- `Test / Python baseline`
- `Bridge Gates / Security baseline`
- `Bridge Gates / Pre-commit baseline`

All three checks passed on draft PR #2 and are required by `Protect main` through GitHub Actions app ID `15368`.

Record evidence for each setting before Phase 0.5B is marked complete.

GitHub App installation is deferred until immediately before automated PR operations. Repository-level Actions allowlisting and SHA-pinning enforcement are deferred until Phase 2 dependencies are finalized; all current workflows are already read-only and SHA-pinned.

## Phase 0.5B Exit Gate

- setup files exist and contain no secrets
- dependencies install in a clean virtual environment
- environment check passes
- Python compilation and smoke tests pass
- pre-commit passes, including shellcheck and secret scanning
- repository visibility and protection decisions are recorded
- required GitHub settings and permission contracts are verified
- no vendor credentials are required for dry-run validation


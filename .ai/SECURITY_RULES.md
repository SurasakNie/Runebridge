# Security Rules

All agents must follow these rules without exception.

## Never commit

- API keys, access tokens, OAuth tokens
- Passwords or passphrases
- SSH private keys or certificates (`.pem`, `.key`, `.p12`, `.pfx`)
- Customer confidential data or personal data (PII)
- `.env` files or other local credential files

## Secret injection rule

Keys must be injected through environment variables only:

- Never pass as command-line arguments
- Never write into `.bridge/` artifact files
- Never write into `.ai/` context files
- Never print in logs

## Commands requiring human approval

Stop and ask before running:

- `rm -rf` on tracked files or directories
- `git reset --hard`
- `git push --force`
- `DROP TABLE` or destructive database operations
- Deploy to production
- Encryption key rotation
- Any command outside the project directory

## Actions requiring human approval before proceeding

- Merge to `main`
- Deploy to any environment
- Delete files or directories not in task scope
- Change authentication, security, or payment code
- Create a GitHub App or modify repository permissions

## GitHub Actions permission baseline

Validation workflows must declare least privilege explicitly:

```yaml
permissions:
  contents: read
```

- Do not rely on repository-default `GITHUB_TOKEN` permissions.
- Keep validation workflows read-only; do not grant `contents: write`, `pull-requests: write`, `issues: write`, `packages: write`, or `id-token: write`.
- Set checkout credential persistence to false when a checkout action is introduced.
- Pin third-party actions to a reviewed full commit SHA.
- Do not use `pull_request_target` with untrusted pull-request code.
- Do not expose repository or environment secrets to pull requests from forks.
- Any workflow that needs additional permission requires a documented reason and human approval before merge.

Required status checks may be added to the `main` ruleset only after their workflow names and job names exist and have completed successfully on the repository.

Phase 0.5B baseline workflow checks:

- `Test / Python baseline`
- `Bridge Gates / Security baseline`
- `Bridge Gates / Pre-commit baseline`

## GitHub App minimum permission contract

The planned conductor GitHub App uses a repository-scoped installation with only:

| Permission | Access | Purpose |
|---|---|---|
| Metadata | Read | Required repository metadata |
| Contents | Read and write | Read the repository and push approved feature-branch commits |
| Pull requests | Read and write | Open and update conductor-created pull requests |
| Checks | Read | Observe validation results without modifying them |
| Actions | Read | Observe workflow runs without dispatching or modifying workflows |

The app must not receive administration, secrets, environments, deployments, organization, members, or security-setting write access. Installation, permission changes, and token issuance require human approval.

## RSK levels

| Level | Meaning | Policy |
|---|---|---|
| RSK-2 | Easy to reverse (docs, comments) | AI may proceed on branch |
| RSK-1 | Normal code with meaningful impact | AI may edit and test; PR required |
| RSK-0 | Irreversible or production-impacting | Stop; human approval required |

Exit code 2 from gate scripts signals RSK-0 — the entire pipeline halts.


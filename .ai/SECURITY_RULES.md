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

## RSK levels

| Level | Meaning | Policy |
|---|---|---|
| RSK-2 | Easy to reverse (docs, comments) | AI may proceed on branch |
| RSK-1 | Normal code with meaningful impact | AI may edit and test; PR required |
| RSK-0 | Irreversible or production-impacting | Stop; human approval required |

Exit code 2 from gate scripts signals RSK-0 — the entire pipeline halts.

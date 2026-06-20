# MCP Server Policy

## Allowed by default

| Server | Access scope | Purpose |
|---|---|---|
| Filesystem MCP | Project folder only | Read/write project files |
| GitHub MCP | This repository only | PR creation, issue tracking |
| Docs/context MCP | Read-only | Reference documentation |

## Add later (require approval)

- Browser MCP (future browser testing; not an Antigravity integration until its headless interface is approved)
- Issue tracker MCP (for task sync)
- Read-only database MCP (for schema inspection only)
- Custom engineering MCP (project-specific)

## Not allowed by default

- Full disk or home directory access
- Production database write access
- Auto-approved shell execution
- Unreviewed third-party MCP servers
- Version-unpinned MCP servers
- Any server requiring credentials not in GitHub Secrets

## GitHub access boundary

- Scope the GitHub connector or App installation to `SurasakNie/Runebridge` only.
- Use metadata read, contents read/write, pull requests read/write, checks read, and Actions read as the maximum planned conductor permission set.
- Do not grant administration or repository-security-setting write permissions to an AI tool.
- Repository visibility, rulesets, secret scanning, push protection, secrets, and App permission changes remain human-controlled RSK-0 actions.
- Use short-lived installation tokens; never store an App private key or token in repository files or pipeline artifacts.


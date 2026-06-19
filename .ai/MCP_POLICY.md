# MCP Server Policy

## Allowed by default

| Server | Access scope | Purpose |
|---|---|---|
| Filesystem MCP | Project folder only | Read/write project files |
| GitHub MCP | This repository only | PR creation, issue tracking |
| Docs/context MCP | Read-only | Reference documentation |

## Add later (require approval)

- Browser MCP (for Antigravity browser testing)
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

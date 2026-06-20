# Runebridge Public Framework and Private Project Repository Architecture

## Purpose

This document describes the approved deployment architecture: the Runebridge framework repository remains public so the required GitHub ruleset capability is available for this setup, while downstream engineering project repositories remain private.

## Repository Model

```text
GitHub
|-- Runebridge (Public framework)
|-- Project-AirPump (Private)
|-- Project-PhoneHolder (Private)
|-- Project-MedicalDevice (Private)
`-- Additional Projects (Private by default)
```

Runebridge contains the vendor-neutral orchestration framework, public documentation, prompts, schemas, gates, and non-secret tooling. Project repositories contain actual engineering work, customer data, private artifacts, and approved credentials.

The public Runebridge repository must never contain live credentials, private project artifacts, customer data, or proprietary downstream source files.

## Repository Controls

Runebridge uses active branch ruleset `Protect main`, targeting the default branch. The verified ruleset:

- blocks branch deletion
- blocks non-fast-forward updates and force pushes
- requires changes through a pull request
- requires a pull request with zero approvals under the solo-project policy; merge remains a manual owner action

Required status checks, resolved-conversation enforcement, secret scanning, and push protection are enabled. Repository-level Actions restrictions and GitHub App installation remain separate pre-automation controls.

## Local Development Layout

```text
D:\Projects\
|-- Runebridge
|-- AirPump
|-- PhoneHolder
`-- MedicalDevice
```

## Dashboard Strategy

### Recommended

Use a local HTML dashboard.

```text
Runebridge
`-- dashboard/
    `-- index.html
```

Access it locally through `localhost`.

## GitHub Plan Recommendation

Use the GitHub plan that provides the required ruleset and security controls for each repository type.

Required capabilities:

- public Runebridge framework repository
- private downstream project repositories
- pull requests and reviews
- repository rulesets
- GitHub Actions
- secret scanning and push protection where available

## Hardware Requirements

Recommended:

```text
CPU: Ryzen 7 class
RAM: 32 GB
SSD: 1 TB NVMe
```

## Appendix A - AI Vendor Independence Strategy

### Goal

Runebridge must remain operational even if:

- Claude Code is unavailable
- Codex is unavailable
- Qwen Code is unavailable
- vendor pricing changes
- a subscription expires

Infrastructure remains permanent while AI workers are replaceable.

### AI Replacement Matrix

| Role | Primary | Alternative |
|---|---|---|
| Planner | Claude Code | Qwen Code |
| Builder | Codex | Qwen Code |
| Reviewer | Claude Code | Qwen Code |
| Final Approval | Human | Human |

## Appendix B - Token Limit Strategy

### Problem

Large engineering projects eventually exceed AI context windows.

### Recommended Pattern

Store project knowledge in repository files.

```text
README.md
PROJECT_CONTEXT.md
ARCHITECTURE.md
DECISIONS.md
OPEN_TASKS.md
```

### Session Recovery

When a new AI session starts:

1. Read `README.md`.
2. Read `PROJECT_CONTEXT.md`.
3. Read `OPEN_TASKS.md`.
4. Read `TASK.md`.

The project can continue without prior chat history.

### Knowledge Preservation Rule

Important engineering decisions must be written into repository documentation.

Repository knowledge is permanent. Chat memory is temporary.


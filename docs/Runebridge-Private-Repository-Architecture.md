# Runebridge Private Repository Architecture

## Purpose

This document describes a recommended deployment architecture for Runebridge (AI Bridge) using GitHub private repositories.

## High-Level Architecture

```text
GitHub
│
├── Runebridge (Private)
├── Project-AirPump (Private)
├── Project-PhoneHolder (Private)
├── Project-MedicalDevice (Private)
└── Additional Projects
```

Runebridge acts as the AI orchestration framework.
Project repositories contain the actual engineering work.

## Local Development Layout

```text
D:\Projects\
│
├── Runebridge
├── AirPump
├── PhoneHolder
└── MedicalDevice
```

## Dashboard Strategy

### Recommended

Use a local HTML dashboard.

```text
Runebridge
└── dashboard/
    └── index.html
```

Access locally through localhost.

## GitHub Plan Recommendation

Start with GitHub Free.

Features:
- Unlimited private repositories
- Unlimited collaborators
- Pull requests
- Issues
- Basic GitHub Actions

## Hardware Requirements

Recommended:

```text
CPU: Ryzen 7 class
RAM: 32 GB
SSD: 1 TB NVMe
```

## Appendix A – AI Vendor Independence Strategy

### Goal

Runebridge must remain operational even if:

- Claude Code is unavailable
- Codex is unavailable
- Qwen Code is unavailable
- Vendor pricing changes
- A subscription expires

Infrastructure remains permanent while AI workers are replaceable.

### AI Replacement Matrix

| Role | Primary | Alternative |
|--------|----------|----------|
| Planner | Claude Code | Qwen Code |
| Builder | Codex | Qwen Code |
| Reviewer | Claude Code | Qwen Code |
| Final Approval | Human | Human |

## Appendix B – Token Limit Strategy

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

1. Read README.md
2. Read PROJECT_CONTEXT.md
3. Read OPEN_TASKS.md
4. Read TASK.md

The project can continue without prior chat history.

### Knowledge Preservation Rule

Important engineering decisions must be written into repository documentation.

Repository knowledge is permanent.
Chat memory is temporary.

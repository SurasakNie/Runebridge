"""Guards against status drift across the tracked project-status documents.

These checks codify the manual "stale-status scan" the reconciliation entries
reference. They use only the standard library so they add no test dependency.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

TASKS = ROOT / ".ai/TASKS.md"
PHASE6_PLAN = ROOT / "docs/Phase-6-Live-Vendor-Validation-Plan.md"

# Documents that must agree on the highest completed phase.
PHASE_STATUS_DOCS = (
    ROOT / "README.md",
    ROOT / ".ai/PROJECT_BRIEF.md",
    ROOT / ".ai/AGENT_HANDOFF.md",
    ROOT / "docs/AI-Bridge-Implementation-Plan-and-Concerns.md",
)

WORK_ITEM_ID = re.compile(r"\bP6-001[A-Z]\b")
PHASES_COMPLETE = re.compile(r"Phases 0\.5A through (\d+)")


def _ids(path: Path) -> set[str]:
    return set(WORK_ITEM_ID.findall(path.read_text(encoding="utf-8")))


def test_phase6_work_item_ids_match_between_tasks_and_plan() -> None:
    tasks_ids = _ids(TASKS)
    plan_ids = _ids(PHASE6_PLAN)
    assert tasks_ids, "no P6-001 work-item IDs found in TASKS.md"
    assert tasks_ids == plan_ids, (
        "Phase 6 work-item IDs drifted between TASKS.md and the Phase 6 plan: "
        f"only in TASKS={sorted(tasks_ids - plan_ids)}, "
        f"only in plan={sorted(plan_ids - tasks_ids)}"
    )


def test_status_docs_agree_on_highest_completed_phase() -> None:
    found: dict[str, set[str]] = {}
    for doc in PHASE_STATUS_DOCS:
        matches = set(PHASES_COMPLETE.findall(doc.read_text(encoding="utf-8")))
        assert matches, f"{doc.relative_to(ROOT)} has no 'Phases 0.5A through N' status claim"
        found[str(doc.relative_to(ROOT))] = matches
    distinct = set().union(*found.values())
    assert len(distinct) == 1, f"status docs disagree on the highest completed phase: {found}"

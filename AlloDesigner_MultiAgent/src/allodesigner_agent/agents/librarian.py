from __future__ import annotations

from typing import Any

from ..models import TaskSpec, TaskTrack


class LibrarianAgent:
    """Draft priors and flag leakage risks before planning/execution."""

    LEAKY_KEYWORDS = [
        "holo",
        "ligand_coords",
        "known_pocket_residues",
        "answer_key",
        "crystal_ligand",
    ]

    def inspect(self, task: TaskSpec) -> dict[str, Any]:
        risks: list[str] = []
        infos: list[str] = []
        for item in task.allowed_priors:
            low = item.lower()
            if any(k in low for k in self.LEAKY_KEYWORDS):
                if task.track == TaskTrack.RETROSPECTIVE_BLIND:
                    risks.append(
                        f"Potential answer leakage prior in blind track: {item}"
                    )

        if task.answer_store_ref and task.track == TaskTrack.RETROSPECTIVE_BLIND:
            infos.append(
                "answer_store_ref is set for evaluation-only recovery metrics; "
                "runtime context must never load it"
            )

        pending = [a.item for a in task.human_approvals if a.status != "approved"]
        return {
            "agent": "librarian",
            "leakage_risks": risks,
            "infos": infos,
            "pending_approvals": pending,
            "recommended_next": (
                "Request human approval on boundary sheet"
                if pending or risks
                else "Boundary ready for planner"
            ),
        }

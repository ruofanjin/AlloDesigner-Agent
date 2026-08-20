from __future__ import annotations

from typing import Any

from ..models import PlanStep, TaskSpec
from .base import BaseStageAgent


class RankingAgent(BaseStageAgent):
    """Stage6 dry-run planner; real docking goes through job pack + return ingest."""

    stage_id = "candidate_ranking"

    def run_iteration(
        self,
        task: TaskSpec,
        step: PlanStep,
        round_idx: int,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        result = {
            "mode": "paper_only_or_external",
            "protocol": list(step.tools) or ["glp1r_virtual_screening_protocol"],
            "alternatives": list(step.alternatives) or ["vina", "karmadock", "glide"],
            "planned_artifacts": [
                "ranked_candidates.csv",
                "protocol_version.json",
                "job_sheet.json",
            ],
            "note": "Emit external job pack; do not claim experimental potency.",
        }
        context["candidate_ranking"] = result
        return {
            "outputs": result,
            "metrics": {},
            "stop": True,
            "stop_reason": "ranking_packet_planned",
            "status_hint": "needs_external",
        }

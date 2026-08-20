from __future__ import annotations

from typing import Any

from ..models import PlanStep, TaskSpec
from .base import BaseStageAgent


class BoundaryAgent(BaseStageAgent):
    stage_id = "boundary"

    def run_iteration(
        self,
        task: TaskSpec,
        step: PlanStep,
        round_idx: int,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        pending = [a.item for a in task.human_approvals if a.status != "approved"]
        sheet = {
            "target": task.target.model_dump(),
            "track": task.track.value,
            "allowed_priors": task.allowed_priors,
            "forbidden_information": task.forbidden_information,
            "answer_store_ref": task.answer_store_ref,
            "pending_approvals": pending,
        }
        context["boundary_sheet"] = sheet
        return {
            "outputs": {"boundary_sheet": sheet},
            "metrics": {"pending_approvals": len(pending)},
            "stop": True,
            "stop_reason": "boundary_sheet_drafted",
        }

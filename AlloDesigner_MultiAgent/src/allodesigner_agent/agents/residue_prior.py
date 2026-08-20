from __future__ import annotations

from typing import Any

from ..models import PlanStep, TaskSpec
from .base import BaseStageAgent


class ResiduePriorAgent(BaseStageAgent):
    stage_id = "residue_prior"

    def run_iteration(
        self,
        task: TaskSpec,
        step: PlanStep,
        round_idx: int,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        threshold = (
            step.params.get("threshold_examples", {}).get(task.target.name)
            or step.params.get("threshold")
            or 0.7
        )
        result = {
            "mode": "dry_run",
            "entrypoint": "../Allo-PocketMiner/case_predict.py",
            "aggregation": step.params.get("ensemble_aggregation", "mean"),
            "threshold": threshold,
            "planned_artifacts": [
                "residue_probabilities.csv",
                "thresholded_residues.json",
            ],
        }
        context["residue_prior"] = result
        return {
            "outputs": result,
            "metrics": {
                "threshold": threshold,
                "reference_pr_auc": 0.701,
                "baseline_pr_auc": 0.582,
            },
            "stop": True,
            "stop_reason": "prior_plan_ready",
        }

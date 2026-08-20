from __future__ import annotations

from typing import Any

from ..models import PlanStep, TaskSpec
from .base import BaseStageAgent


class PocketEvalAgent(BaseStageAgent):
    stage_id = "pocket_evaluation"

    def run_iteration(
        self,
        task: TaskSpec,
        step: PlanStep,
        round_idx: int,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        eps = step.params.get("dbscan_eps_examples", {}).get(task.target.name, 6.0)
        result = {
            "mode": "dry_run",
            "clustering": {
                "algorithm": "dbscan",
                "eps": eps,
                "min_samples": step.params.get("dbscan_min_samples", 2),
            },
            "scorers": ["deepallo", "plb", "fpocket_distance"],
            "consensus_topk_clusters": step.params.get("consensus_topk_clusters", 7),
            "planned_artifacts": [
                "pocket_cluster_ranking.csv",
                "consensus_residues.json",
            ],
        }
        context["pocket_evaluation"] = result
        return {
            "outputs": result,
            "metrics": {"eps": eps, "topk": result["consensus_topk_clusters"]},
            "stop": True,
            "stop_reason": "evaluation_plan_ready",
        }

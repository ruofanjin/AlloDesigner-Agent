from __future__ import annotations

from typing import Any

from ..models import PlanStep, TaskSpec
from .base import BaseStageAgent


class EnsembleAgent(BaseStageAgent):
    stage_id = "ensemble_enrichment"

    def run_iteration(
        self,
        task: TaskSpec,
        step: PlanStep,
        round_idx: int,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        max_rounds = int(step.params.get("iterative_enrichment_rounds", 6))
        # Simulated enrichment curve approaching <= 5A
        start = 5.5
        distance = max(4.45, start - 0.15 * round_idx)
        metrics = {
            "round": round_idx,
            "top10_percent_mean_distance": round(distance, 3),
            "preference_metric": step.params.get(
                "preference_metric", "cluster_center_to_fpocket_distance"
            ),
        }
        outputs = {
            "mode": "dry_run_multi_round",
            "tools": step.tools,
            "planned_scripts": [
                "../AlphaFlow/1-mmseqs_search_helper.py",
                "../Allo_af_claseq/11_sequence_voting.py",
                "../Allo_af_claseq/12_recompile.py",
            ],
            "retain_top_fraction": step.params.get("retain_top_fraction", 0.2),
        }
        stop = distance <= 5.0 or round_idx >= max_rounds
        if stop:
            context["preferred_ensemble"] = {
                "rounds": round_idx,
                "distance": distance,
            }
        return {
            "outputs": outputs,
            "metrics": metrics,
            "stop": stop,
            "stop_reason": "distance_saturated" if distance <= 5.0 else "max_rounds",
        }

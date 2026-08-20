from __future__ import annotations

from typing import Any

from ..models import PlanStep, TaskSpec
from .base import BaseStageAgent


class PhysicsAgent(BaseStageAgent):
    stage_id = "physics_sampling"

    def run_iteration(
        self,
        task: TaskSpec,
        step: PlanStep,
        round_idx: int,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        job = {
            "mode": "allo_md_job_pack",
            "backend": "Allo-MD",
            "sampler": "ai_prior_metadynamics",
            "allo_md_profile": step.params.get(
                "allo_md_profile", "distance-simulation-only"
            ),
            "cv_candidates": step.params.get(
                "cv_candidates", ["pocket_sasa", "key_residue_pair_distance"]
            ),
            "budget_ns": step.params.get("suggested_budget_ns", 50),
            "benchmarks": step.benchmarks,
            "requires_callback": True,
        }
        context["physics_job"] = job
        return {
            "outputs": job,
            "metrics": {"planned_budget_ns": job["budget_ns"]},
            "stop": True,
            "stop_reason": "job_sheet_emitted",
        }

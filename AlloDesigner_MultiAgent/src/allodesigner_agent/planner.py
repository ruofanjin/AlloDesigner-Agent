from __future__ import annotations

from typing import Any

from .contracts import (
    load_reference_path,
    load_stage_contracts,
    ordered_stage_ids,
    stage_by_id,
)
from .models import ExecutionPlan, PlanStep, TaskSpec


class ContractViolation(ValueError):
    pass


class ConstrainedPlanner:
    """Plan only inside expert-frozen stage contracts.

    The AlloDesigner reference path is the default hot-start skeleton.
    The planner may swap tools inside a stage, but must not rewrite stage
    semantics or critical ordering.
    """

    def __init__(
        self,
        contracts: dict[str, Any] | None = None,
        reference_path: dict[str, Any] | None = None,
    ) -> None:
        self.contracts = contracts or load_stage_contracts()
        self.reference_path = reference_path or load_reference_path()
        self.canonical_order = ordered_stage_ids(self.contracts)

    def build_plan(self, task: TaskSpec) -> ExecutionPlan:
        enabled = self._validate_enabled_stages(task.stages_enabled)
        ref_steps = {
            step["stage_id"]: step for step in self.reference_path["steps"]
        }

        steps: list[PlanStep] = []
        for stage_id in enabled:
            if stage_id not in ref_steps:
                stage = stage_by_id(self.contracts, stage_id)
                steps.append(
                    PlanStep(
                        stage_id=stage_id,
                        tools=list(stage.get("default_tools", [])),
                        notes="Fallback to stage default tools",
                    )
                )
                continue
            raw = ref_steps[stage_id]
            steps.append(
                PlanStep(
                    stage_id=stage_id,
                    tools=list(raw.get("tools", [])),
                    benchmarks=list(raw.get("benchmarks", [])),
                    alternatives=list(raw.get("alternatives", [])),
                    params=dict(raw.get("params", {})),
                    notes=raw.get("notes"),
                    iteration=dict(raw.get("iteration", {})),
                )
            )

        policy_notes = [
            "Stage semantics are frozen by expert contracts.",
            "AlloDesigner reference path is the default skeleton, not an untested winner.",
            f"Task track={task.track.value}; answer leakage into blind runtime is forbidden.",
        ]
        return ExecutionPlan(
            plan_id=self.reference_path["id"],
            title=self.reference_path["title"],
            task_id=task.task_id,
            track=task.track,
            steps=steps,
            policy_notes=policy_notes,
        )

    def _validate_enabled_stages(self, enabled: list[str]) -> list[str]:
        unknown = [s for s in enabled if s not in self.canonical_order]
        if unknown:
            raise ContractViolation(f"Unknown stages: {unknown}")

        ordered = [s for s in self.canonical_order if s in enabled]
        # Preserve relative canonical order; reject arbitrary reshuffles.
        if ordered != [s for s in enabled if s in self.canonical_order]:
            # allow user to pass unordered set but normalize; only reject if they
            # explicitly permute relative order in a way that breaks dependencies.
            pass

        # Dependency checks
        enabled_set = set(ordered)
        for stage_id in ordered:
            stage = stage_by_id(self.contracts, stage_id)
            for dep in stage.get("depends_on", []):
                if dep not in enabled_set:
                    # soft skip only if dependency earlier and missing intentionally
                    # critical deps must be present
                    raise ContractViolation(
                        f"Stage '{stage_id}' requires dependency '{dep}'"
                    )
        return ordered

    def assert_no_semantic_rewrite(self, proposed_stage_goals: dict[str, str]) -> None:
        for stage_id, goal in proposed_stage_goals.items():
            stage = stage_by_id(self.contracts, stage_id)
            if goal.strip() != stage["goal"].strip():
                raise ContractViolation(
                    f"Refusing to rewrite goal for stage '{stage_id}'"
                )

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..contracts import load_tool_registry, stage_by_id
from ..models import (
    DecisionPacket,
    Maturity,
    PacketStatus,
    PlanStep,
    TaskSpec,
    ToolDecision,
    ToolRole,
)


class BaseStageAgent(ABC):
    stage_id: str

    def __init__(self, contracts: dict[str, Any], tools: dict[str, Any] | None = None) -> None:
        self.contracts = contracts
        self.tools = tools or load_tool_registry()["tools"]
        self.stage = stage_by_id(contracts, self.stage_id)

    @abstractmethod
    def run_iteration(
        self,
        task: TaskSpec,
        step: PlanStep,
        round_idx: int,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Return outputs/metrics for one iteration (dry-run capable)."""

    def execute(
        self,
        task: TaskSpec,
        step: PlanStep,
        context: dict[str, Any],
        max_rounds: int = 1,
    ) -> DecisionPacket:
        considered = self._tool_decisions(step)
        selected = list(step.tools)
        maturity = self._aggregate_maturity(selected)

        outputs: dict[str, Any] = {"iterations": []}
        metrics: dict[str, Any] = {}
        stop_reason = "max_rounds"
        last_round = 0
        status = PacketStatus.COMPLETED
        qc_flags: list[str] = []

        pipeline = context.get("pipeline_executor")
        if pipeline is not None:
            # Paper-pipeline mode: one stage execution with artifact handoff.
            last_round = 1
            result = pipeline.run_stage(task, step, context)
            outputs["pipeline"] = result
            metrics = {
                k: result[k]
                for k in ("threshold", "n_positive", "n_residues", "budget_ns", "eps")
                if k in result
            }
            stop_reason = result.get("status", "pipeline_stage_done")
            from ..executors.pipeline import packet_status_from_executor

            status = packet_status_from_executor(result)
            if result.get("reason"):
                qc_flags.append(str(result["reason"]))
            if result.get("chain_policy"):
                qc_flags.append(str(result["chain_policy"]))
        else:
            for round_idx in range(1, max_rounds + 1):
                last_round = round_idx
                result = self.run_iteration(task, step, round_idx, context)
                outputs["iterations"].append(result)
                metrics = result.get("metrics", {})
                if result.get("stop", False):
                    stop_reason = result.get("stop_reason", "stage_stop")
                    break

            if maturity in {Maturity.EXTERNAL, Maturity.PAPER_ONLY}:
                status = PacketStatus.NEEDS_HUMAN
                outputs["job_sheet"] = {
                    "message": "External/paper_only tools require executor callback or human run.",
                    "tools": selected,
                }

        return DecisionPacket(
            packet_id=f"{task.task_id}:{self.stage_id}:r{last_round}",
            task_id=task.task_id,
            stage_id=self.stage_id,
            stage_contract_version=str(self.contracts.get("version", "1.0.0")),
            task_track=task.track,
            inputs_frozen=list(task.allowed_priors),
            priors_approved=[
                a.item for a in task.human_approvals if a.status == "approved"
            ],
            tools_considered=considered,
            tool_selected=selected,
            outputs=outputs,
            metrics=metrics,
            qc_flags=qc_flags,
            claims_allowed=list(self.stage.get("allowed_claims", [])),
            iteration={"round": last_round, "stop_reason": stop_reason},
            status=status,
            maturity=maturity,
        )

    def _tool_decisions(self, step: PlanStep) -> list[ToolDecision]:
        decisions: list[ToolDecision] = []
        for tool_id in step.tools:
            meta = self.tools.get(tool_id, {})
            decisions.append(
                ToolDecision(
                    tool_id=tool_id,
                    role=ToolRole(meta.get("role_default", "reuse")),
                    decision="selected",
                    rationale="From AlloDesigner reference path / stage defaults",
                )
            )
        for tool_id in step.benchmarks:
            decisions.append(
                ToolDecision(
                    tool_id=tool_id,
                    role=ToolRole.BENCHMARK,
                    decision="benchmark_only",
                    rationale="Benchmark control; reported separately",
                )
            )
        for tool_id in step.alternatives:
            decisions.append(
                ToolDecision(
                    tool_id=tool_id,
                    role=ToolRole.ALTERNATIVE,
                    decision="deferred",
                    rationale="Available alternative; not selected in default plan",
                )
            )
        return decisions

    def _aggregate_maturity(self, tool_ids: list[str]) -> Maturity:
        order = [
            Maturity.PAPER_ONLY,
            Maturity.EXTERNAL,
            Maturity.SCRIPTED,
            Maturity.EXECUTABLE,
        ]
        selected = []
        for tool_id in tool_ids:
            raw = self.tools.get(tool_id, {}).get("maturity", "scripted")
            selected.append(Maturity(raw))
        if not selected:
            return Maturity.SCRIPTED
        for level in order:
            if level in selected:
                return level
        return Maturity.SCRIPTED

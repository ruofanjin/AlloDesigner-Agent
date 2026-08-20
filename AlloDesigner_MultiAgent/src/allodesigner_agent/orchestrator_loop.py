"""LLM/heuristic orchestrator loop: plan → critic → execute → observe → replan|continue|stop."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .contracts import ROOT, load_stage_contracts
from .models import (
    DecisionPacket,
    Maturity,
    PacketStatus,
    ReasoningPlan,
    TaskSpec,
    ToolDecision,
    ToolResult,
    ToolRole,
)
from .reasoning.critic_gate import ReasoningCritic
from .reasoning.planner import AutonomousReasoningPlanner
from .tools.router import ToolRouter


class ReasoningOrchestrator:
    def __init__(
        self,
        run_dir: Path | None = None,
        router: ToolRouter | None = None,
    ) -> None:
        self.contracts = load_stage_contracts()
        self.router = router or ToolRouter()
        self.planner = AutonomousReasoningPlanner(router=self.router)
        self.critic = ReasoningCritic()
        self.run_dir = run_dir

    def run(
        self,
        task: TaskSpec,
        *,
        force_missing_stage4: bool = False,
        max_replans: int = 2,
    ) -> dict[str, Any]:
        run_dir = self.run_dir or (
            ROOT
            / "runs"
            / f"reason_{task.task_id}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        )
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "packets").mkdir(exist_ok=True)

        history: list[dict[str, Any]] = []
        plan: ReasoningPlan | None = None
        packets: list[DecisionPacket] = []
        node_results: dict[str, ToolResult] = {}

        for replan_i in range(max_replans + 1):
            plan = self.planner.build(task, force_missing_stage4=force_missing_stage4)
            (run_dir / f"reasoning_plan_r{replan_i}.json").write_text(
                plan.model_dump_json(indent=2) + "\n", encoding="utf-8"
            )
            gate = self.critic.review_plan(task, plan, self.contracts)
            (run_dir / f"critic_plan_r{replan_i}.json").write_text(
                json.dumps(gate, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            history.append({"replan": replan_i, "critic_plan": gate})
            if not gate["passed"]:
                # Cannot auto-fix contract violations; stop.
                report = self._finalize(
                    task, run_dir, plan, packets, node_results, history, status="blocked_by_critic"
                )
                return report

            # Execute DAG in dependency order
            pending = {n.node_id: n for n in plan.execution_dag}
            completed: set[str] = set()
            failed = False
            replan_needed = False

            while pending:
                ready = [
                    n
                    for n in pending.values()
                    if all(d in completed for d in n.depends_on)
                ]
                if not ready:
                    failed = True
                    history.append({"error": "DAG deadlock", "pending": list(pending)})
                    break
                for node in ready:
                    result = self.router.invoke(node.tool_id, node.action, node.args)
                    node_results[node.node_id] = result
                    node.status = "completed" if result.ok else "failed"
                    node.result_ref = json.dumps(result.outputs)[:200]
                    history.append(
                        {
                            "node_id": node.node_id,
                            "tool_id": node.tool_id,
                            "ok": result.ok,
                            "maturity_route": result.maturity_route,
                            "error": result.error,
                            "product_maturity": result.product_maturity,
                        }
                    )
                    del pending[node.node_id]

                    if result.ok:
                        completed.add(node.node_id)
                        packet = self._packet_from_node(task, node.stage_id, result, plan)
                        crev = self.critic.review_packet(
                            task,
                            packet,
                            self.contracts,
                            product_maturity=result.product_maturity,
                            claimed_completion=result.ok,
                        )
                        packet.critic = crev
                        if not crev["passed"]:
                            packet.status = PacketStatus.BLOCKED
                            packet.qc_flags.extend(crev["findings"])
                        else:
                            packet.status = PacketStatus.COMPLETED
                        packets.append(packet)
                        self.router.invoke(
                            "packet.write",
                            "write",
                            {
                                "out_dir": str(run_dir / "packets"),
                                "filename": f"{packet.packet_id}.json",
                                "packet": json.loads(packet.model_dump_json()),
                            },
                        )
                    else:
                        if node.on_failure == "replan":
                            replan_needed = True
                            force_missing_stage4 = True
                            break
                        if node.on_failure == "stop":
                            failed = True
                            break
                        if node.on_failure == "escalate":
                            failed = True
                            break
                        # continue_with_uncertainty
                        completed.add(node.node_id)
                        packet = self._packet_from_node(task, node.stage_id, result, plan)
                        packet.status = PacketStatus.NEEDS_HUMAN
                        packet.qc_flags.append(result.error or "uncertainty")
                        packets.append(packet)
                if failed or replan_needed:
                    break

            if replan_needed and replan_i < max_replans:
                continue
            status = "completed" if not failed else "failed"
            return self._finalize(task, run_dir, plan, packets, node_results, history, status=status)

        return self._finalize(
            task, run_dir, plan, packets, node_results, history, status="failed_max_replans"
        )

    def _packet_from_node(
        self,
        task: TaskSpec,
        stage_id: str,
        result: ToolResult,
        plan: ReasoningPlan,
    ) -> DecisionPacket:
        stage_reason = next((s for s in plan.stages if s.stage_id == stage_id), None)
        tools_considered = []
        selected = []
        if stage_reason:
            for t in stage_reason.tools:
                tools_considered.append(
                    ToolDecision(
                        tool_id=t.tool_id,
                        role=t.role,
                        decision=t.decision,
                        rationale=t.rationale,
                    )
                )
                if t.decision == "selected":
                    selected.append(t.tool_id)
        if result.tool_id not in selected:
            selected.append(result.tool_id)
            tools_considered.append(
                ToolDecision(
                    tool_id=result.tool_id,
                    role=ToolRole.ADAPT,
                    decision="selected",
                    rationale="Executed via ToolRouter",
                )
            )
        maturity = Maturity.SCRIPTED
        if result.product_maturity == "partial/seeded":
            maturity = Maturity.EXTERNAL
        elif result.maturity_route == "paper_only_placeholder":
            maturity = Maturity.PAPER_ONLY
        elif result.maturity_route in {"local_invoke", "reuse_artifact", "historical_replay"}:
            maturity = Maturity.SCRIPTED

        return DecisionPacket(
            packet_id=f"{task.task_id}:{stage_id}:{result.tool_id}",
            task_id=task.task_id,
            stage_id=stage_id,
            task_track=task.track,
            tools_considered=tools_considered,
            tool_selected=selected,
            outputs=result.outputs,
            metrics=result.metrics,
            claims_allowed=list(result.claims_allowed),
            status=PacketStatus.RUNNING,
            maturity=maturity,
            iteration={"stop_reason": "node_executed"},
        )

    def _finalize(
        self,
        task: TaskSpec,
        run_dir: Path,
        plan: ReasoningPlan | None,
        packets: list[DecisionPacket],
        node_results: dict[str, ToolResult],
        history: list[dict[str, Any]],
        *,
        status: str,
    ) -> dict[str, Any]:
        # Narrative reasoning chain for humans
        narrative = []
        if plan:
            narrative.append(plan.scientific_hypothesis)
            for s in plan.stages:
                narrative.append(f"[{s.stage_id}] {s.why_this_path}")
                if s.uncertainty:
                    narrative.append(f"  uncertainty: {s.uncertainty}")

        report = {
            "task_id": task.task_id,
            "status": status,
            "run_dir": str(run_dir),
            "planner_mode": plan.planner_mode if plan else None,
            "reasoning_narrative": narrative,
            "reasoning_plan": json.loads(plan.model_dump_json()) if plan else None,
            "packets": [json.loads(p.model_dump_json()) for p in packets],
            "node_results": {
                k: json.loads(v.model_dump_json()) for k, v in node_results.items()
            },
            "history": history,
            "claim_boundary": plan.claim_policy if plan else {},
            "product_note": (
                "合同内自主推理 demo：推理链由 AutonomousReasoningPlanner 生成；"
                "非论文级端到端科学重算。"
            ),
        }
        (run_dir / "report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (run_dir / "reasoning_narrative.md").write_text(
            "# Reasoning narrative\n\n"
            + "\n".join(f"- {line}" for line in narrative)
            + "\n",
            encoding="utf-8",
        )
        return report

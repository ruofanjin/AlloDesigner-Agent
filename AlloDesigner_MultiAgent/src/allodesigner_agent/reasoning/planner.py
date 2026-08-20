"""Autonomous ReasoningPlan builder inside frozen stage contracts.

Forms the reasoning chain from TaskSpec + artifact availability + budgets.
Does not rewrite stage goals or hard dependency order.
"""
from __future__ import annotations

from typing import Any

from ..contracts import (
    load_reference_path,
    load_stage_contracts,
    load_tool_registry,
    ordered_stage_ids,
    stage_by_id,
)
from ..models import (
    ExecutionNode,
    MaturityRoute,
    ReasoningPlan,
    StageReasoning,
    TaskSpec,
    ToolConsideration,
    ToolRole,
)
from ..tools.router import ToolRouter


class AutonomousReasoningPlanner:
    """Heuristic-autonomous planner: reasoning chain adapts to artifacts/budget."""

    def __init__(
        self,
        contracts: dict[str, Any] | None = None,
        registry: dict[str, Any] | None = None,
        router: ToolRouter | None = None,
    ) -> None:
        self.contracts = contracts or load_stage_contracts()
        self.registry = registry or load_tool_registry()
        self.reference = load_reference_path()
        self.router = router or ToolRouter(self.registry)
        self.canonical = ordered_stage_ids(self.contracts)

    def build(self, task: TaskSpec, *, force_missing_stage4: bool = False) -> ReasoningPlan:
        arts = self.router.invoke("artifacts.resolve").outputs.get("available", {})
        enabled = [s for s in self.canonical if s in task.stages_enabled]

        stages: list[StageReasoning] = []
        dag: list[ExecutionNode] = []
        uncertainty: list[str] = []
        prev_node: str | None = None

        budget = task.budget or {}
        max_md_ns = float(budget.get("max_md_ns", 1.0))
        allow_external_vs = bool(budget.get("allow_external_vs", True))
        prefer_recompute = bool(budget.get("prefer_recompute", False))

        for stage_id in enabled:
            stage = stage_by_id(self.contracts, stage_id)
            sr, nodes, notes = self._reason_stage(
                task,
                stage,
                arts,
                max_md_ns=max_md_ns,
                allow_external_vs=allow_external_vs,
                prefer_recompute=prefer_recompute,
                force_missing_stage4=force_missing_stage4,
            )
            stages.append(sr)
            uncertainty.extend(notes)
            for node in nodes:
                if prev_node and not node.depends_on:
                    node.depends_on = [prev_node]
                dag.append(node)
                prev_node = node.node_id

        hypothesis = (
            f"For target {task.target.name} on track {task.track.value}, "
            "pursue cryptic allosteric pocket discovery via the frozen six-stage "
            "decomposition; tool choices and replay/reuse adapt to available artifacts "
            f"and budget (max_md_ns={max_md_ns}, prefer_recompute={prefer_recompute})."
        )

        return ReasoningPlan(
            plan_id=f"reason_{task.task_id}",
            task_id=task.task_id,
            track=task.track,
            scientific_hypothesis=hypothesis,
            information_boundary={
                "allowed_priors": list(task.allowed_priors),
                "forbidden_information": list(task.forbidden_information),
                "leakage_scan": [
                    "answer_store_ref must not enter blind runtime tools",
                    "HOLO/ligand labels forbidden as planning features on retrospective_blind",
                ],
            },
            stages=stages,
            execution_dag=dag,
            global_stop_policy={
                "on_hard_failure": "escalate",
                "on_soft_failure": "continue_with_uncertainty",
                "max_stage_iterations": int(budget.get("max_stage_iterations", 1)),
            },
            claim_policy={
                "allowed": [
                    "Agent 在合同内自主生成了推理链与工具图",
                    "计算候选物已排序，待实验/专家复核",
                ],
                "forbidden": [
                    "Agent 发明了新的科学主路径并已证实",
                    "端到端论文级发现已完成",
                    "有效配体/抑制剂已被证实",
                    "真实口袋已确认",
                ],
            },
            uncertainty_notes=uncertainty,
            planner_mode="heuristic_autonomous",
        )

    def _reason_stage(
        self,
        task: TaskSpec,
        stage: dict[str, Any],
        arts: dict[str, str],
        *,
        max_md_ns: float,
        allow_external_vs: bool,
        prefer_recompute: bool,
        force_missing_stage4: bool,
    ) -> tuple[StageReasoning, list[ExecutionNode], list[str]]:
        sid = stage["id"]
        notes: list[str] = []
        nodes: list[ExecutionNode] = []

        if sid == "boundary":
            tools = [
                ToolConsideration(
                    tool_id="case_protocol_template",
                    role=ToolRole.REUSE,
                    decision="selected",
                    rationale="Freeze information boundary from case protocol template.",
                )
            ]
            route = MaturityRoute.LOCAL_INVOKE
            why = "Human-approved boundary must precede any scientific tool use."
            nodes.append(
                ExecutionNode(
                    node_id=f"{sid}.packet",
                    stage_id=sid,
                    tool_id="packet.write",
                    action="write",
                    args={"stage_id": sid, "mode": "boundary_freeze"},
                    on_failure="escalate",
                )
            )

        elif sid == "residue_prior":
            if prefer_recompute and not arts.get("retrospective_run"):
                why = "Prefer recompute but no executable path guaranteed; fall back to replay."
                notes.append("Stage2 recompute requested but demo slice uses retrospective replay.")
            else:
                why = (
                    "Retrospective artifacts exist; replay residue prior to keep blind demo "
                    "auditable without re-running PocketMiner."
                )
            tools = [
                ToolConsideration(
                    tool_id="allo_pocketminer",
                    role=ToolRole.REUSE,
                    decision="deferred",
                    rationale="Executable in principle; deferred for demo budget.",
                ),
                ToolConsideration(
                    tool_id="stage2.replay_residue_prior",
                    role=ToolRole.ADAPT,
                    decision="selected",
                    rationale="historical_replay of retrospective residue_prior artifacts.",
                ),
            ]
            route = MaturityRoute.HISTORICAL_REPLAY
            nodes.append(
                ExecutionNode(
                    node_id=f"{sid}.replay",
                    stage_id=sid,
                    tool_id="stage2.replay_residue_prior",
                    action="replay",
                    on_failure="escalate",
                )
            )

        elif sid == "ensemble_enrichment":
            why = "Reuse retrospective ensemble_enrichment; full AF-ClaSeq recompute out of demo budget."
            tools = [
                ToolConsideration(
                    tool_id="allo_stepwise",
                    role=ToolRole.REUSE,
                    decision="deferred",
                    rationale="Scripted/historical path preferred for this slice.",
                ),
                ToolConsideration(
                    tool_id="stage3.replay_ensemble",
                    role=ToolRole.ADAPT,
                    decision="selected",
                    rationale="Replay ensemble artifacts from retrospective run.",
                ),
            ]
            route = MaturityRoute.HISTORICAL_REPLAY
            notes.append("Stage3 not recomputed; uncertainty carried to pocket evaluation.")
            nodes.append(
                ExecutionNode(
                    node_id=f"{sid}.replay",
                    stage_id=sid,
                    tool_id="stage3.replay_ensemble",
                    action="replay",
                    on_failure="continue_with_uncertainty",
                )
            )

        elif sid == "physics_sampling":
            has4 = bool(arts.get("stage4_md_run")) and not force_missing_stage4
            if has4 and max_md_ns <= 1.0:
                why = (
                    "1 ns Allo-MD demo artifact present and budget<=1ns; "
                    "reuse rather than relaunch MD (not paper 200ns)."
                )
                route = MaturityRoute.REUSE_ARTIFACT
                tools = [
                    ToolConsideration(
                        tool_id="ai_prior_metadynamics",
                        role=ToolRole.REUSE,
                        decision="selected",
                        rationale="Reuse glp1r_distance_1ns_demo_001 outputs.",
                    )
                ]
                nodes.append(
                    ExecutionNode(
                        node_id=f"{sid}.reuse",
                        stage_id=sid,
                        tool_id="stage4.reuse_or_status",
                        action="reuse",
                        args={"force_missing_stage4": False},
                        on_failure="replan",
                    )
                )
            elif force_missing_stage4 or not has4:
                why = (
                    "Stage4 artifact unavailable under current assumptions; "
                    "emit Allo-MD job_pack path instead of fabricating success."
                )
                route = MaturityRoute.JOB_PACK
                tools = [
                    ToolConsideration(
                        tool_id="ai_prior_metadynamics",
                        role=ToolRole.REUSE,
                        decision="deferred",
                        rationale="Would require external/local Allo-MD job execution.",
                    )
                ]
                notes.append("physics_sampling requires job_pack; soft dependency for Stage5 noted.")
                nodes.append(
                    ExecutionNode(
                        node_id=f"{sid}.status",
                        stage_id=sid,
                        tool_id="stage4.reuse_or_status",
                        action="status",
                        args={"force_missing_stage4": True},
                        on_failure="continue_with_uncertainty",
                    )
                )
            else:
                why = "Budget requests longer MD than demo; keep demo reuse with explicit uncertainty."
                route = MaturityRoute.REUSE_ARTIFACT
                notes.append(f"Requested max_md_ns={max_md_ns} exceeds demo; still reusing 1ns with uncertainty.")
                tools = [
                    ToolConsideration(
                        tool_id="ai_prior_metadynamics",
                        role=ToolRole.REUSE,
                        decision="selected",
                        rationale="Reuse 1ns demo under longer-budget request with uncertainty flag.",
                    )
                ]
                nodes.append(
                    ExecutionNode(
                        node_id=f"{sid}.reuse",
                        stage_id=sid,
                        tool_id="stage4.reuse_or_status",
                        action="reuse",
                        on_failure="replan",
                    )
                )

        elif sid == "pocket_evaluation":
            has5 = bool(arts.get("stage5_run"))
            has4 = bool(arts.get("stage4_md_run")) and not force_missing_stage4
            why = (
                "Combine historical_replay pocket_01 handoff with Stage4-frame fpocket "
                "consistency check when frames exist."
            )
            tools = [
                ToolConsideration(
                    tool_id="stage5.historical_replay",
                    role=ToolRole.REUSE,
                    decision="selected",
                    rationale="Frozen expert handoff is the Stage5 gate for GLP1 retrospective.",
                ),
                ToolConsideration(
                    tool_id="stage5.fpocket_from_frames_status",
                    role=ToolRole.SUPPLEMENT,
                    decision="selected" if has4 else "deferred",
                    rationale="Geometric overlap vs pocket_01 from Stage4 frames."
                    if has4
                    else "No Stage4 frames; skip fpocket track.",
                ),
                ToolConsideration(
                    tool_id="fpocket",
                    role=ToolRole.REUSE,
                    decision="benchmark_only",
                    rationale="Already executed in Stage5 demo; status reuse only.",
                ),
            ]
            route = MaturityRoute.HISTORICAL_REPLAY
            nodes.append(
                ExecutionNode(
                    node_id=f"{sid}.historical",
                    stage_id=sid,
                    tool_id="stage5.historical_replay",
                    action="replay",
                    on_failure="escalate",
                )
            )
            if has4:
                nodes.append(
                    ExecutionNode(
                        node_id=f"{sid}.fpocket",
                        stage_id=sid,
                        tool_id="stage5.fpocket_from_frames_status",
                        action="status",
                        depends_on=[f"{sid}.historical"],
                        on_failure="continue_with_uncertainty",
                    )
                )
            elif not has5:
                notes.append("Stage5 artifacts incomplete.")

        elif sid == "candidate_ranking":
            if not allow_external_vs:
                why = "Budget disallows external VS; emit plan-only placeholder and stop before fake scores."
                route = MaturityRoute.PAPER_ONLY_PLACEHOLDER
                tools = [
                    ToolConsideration(
                        tool_id="glp1r_virtual_screening_protocol",
                        role=ToolRole.REUSE,
                        decision="deferred",
                        rationale="paper_only cascade not executed.",
                    )
                ]
                notes.append("candidate_ranking skipped for docking execution; job pack not emitted.")
                nodes.append(
                    ExecutionNode(
                        node_id=f"{sid}.blocked",
                        stage_id=sid,
                        tool_id="stage6.emit_job_pack",
                        action="emit",
                        args={"dry_block": True},
                        on_failure="stop",
                    )
                )
            else:
                why = (
                    "Stage6 is external: emit Vina/Glide job pack and ingest returns; "
                    "seeded returns remain partial/seeded."
                )
                route = MaturityRoute.JOB_PACK
                tools = [
                    ToolConsideration(
                        tool_id="vina",
                        role=ToolRole.ALTERNATIVE,
                        decision="selected",
                        rationale="Accepted external return engine.",
                    ),
                    ToolConsideration(
                        tool_id="glide",
                        role=ToolRole.ALTERNATIVE,
                        decision="selected",
                        rationale="Accepted external return engine.",
                    ),
                    ToolConsideration(
                        tool_id="glp1r_virtual_screening_protocol",
                        role=ToolRole.REUSE,
                        decision="deferred",
                        rationale="Paper cascade reference only.",
                    ),
                ]
                nodes.append(
                    ExecutionNode(
                        node_id=f"{sid}.emit",
                        stage_id=sid,
                        tool_id="stage6.emit_job_pack",
                        action="emit",
                        on_failure="escalate",
                    )
                )
                nodes.append(
                    ExecutionNode(
                        node_id=f"{sid}.ingest",
                        stage_id=sid,
                        tool_id="stage6.ingest_seeded_returns",
                        action="ingest_status",
                        depends_on=[f"{sid}.emit"],
                        on_failure="continue_with_uncertainty",
                    )
                )
        else:
            why = "Fallback stage reasoning."
            tools = []
            route = MaturityRoute.LOCAL_INVOKE

        sr = StageReasoning(
            stage_id=sid,
            goal_locked=stage["goal"],
            why_this_path=why,
            tools=tools,
            iteration_policy={
                "loop": "propose→tool→score→critic→continue|stop|escalate",
                "max_rounds": 1,
            },
            maturity_route=route,
            handoff_out=list(stage.get("completion_criteria", [])),
            soft_skip=False,
            uncertainty="; ".join(notes) if notes else None,
        )
        return sr, nodes, notes

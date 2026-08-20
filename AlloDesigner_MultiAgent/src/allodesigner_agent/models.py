from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskTrack(str, Enum):
    RETROSPECTIVE_BLIND = "retrospective_blind"
    RETROSPECTIVE_INFORMED = "retrospective_informed"
    EXPLORATORY = "exploratory"


class ToolRole(str, Enum):
    REUSE = "reuse"
    ADAPT = "adapt"
    ALTERNATIVE = "alternative"
    SUPPLEMENT = "supplement"
    BENCHMARK = "benchmark"
    INAPPLICABLE = "inapplicable"


class PacketStatus(str, Enum):
    PLANNED = "planned"
    RUNNING = "running"
    NEEDS_HUMAN = "needs_human"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class Maturity(str, Enum):
    EXECUTABLE = "executable"
    SCRIPTED = "scripted"
    EXTERNAL = "external"
    PAPER_ONLY = "paper_only"


class HumanApproval(BaseModel):
    item: str
    approver: str
    status: str = "pending"
    timestamp: str | None = None
    note: str | None = None


class TargetSpec(BaseModel):
    name: str
    sequence_ref: str
    uniprot: str | None = None
    organism: str | None = None


class TaskSpec(BaseModel):
    task_id: str
    target: TargetSpec
    track: TaskTrack
    plan_id: str = "allodesigner_reference_path"
    stages_enabled: list[str]
    allowed_priors: list[str] = Field(default_factory=list)
    forbidden_information: list[str] = Field(default_factory=list)
    answer_store_ref: str | None = None
    human_approvals: list[HumanApproval] = Field(default_factory=list)
    budget: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None


class ToolDecision(BaseModel):
    tool_id: str
    role: ToolRole
    decision: str
    rationale: str = ""


class DecisionPacket(BaseModel):
    packet_id: str
    task_id: str
    stage_id: str
    stage_contract_version: str = "1.0.0"
    task_track: TaskTrack
    inputs_frozen: list[str] = Field(default_factory=list)
    priors_approved: list[str] = Field(default_factory=list)
    tools_considered: list[ToolDecision] = Field(default_factory=list)
    tool_selected: list[str] = Field(default_factory=list)
    outputs: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    qc_flags: list[str] = Field(default_factory=list)
    human_interventions: list[str] = Field(default_factory=list)
    claims_allowed: list[str] = Field(default_factory=list)
    iteration: dict[str, Any] = Field(default_factory=dict)
    critic: dict[str, Any] = Field(default_factory=dict)
    status: PacketStatus = PacketStatus.PLANNED
    maturity: Maturity = Maturity.SCRIPTED


class PlanStep(BaseModel):
    stage_id: str
    tools: list[str] = Field(default_factory=list)
    benchmarks: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None
    iteration: dict[str, Any] = Field(default_factory=dict)


class ExecutionPlan(BaseModel):
    plan_id: str
    title: str
    task_id: str
    track: TaskTrack
    steps: list[PlanStep]
    policy_notes: list[str] = Field(default_factory=list)


class MaturityRoute(str, Enum):
    LOCAL_INVOKE = "local_invoke"
    JOB_PACK = "job_pack"
    HISTORICAL_REPLAY = "historical_replay"
    REUSE_ARTIFACT = "reuse_artifact"
    PAPER_ONLY_PLACEHOLDER = "paper_only_placeholder"


class ToolConsideration(BaseModel):
    tool_id: str
    role: ToolRole
    decision: str
    rationale: str = ""


class StageReasoning(BaseModel):
    stage_id: str
    goal_locked: str
    why_this_path: str
    tools: list[ToolConsideration] = Field(default_factory=list)
    iteration_policy: dict[str, Any] = Field(default_factory=dict)
    maturity_route: MaturityRoute
    handoff_out: list[str] = Field(default_factory=list)
    soft_skip: bool = False
    uncertainty: str | None = None


class ExecutionNode(BaseModel):
    node_id: str
    stage_id: str
    tool_id: str
    action: str
    args: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    on_failure: str = "escalate"
    status: str = "pending"
    result_ref: str | None = None


class ReasoningPlan(BaseModel):
    """Agent-formed reasoning chain inside frozen stage contracts."""

    schema_version: str = "1.0.0"
    plan_id: str
    task_id: str
    track: TaskTrack
    scientific_hypothesis: str
    information_boundary: dict[str, Any] = Field(default_factory=dict)
    stages: list[StageReasoning] = Field(default_factory=list)
    execution_dag: list[ExecutionNode] = Field(default_factory=list)
    global_stop_policy: dict[str, Any] = Field(default_factory=dict)
    claim_policy: dict[str, Any] = Field(default_factory=dict)
    uncertainty_notes: list[str] = Field(default_factory=list)
    planner_mode: str = "heuristic_autonomous"


class ToolResult(BaseModel):
    ok: bool
    tool_id: str
    action: str
    maturity_route: str
    outputs: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    claims_allowed: list[str] = Field(default_factory=list)
    claims_forbidden: list[str] = Field(default_factory=list)
    error: str | None = None
    product_maturity: str | None = None

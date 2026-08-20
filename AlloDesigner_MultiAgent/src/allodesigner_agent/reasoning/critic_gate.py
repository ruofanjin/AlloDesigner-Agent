"""Plan-level and packet-level critic gates for autonomous reasoning."""
from __future__ import annotations

from typing import Any

from ..agents.critic import CriticAgent
from ..contracts import ordered_stage_ids, stage_by_id
from ..models import DecisionPacket, ReasoningPlan, TaskSpec, TaskTrack


class ReasoningCritic:
    """Enforce frozen contracts on ReasoningPlan + runtime claims."""

    def __init__(self) -> None:
        self.packet_critic = CriticAgent()

    def review_plan(
        self,
        task: TaskSpec,
        plan: ReasoningPlan,
        contracts: dict[str, Any],
    ) -> dict[str, Any]:
        findings: list[str] = []
        canonical = ordered_stage_ids(contracts)
        plan_stage_ids = [s.stage_id for s in plan.stages]

        # Must not invent unknown stages
        for sid in plan_stage_ids:
            if sid not in canonical:
                findings.append(f"Unknown stage in reasoning plan: {sid}")

        # Must preserve relative order of included stages
        ordered = [s for s in canonical if s in plan_stage_ids]
        if ordered != plan_stage_ids:
            findings.append(
                f"Stage order rewrite rejected: got {plan_stage_ids}, expected {ordered}"
            )

        enabled = set(task.stages_enabled)
        for sid in ordered:
            stage = stage_by_id(contracts, sid)
            # Hard dependencies must be present in plan (or soft_skip with uncertainty)
            for dep in stage.get("depends_on", []):
                if dep not in enabled:
                    findings.append(f"Hard dependency '{dep}' missing for '{sid}'")
                elif dep not in plan_stage_ids:
                    findings.append(f"Plan omits hard dependency '{dep}' required by '{sid}'")

            sr = next(s for s in plan.stages if s.stage_id == sid)
            # Goal must match contract (locked)
            if sr.goal_locked.strip() != stage["goal"].strip():
                findings.append(f"Goal rewrite for {sid} forbidden")

            # Soft skip only for soft_depends_on consumers or explicit soft_skip with uncertainty
            if sr.soft_skip and not sr.uncertainty:
                findings.append(f"soft_skip on {sid} requires uncertainty note")

            # paper_only route cannot claim local success maturity in plan claim_policy per stage
            if sr.maturity_route.value == "paper_only_placeholder":
                for t in sr.tools:
                    if t.decision == "selected" and "complete" in t.rationale.lower():
                        findings.append(f"paper_only tool selected as complete on {sid}")

        # Blind leakage in information boundary narrative
        if task.track == TaskTrack.RETROSPECTIVE_BLIND:
            blob = json_dumps_lower(plan.information_boundary) + " " + plan.scientific_hypothesis.lower()
            for token in ("holo structure answer", "ligand answer", "5vex answer inject"):
                if token in blob:
                    findings.append(f"Blind-track leakage risk: {token}")
            for prior in plan.information_boundary.get("forbidden_information", []):
                if prior.lower() in blob and "forbidden" not in blob:
                    pass  # listed as forbidden is OK

        # Claim policy must not allow stage forbidden claims globally
        allowed = set(plan.claim_policy.get("allowed", []))
        for sid in plan_stage_ids:
            stage = stage_by_id(contracts, sid)
            for fc in stage.get("forbidden_claims", []):
                if fc in allowed:
                    findings.append(f"Global claim_policy allows forbidden claim: {fc}")

        # DAG nodes must reference known plan stages
        stage_set = set(plan_stage_ids)
        for node in plan.execution_dag:
            if node.stage_id not in stage_set:
                findings.append(f"DAG node {node.node_id} references missing stage {node.stage_id}")

        passed = len(findings) == 0
        return {
            "passed": passed,
            "findings": findings,
            "action": "approve" if passed else "revise",
        }

    def review_packet(
        self,
        task: TaskSpec,
        packet: DecisionPacket,
        contracts: dict[str, Any],
        *,
        product_maturity: str | None = None,
        claimed_completion: bool = False,
    ) -> dict[str, Any]:
        base = self.packet_critic.review(task, packet, contracts)
        findings = list(base.get("findings", []))

        # Maturity overclaim: seeded/demo cannot claim executable full VS/MD
        if product_maturity in {"partial/seeded", "partial/demo", "paper_only"}:
            for claim in packet.claims_allowed:
                low = claim.lower()
                if "全库" in claim or "论文级" in claim or "已证实" in claim:
                    findings.append(f"Maturity overclaim under {product_maturity}: {claim}")
                if product_maturity == "partial/seeded" and "真实对接" in claim:
                    findings.append(f"Seeded return cannot claim real docking: {claim}")

        if claimed_completion and product_maturity == "paper_only":
            findings.append("paper_only cannot be marked scientifically completed")

        # Forbidden claim substrings often used in overclaim
        stage = stage_by_id(contracts, packet.stage_id)
        for fc in stage.get("forbidden_claims", []):
            for claim in packet.claims_allowed:
                if fc == claim or (len(fc) > 4 and fc in claim):
                    findings.append(f"Packet claim hits forbidden boundary: {claim}")

        passed = len(findings) == 0
        return {
            "passed": passed,
            "findings": findings,
            "claims_allowed": base.get("claims_allowed", []),
            "claims_forbidden": base.get("claims_forbidden", []),
        }


def json_dumps_lower(obj: Any) -> str:
    import json

    return json.dumps(obj, ensure_ascii=False).lower()

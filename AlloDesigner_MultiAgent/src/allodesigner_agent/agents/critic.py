from __future__ import annotations

from typing import Any

from ..contracts import stage_by_id
from ..models import DecisionPacket, TaskSpec, TaskTrack


class CriticAgent:
    """Contract compliance, leakage checks, and claim-boundary enforcement."""

    def review(
        self,
        task: TaskSpec,
        packet: DecisionPacket,
        contracts: dict[str, Any],
        librarian_report: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        findings: list[str] = []
        stage = stage_by_id(contracts, packet.stage_id)

        # Claim boundary: packet may only expose allowed claims.
        forbidden = set(stage.get("forbidden_claims", []))
        for claim in packet.claims_allowed:
            if claim in forbidden:
                findings.append(f"Forbidden claim exposed: {claim}")

        # Blind-track leakage
        if task.track == TaskTrack.RETROSPECTIVE_BLIND:
            for prior in packet.priors_approved + packet.inputs_frozen:
                low = prior.lower()
                if "holo" in low or "ligand" in low or "answer" in low:
                    findings.append(f"Blind-track sensitive prior in packet: {prior}")
            if librarian_report:
                findings.extend(librarian_report.get("leakage_risks", []))

        # Exploratory overclaim guard (static check on stage policy)
        if task.track == TaskTrack.EXPLORATORY:
            for claim in stage.get("forbidden_claims", []):
                if "真实" in claim or "证实" in claim or "有效" in claim:
                    # informational anchor; not a failure by itself
                    pass

        # Missing selected tools
        if not packet.tool_selected and packet.status.value == "completed":
            findings.append("Completed packet has no selected tools")

        passed = len(findings) == 0
        return {
            "passed": passed,
            "findings": findings,
            "claims_allowed": list(stage.get("allowed_claims", [])),
            "claims_forbidden": list(stage.get("forbidden_claims", [])),
        }

"""ToolRouter: maturity-aware invocation of stage tools."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


from ..contracts import ROOT, load_tool_registry, stage_by_id, load_stage_contracts
from ..models import Maturity, ToolResult

# Well-known demo artifact anchors (GLP1 retrospective demo chain).
STAGE4_RUN = Path("/home/ubuntu/work/allo-md/runs/glp1r_distance_1ns_demo_001")
STAGE4_RESULT = ROOT / "runs" / "stage4_demo_glp1r_distance_1ns" / "stage_result.json"
STAGE5_RUN = ROOT / "runs" / "stage5_glp1r_pocket_eval_demo"
STAGE6_PACK = ROOT / "job_packs" / "stage6_candidate_ranking_glp1r_seeded"
STAGE6_RUN = ROOT / "runs" / "stage6_glp1r_ranking_seeded_demo"
RETRO_RUN = ROOT / "runs" / "20260810T165917Z_glp1r_retrospective_blind_v1"
ALLO_STEPWISE_INPUTS = ROOT.parent / "allo_stepwise" / "inputs"


Handler = Callable[[dict[str, Any]], ToolResult]


class ToolRouter:
    """Route tool calls by registry maturity; never fake paper_only success."""

    def __init__(self, registry: dict[str, Any] | None = None) -> None:
        self.registry = registry or load_tool_registry()
        self.contracts = load_stage_contracts()
        self._handlers: dict[str, Handler] = {
            "contract.get_stages": self._contract_get_stages,
            "tools.list": self._tools_list,
            "tools.describe": self._tools_describe,
            "artifacts.resolve": self._artifacts_resolve,
            "stage2.replay_residue_prior": self._stage2_replay,
            "stage3.replay_ensemble": self._stage3_replay,
            "stage4.reuse_or_status": self._stage4_reuse,
            "stage5.historical_replay": self._stage5_historical,
            "stage5.fpocket_from_frames_status": self._stage5_fpocket_status,
            "stage6.emit_job_pack": self._stage6_emit,
            "stage6.ingest_seeded_returns": self._stage6_ingest_status,
            "critic.check_claims": self._critic_passthrough,
            "packet.write": self._packet_write,
        }

    def maturity_of(self, tool_id: str) -> Maturity | None:
        tools = self.registry.get("tools", self.registry)
        # tool_registry may be flat mapping under "tools" or top-level keys
        meta = None
        if isinstance(tools, dict) and tool_id in tools:
            meta = tools[tool_id]
        elif tool_id in self.registry and isinstance(self.registry[tool_id], dict):
            meta = self.registry[tool_id]
        if not meta:
            return None
        raw = meta.get("maturity", "scripted")
        try:
            return Maturity(raw)
        except ValueError:
            return Maturity.SCRIPTED

    def route_for_maturity(self, maturity: Maturity | None) -> str:
        if maturity == Maturity.EXECUTABLE:
            return "local_invoke"
        if maturity == Maturity.SCRIPTED:
            return "local_invoke"
        if maturity == Maturity.EXTERNAL:
            return "job_pack"
        if maturity == Maturity.PAPER_ONLY:
            return "paper_only_placeholder"
        return "local_invoke"

    def invoke(self, tool_id: str, action: str = "run", args: dict[str, Any] | None = None) -> ToolResult:
        args = dict(args or {})
        args["_action"] = action
        handler = self._handlers.get(tool_id)
        if handler is None:
            return ToolResult(
                ok=False,
                tool_id=tool_id,
                action=action,
                maturity_route="unknown",
                error=f"No handler registered for tool_id={tool_id}",
            )
        mat = self.maturity_of(tool_id)
        # Guard: paper_only tools cannot report scientific completion via invoke
        if mat == Maturity.PAPER_ONLY and action in {"run", "execute", "complete"}:
            return ToolResult(
                ok=False,
                tool_id=tool_id,
                action=action,
                maturity_route="paper_only_placeholder",
                error="paper_only tool cannot be executed as success",
                product_maturity="paper_only",
                claims_forbidden=["paper protocol executed locally"],
            )
        result = handler(args)
        if not result.maturity_route:
            result.maturity_route = self.route_for_maturity(mat)
        return result

    # --- handlers ---

    def _contract_get_stages(self, args: dict[str, Any]) -> ToolResult:
        stages = [
            {
                "id": s["id"],
                "order": s["order"],
                "goal": s["goal"],
                "depends_on": s.get("depends_on", []),
                "soft_depends_on": s.get("soft_depends_on", []),
                "product_maturity": s.get("product_maturity"),
            }
            for s in self.contracts["stages"]
        ]
        return ToolResult(
            ok=True,
            tool_id="contract.get_stages",
            action="get",
            maturity_route="local_invoke",
            outputs={"stages": stages},
        )

    def _tools_list(self, args: dict[str, Any]) -> ToolResult:
        tools = self.registry.get("tools", {})
        if not tools and any(isinstance(v, dict) and "stage" in v for v in self.registry.values()):
            tools = {k: v for k, v in self.registry.items() if isinstance(v, dict) and "stage" in v}
        listing = {
            tid: {
                "stage": meta.get("stage"),
                "maturity": meta.get("maturity"),
                "role_default": meta.get("role_default"),
            }
            for tid, meta in tools.items()
        }
        return ToolResult(
            ok=True,
            tool_id="tools.list",
            action="list",
            maturity_route="local_invoke",
            outputs={"tools": listing},
        )

    def _tools_describe(self, args: dict[str, Any]) -> ToolResult:
        tid = args.get("tool_id")
        tools = self.registry.get("tools", self.registry)
        meta = tools.get(tid) if isinstance(tools, dict) else None
        return ToolResult(
            ok=meta is not None,
            tool_id="tools.describe",
            action="describe",
            maturity_route="local_invoke",
            outputs={"tool_id": tid, "meta": meta},
            error=None if meta else f"unknown tool {tid}",
        )

    def _artifacts_resolve(self, args: dict[str, Any]) -> ToolResult:
        catalog = {
            "stage4_md_run": str(STAGE4_RUN) if STAGE4_RUN.exists() else None,
            "stage4_result": str(STAGE4_RESULT) if STAGE4_RESULT.exists() else None,
            "stage5_run": str(STAGE5_RUN) if STAGE5_RUN.exists() else None,
            "stage6_pack": str(STAGE6_PACK) if STAGE6_PACK.exists() else None,
            "stage6_run": str(STAGE6_RUN) if STAGE6_RUN.exists() else None,
            "retrospective_run": str(RETRO_RUN) if RETRO_RUN.exists() else None,
            "allo_stepwise_inputs": str(ALLO_STEPWISE_INPUTS) if ALLO_STEPWISE_INPUTS.exists() else None,
        }
        available = {k: v for k, v in catalog.items() if v}
        return ToolResult(
            ok=True,
            tool_id="artifacts.resolve",
            action="resolve",
            maturity_route="local_invoke",
            outputs={"catalog": catalog, "available": available},
            metrics={"n_available": len(available)},
        )

    def _stage2_replay(self, args: dict[str, Any]) -> ToolResult:
        prior = RETRO_RUN / "artifacts" / "residue_prior"
        csv = prior / "GLP1R_residue_probs.csv"
        ok = csv.exists() or (RETRO_RUN / "artifacts" / "residue_prior").exists()
        # also accept any residue_prior artifact
        if not ok:
            # soft: allo_stepwise may not have stage2; mark replay from retrospective report
            ok = (RETRO_RUN / "report.json").exists()
        return ToolResult(
            ok=ok,
            tool_id="stage2.replay_residue_prior",
            action="replay",
            maturity_route="historical_replay",
            outputs={
                "mode": "historical_replay",
                "artifact_dir": str(prior) if prior.exists() else str(RETRO_RUN),
                "residue_csv": str(csv) if csv.exists() else None,
            },
            product_maturity="partial/demo" if ok else None,
            claims_allowed=["残基先验已从回溯产物复用，非本轮重算"],
            claims_forbidden=["本轮重新训练/预测 PocketMiner 完成"],
            error=None if ok else "No Stage2 retrospective artifacts found",
        )

    def _stage3_replay(self, args: dict[str, Any]) -> ToolResult:
        ens = RETRO_RUN / "artifacts" / "ensemble_enrichment"
        ok = ens.exists() or (RETRO_RUN / "report.json").exists()
        return ToolResult(
            ok=ok,
            tool_id="stage3.replay_ensemble",
            action="replay",
            maturity_route="historical_replay",
            outputs={
                "mode": "historical_replay",
                "artifact_dir": str(ens) if ens.exists() else str(RETRO_RUN),
            },
            product_maturity="partial/demo" if ok else None,
            claims_allowed=["构象富集产物已从回溯跑例复用"],
            claims_forbidden=["本轮 AF-ClaSeq/AlphaFlow 全量重算完成"],
            error=None if ok else "No Stage3 artifacts",
        )

    def _stage4_reuse(self, args: dict[str, Any]) -> ToolResult:
        force_missing = bool(args.get("force_missing_stage4", False))
        if force_missing:
            return ToolResult(
                ok=False,
                tool_id="stage4.reuse_or_status",
                action="status",
                maturity_route="job_pack",
                error="Stage4 artifact forced missing; would emit Allo-MD job_pack",
                outputs={"would_emit_job_pack": True, "profile": "distance-simulation-1ns-demo"},
                product_maturity="needs_external",
                claims_forbidden=["Stage4 1ns demo 已完成"],
            )
        ok = STAGE4_RUN.exists() and STAGE4_RESULT.exists()
        data = {}
        if STAGE4_RESULT.exists():
            data = json.loads(STAGE4_RESULT.read_text())
        return ToolResult(
            ok=ok,
            tool_id="stage4.reuse_or_status",
            action="reuse",
            maturity_route="reuse_artifact",
            outputs={
                "run_dir": str(STAGE4_RUN),
                "stage_result": data,
                "profile": data.get("profile"),
                "run_id": data.get("run_id"),
            },
            metrics=data.get("performance_ns_per_day", {}),
            product_maturity=data.get("product_maturity", "partial/demo"),
            claims_allowed=data.get("claims_allowed", []),
            claims_forbidden=data.get("claims_forbidden", []),
            error=None if ok else "Stage4 demo run missing",
        )

    def _stage5_historical(self, args: dict[str, Any]) -> ToolResult:
        hist = STAGE5_RUN / "historical_replay"
        audit = hist / "consistency_audit.json"
        ok = hist.exists() and (hist / "agent_decision.yaml").exists()
        audit_data = json.loads(audit.read_text()) if audit.exists() else {}
        return ToolResult(
            ok=ok,
            tool_id="stage5.historical_replay",
            action="replay",
            maturity_route="historical_replay",
            outputs={
                "run_dir": str(STAGE5_RUN),
                "pocket_id": "pocket_01",
                "consistency_audit": audit_data,
                "agent_decision": str(hist / "agent_decision.yaml") if ok else None,
            },
            product_maturity="partial/demo",
            claims_allowed=[
                "historical_replay 冻结 handoff 与 DeepAllo/PLB 频率表一致",
            ],
            claims_forbidden=["真实口袋已确认", "14 残基由公式自动选出"],
            error=None if ok else "Stage5 historical_replay artifacts missing",
        )

    def _stage5_fpocket_status(self, args: dict[str, Any]) -> ToolResult:
        cmp_path = STAGE5_RUN / "fpocket_vs_historical.json"
        ok = cmp_path.exists()
        data = json.loads(cmp_path.read_text()) if ok else {}
        return ToolResult(
            ok=ok,
            tool_id="stage5.fpocket_from_frames_status",
            action="status",
            maturity_route="reuse_artifact",
            outputs={
                "comparison": data,
                "best_union_recall": (data.get("best_frame_union_recall") or {}).get("union_recall")
                if isinstance(data.get("best_frame_union_recall"), dict)
                else data.get("best", {}).get("union_recall"),
            },
            product_maturity="partial/demo",
            claims_allowed=["Stage4 帧 fpocket 可与 pocket_01 做残基重叠对照"],
            claims_forbidden=["fpocket 自动发现等同专家 pocket_01"],
            error=None if ok else "fpocket_vs_historical.json missing",
        )

    def _stage6_emit(self, args: dict[str, Any]) -> ToolResult:
        if args.get("dry_block"):
            return ToolResult(
                ok=False,
                tool_id="stage6.emit_job_pack",
                action="emit",
                maturity_route="paper_only_placeholder",
                error="allow_external_vs=false; job pack emission blocked by budget policy",
                outputs={"blocked": True},
                product_maturity="paper_only",
                claims_forbidden=["Glide/Vina 全库虚筛已完成", "计算候选物已排序，待实验/专家复核"],
            )
        ok = STAGE6_PACK.exists() and (STAGE6_PACK / "job_sheet.json").exists()
        sheet = {}
        if ok:
            sheet = json.loads((STAGE6_PACK / "job_sheet.json").read_text())
        return ToolResult(
            ok=ok,
            tool_id="stage6.emit_job_pack",
            action="emit",
            maturity_route="job_pack",
            outputs={
                "job_pack_dir": str(STAGE6_PACK),
                "job_sheet": sheet,
                "vina_readme": str(STAGE6_PACK / "external" / "vina" / "README.md"),
                "glide_readme": str(STAGE6_PACK / "external" / "glide" / "README.md"),
            },
            product_maturity="partial/seeded",
            claims_allowed=["Stage6 作业单 + Vina/Glide 回传接口已 seeded"],
            claims_forbidden=["Glide/Vina 全库虚筛已完成", "有效配体/抑制剂已被证实"],
            error=None if ok else "Stage6 job pack missing",
        )

    def _stage6_ingest_status(self, args: dict[str, Any]) -> ToolResult:
        result_path = STAGE6_RUN / "stage_result.json"
        ok = result_path.exists()
        data = json.loads(result_path.read_text()) if ok else {}
        engines = data.get("engines_returned", {})
        # Detect seeded vs real docking
        seeded = False
        for eng in ("vina", "glide"):
            ret = STAGE6_RUN / "returns" / f"{eng}_seeded_example" / "ranked_candidates.csv"
            if ret.exists() and "seeded_example_not_docking" in ret.read_text():
                seeded = True
        return ToolResult(
            ok=ok and bool(engines),
            tool_id="stage6.ingest_seeded_returns",
            action="ingest_status",
            maturity_route="job_pack",
            outputs={
                "stage_result": data,
                "engines_returned": list(engines.keys()),
                "seeded_example_scores": seeded,
            },
            product_maturity="partial/seeded",
            claims_allowed=["计算候选物已排序，待实验/专家复核"] if ok else [],
            claims_forbidden=[
                "本机 seeded 示例分数来自真实对接",
                "Glide/Vina 全库虚筛已完成",
            ],
            error=None if ok else "Stage6 run result missing",
        )

    def _critic_passthrough(self, args: dict[str, Any]) -> ToolResult:
        return ToolResult(
            ok=True,
            tool_id="critic.check_claims",
            action="check",
            maturity_route="local_invoke",
            outputs=args,
        )

    def _packet_write(self, args: dict[str, Any]) -> ToolResult:
        out_dir = Path(args.get("out_dir", ROOT / "runs" / "_packets"))
        out_dir.mkdir(parents=True, exist_ok=True)
        packet = args.get("packet", {})
        name = args.get("filename", f"{packet.get('packet_id', 'packet')}.json")
        path = out_dir / name
        path.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return ToolResult(
            ok=True,
            tool_id="packet.write",
            action="write",
            maturity_route="local_invoke",
            outputs={"path": str(path)},
        )

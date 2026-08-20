#!/usr/bin/env python3
"""Validate workflow_material_pack completeness for the GLP1 demo chain."""
from __future__ import annotations

import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent


def ok(path: Path) -> bool:
    try:
        return path.exists()
    except OSError:
        return False


def main() -> int:
    checks: list[tuple[str, Path]] = [
        ("contracts stages", PACK / "00_contracts" / "stages.yaml"),
        ("contracts tools", PACK / "00_contracts" / "tool_registry.yaml"),
        ("contracts reference", PACK / "00_contracts" / "reference_path.yaml"),
        ("schema reasoning", PACK / "00_contracts" / "reasoning_plan.schema.json"),
        ("schema execution", PACK / "00_contracts" / "execution_node.schema.json"),
        ("schema stage6 return", PACK / "00_contracts" / "stage6_vs_return.schema.json"),
        ("taskspec", PACK / "01_taskspec" / "TaskSpec.yaml"),
        ("stage2 residue prior link", PACK / "02_stage2_residue_prior" / "artifacts" / "residue_prior"),
        ("stage3 frozen handoff csv", PACK / "03_stage3_ensemble" / "allo_stepwise_inputs_frozen" / "glp1_historical_holo_cluster_mapped_residues.csv"),
        ("stage3 deepallo csv", PACK / "03_stage3_ensemble" / "allo_stepwise_inputs_frozen" / "glp1-deepallo-score-residue_probabilities_top_7.csv"),
        ("stage3 plb csv", PACK / "03_stage3_ensemble" / "allo_stepwise_inputs_frozen" / "glp1-plb-score-residue_probabilities_top_7.csv"),
        ("stage4 md run", PACK / "04_stage4_physics" / "md_run_glp1r_distance_1ns_demo_001"),
        ("stage4 metad xtc", PACK / "04_stage4_physics" / "md_run_glp1r_distance_1ns_demo_001" / "stages" / "distance_metad_1ns" / "distance_metad_1ns.xtc"),
        ("stage4 stage_result", PACK / "04_stage4_physics" / "multiagent_stage_result" / "stage_result.json"),
        ("stage5 snapshot result", PACK / "05_stage5_pocket" / "snapshot_key_files" / "stage_result.json"),
        ("stage5 consistency", PACK / "05_stage5_pocket" / "snapshot_key_files" / "consistency_audit.json"),
        ("stage5 agent_decision", PACK / "05_stage5_pocket" / "snapshot_key_files" / "agent_decision.yaml"),
        ("stage5 fpocket compare", PACK / "05_stage5_pocket" / "snapshot_key_files" / "fpocket_vs_historical.json"),
        ("stage6 job_sheet", PACK / "06_stage6_vs" / "job_pack" / "job_sheet.json"),
        ("stage6 receptor", PACK / "06_stage6_vs" / "job_pack" / "inputs" / "receptor.pdb"),
        ("stage6 pocket def", PACK / "06_stage6_vs" / "job_pack" / "inputs" / "pocket_definition.json"),
        ("stage6 seeded stage_result", PACK / "06_stage6_vs" / "seeded_returns_run" / "stage_result.json"),
        ("runtime binaries doc", PACK / "07_runtime_env" / "REQUIRED_BINARIES.md"),
        ("site paths example", PACK / "07_runtime_env" / "site_paths.env.example"),
    ]
    missing = []
    for name, path in checks:
        status = "OK" if ok(path) else "MISS"
        print(f"{status:4}  {name}: {path}")
        if status == "MISS":
            missing.append(name)
    print("---")
    if missing:
        print(f"INCOMPLETE: {len(missing)} missing")
        return 1
    print("COMPLETE: demo material pack ready for reason-run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

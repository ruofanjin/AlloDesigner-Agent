#!/usr/bin/env python3
"""Write schema-conformant seeded example returns for Vina and Glide (NOT real docking)."""
from __future__ import annotations

import csv
import json
from pathlib import Path

PACK = Path(__file__).resolve().parents[1]
ROOT = PACK.parents[1]
RUN = ROOT / "runs" / "stage6_glp1r_ranking_seeded_demo"

# Deterministic placeholder scores (kcal/mol-like). Marked score_type=seeded_example_not_docking.
SEEDS = [
    ("SEED_001", "CCO", -7.8),
    ("SEED_002", "CC(=O)O", -7.4),
    ("SEED_003", "c1ccccc1", -6.9),
    ("SEED_004", "CC(C)O", -6.6),
    ("SEED_005", "C1CCCCC1", -6.3),
    ("SEED_006", "CCN", -6.0),
    ("SEED_007", "CC(=O)N", -5.8),
    ("SEED_008", "c1ccncc1", -5.5),
    ("SEED_009", "CC(C)N", -5.2),
    ("SEED_010", "COC", -5.0),
    ("SEED_011", "CCC(=O)O", -4.8),
    ("SEED_012", "c1ccc(O)cc1", -4.5),
    ("SEED_013", "CC(C)CO", -4.2),
    ("SEED_014", "CSCC", -3.9),
    ("SEED_015", "CC(=O)OC", -3.6),
]


def write_engine(engine: str, score_shift: float) -> Path:
    out = RUN / "returns" / f"{engine}_seeded_example"
    out.mkdir(parents=True, exist_ok=True)
    (out / "poses").mkdir(exist_ok=True)
    ranked = []
    for i, (lid, smi, sc) in enumerate(sorted(SEEDS, key=lambda x: x[2] + score_shift), 1):
        score = round(sc + score_shift, 2)
        ranked.append(
            {
                "rank": i,
                "ligand_id": lid,
                "smiles": smi,
                "score": score,
                "score_type": "seeded_example_not_docking",
                "engine": engine,
                "pocket_id": "pocket_01",
                "receptor_frame": "t0250",
                "pose_path": f"poses/{lid}.pdbqt",
                "notes": "interface demo only; replace with real docking return",
            }
        )
        (out / "poses" / f"{lid}.pdbqt").write_text(
            f"REMARK seeded placeholder pose for {lid} engine={engine}\n"
        )
    csv_path = out / "ranked_candidates.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(ranked[0].keys()))
        w.writeheader()
        w.writerows(ranked)
    scores = [r["score"] for r in ranked]
    scores_sorted = sorted(scores)
    dist = {
        "engine": engine,
        "n": len(scores),
        "score_units": "kcal/mol_like_placeholder",
        "bins": [
            {"lo": -8.0, "hi": -6.0, "count": sum(1 for s in scores if -8.0 <= s < -6.0)},
            {"lo": -6.0, "hi": -4.0, "count": sum(1 for s in scores if -6.0 <= s < -4.0)},
            {"lo": -4.0, "hi": -2.0, "count": sum(1 for s in scores if -4.0 <= s < -2.0)},
        ],
        "note": "placeholder distribution; not docking",
    }
    (out / "score_distribution.json").write_text(json.dumps(dist, indent=2) + "\n")
    (out / "protocol_version.json").write_text(
        (PACK / "protocol_version.json").read_text()
    )
    ret = {
        "schema_version": "1.0.0",
        "stage_id": "candidate_ranking",
        "status": "demo_completed",
        "product_maturity": "partial/seeded",
        "engine": engine,
        "protocol_version": "vina_or_glide_external_v0",
        "inputs_consumed": {
            "request_id": "stage6_glp1r_ranking_seeded_v1",
            "pocket_id": "pocket_01",
            "receptor": str(PACK / "inputs" / "receptor.pdb"),
            "n_library": 15,
        },
        "ranked_candidates_csv": "ranked_candidates.csv",
        "poses_dir": "poses/",
        "score_distribution": dist,
        "metrics": {
            "n_scored": 15,
            "top_n": 10,
            "score_min": min(scores),
            "score_median": scores_sorted[len(scores_sorted) // 2],
            "score_max": max(scores),
            "score_units": "kcal/mol_like_placeholder",
        },
        "operator_notes": (
            f"Seeded example return for {engine} — scores are NOT from real docking. "
            "Replace by external Vina/Glide return using the same schema."
        ),
        "claims_allowed": ["计算候选物已排序，待实验/专家复核", "Stage6 作业单 + 回传接口已 seeded"],
        "claims_forbidden": [
            "有效配体/抑制剂已被证实",
            "Glide/Vina 全库虚筛已完成",
            "本示例分数来自真实对接",
        ],
    }
    (out / "return.json").write_text(json.dumps(ret, indent=2) + "\n")
    return out


def main() -> None:
    for eng, shift in (("vina", 0.0), ("glide", -0.15)):
        p = write_engine(eng, shift)
        print(f"wrote {p}")


if __name__ == "__main__":
    main()

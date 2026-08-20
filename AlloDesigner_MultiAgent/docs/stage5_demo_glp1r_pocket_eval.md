# Stage5 demo record — GLP1R pocket evaluation

**Status**: `partial / demo`  
**Completed (UTC)**: 2026-08-14  
**Run dir**: `/home/ubuntu/file2/jrf/AlloDesigner/AlloDesigner_MultiAgent/runs/stage5_glp1r_pocket_eval_demo`

## What ran

Two parallel Stage5 tracks (product decision: both allowed):

| Track | What | Result |
|---|---|---|
| **A. historical_replay** | Seed frozen Step3 DeepAllo/PLB tables + 14-residue handoff; SHA256 + ⊆ audit | Pass |
| **B. Stage4 frames → fpocket** | Protein frames from `glp1r_distance_1ns_demo_001` metad xtc; fpocket geometry; overlap vs `pocket_01` | Pass (demo) |

## Track A — historical_replay

Inputs (SHA256 match frozen allo_stepwise):

| File | SHA256 |
|---|---|
| `glp1_historical_holo_cluster_mapped_residues.csv` | `0213fabe2b7eb965b4756ab8f0278bc76164e3458c20ede97028066030305354` |
| `glp1-deepallo-score-residue_probabilities_top_7.csv` | `c4d5cdedb3ccd42ec7737b987500329d4141a9a6a00b1fedf707e00fb3e6edc0` |
| `glp1-plb-score-residue_probabilities_top_7.csv` | `6f3fb69adc352e99cbc09b6b85525141e78fc31779728314658ffbb79568d67a` |

**pocket_01 residues (expert handoff)**:  
`354, 355, 357, 358, 365, 369, 410, 411, 412, 413, 414, 415, 416, 417`

Consistency audit (`historical_replay/consistency_audit.json`):

- all 14 ∈ DeepAllo top-7 frequency table
- all 14 ∈ PLB top-7 frequency table
- **not** claimed as automatic DeepAllo∩PLB fusion

`agent_decision`: `mode=historical_replay`, `CONTINUE`, `n_residues=14`.

## Track B — Stage4 frames → fpocket

Source MD: `/home/ubuntu/work/allo-md/runs/glp1r_distance_1ns_demo_001`  
Stage: `distance_metad_1ns` (Protein group, 7952 ATOM)

Selected dump tags (xtc nearest frame may differ; see PDB TITLE):

`0, 84, 250, 334, 500, 750, 999` ps (incl. max rbias / extreme mean-d)

Per-frame **union** recall vs historical 14 (residues lining **any** fpocket pocket on that frame):

| Frame tag | Union recall |
|---|---:|
| t0000 | 0.79 |
| t0084 | 0.79 |
| t0250 | **1.00** |
| t0334 | **1.00** |
| t0500 | 0.71 |
| t0750 | 0.86 |
| t0999 | 0.71 |

Best single pocket (t0250 / pocket 41): overlap **7/14** (recall 0.50), Jaccard 0.29 — geometric fragment of the historical set, not an automatic replacement for expert `pocket_01`.

Machine-readable: `fpocket_vs_historical.json`.

## Consistency口径（对合作者）

| 可说 | 不可说 |
|---|---|
| historical_replay 冻结 handoff 与 DeepAllo/PLB 频率表一致 | 14 残基由公式自动选出 |
| Stage4 1 ns 帧上 fpocket 能覆盖历史残基集合（多帧 union） | 单口袋 = pocket_01 / 机制已证实 |
| Stage5 demo 可对接 Stage4 产物做几何对照 | 论文级 MDpocket 50 ns / DBSCAN 全栈已复现 |
| 成熟度 **partial/demo** | Stage5 产品编排（MultiAgent CLI）已恢复完整 |

## Gaps (honest)

- MultiAgent `_pocket_eval` 源码仍缺；本 run 为手工接线 demo，非 `python -m allodesigner_agent` 一键产出。
- 未重跑 DeepAllo/PLB/DBSCAN 于 MD 帧；未跑 Allo-MD `mdpocket_distance_*`。
- 下一步产品化：把抽帧→fpocket→vs pocket_01 报告写回 Stage5 executor。

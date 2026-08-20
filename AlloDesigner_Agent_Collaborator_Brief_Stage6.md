# AlloDesigner Agent — Stage6 状态快报（合作者）

**日期**：2026-08-14（UTC）  
**结论**：Stage6（candidate_ranking）**作业单 + Vina/Glide 回传接口已 seeded**，成熟度 **`partial / seeded`**。本机示例回传**不是**真实对接分数。

## 交付

1. Job pack：受体 `t0250`、pocket_01 盒子、seed 库、Vina/Glide 操作说明  
2. 回传 schema + `ingest_return.py`  
3. Vina / Glide 双引擎示例回传已 ingest → `stage_result.json`

路径：  
`AlloDesigner_MultiAgent/job_packs/stage6_candidate_ranking_glp1r_seeded/`  
`AlloDesigner_MultiAgent/runs/stage6_glp1r_ranking_seeded_demo/`  
文档：`AlloDesigner_MultiAgent/docs/stage6_seeded_job_pack.md`

## 口径

| 可说 | 不可说 |
|---|---|
| 外部虚筛可按作业单执行并回传 | 全库 / 论文 cascade 已完成 |
| 接口 demo 已通 | 示例分数来自真实 Vina/Glide |
| 计算排序待专家复核 | 有效配体已证实 |

## 下一步

在装有 Vina 或 Schrödinger 的站点按 `external/*/README.md` 跑真实对接，替换 `returns/*_seeded_example`。

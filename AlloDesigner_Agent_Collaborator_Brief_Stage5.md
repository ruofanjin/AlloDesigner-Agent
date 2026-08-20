# AlloDesigner Agent — Stage5 状态快报（合作者）

**日期**：2026-08-14（UTC）  
**结论**：Stage5（pocket_evaluation）本地 **demo 已完成**，成熟度 **`partial / demo`**。双轨：historical_replay + Stage4 帧 fpocket 对照。

## 跑通了什么

1. **historical_replay**：冻结 DeepAllo/PLB 频率表 + 14 残基 handoff；SHA256 一致；14 ⊆ 两表；`agent_decision=CONTINUE` / `pocket_01`。  
2. **Stage4 帧**：从 `glp1r_distance_1ns_demo_001` metad 抽 7 个 Protein 帧 → fpocket；相对历史 14 残基，多帧 **union recall 最高 1.0**（单口袋最佳重叠 7/14）。

## 产物位置

`/home/ubuntu/file2/jrf/AlloDesigner/AlloDesigner_MultiAgent/runs/stage5_glp1r_pocket_eval_demo/`

文档：[`AlloDesigner_MultiAgent/docs/stage5_demo_glp1r_pocket_eval.md`](AlloDesigner_MultiAgent/docs/stage5_demo_glp1r_pocket_eval.md)

## 对合作者的口径

| 可说 | 不可说 |
|---|---|
| 历史口袋 handoff 与评分表一致可复核 | 14 残基由自动融合选出 |
| Stage4 1 ns 帧可做几何口袋对照 | 真实口袋已确认 / 机制已证实 |
| Stage5 demo 成熟度 partial/demo | 论文级 MDpocket/全栈重算已完成 |

## 下一步（产品）

Stage6 虚筛外接；或把抽帧→fpocket→vs pocket_01 写回 MultiAgent executor（需先恢复缺失 `.py`）。

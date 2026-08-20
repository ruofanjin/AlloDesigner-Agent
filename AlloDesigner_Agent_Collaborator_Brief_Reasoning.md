# AlloDesigner Agent — 自主推理编排快报（合作者）

**日期**：2026-08-14（UTC）  
**结论**：已落地「**合同内自主推理**」编排器：Agent 生成 ReasoningPlan/DAG，Critic 门控后调用 ToolRouter；GLP1 retrospective demo 切片已跑通。

## 原则

- **冻结**：六阶段科学语义与硬依赖  
- **自主**：每阶段为何走 replay/reuse/job_pack、工具角色、不确定性叙事、执行图  

## 入口

```bash
python -m allodesigner_agent reason-run --task examples/glp1r_reason_demo.yaml
```

证据目录：`AlloDesigner_MultiAgent/runs/reason_glp1r_demo_v1/`  
文档：`AlloDesigner_MultiAgent/docs/reasoning_orchestrator.md`

## 已验证的“真推理”（非只改文案）

| 条件 | DAG 变化 |
|---|---|
| 默认（Stage4 1ns 存在） | physics=`reuse_artifact`；pocket 含 fpocket 节点 |
| `--force-missing-stage4` | physics=`job_pack`；pocket 仅 historical |
| `allow_external_vs=false` | Stage6=`paper_only_placeholder`（blocked） |

## 口径

| 可说 | 不可说 |
|---|---|
| 推理链由 Agent 在合同内自主搭建 | 端到端论文级科学发现已完成 |
| Demo 串联 Stage2–6 产物/作业单 | 真实 Vina/Glide 全库虚筛已完成 |

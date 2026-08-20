# SUPPLEMENT — Stage4/5/6 状态摘录

更新于 2026-08-14。

## Stage4 / Allo-MD

- [x] Allo-MD 包完整性（LFS/gro checksum）已通过正式 clone 修复  
- [x] 本机 GMX+PLUMED+fpocket 安装与 doctor 通过  
- [x] **1 ns demo 全链路完成**（`distance-simulation-1ns-demo` / `glp1r_distance_1ns_demo_001`）  
- [ ] 正式冻结 `distance-simulation-only`（~200 ns）— **可选，当前产品决策不跑**  

证据：`AlloDesigner_MultiAgent/docs/stage4_demo_glp1r_1ns.md`。

## Stage5 / pocket evaluation

- [x] **historical_replay** 冻结 handoff 种子 + SHA256 + 14 ⊆ DeepAllo/PLB 频率表核对  
- [x] **Stage4 帧 → fpocket** 手工接线 demo；多帧 union recall vs pocket_01 可达 1.0  
- [ ] MultiAgent `_pocket_eval` 自动回传（源码缺口）  
- [ ] DeepAllo/PLB/DBSCAN 对 MD 帧重算  
- [ ] Allo-MD MDpocket 正式阶段  

证据：`AlloDesigner_MultiAgent/docs/stage5_demo_glp1r_pocket_eval.md`

## Stage6 / candidate ranking（虚筛）

- [x] **作业单** seeded（receptor t0250 + pocket_01 box + seed 库）  
- [x] **Vina / Glide** 外部操作说明 + 回传 schema + ingest  
- [x] 双引擎 **seeded example return** 已 ingest（**非真实对接分数**）  
- [ ] 本机/外站真实 Vina 对接回传  
- [ ] 本机/外站真实 Glide 对接回传  
- [ ] 论文级 KarmaDock/Glide/Vina cascade  

证据：`AlloDesigner_MultiAgent/docs/stage6_seeded_job_pack.md`  
Pack：`AlloDesigner_MultiAgent/job_packs/stage6_candidate_ranking_glp1r_seeded/`  
Run：`AlloDesigner_MultiAgent/runs/stage6_glp1r_ranking_seeded_demo/`

### 成熟度一览

| Stage | product_maturity |
|---|---|
| 4 physics_sampling | partial/demo |
| 5 pocket_evaluation | partial/demo |
| 6 candidate_ranking | partial/seeded |

## 自主推理编排（合同内）

- [x] ReasoningPlan / ExecutionNode schema  
- [x] ToolRouter + ReasoningCritic + Orchestrator 最小环  
- [x] GLP1 retrospective demo 切片 `runs/reason_glp1r_demo_v1`（DAG 随预算/产物改写）  
- [ ] LLM-assisted planner 后端（当前为 heuristic_autonomous）  
- [ ] Stage2/3/4/6 科学重算工具全量接入  

证据：`AlloDesigner_MultiAgent/docs/reasoning_orchestrator.md`  
Brief：`AlloDesigner_Agent_Collaborator_Brief_Reasoning.md`

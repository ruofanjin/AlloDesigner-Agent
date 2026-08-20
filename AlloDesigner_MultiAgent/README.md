# AlloDesigner Multi-Agent

受控多智能体系统：把 AlloDesigner 论文主路径固化为**专家冻结的阶段合同**，Agent 只在合同内做工具选择、多轮迭代与审计交付。

## 核心口径

- **固定**：生物学问题分解、阶段目标、科学约束、信息边界  
- **开放**：每个阶段内的工具选择、参数搜索、对照实验  
- **默认最优骨架**：AlloDesigner 参考主路径（可被证据挑战，但不可被 Agent 擅自删改阶段语义）  
- **输出**：可复核决策包，不是最终科学结论  

## 多智能体角色

| Agent | 职责 |
| --- | --- |
| `Coordinator` | 加载任务、冻结轨道、按阶段调度 |
| `Librarian` | 文献/先验草案、泄漏风险标注 |
| `Planner` | 在阶段合同约束下生成执行图（默认挂载参考路径） |
| `StageExecutor` ×6 | 各阶段执行与多轮迭代 |
| `Critic` | 盲态隔离、过度宣称、合同合规检查 |
| `Reporter` | 汇总决策包、工具比较表、审计日志 |

## 六阶段合同

1. `boundary` — 目标与信息边界  
2. `residue_prior` — 残基/区域先验  
3. `ensemble_enrichment` — 构象生成与 MSA 富集  
4. `physics_sampling` — 物理定向采样  
5. `pocket_evaluation` — 开放样口袋评价  
6. `candidate_ranking` — 候选物排序  

## 快速开始

```bash
cd /home/ubuntu/file2/jrf/AlloDesigner/AlloDesigner_MultiAgent
pip install -e .
python -m allodesigner_agent plan --task examples/glp1r_retrospective_blind.yaml
python -m allodesigner_agent dry-run --task examples/glp1r_retrospective_blind.yaml

# 先比对各阶段环境：已有可复用 vs 需按 yml 新建
python -m allodesigner_agent resolve-envs --task examples/glp1r_retrospective_blind.yaml

# 按论文参考路径自动串接（默认：特殊阶段缺环境则按 lockfile 创建）
python -m allodesigner_agent run --task examples/glp1r_retrospective_blind.yaml
python -m allodesigner_agent run --task examples/glp1r_retrospective_blind.yaml --no-ensure-envs
```

环境策略见 [docs/environments.md](docs/environments.md)。非特殊阶段用当前基础环境；特殊阶段先 resolve/reuse/create，再执行。

## 目录结构

```text
AlloDesigner_MultiAgent/
├── configs/           # 阶段合同、工具池、参考路径
├── schemas/           # JSON Schema
├── docs/              # 架构说明
├── examples/          # 示例任务
├── src/allodesigner_agent/
└── runs/              # 运行输出
```

## 快速开始（合同内自主推理）

```bash
cd AlloDesigner_MultiAgent
pip install -e .
python -m allodesigner_agent reason-run --task examples/glp1r_reason_demo.yaml \
  --run-dir runs/reason_glp1r_demo_v1
```

全流程材料包（合同/TaskSpec/各 Stage 产物清单与检查脚本）：  
[workflow_material_pack/](workflow_material_pack/) — 先跑 `python workflow_material_pack/prepare_check.py`。

说明见 [docs/reasoning_orchestrator.md](docs/reasoning_orchestrator.md)。

## 与仓库其他模块的关系

| 阶段 | 默认工具 | 现有代码 |
| --- | --- | --- |
| residue_prior | allo_pocketminer | `../Allo-PocketMiner/` |
| ensemble_enrichment | allo_stepwise (+ optional alphaflow) | `../allo_stepwise/`, `../AlphaFlow/` |
| pocket_evaluation | **historical_replay + Stage4 帧 fpocket 对照**（`partial/demo`） | 记录：`docs/stage5_demo_glp1r_pocket_eval.md`；run：`runs/stage5_glp1r_pocket_eval_demo`；冻结表：`../allo_stepwise/inputs/` |
| physics_sampling | Allo-MD **1 ns demo 已完成**（`partial/demo`） | 记录：`docs/stage4_demo_glp1r_1ns.md`；run：`/home/ubuntu/work/allo-md/runs/glp1r_distance_1ns_demo_001`；正式 ~200 ns 可选 |
| candidate_ranking | **作业单 + Vina/Glide 回传**（`partial/seeded`） | pack：`job_packs/stage6_candidate_ranking_glp1r_seeded`；run：`runs/stage6_glp1r_ranking_seeded_demo`；文档：`docs/stage6_seeded_job_pack.md` |

## 设计文档

- [docs/architecture.md](docs/architecture.md)
- [docs/reasoning_orchestrator.md](docs/reasoning_orchestrator.md)（合同内自主推理）
- [docs/relation_to_story_plan.md](docs/relation_to_story_plan.md)（与 story plan 的关系）
- [docs/md_backend_choice.md](docs/md_backend_choice.md)（Stage4 为何用 Allo-MD）
- [docs/stage4_demo_glp1r_1ns.md](docs/stage4_demo_glp1r_1ns.md)（Stage4 1 ns demo 完成记录）
- [docs/stage5_demo_glp1r_pocket_eval.md](docs/stage5_demo_glp1r_pocket_eval.md)（Stage5 historical_replay + Stage4 帧对照）
- [docs/stage6_seeded_job_pack.md](docs/stage6_seeded_job_pack.md)（Stage6 作业单 + Vina/Glide 回传）
- [AlloDesigner_Agent_Story_Brief.md](../AlloDesigner_Agent_Story_Brief.md)

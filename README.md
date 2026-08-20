# AlloDesigner-Agent

**AlloDesigner-Agent** 是 AlloDesigner 隐匿变构口袋（cryptic allosteric pocket）发现链路中的 **Agent 编排与工程化交付**：把六阶段科学合同变成可执行的推理链（ReasoningPlan）、工具路由（ToolRouter）、决策包与 demo 产物，并以 GLP-1R 回溯案例跑通端到端演示。

项目定位不是替换论文科学主路径本身，而是在冻结阶段语义下，让 Agent **自主选择** replay / reuse / job_pack 等执行策略，输出可审计的计划、DAG 与宣称边界。当前成熟度：**partial/demo–seeded**（1 ns MD demo、口袋对照 demo、虚筛作业单 seeded；非论文级 ~200 ns / 全库对接复现）。

---

## 本仓库核心内容

1. **合同内自主推理编排**：`ReasoningOrchestrator`（plan → critic → execute → observe → replan）  
2. **MultiAgent 合同与工具注册**：`stages.yaml` / `tool_registry.yaml` / schemas  
3. **Stage4–6 工程落地**：Allo-MD 1 ns demo 接线、Stage5 historical_replay + fpocket 对照、Stage6 Vina/Glide 作业单与回传 ingest  
4. **材料包与文档**：`workflow_material_pack/`、各 Stage demo 记录与 Brief  

---

## 仓库结构（文件导览）

| 路径 | 说明 |
|---|---|
| `AlloDesigner_MultiAgent/` | **Agent 核心包**：编排代码、配置、demo runs、作业单、材料包 |
| `AlloDesigner_MultiAgent/src/allodesigner_agent/` | Python 包：`orchestrator_loop.py`、`reasoning/`、`tools/router.py`、`cli.py` |
| `AlloDesigner_MultiAgent/configs/` | `stages.yaml`、`tool_registry.yaml`、`reference_path.yaml` |
| `AlloDesigner_MultiAgent/schemas/` | ReasoningPlan / ExecutionNode / Stage6 回传等 JSON Schema |
| `AlloDesigner_MultiAgent/examples/` | TaskSpec 示例（如 `glp1r_reason_demo.yaml`） |
| `AlloDesigner_MultiAgent/docs/` | 架构、推理编排、Stage4/5/6 demo 记录 |
| `AlloDesigner_MultiAgent/workflow_material_pack/` | 跑通 demo 链所需材料清单、`prepare_check.py`、`TaskSpec.yaml` |
| `AlloDesigner_MultiAgent/job_packs/stage6_candidate_ranking_glp1r_seeded/` | Stage6 虚筛作业单 + `run_vina.sh` / Glide 说明 + ingest |
| `AlloDesigner_MultiAgent/runs/` | 已跑通的 demo 产物（reason / stage4–6 / retrospective） |
| `Allo-MD/agent/` | 物理采样后端：`agentctl` + `stages/*.sh`（含 1 ns demo 脚本） |
| `allo_stepwise/commands/` | Stepwise 环境检查 / audit / MSA 等 shell 命令入口 |
| `Allo-PocketMiner/`、`AlphaFlow/`、`deepallo-main/` | 关联科学模块代码（大权重/数据未入库，见文末） |

根目录另有 Story/Stage Brief 与 `SUPPLEMENT_STATUS.md`，用于阶段成熟度与口径说明。

---

## Demo / Example 怎么跑

### 0. 环境

```bash
git clone https://github.com/ruofanjin/AlloDesigner-Agent.git
cd AlloDesigner-Agent/AlloDesigner_MultiAgent
python3 -m pip install -e .
```

依赖：Python ≥ 3.10，`pyyaml`、`pydantic`（见 `pyproject.toml`）。

### 1. 材料自检（推荐先跑）

```bash
python workflow_material_pack/prepare_check.py
```

材料包说明：`workflow_material_pack/README.md`、`CHECKLIST.md`、`MANIFEST.yaml`。  
TaskSpec：`workflow_material_pack/01_taskspec/TaskSpec.yaml`（与 `examples/glp1r_reason_demo.yaml` 同用途）。

### 2. Agent 自主推理全链路 demo（主入口）

只生成计划 + Critic：

```bash
python -m allodesigner_agent reason-plan \
  --task examples/glp1r_reason_demo.yaml \
  --out /tmp/reason_plan.json
```

执行 plan → critic → tool DAG（产出叙事与 report）：

```bash
python -m allodesigner_agent reason-run \
  --task examples/glp1r_reason_demo.yaml \
  --run-dir runs/reason_glp1r_demo_v1
```

可选：模拟 Stage4 缺失，观察 DAG 改写：

```bash
python -m allodesigner_agent reason-plan \
  --task examples/glp1r_reason_demo.yaml \
  --force-missing-stage4
```

**预期产物（示例目录 `runs/reason_glp1r_demo_v1/`）**

- `reasoning_plan_r0.json` — 自主 ReasoningPlan + ExecutionDAG  
- `critic_plan_r0.json` — 合同门结果  
- `reasoning_narrative.md` — 人类可读推理叙事  
- `packets/*.json` — 各节点 Decision Packet  
- `report.json` — 全量审计包  

原理说明：`docs/reasoning_orchestrator.md`、`docs/architecture.md`。

### 3. Stage4 物理采样 demo（Allo-MD shell 阶段）

入口二进制：`Allo-MD/agent/agentctl`。  
1 ns demo 相关脚本：

- `Allo-MD/agent/stages/41_distance_monitor_1ns.sh`  
- `Allo-MD/agent/stages/51_distance_metad_1ns.sh`  
- 以及 equilibration / normal branch：`20_equilibration.sh`、`30_normal_branch.sh`  

医生检查：`Allo-MD/agent/stages/00_doctor.sh`  

记录与产物口径：`AlloDesigner_MultiAgent/docs/stage4_demo_glp1r_1ns.md`  
（完整轨迹通常在站点 run 目录；材料包内为 `*.path.txt` 指针。）

### 4. Stage5 口袋评价 demo

已完成对照产物：`runs/stage5_glp1r_pocket_eval_demo/`  

- historical_replay：`historical_replay/`（pocket_01 / 14 残基）  
- Stage4 帧 fpocket：`fpocket/`、`fpocket_vs_historical.json`  

说明：`docs/stage5_demo_glp1r_pocket_eval.md`。

### 5. Stage6 虚筛作业单 + 回传 demo

作业包：`job_packs/stage6_candidate_ranking_glp1r_seeded/`

```bash
cd job_packs/stage6_candidate_ranking_glp1r_seeded

# 生成 Vina/Glide 形态的 seeded 示例回传（非真实对接分数）
python3 scripts/make_seeded_return_example.py

# 校验并写入 MultiAgent run
python3 scripts/ingest_return.py --pack-dir . \
  --return-dir ../../runs/stage6_glp1r_ranking_seeded_demo/returns/vina_seeded_example \
  --promote-run-dir ../../runs/stage6_glp1r_ranking_seeded_demo
```

外站真对接脚本示例：

- Vina：`external/vina/run_vina.sh` + `vina.conf`  
- Glide：`external/glide/README.md` + `grid_box.txt`  

说明：`docs/stage6_seeded_job_pack.md`。

### 6. allo_stepwise 命令入口（historical / 环境）

```bash
cd allo_stepwise
./commands/00_check_environment.sh --allow-missing-external
./commands/00_plan.sh
# 可选证据审计：
# ./commands/01_audit_step3_handoff.sh
```

其余 `commands/02_*.sh` … `13_*.sh` 对应迭代 MSA / ColabFold / 投票等逐步流水线（需配套环境与数据）。

---

## 已有 demo 跑例（可直接对照）

| Run | 含义 |
|---|---|
| `AlloDesigner_MultiAgent/runs/reason_glp1r_demo_v1/` | 自主推理编排 demo |
| `.../stage4_demo_glp1r_distance_1ns/` | Stage4 1 ns 完成记录（JSON） |
| `.../stage5_glp1r_pocket_eval_demo/` | Stage5 口袋对照 |
| `.../stage6_glp1r_ranking_seeded_demo/` | Stage6 作业单回传 |
| `.../20260810T165917Z_glp1r_retrospective_blind_v1/` | 回溯盲态 MultiAgent 参考跑例 |

---

## 未随仓库分发的大文件

- `AlphaFlow/weights/*.pt`（约 2.6GB）  
- `Allo-MD/agent/install/sources/*` 第三方源码包（含 >100MB）  
- Stage4 完整 MD 轨迹目录（见材料包 `*.path.txt`）  
- `allo_stepwise/workdir/`  

缺少大文件时，**Agent 推理 demo（第 2 节）仍可运行**；真重算 MD / 对接需自备对应二进制与输入。

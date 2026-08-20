# Reasoning Orchestrator — 合同内自主推理

**产品口径**：Agent 自主生成推理链与工具图；六阶段科学合同冻结。  
**Demo run**：`runs/reason_glp1r_demo_v1/`  
**TaskSpec**：`examples/glp1r_reason_demo.yaml`

## 怎么跑

```bash
cd AlloDesigner_MultiAgent
pip install -e .
python -m allodesigner_agent reason-run --task examples/glp1r_reason_demo.yaml \
  --run-dir runs/reason_glp1r_demo_v1
```

对照（DAG 应改写）：

```bash
# Stage4 当作缺失 → physics 走 job_pack，pocket 去掉 fpocket 节点
python -m allodesigner_agent reason-plan --task examples/glp1r_reason_demo.yaml \
  --force-missing-stage4 --out /tmp/reason_missing_s4.json
```

## 产出

| 文件 | 含义 |
|---|---|
| `reasoning_plan_r0.json` | 自主 ReasoningPlan + ExecutionDAG |
| `critic_plan_r0.json` | 合同门结果 |
| `packets/*.json` | 每节点 Decision Packet |
| `reasoning_narrative.md` | 人类可读推理叙事 |
| `report.json` | 全量审计包 |

## 模块

- `reasoning/planner.py` — `AutonomousReasoningPlanner`
- `reasoning/critic_gate.py` — `ReasoningCritic`
- `tools/router.py` — `ToolRouter`（成熟度路由）
- `orchestrator_loop.py` — `plan→critic→execute→observe→replan`

## 可说 / 不可说

| 可说 | 不可说 |
|---|---|
| Agent 在合同内自主生成了可执行推理链 | Agent 发明并证实了新科学主路径 |
| 预算/产物变化会改写 DAG | 论文级端到端发现已完成 |
| GLP1 demo 切片已串联 | Stage2/3/6 已全量科学重算 |

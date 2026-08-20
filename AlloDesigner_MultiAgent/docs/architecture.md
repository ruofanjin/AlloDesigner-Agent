# AlloDesigner Multi-Agent 架构

## 1. 设计原则

1. **阶段合同优先**：Agent 不得改写六阶段科学语义。  
2. **参考路径热启动**：新任务默认挂载 AlloDesigner 主路径。  
3. **环节内开放探索**：工具替换、参数迭代、对照实验在阶段内进行。  
4. **双轨隔离**：回溯盲态 / 回溯知情 / 探索轨分库运行与报告。  
5. **决策包交付**：每个阶段产出可审计 Decision Packet。  
6. **合同内自主推理**：推理链、工具图、迭代策略由 Agent 生成；六阶段骨架冻结。

## 2. 运行时拓扑

```text
Human Expert
    | 冻结 TaskSpec + 审批先验
    v
ReasoningOrchestrator          (轻量；兼容原 Coordinator 语义)
    ├── AutonomousReasoningPlanner  → ReasoningPlan + ExecutionDAG
    ├── ReasoningCritic             → 合同 / 盲态 / 宣称 / 成熟度门
    ├── ToolRouter                  → 成熟度路由（local / replay / job_pack / paper_only）
    ├── Decision Packets            → 每节点可审计
    └── Reporter                    → report.json + reasoning_narrative.md
```

旧角色映射：Librarian/Planner/StageAgents/Critic/Reporter 的**语义保留**；实现上由 `ReasoningOrchestrator` 承载，不阻塞于恢复全部历史 `.py`。

## 3. 自主推理 vs 冻结合同

| 层 | 谁做主 |
|---|---|
| 科学合同（六阶段、硬依赖、human_freezes、forbidden claims） | 冻结 |
| ReasoningPlan（为何选路径、工具角色、成熟度路由、不确定性） | Agent 自主 |
| ExecutionDAG（具体 tool calls） | Agent 提议 + Critic 批准 |
| 宣称 / product_maturity | Critic 强制 |

入口：

```bash
python -m allodesigner_agent reason-run --task examples/glp1r_reason_demo.yaml
python -m allodesigner_agent reason-plan --task examples/glp1r_reason_demo.yaml --force-missing-stage4
```

Schema：`schemas/reasoning_plan.schema.json`、`schemas/execution_node.schema.json`。

## 4. 规划约束

Planner 允许：

- 为某阶段选择/替换工具（角色：reuse / adapt / alternative / supplement / benchmark）  
- 在阶段内插入多轮迭代子步骤  
- 按产物可用性在 replay / reuse / job_pack 间改写 DAG  

Planner 禁止：

- 删除或合并会改变科学语义的阶段  
- 改写阶段 goal 文本  
- 调换关键硬依赖顺序  
- 在盲态轨注入 HOLO/配体答案特征  
- 将 `paper_only` 伪造成功  

## 5. 多轮迭代模型

```text
plan → critic → execute_next → observe → replan|continue|stop|escalate
```

节点失败策略来自 ExecutionNode.on_failure（replan / continue_with_uncertainty / escalate / stop）。

## 6. 成熟度分层与路由

| 层级 | Orchestrator 行为 |
| --- | --- |
| `executable` / `scripted` | `local_invoke` 或 `historical_replay` / `reuse_artifact` |
| `external` | 只允许 `job_pack` + 回传 ingest |
| `paper_only` | 占位；不得报告科学完成 |

## 7. GLP1 demo 垂直切片

`examples/glp1r_reason_demo.yaml` → `runs/reason_glp1r_demo_v1/`  

验证点：关闭 Stage4 产物或改预算时，ReasoningPlan/DAG **结构变化**（不仅是自然语言变化）。见 `docs/reasoning_orchestrator.md`。

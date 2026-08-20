# AlloDesigner-Agent

本仓库给 **AlloDesigner 合作者**下载与使用：**作者负责的 Agent 编排部分**（合同、推理链、工具路由、Stage 作业单/回传与 GLP-1R demo 材料），不是完整论文科学栈的官方全集。

Agent 在冻结的六阶段科学合同内自主生成 ReasoningPlan / ExecutionDAG，串联残基先验 → 构象富集 → 物理采样 → 口袋评价 → 虚筛回传；当前成熟度为 **partial/demo–seeded**（可审计 demo，不等于论文级全量重算或实验效力确认）。

## 合作者先看这里

| 你要做的事 | 入口 |
|---|---|
| 只跑 Agent 推理串联 demo | `AlloDesigner_MultiAgent/` + 下方「快速开始」 |
| 核对材料是否齐全 | `AlloDesigner_MultiAgent/workflow_material_pack/prepare_check.py` |
| 了解宣称边界 / 阶段状态 | 根目录 `SUPPLEMENT_STATUS.md`、`AlloDesigner_Agent_Collaborator_Brief_*.md` |
| 接 Stage4 MD / Stage6 对接 | `Allo-MD/`、`job_packs/stage6_*`（需本机或站点环境） |

科学侧重算（PocketMiner 训练、长 MD、真 Glide 全库等）仍由对应模块负责人/站点环境提供；本仓提供 **接口、合同与 demo 产物指针**。

## 主要目录

| 路径 | 作用 |
|---|---|
| `AlloDesigner_MultiAgent/` | **核心**：合同、`ReasoningOrchestrator`、Stage4–6 demo、`workflow_material_pack/` |
| `Allo-MD/` | 物理采样后端（agentctl）；大安装包需自备 |
| `allo_stepwise/` | historical_replay 冻结输入与脚本快照 |
| `Allo-PocketMiner/` | 残基先验代码（大 `.npy` 未入库） |
| `AlphaFlow/` | 构象相关代码壳（权重未入库） |

## 快速开始（Agent demo）

```bash
git clone https://github.com/ruofanjin/AlloDesigner-Agent.git
cd AlloDesigner-Agent/AlloDesigner_MultiAgent
pip install -e .
python workflow_material_pack/prepare_check.py
python -m allodesigner_agent reason-run \
  --task workflow_material_pack/01_taskspec/TaskSpec.yaml \
  --run-dir runs/reason_from_clone
```

详细编排说明：`AlloDesigner_MultiAgent/docs/reasoning_orchestrator.md`。

## 未随仓库分发的内容

- `AlphaFlow/weights/*.pt`（约 2.6GB）
- `Allo-MD/agent/install/sources/*` 第三方源码包（含 >100MB）
- Stage4 实际 MD 轨迹（站点路径，见 `workflow_material_pack` 内 `*.path.txt`）
- `allo_stepwise/workdir` 本地工作区

缺少上述文件时，Agent 仍可按 demo/replay/job-pack 路径规划；真重算需合作者按各模块文档补齐环境。

# AlloDesigner

AlloDesigner 是面向隐匿变构口袋（cryptic allosteric pocket）发现的多阶段工作流与多智能体编排原型，覆盖残基先验、构象富集、物理采样、口袋评价到虚筛作业单回传。本仓库以 GLP-1R 回溯 demo 为主路径，展示合同约束下的自主推理链（ReasoningPlan / ToolRouter），并可衔接 Allo-MD、PocketMiner、allo_stepwise 与外部 Vina/Glide。当前交付为 **partial/demo–seeded** 成熟度：可审计串联，不等于论文级全量重算或实验效力确认。

## 主要目录

| 路径 | 作用 |
|---|---|
| `AlloDesigner_MultiAgent/` | 合同、自主推理编排、Stage4–6 demo 与 `workflow_material_pack/` |
| `Allo-MD/` | GROMACS+PLUMED agentctl 物理采样后端 |
| `Allo-PocketMiner/` | 残基级 cryptic 先验 |
| `allo_stepwise/` | Stepwise / historical_replay 证据与脚本 |
| `AlphaFlow/` | 构象生成相关代码（权重见下） |

## 未纳入 Git 的大文件

- `AlphaFlow/weights/*.pt`（约 2.6GB）：请按 AlphaFlow 官方说明自行下载。
- `Allo-MD/agent/install/sources/*.{tar.gz,tar.bz2}`：由 Allo-MD 安装脚本拉取，勿直接推入 GitHub（含 >100MB 包）。
- Stage4 轨迹默认在站点目录 `/home/ubuntu/work/allo-md/runs/`，不在本仓库树内。

## 快速开始（推理 demo）

```bash
cd AlloDesigner_MultiAgent
pip install -e .
python workflow_material_pack/prepare_check.py
python -m allodesigner_agent reason-run --task workflow_material_pack/01_taskspec/TaskSpec.yaml
```

更多说明见 `AlloDesigner_MultiAgent/docs/reasoning_orchestrator.md` 与根目录 Brief / `SUPPLEMENT_STATUS.md`。

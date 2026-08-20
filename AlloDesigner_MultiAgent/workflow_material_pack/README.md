# Workflow Material Pack — 全流程材料包

路径：`AlloDesigner_MultiAgent/workflow_material_pack/`

本目录说明并汇总：**要把「合同内自主推理」端到端 demo 链跑通，需要准备哪些文件/环境**。  
大体积产物用 **符号链接** 指向现有 run；关键小文件做了 **快照拷贝**，便于打包移交。

## 两种完成标准（先选口径）

| 口径 | 要准备什么 | 结果成熟度 |
|---|---|---|
| **A. Demo 串联（当前推荐）** | 本包所列 contracts + TaskSpec + Stage2/3 回溯产物 + Stage4 1ns + Stage5 对照 + Stage6 job pack/回传 | partial/demo + partial/seeded |
| **B. 科学重算** | A 的基础上再加 PocketMiner 重跑、AF-ClaSeq、长 MD、真 Vina/Glide | 另立预算与站点 SOP |

本包默认服务 **口径 A**。

## 目录地图

```text
00_contracts/          阶段合同、工具注册、schema（拷贝）
01_taskspec/           冻结 TaskSpec.yaml
02_stage2_residue_prior/   Stage2 回溯产物（链接）
03_stage3_ensemble/        Stage3 产物链接 + 冻结 CSV 拷贝
04_stage4_physics/         Allo-MD 1ns run + stage_result（链接）
05_stage5_pocket/          Stage5 run 链接 + 关键 JSON 快照
06_stage6_vs/              作业单链接 + seeded 回传链接 + 快照
07_runtime_env/            本机二进制与路径模板（不入库二进制）
09_reasoning_outputs/      自主推理 demo 输出链接
```

## 最小使用步骤

```bash
cd AlloDesigner_MultiAgent
python workflow_material_pack/prepare_check.py
# 全部 OK 后：
pip install -e .
python -m allodesigner_agent reason-run \
  --task workflow_material_pack/01_taskspec/TaskSpec.yaml \
  --run-dir runs/reason_from_material_pack
```

## 移交打包建议

- **轻量移交**：打包本目录（含 symlink 清单）+ `MANIFEST.yaml`，接收方按 `07_runtime_env/site_paths.env.example` 重链大文件。  
- **离线完整移交**：另拷 Stage4 MD run（~0.7GB+）与 Stage5 frames/fpocket；不要指望只靠 symlink。

详见 [CHECKLIST.md](CHECKLIST.md)、[MANIFEST.yaml](MANIFEST.yaml)。

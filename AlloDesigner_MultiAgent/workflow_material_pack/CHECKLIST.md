# 材料准备清单（Demo 全流程）

勾选完成后再跑 `prepare_check.py`。

## 0. 合同与任务

- [ ] `00_contracts/stages.yaml` / `tool_registry.yaml` / `reference_path.yaml`
- [ ] `00_contracts/*.schema.json`（含 reasoning_plan / execution_node / stage6 return）
- [ ] `01_taskspec/TaskSpec.yaml`（人类已批 `human_approvals`；盲态轨禁 HOLO/配体注入）

## 1. Stage2 残基先验（replay）

- [ ] `02_stage2_residue_prior/artifacts/residue_prior/`（至少含残基概率表或 stage_result）
- [ ] 若要重算：Allo-PocketMiner 权重与 case 输入（本 demo 不强制）

## 2. Stage3 构象富集（replay）

- [ ] `03_stage3_ensemble/artifacts/ensemble_enrichment/`
- [ ] `03_stage3_ensemble/allo_stepwise_inputs_frozen/*.csv` + `SHA256SUMS.txt`
- [ ] 核对历史 14 残基 handoff CSV 在冻结输入中

## 3. Stage4 物理采样（reuse 1ns demo）

- [ ] `04_stage4_physics/md_run_glp1r_distance_1ns_demo_001/` 存在且含 metad xtc/gro
- [ ] `04_stage4_physics/multiagent_stage_result/stage_result.json`
- [ ] （重算时）`site.env` + GMX/PLUMED 栈可用

## 4. Stage5 口袋评价

- [ ] `05_stage5_pocket/stage5_run/historical_replay/`（agent_decision + consistency_audit）
- [ ] `fpocket_vs_historical.json`（Stage4 帧对照）
- [ ] 口径：pocket_01 = 专家 14 残基，非自动融合

## 5. Stage6 虚筛作业单 + 回传

- [ ] `06_stage6_vs/job_pack/`（receptor、pocket box、vina/glide 说明、ingest 脚本）
- [ ] 回传：`return.json` + `ranked_candidates.csv`（真对接或 seeded 示例）
- [ ] 口径：seeded ≠ 真实对接；不可宣称有效配体

## 6. 运行时环境

- [ ] Python 包可 `pip install -e AlloDesigner_MultiAgent`
- [ ] 按需：GMX、fpocket、Vina/Glide（见 `07_runtime_env/`）

## 7. 推理编排验收

- [ ] `python workflow_material_pack/prepare_check.py` 退出码 0
- [ ] `reason-run` 产出 `reasoning_plan_r0.json` + `report.json`
- [ ] 改预算或 `--force-missing-stage4` 时 DAG 结构变化

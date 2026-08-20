# GLP1R 全流程自动化运行摘要

**run_id**: `20260809T130025Z_glp1r_retrospective_blind_v1`  
**命令**: `python -m allodesigner_agent run --task examples/glp1r_retrospective_blind.yaml --ensure-envs`

## 阶段结果

| 阶段 | 状态 | 环境决策 | 说明 |
| --- | --- | --- | --- |
| boundary | completed | use_current | 信息边界表已生成 |
| residue_prior | **completed** | reuse `allo-pocketminer` | 真实跑通 Allo-PocketMiner：491 残基，阈值 0.7，阳性 119 |
| ensemble_enrichment | needs_human | reuse | 缺 AlphaFlow `predict.py`/权重与 AF_ClaSeq case 目录；已写出 `run_chain.sh` |
| physics_sampling | needs_human | create deferred | OpenMM 重环境 `auto_create=false`；已出 job sheet |
| pocket_evaluation | **completed** | reuse | 由 Stage2 阳性残基自动汇总 + 论文侧 DeepAllo/PLB CSV 挂载 |
| candidate_ranking | needs_human | use_current | 虚筛未入库；已出 job sheet |

## 关键产物

- `artifacts/residue_prior/GLP1R_residue_probs.csv`
- `artifacts/pocket_evaluation/auto_positive_residues.json`
- `artifacts/pocket_evaluation/glp1-*-residue_probabilities_top_7.csv`
- 各阶段 `env_decision.json` / `stage_result.json` / `report.json`

## 阻塞与下一步

1. 准备 AlphaFlow 上游代码与权重，或接入 ColabFold 预测目录  
2. 准备 `AF_ClaSeq/case/...` 运行目录 + fpocket/DeepAllo  
3. 如需物理采样：将 `allo_openmm_physics.auto_create` 设为 true 并创建环境，或回传 MD 轨迹  
4. 虚筛按 `candidate_ranking/job_sheet.json` 外部执行后回调  

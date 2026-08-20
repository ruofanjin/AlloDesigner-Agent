# GLP1 Allo stepwise 自包含文件清单

本文件中的相对路径都以 allo_stepwise 为根。该目录可以整体复制到目标服务器；父级 glp1_repro 不再是正式运行依赖。

## 1. 必需运行文件

| 路径 | 用途 |
|---|---|
| README.md | 自包含包入口和分步命令 |
| docs/REVIEWER_REPRODUCTION_GUIDE.md | 审稿人部署、执行、缺口与验收说明 |
| docs/AUTONOMOUS_ALLOSTERIC_POCKET_AGENT_PROMPT.md | 自主口袋证据gate、0–3候选选择、多分支MSA/构象富集和继续/停止决策Prompt |
| scripts/run_stepwise_allo.py | 唯一正式 stepwise runner |
| commands/00_check_environment.sh | strict preflight；缺 ColabFold、fpocket、Python 包或核心输入时非零退出 |
| commands/00_plan.sh | 路径审计和阶段计划；默认不要求未打包的完整 Step 3 历史证据 |
| commands/01_audit_step3_handoff.sh | 可选完整 Step 3 历史证据审计 |
| commands/02–13 | MSA、预测命令生成、评价、投票和 final 阶段 |
| configs/stepwise_glp1_allo.yaml | 可移植入口配置；root=auto |
| configs/stepwise/*.yaml | 分阶段参数和输入输出契约 |
| inputs/6x18_chianR_R.a3m | 主输入 MSA |
| inputs/6x18_MODEL_0.pdb | 491-aa query/reference PDB |
| inputs/glp1_historical_holo_cluster_mapped_residues.csv | 冻结的 14-residue downstream handoff |
| inputs/glp1-deepallo-score-residue_probabilities_top_7.csv | 历史 DeepAllo top-7 残基频率证据 |
| inputs/glp1-plb-score-residue_probabilities_top_7.csv | 历史 PLB top-7 残基频率证据 |
| src/af_claseq/pipeline/sequence_recompile.py | voting 后的 prediction/control MSA 重编译 |
| src/af_claseq/utils/sequence_processing.py | A3M/PDB 序列读取 |
| src/af_claseq/utils/logging_utils.py | sequence_processing 日志依赖 |
| environment.yml | core-eval Conda 环境；不包含 ColabFold/JAX 或 fpocket |
| workdir/ | 唯一运行输出根；clean bundle仅保留README |
| generated/ | 目标服务器临时ColabFold命令输出根；clean bundle不含继承的shell |

## 2. 核心输入 SHA-256

| 文件 | SHA-256 |
|---|---|
| inputs/6x18_chianR_R.a3m | 27deb4e6de2eb2311912a29918af7d88043096d603edd589f662fda5f4b8028a |
| inputs/6x18_MODEL_0.pdb | dd4ad9e7d23dcdb38fdf790157c2f522e20e00fb7baf35eee228fb7463e0c999 |
| inputs/glp1_historical_holo_cluster_mapped_residues.csv | 0213fabe2b7eb965b4756ab8f0278bc76164e3458c20ede97028066030305354 |
| inputs/glp1-deepallo-score-residue_probabilities_top_7.csv | c4d5cdedb3ccd42ec7737b987500329d4141a9a6a00b1fedf707e00fb3e6edc0 |
| inputs/glp1-plb-score-residue_probabilities_top_7.csv | 6f3fb69adc352e99cbc09b6b85525141e78fc31779728314658ffbb79568d67a |

commands/00_check_environment.sh 会逐项验证这些 hash。

## 3. 可选历史证据

evidence/step3_historical 当前只包含布局说明。完整运行 commands/01_audit_step3_handoff.sh 前，必须按 evidence/step3_historical/README.md 提供：

- 50 个 PocketMiner/AlloDesigner prediction arrays；
- structure NPY 和 491-residue binary label；
- Iteration 1 的 10 份 candidate distance、DeepAllo 和 PLB CSV；
- 原始专家 handoff、5VEX cluster evidence 和 residue mapping pickle。

缺少这些文件不影响冻结 14-residue handoff 后的 MSA、构象生成和评价，但不能声称重新复现了 Step 3 discovery。

## 4. 非运行材料

| 路径 | 处理 |
|---|---|
| source_snapshot/ | 历史算法考古；含其他蛋白和旧绝对路径，禁止作为正式入口 |
| commands/99_historical_project_glp1_colabfold.sh | 永久禁用的历史命令记录 |
| generated/README.md | 说明目标服务器必须按阶段重新生成ColabFold命令 |

父级 glp1_repro 中保留的 legacy_generated_commands、legacy_case_scripts、figures、legacy configs、full-pipeline scripts、重复apo PDB和完整上游AF-ClaSeq源码都不是本stepwise runner的运行依赖。

## 5. 外部软件

必须另外部署：

- ColabFold 1.5.5 历史 profile及 AlphaFold 参数；
- fpocket 4.0；
- 与 ColabFold 匹配的 GPU、CUDA/JAX 环境。

可通过 PYTHON_BIN、COLABFOLD_BIN 和 FPOCKET_BIN 覆盖目标服务器可执行路径。完整 Step 3 corrected rerun 还需要未随包提供的 PocketMiner、ProtBERT、MTL checkpoint 和 AutoGluon predictor。

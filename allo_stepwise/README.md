# GLP1 Allo stepwise 自包含复现包

本目录现在是正式运行根，可以整体复制到另一台服务器。运行代码不再依赖父级 glp1_repro 中的 configs、inputs、src、environment.yml 或 workdir。

当前科学边界仍是：

> 可以从已提供 A3M 和冻结的 14-residue 历史专家 handoff 开始，运行 MSA 分组、ColabFold 构象生成、fpocket 距离评价、M-fold、投票和 final 评价。原始 MSA 搜索、完整 Step 3 discovery/DeepAllo/PLB 重算，以及最终候选构象验证仍不是自包含实现。

Step 3 的历史处理脚本和预计算结果确实存在于 `source_snapshot/` 及原 GLP1 case；当前缺少的是参数化、覆盖全部 10 个 shuffle 且严格验收的正式执行入口。专家最终选择作为 Step 3 计算后的独立 gate 处理。

计算性 Step 3 的最终产物就是 `inputs/glp1-deepallo-score-residue_probabilities_top_7.csv` 和 `inputs/glp1-plb-score-residue_probabilities_top_7.csv` 两份独立指标表；候选簇、距离和簇级评分只作为可追溯中间结果。

完整部署、输入、人工先验、历史兼容、候选评价、缺口和清理清单见 docs/REVIEWER_REPRODUCTION_GUIDE.md。
将人工 gate 扩展为文献/结构/多工具自主证据门、选择 0–3 个候选口袋并分支富集的
可复制 Prompt 见 docs/AUTONOMOUS_ALLOSTERIC_POCKET_AGENT_PROMPT.md。

## 1. 自包含目录

    allo_stepwise/
    ├── README.md
    ├── MANIFEST.md
    ├── environment.yml
    ├── commands/
    │   ├── 00_check_environment.sh
    │   ├── 00_plan.sh
    │   ├── 01_audit_step3_handoff.sh
    │   ├── 02_prepare_iteration_input.sh
    │   ├── 03_generate_iteration_msas.sh
    │   ├── 04_write_iteration_colabfold_commands.sh
    │   ├── 05_iteration_metric_stack.sh
    │   ├── 06_select_iteration_msa.sh
    │   ├── 07_combine_iterations.sh
    │   ├── 08_prepare_mfold_msas.sh
    │   ├── 09_write_mfold_colabfold_commands.sh
    │   ├── 10_sampling_metric_stack.sh
    │   ├── 11_vote_and_recompile.sh
    │   ├── 12_write_final_colabfold_commands.sh
    │   └── 13_final_metric_stack.sh
    ├── configs/
    ├── inputs/
    ├── src/
    ├── docs/
    ├── evidence/step3_historical/
    ├── generated/
    ├── scripts/
    ├── source_snapshot/
    └── workdir/

正式 runner 是 scripts/run_stepwise_allo.py。source_snapshot 和 commands/99_historical_project_glp1_colabfold.sh 只用于 provenance，不得执行。

所有运行输出只允许写入：

    workdir/
    generated/

## 2. 配置与输入

configs/stepwise_glp1_allo.yaml 使用 root: auto，由 runner 根据自身位置确定包根，不需要为目标服务器修改绝对路径。

核心输入：

| 路径 | 作用 |
|---|---|
| inputs/6x18_chianR_R.a3m | 已提供的原始 GLP1 A3M |
| inputs/6x18_MODEL_0.pdb | 491-aa query PDB |
| inputs/glp1_historical_holo_cluster_mapped_residues.csv | 冻结的 14 个评价残基 |
| inputs/glp1-deepallo-score-residue_probabilities_top_7.csv | DeepAllo历史频率证据 |
| inputs/glp1-plb-score-residue_probabilities_top_7.csv | PLB历史频率证据 |

输入 hash 见 MANIFEST.md，并由 strict preflight 自动验证。

关键历史参数：

| 阶段 | 参数 |
|---|---|
| coverage | 0.8，历史物理输出986 records |
| Iteration | seed42，10 shuffles，每组16 |
| 富集 | Iteration 1–2最低20%，以后最低10% |
| M-fold source | Iteration 1–5，min_distance严格小于5 Å，历史759条 |
| M-fold | seed43，group size20，37 initial、37 samplings |
| residues | 354、355、357、358、365、369、410–417 |
| DBSCAN | eps6 Å，min_samples2 |
| voting | clean round_1、focused 20 bins |
| recompile | 历史 bins3/4 |

## 3. 部署

Core环境：

    cd /path/to/allo_stepwise
    conda env create -f environment.yml
    conda activate glp1_allo_core

ColabFold和fpocket应分别部署。目标服务器路径可通过环境变量覆盖：

    export PYTHON_BIN=python
    export COLABFOLD_BIN=/path/to/colabfold_batch
    export FPOCKET_BIN=/path/to/fpocket

严格检查：

    ./commands/00_check_environment.sh

该命令在缺少Python包、ColabFold、fpocket、核心输入或hash错误时非零退出。只做代码/输入审计、尚未加载外部程序时可用：

    ./commands/00_check_environment.sh --allow-missing-external

## 4. Step 3 两种使用方式

默认 frozen-handoff 模式只消费 inputs 下三张证据CSV，不声称重跑PocketMiner、DeepAllo或PLB：

    ./commands/00_plan.sh

00_plan 默认只做自包含路径审计和计划打印，不再因目标服务器没有原历史目录而失败。

完整历史证据与冻结专家 handoff 的只读审计是可选项。该命令不执行 Step 3 计算；先按 evidence/step3_historical/README.md 填充全部文件，再运行：

    ./commands/01_audit_step3_handoff.sh

或：

    RUN_STEP3_AUDIT=1 ./commands/00_plan.sh

## 5. Iterative shuffling

首次准备：

    ./commands/02_prepare_iteration_input.sh

每轮 N=1..7：

    ./commands/03_generate_iteration_msas.sh N
    ./commands/04_write_iteration_colabfold_commands.sh N
    # 执行 generated/iteration_N_colabfold_commands.sh 并等待10个shuffle完成
    RUN_FPOCKET=1 ./commands/05_iteration_metric_stack.sh N
    ./commands/06_select_iteration_msa.sh N

Iteration 1–7 的历史 group A3M 已经逐记录核验一致。历史 combined unique counts 为852、723、446、234、119、82、68；但使用当前精确 group-directory 匹配后，Iteration 1预期为857而不是历史852。不能把 corrected 结果与 historical结果混用。

## 6. M-fold

    ./commands/07_combine_iterations.sh
    ./commands/08_prepare_mfold_msas.sh
    ./commands/09_write_mfold_colabfold_commands.sh
    # 执行 generated/mfold_colabfold_commands.sh
    RUN_FPOCKET=1 ./commands/10_sampling_metric_stack.sh

历史预期为759条source sequences和1,333个sampling group metrics。voting配置现在直接固定到 round_1/02_sampling，不再扫描父目录中的其他round。

## 7. Voting和final

    ./commands/11_vote_and_recompile.sh
    ./commands/12_write_final_colabfold_commands.sh
    # 执行 generated/final_colabfold_commands.sh
    RUN_FPOCKET=1 ./commands/13_final_metric_stack.sh

当前13只生成每个prediction/control PDB的平均口袋距离。它不会自动生成可信的final candidate ranking，也不检查pLDDT、pTM、PAE、构象聚类或prediction/control统计。

## 8. 关键失败策略

- 05、10、13只有设置RUN_FPOCKET=1才真正执行fpocket。
- 不要复用来源不明的workdir；每个复现run应从空目录开始。
- generated当前为空；迁移前的11个旧脚本已移到父级legacy_generated_commands，目标机必须重新生成。
- 任一预测、sampling或CSV缺失时，当前runner仍有部分SKIP路径；必须按复现指南的expected counts人工或自动验齐。
- historical replay和corrected rerun必须使用不同run目录和manifest。

## 9. 当前未完成项

仍未自包含：

- 从canonical sequence搜索原始MSA；
- PocketMiner/AlloDesigner、ProtBERT、DeepAllo和AutoGluon模型；
- 完整Step 3原始证据；
- expert_decision.yaml和bin_decision.yaml；
- final_candidate_conformations.csv及代表PDB；
- lockfile、容器digest、全局SHA256SUMS和golden tests。

这些不是目录迁移能够替代的科学输入。P0–P2补充顺序及reviewer-ready验收标准见复现指南。

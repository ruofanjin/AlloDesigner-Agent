# GLP1 变构口袋构象流程：审稿人复现执行说明与缺口审计

版本日期：2026-08-10

适用目录：allo_stepwise（自包含运行根）

## 0. 结论先行

当前代码包的准确状态是：

> allo_stepwise 已可整体复制到独立服务器，并从已提供 A3M 和冻结专家 handoff 开始执行下游流程；它仍不是从 canonical sequence、原始 MSA 搜索、Step 3 discovery 到最终候选确认的全链自包含包。


已经确认可精确重现的部分：

- 给定现有 A3M 和上一轮历史 combined A3M，coverage 过滤、seed 42 的 Iteration 1–7 分组，共 2,190 个 group A3M，与历史逐文件、逐记录一致。
- 给定历史 759 条 M-fold 输入，seed 43 的 37 个 initial groups 和 1,333 个 leave-one-out sampling group A3M，与历史逐文件、逐记录一致。
- 在只读取 round_1 的前提下，20-bin focused voting 的 759 行结果及原始 votes 与历史一致。

尚不能由正式 runner 一键复现或尚未实现的部分：

- 从 GLP1 canonical sequence 重新搜索得到原始 A3M。
- 从 Iteration 1 构象参数化执行候选簇构建、DeepAllo 和 PLB。相关历史处理代码及历史结果已经存在，但尚未整理成跨服务器、fail-closed 的正式命令。
- 专家选择尚未形成有签名、有理由、有输入 hash 的独立人工 gate。
- 历史数值完全兼容的 fpocket group 匹配。
- 独立、可审核的最终候选构象筛选、排序、聚类、置信度过滤和导出。
- ColabFold/Step 3 环境锁、模型与数据库 manifest、阶段完整性 barrier、golden tests、容器和结果归档。

因此，审稿人交付前必须先选择下列复现声明之一。

本文将“计算性 Step 3”明确限定为：从 Iteration 1 的 620 个构象及其 fpocket
结果出发，结合 PocketMiner/AlloDesigner 阳性残基，生成候选残基簇、候选簇到
fpocket 的距离、DeepAllo/PLB 簇级分数及各自的 top-k 残基频率。候选簇、距离和
簇级分数是可审核的中间产物；Step 3 的两个最终指标产物明确限定为 DeepAllo
top-7 残基频率表和 PLB top-7 残基频率表，其冻结参考副本位于 `inputs/`。专家对
候选口袋的最终批准属于紧随其后的人工 gate，本节不把它算入 Step 3 计算本身。

| 模式 | 目的 | 可以声称什么 | 必须提供什么 |
|---|---|---|---|
| historical_replay | 复核论文中既有结果 | 按冻结的历史 Step 3 证据重放下游流程 | 预计算 Step 3 全证据、历史选择清单、历史 bug 说明、golden outputs |
| corrected_rerun | 用修正代码获得新结果 | 精确 group 匹配和修正索引下的重新分析 | 重新运行全部下游并生成新的结果、统计、hash 和版本号 |
| de_novo_full | 从 canonical sequence 端到端重建 | 包括原始 MSA 搜索和 Step 3 模型推理 | 数据库版本、搜索参数、全部模型、权重、预处理代码、专家 gate |

historical_replay 与 corrected_rerun 的结果不能混称为同一套“精确复现”。

## 1. 流程边界和阶段图

当前正式 runner 的实际链路如下。

| 阶段 | 主要输入 | 主要输出 | 当前状态 |
|---|---|---|---|
| 原始 MSA 搜索 | GLP1 canonical sequence、序列数据库 | 原始 A3M | 未提供 |
| 02 coverage 过滤 | 现有 A3M、参考 PDB query | filtered_sequences.a3m | 已实现 |
| 03 Iteration 分组 | filtered 或上一轮 combined A3M | 10 个 shuffle 下的 group A3M | 已实现并核验 |
| 04 ColabFold | group A3M、AF2 参数 | 每组预测 PDB | 只生成命令，目标机环境未锁 |
| Step 3 计算 | Iteration 1 PDB、PocketMiner/AlloDesigner labels、fpocket、DeepAllo、PLB | 最终交付两份独立的 DeepAllo/PLB top-7 残基频率排名表；同时保存候选簇与簇级分数作为审计中间件 | 历史代码与结果存在；runner 尚未参数化执行 |
| 专家 gate | Step 3 评分证据、5VEX 结构先验与 mapping | 批准的候选口袋残基集 | 与 Step 3 计算分离；当前只有冻结历史 handoff |
| 05 结构评价 | PDB、fpocket、冻结的 14 residues | group 平均 pocket distance | 已实现，但有兼容性和完整性风险 |
| 06 Iteration 富集 | 每 shuffle 的距离 CSV | 下一轮 combined A3M | 已实现 |
| 07 M-fold 汇总 | Iteration 1–5 指标与序列 | 759 条 source MSA | 已实现 |
| 08 M-fold 拆分 | 759 条 source MSA | 37 initial、1,333 sampling A3M | 已实现并核验 |
| 09–10 预测与评价 | sampling A3M | 1,333 行 sampling metric | 预测外部执行；评价已实现 |
| 11 voting/recompile | sampling metric、sampling A3M | voting、prediction/control MSA | 已实现；配置已固定只读取 round_1/02_sampling |
| 12–13 final | prediction/control MSA、PDB | 各 PDB 平均距离 | 只到距离表，没有候选导出 |

Step 3 计算与随后的专家 gate 应插在 Iteration 1 预测和 Iteration 1 评价/筛选之间。当前命令编号 04、05、06 之间尚没有真正的 Step 3 执行命令或人工批准 barrier。

对无可用人工先验的新靶点，可按
`docs/AUTONOMOUS_ALLOSTERIC_POCKET_AGENT_PROMPT.md` 实施文献、同源结构、几何/配体可结合性、
模型集合持续性、变构通信和进化证据的自主 gate。该 gate 输出是 agent decision，
不能伪称为人类 expert approval；当前 runner 也尚未实现该 Prompt 所需的多分支编排。

## 2. 输入契约

### 2.1 核心输入

| 输入 | 当前用途 | 当前 SHA-256 |
|---|---|---|
| inputs/6x18_chianR_R.a3m | coverage 过滤及全部 MSA 分组 | 27deb4e6de2eb2311912a29918af7d88043096d603edd589f662fda5f4b8028a |
| inputs/6x18_MODEL_0.pdb | 提取 query 序列并前置到 group A3M | dd4ad9e7d23dcdb38fdf790157c2f522e20e00fb7baf35eee228fb7463e0c999 |
| historical_handoff CSV | 14 个冻结残基 | 0213fabe2b7eb965b4756ab8f0278bc76164e3458c20ede97028066030305354 |
| inputs/glp1-deepallo-score-residue_probabilities_top_7.csv | Step 3 DeepAllo最终指标的冻结参考 | c4d5cdedb3ccd42ec7737b987500329d4141a9a6a00b1fedf707e00fb3e6edc0 |
| inputs/glp1-plb-score-residue_probabilities_top_7.csv | Step 3 PLB最终指标的冻结参考 | 6f3fb69adc352e99cbc09b6b85525141e78fc31779728314658ffbb79568d67a |

原始 A3M 的重要兼容行为：

- 物理记录数为 7,483，unique headers 为 7,392。
- 有 75 个重复 header，其中 74 个对应冲突序列。
- runner 采用字典的 last-write-wins，而不是 first-write-wins。
- coverage 过滤后为 985 个 unique candidates；文件物理写入前置 query 后共 986 条记录，后续再按 header 折叠。

这项行为必须写入输入规范并由 golden test 锁定，否则采用普通去重方式会得到不同 MSA。

### 2.2 序列与残基编号

A3M query 与 PDB 提取序列当前均为 491 aa，逐位一致，但代码没有强制验证。文件名保留 chainR，预测结构中实际链标识可为 chain A；冻结的 354、355、357、358、365、369、410–417 是该 491-aa construct 的 PDB residue number。

正式交付还必须增加：

- canonical FASTA；
- construct 与 UniProt、PDB accession、chain、resseq、icode 的映射表；
- N/C 端标签、截短或突变说明；
- preflight equality check；
- 所有专家残基的 chain-aware 标识。

### 2.3 historical_replay 需要本地打包的 Step 3 证据

step3-audit 现在只引用包内 evidence/step3_historical 相对路径，但这些完整证据尚未填充。以下历史证据总量很小，应直接随包附带：

- 10 张原始 pocket-distance CSV，约 0.42 MB；
- 10 张 DeepAllo CSV，约 0.48 MB；
- 10 张 PLB CSV，约 2.45 MB；
- 50 个 PocketMiner prediction NPY，约 0.20 MB；
- structure NPY，约 1.3 MB；
- 491 行 label、5VEX evidence、完整 mapping、handoff 和专家决定文件。

historical_replay 不需要分发约 3.4 GB 的 DeepAllo 模型，只需分发可校验的预计算证据及其 SHA-256。corrected_rerun 或 de_novo_full 才需要模型权重。

### 2.4 Step 3 最终输出与排序契约

Step 3 成功的最终判据不是自动选出14个专家残基，而是重新得到以下两份独立指标表：

- `inputs/glp1-deepallo-score-residue_probabilities_top_7.csv`：114个唯一残基；
- `inputs/glp1-plb-score-residue_probabilities_top_7.csv`：108个唯一残基。

两者的历史schema都是 `residue_number,probability`。这里的 `probability` 是：先在
每个 `shuffle + group` 内按对应簇级分数降序选择top 7，再以全部620个group的
4,340个入选簇实例为分母，计算残基出现频率；它不是DeepAllo模型的原始概率，也
不是PLB概率。DeepAllo和PLB必须保持为两张独立排名表，不在Step 3内融合。

已核实包内两份CSV与历史case原文件逐字节一致，但历史文件的物理行顺序并未按
`probability` 降序排列。因此正式实现应同时满足：

1. 生成与冻结参考逐残基、逐数值一致的原始兼容表；`inputs/`只作只读golden
   reference，不得被运行覆盖。
2. Reviewer-facing排序视图按 `probability` 降序、`residue_number` 升序处理并写明
   `rank`；并列频率使用相同rank还是连续行号必须在manifest中固定。
3. 排序视图与历史兼容表只允许改变行序及新增派生列，不能改变残基集合和频率值。

## 3. 软件、模型和硬件部署

### 3.1 建议拆分三个环境

| profile | 组件 | 用途 |
|---|---|---|
| core-eval | Python、NumPy、pandas、PyYAML、Biopython、scikit-learn、SciPy、matplotlib、fpocket 4.0 | MSA、结构后处理、距离、投票与重编译 |
| colabfold-gpu | ColabFold 1.5.5 指定 commit、JAX/CUDA、AlphaFold2 参数 | 全部构象预测 |
| step3-corrected | PyTorch、Transformers、AutoGluon、XGBoost、ProtBERT、MTL checkpoint、PocketMiner/AlloDesigner | 重新生成 Step 3 证据 |

environment.yml 已移动到包根，移除本机 prefix，并固定审计机器上的 core-eval 版本；活动wrapper默认使用 PATH中的python，也可用PYTHON_BIN覆盖。它仍不是conda-lock，且不包含ColabFold/JAX、fpocket或Step 3模型环境。

本机只读核验到的环境是：

| 组件 | 版本 |
|---|---|
| Python | 3.11.11 |
| NumPy | 1.26.4 |
| pandas | 2.2.3 |
| PyYAML | 6.0.2 |
| Biopython | 1.84 |
| scikit-learn | 1.4.0 |
| SciPy | 1.12.0 |
| matplotlib | 3.10.1 |
| joblib | 1.4.2 |
| PyTorch | 2.3.1+cu121 |
| Transformers | 4.39.3 |
| AutoGluon | 1.1.1 |
| XGBoost | 2.0.3 |
| fpocket | 4.0 |

这些只是“当前机器观测值”，不是已验证的最终 lock。AutoGluon 模型自己的 metadata 还显示 Python 3.11.9、AutoGluon 1.1.1、Torch 2.2.2+cu118，说明环境已经发生漂移。

### 3.2 ColabFold 历史配置

历史 config.json 给出的关键参数为：

- ColabFold 1.5.5；
- commit 64c8b2fe2ecf3199bc2d3c60b5da4b929a41086e；
- model type alphafold2_ptm；
- templates false；
- num_relax 0；
- rank_by plddt；
- max_seq 512；
- max_extra_seq 5120；
- num_recycle 3；
- use_dropout false；
- bfloat16 true；
- Iteration/M-fold：1 model、1 seed、random seed 42；
- final：5 models、8 seeds、random seed 0。

当前配置只编码了其中一部分，final 没有显式传 seed 0。正式交付应保存原 config.json、模型参数版本、权重下载方式、SHA-256 和许可说明。

现有 A3M 可以直接作为 ColabFold 输入，不要求审稿人重新运行数据库搜索。若论文声明从 GLP1 sequence 端到端生成原始 MSA，则还必须给出 MMseqs2/HHblits 命令、数据库 release/date、过滤参数和数据库许可。

### 3.3 Step 3 模型资产

需要先区分“历史算法代码存在”和“当前包已有可移植执行入口”。`source_snapshot/`
保留了 Step 3 的处理逻辑，但这些文件是一次性脚本快照：

| 快照 | 实际职责 | 当前限制 |
|---|---|---|
| `4_postgrasp_clustering_pocketminer_apo_dir_step3.py` | 对阳性残基 CA 做 DBSCAN 并写候选 cluster PDB | 当前激活 PCKS9/eps4.5，且循环从 shuffle 2 开始 |
| `5_calculte_group_cluster_fpocket_dcc_all_shuffle_step3.py` | 计算候选簇到最近 fpocket 的距离 | 当前激活 PCKS9/Iteration 8 路径 |
| `6_inference_case_pocketminer_cluster_to_deepallo_run.py` | 加载 ProtBERT、MTL checkpoint 和 AutoGluon，生成簇级 `deepallo_score` | 只硬编码 shuffle 10，并混用 PCKS9 序列与 GLP1 构象路径 |
| `6.1_calculate_apo_pocketminer_cluster_deepallo_score.py` | 对已有 DeepAllo CSV 按每个 group 取 top-k，汇总残基频率 | **不执行 DeepAllo 模型推理**；当前激活 PCKS9/eps4.5 |
| `7_plb_calculation_pocketminer_apo_dir_step3.py` | 按 cluster residue composition 的 Soga RA 值加和，生成簇级 `plb_score` | 循环 10 个 shuffle，但当前激活 PCKS9/eps4.5，缺文件会静默继续 |
| `7.1_calculate_apo_pocketminer_cluster_plb_score.py` | 对已有 PLB CSV 按每个 group 取 top-k，汇总残基频率 | 不计算原始 PLB；当前激活 PCKS9/eps4.5 |

因此，DeepAllo 和 PLB 的历史“处理代码”确实已经保存；缺少的是把这些逻辑改成
GLP1 参数化输入、覆盖全部 10 个 shuffle、严格检查完整性并记录 provenance 的
reviewer-runnable Step 3 命令。不能把 `6.1` 单独描述为 DeepAllo 计算入口，也不能
直接执行当前快照来覆盖 GLP1 历史结果。

corrected_rerun 至少需要：

- PocketMiner/AlloDesigner 的模型定义、50 个 checkpoint、结构预处理和推理入口；
- ProtBERT 模型与 tokenizer；
- MTL checkpoint；
- AutoGluon predictor 完整目录；
- 19 个 fpocket descriptor 的字段、次序、单位、缺失值策略；
- DeepAllo residue-to-token 映射规则；
- PLB 的 Soga RA 参数表和 cluster-size 处理规则。

当前外部资产观测值包括约 1.6 GB ProtBERT、约 1.6 GB MTL checkpoint 和约 259 MB AutoGluon bundle。必须用 per-file manifest 校验目录模型；只记录目录名不足以保证可复现。

历史 DeepAllo 有已知的 residue index 加一偏移。historical_replay 必须保留并标注；corrected_rerun 必须修正后全链重跑并生成新 fingerprint。

### 3.4 硬件和资源

当前主机为单张 RTX 3090 24 GB，历史计算日志合计约 25 GPU-hours，不含文件编译、fpocket 和调度等待。建议声明“已验证或保守最低 24 GB 单 GPU”，并预留：

- 3,640 个 ColabFold query/model 输出单元；
- Iteration 2,190；
- M-fold 1,370，其中 37 个 initial-split 预测没有当前下游消费者，可在非历史 QC 模式跳过；
- final 80；
- 每个独立 shuffle/sampling 目录可并行；
- 至少 50 GB 单次运行空间，建议 100 GB scratch；
- CPU 阶段包括 MSA 操作、fpocket、DBSCAN、距离、投票和结果汇总。

## 4. 本次已完成的自包含迁移

2026-08-10 已完成以下改造：

| 原问题 | 当前处理 |
|---|---|
| root写死父级本机路径 | configs使用root: auto；runner从scripts位置推导allo_stepwise根 |
| configs、inputs、src、environment和workdir在父级 | 最小必需文件已移动到allo_stepwise |
| wrapper从commands/../..寻找父级 | 14个活动wrapper统一以commands/..为包根 |
| 默认本机deepallo Python | 默认python，可用PYTHON_BIN覆盖 |
| fpocket和ColabFold路径硬编码 | 配置使用命令名，可用FPOCKET_BIN和COLABFOLD_BIN覆盖 |
| 00_plan强制外部Step 3 audit | 默认只运行路径审计和plan；完整audit改为显式可选 |
| Step 3证据配置为本机绝对路径 | 改为evidence/step3_historical包内布局 |
| voting扫描所有round_* | 配置固定到round_1/02_sampling |
| 环境检查缺程序仍exit 0 | 新strict preflight默认非零失败，并验证五个核心输入hash |

仍待完成的工程护栏：

- 迁移前11份generated脚本已移到父级legacy_generated_commands；目标机必须重新生成；
- 每个stage仍需原子stage_done manifest和expected-count强制barrier；
- 每次运行仍应使用run_id或input fingerprint隔离，禁止复用未知旧结果；
- strict preflight仍需扩展到ColabFold commit、fpocket版本、AF2参数hash、GPU/JAX和空输出目录；
- 完整Step 3 evidence尚未复制到evidence目录。

## 5. 目标机执行说明

以下命令可在整体复制allo_stepwise后直接用于frozen-handoff下游profile；它们仍不代表原始MSA搜索或Step 3 discovery已经自包含。

### 5.1 解包与校验

    cd /path/to/allo_stepwise
    conda env create -f environment.yml
    conda activate glp1_allo_core
    export COLABFOLD_BIN=/path/to/colabfold_batch
    export FPOCKET_BIN=/path/to/fpocket
    ./commands/00_check_environment.sh
    ./commands/00_plan.sh

当前strict preflight已自动检查：

- 七个core Python imports；
- ColabFold和fpocket可执行文件存在；
- 五个核心输入存在且SHA-256正确；
- root、workdir、generated和配置输出不越界；
- 冻结14-residue CSV可被plan读取。

正式reviewer运行前仍需人工或新增代码检查：A3M/PDB query完全一致、外部工具精确版本、ColabFold commit与AF2参数hash、GPU/JAX、空workdir、Step 3 evidence和selection fingerprint。

### 5.2 historical_replay 的 Step 3 审计

    ./commands/01_audit_step3_handoff.sh

该 wrapper 只调用 `run_stepwise_allo.py step3-audit`；它不调用 `source_snapshot/`
中的任何脚本。它是“冻结历史证据及其下游 handoff 的只读一致性审计”，不是
Step 3 计算命令。当前实际检查如下：

- 11 个配置路径存在；AlloDesigner prediction NPY 恰有 50 份；
- 6 张关键 CSV 的 SHA-256；
- AlloDesigner label CSV 为 491 行、其中 119 个阳性残基；
- DeepAllo/PLB top-7 表包含规定列，分别覆盖 114/108 个残基；
- candidate-distance、DeepAllo、PLB 三类历史 CSV 各有 10 份，合计行数分别为
  9,843、7,641、7,641；
- 冻结历史选择与包内选择是相同的 14-residue 集合，且是 AlloDesigner positives
  的子集并同时出现在两张 top-7 表中；
- 5VEX cluster evidence 中 `DCC < 10 A` 的集合恰为 clusters 8、9、14；
- 下游 active residue set 与冻结的 14 个残基一致；future output 路径没有越界。

因此，这个命令仍包含“历史专家 handoff 一致性”检查，超出了本文定义的、不含
专家选择的 Step 3 计算边界。若只想复核 `Iteration_1/pocketminer_cluster_deepallo_score/`
的生成，当前没有独立的 `step3-score-audit` 命令。

该命令明确**不会**：

- 运行 PocketMiner/AlloDesigner、DBSCAN、fpocket、DeepAllo 或 PLB；
- 生成候选 cluster、簇级分数、top-k 表或任何新输出；
- 重新计算 50 个 NPY 的均值、验证 NPY shape/hash，或读取 mapping pickle 内容；
- 检查 10 份 candidate/DeepAllo/PLB 表的 candidate key 一一对应；
- 重算 `min_distance < 10` 过滤、每 group top 7、频率分母或 score 排序；
- 执行新的人工选择，生成或验证 `expert_decision.yaml`。

配置中的 `expected_group_count_per_shuffle: 62` 当前也没有被 runner 使用。故即使
审计退出 0，也只能说明上述有限的路径、schema、计数、hash 和集合关系一致，不能
声称已经重算 Step 3。

该命令不是默认 preflight。当前 `evidence/step3_historical/` 只有布局说明，完整证据
尚未填充，所以命令会非零退出；配置中的 `evidence_bundled: false` 目前不会让 runner
自动跳过。默认 `python` 必须含 core 依赖，也可显式运行：

    PYTHON_BIN=/path/to/core-env/bin/python ./commands/01_audit_step3_handoff.sh

未打包完整历史证据时，frozen-handoff 下游 profile 应把该审计记录为 `NOT RUN`。

### 5.3 Iterative shuffling

    ./commands/02_prepare_iteration_input.sh

对 N 从 1 到 7，依次执行：

    ./commands/03_generate_iteration_msas.sh N
    ./commands/04_write_iteration_colabfold_commands.sh N
    # 在 colabfold-gpu 环境执行生成的本轮命令并等待全部成功
    RUN_FPOCKET=1 ./commands/05_iteration_metric_stack.sh N
    ./commands/06_select_iteration_msa.sh N

严格 barrier：

| Iteration | 输入 unique candidates | 每 shuffle groups | 10 shuffles 预测单元 | 历史 combined unique |
|---|---:|---:|---:|---:|
| 1 | 985 | 62 | 620 | 852 |
| 2 | 852 | 54 | 540 | 723 |
| 3 | 723 | 46 | 460 | 446 |
| 4 | 446 | 28 | 280 | 234 |
| 5 | 234 | 15 | 150 | 119 |
| 6 | 119 | 8 | 80 | 82 |
| 7 | 82 | 6 | 60 | 68 |

表中的 combined 数是 historical_replay 预期值。使用当前精确 group 匹配逻辑时，Iteration 1 已知会得到 857 而不是 852，因此 corrected_rerun 必须生成自己的新基准，不能继续套用该表。

### 5.4 M-fold sampling

    ./commands/07_combine_iterations.sh
    ./commands/08_prepare_mfold_msas.sh
    ./commands/09_write_mfold_colabfold_commands.sh
    # 执行 sampling_1 至 sampling_37 的 ColabFold 命令
    RUN_FPOCKET=1 ./commands/10_sampling_metric_stack.sh

historical_replay 预期：

- Iteration 1–5 中 group mean distance 严格小于 5 Å；
- 去重后 759 条 source sequences；
- 37 个 initial groups；
- 37 个 leave-one-out samplings；
- 36 个 sampling 各 36 groups，1 个 sampling 有 37 groups；
- 总计 1,333 个 sampling group metrics。

当前 09 还会为 37 个 initial groups 预测，但后续没有消费者。历史严格重放可保留；节省计算的 corrected profile 应明确跳过并记录。

### 5.5 Voting、recompile 和 final

voting输入现已固定到配置指定的round_1/02_sampling，不再扫描父级其他round。仍应使用干净workdir，避免同一round内的旧sampling输出。

    ./commands/11_vote_and_recompile.sh
    ./commands/12_write_final_colabfold_commands.sh
    # 执行 prediction/control final ColabFold
    RUN_FPOCKET=1 ./commands/13_final_metric_stack.sh

historical_replay 的 clean round_1 应得到：

- 1,333 sampling A3M/metric pairs；
- 759 个 sequence headers；
- 20 个由观测 min/max 定义的等宽 focused bins；
- 历史 min 3.5193333333 Å，max 11.298 Å；
- bins 3/4 约对应 4.2972 到 5.0751 Å；
- query 的 selected bin 为 7，Vote_Count 191，Total_Votes 1,370；
- target bins 3/4 最终只有 5 条 homolog，加入 query 后为 6-record A3M；
- prediction 40 PDB，control 40 PDB。

target bins 3/4 是第二个人工/事后选择点，必须给出预注册依据和批准记录。当前代码还允许观测 max 被 np.digitize 分到 bin 21，应明确边界规则并增加测试。

## 6. 构象评价的精确定义

当前“口袋距离”不是 fpocket score，定义如下：

1. 对每个 ColabFold PDB 运行 fpocket。
2. 对 pockets 目录下每个 pocket PDB 的所有 atom 坐标取算术均值，得到 pocket center。
3. 对批准残基的 CA 坐标做 DBSCAN，eps 6 Å、min_samples 2。
4. 每个残基簇写出完整 residue atoms。
5. 对完整 residue atoms 取算术均值，得到 cluster center。
6. 对每个 cluster center 计算到同一构象任意 pocket center 的最小欧氏距离。
7. 单个距离先四舍五入到 0.001 Å。
8. group 或 final PDB 的 score 是所有 residue clusters 距离的不加权均值。

当前评价没有使用：

- fpocket score、druggability、volume 或 pocket rank；
- pLDDT、pTM、PAE；
- 结构冲突、跨膜拓扑和链完整性；
- RMSD、TM-score 或构象多样性；
- 口袋稳定性或动力学；
- prediction 相对 control 的预注册统计检验。

因此平均 pocket distance 只能作为候选富集指标，不能单独证明获得了可信的变构构象。

## 7. Step 3 计算与后续专家先验

历史 Step 3 的计算性链条为：

1. 50 个 PocketMiner/AlloDesigner prediction arrays 取均值。
2. 阈值大于等于 0.7 得到 119 个 positives。
3. 对 Iteration 1 构象中的 positives CA 做 DBSCAN。
4. 候选簇到 fpocket center 的 DCC 严格小于 10 Å。
5. DeepAllo 使用 pocket residue ProtBERT embedding 均值加 19 个 fpocket descriptors。
6. PLB 使用 cluster residue composition 的 Soga RA 加和。
7. 每个 shuffle/group 各取 DeepAllo top 7 和 PLB top 7。

以上第 1–7 步构成本文定义的 Step 3 计算，目标输出为
`Iteration_1/pocketminer_cluster_deepallo_score/` 及其上游 candidate-distance/cluster
证据。随后是独立人工决策：

8. 专家引入 5VEX holo 结构、5VEX→6X18 mapping 与结构审查。
9. 最终选择 5VEX clusters 8、9、14，冻结为 14 个 residues。
10. 更下游又人工固定 focused bins 3/4。

应增加两个不可绕过的人工 gate。

expert_decision.yaml 至少包含：

| 字段 | 内容 |
|---|---|
| decision_id | 稳定 ID |
| mode | historical_replay 或 corrected_rerun |
| experts | 姓名或匿名角色、领域资质 |
| date | ISO 日期 |
| evidence | 每个输入文件 SHA-256 |
| include_clusters | 8、9、14 或新选择 |
| exclude_clusters | 被排除项目及理由 |
| selected_residues | chain、resseq、icode、construct index |
| rationale | 5VEX、DeepAllo、PLB、几何和生物学依据 |
| conflicts | 是否使用 holo 先验及其循环性风险 |
| approval | 签名或不可变确认记录 |

bin_decision.yaml 至少记录 binning 数据范围、边界、目标 bins、选择依据、批准人和输入 hash。

必须明确：该历史流程使用 5VEX holo-derived residue set 定义后续评价目标，因此属于 holo-guided enrichment，不是完全盲目的 de novo allosteric-pocket discovery。

## 8. 历史兼容与科学修正

### 8.1 group 匹配 bug

历史距离脚本使用 substring 匹配 group_id。例如 group_2 可能错误命中 group_24。当前 runner 使用完整 model stem 精确匹配，科学上更合理，但不再数值复现历史。

只读重算 Iteration 1 显示：

- 1,494 个下游 cluster distances 中 71 个改变；
- 10 个 shuffles 中 7 个的最低 20% group 集合改变；
- 历史 combined 为 852，修正后为 857。

必须实现显式模式开关，分别输出到不同 run_id，结果表和论文说明中不得混用。

### 8.2 其他兼容风险

- 历史 DeepAllo residue/token mapping 有加一偏移。
- 历史 final seed 为 0，当前 runner 未显式传入。
- 新 runner 对 control 使用 seed 42，而历史 control 来自未固定 random.sample，序列不一致。
- 距离先保留 3 位小数，再经过 quantile、严格小于 5 Å 和动态 bins，会产生级联差异。
- fpocket/JAX/GPU 版本微差可能改变阈值边界附近的序列选择。
- 输出 CSV schema 和文件名与历史脚本不完全一致，应按语义和数值验收，而不是要求旧文件逐字节相同。

## 9. 当前已有候选构象的评价

历史外部目录中有 40 个 prediction 和 40 个 control PDB，但没有打包到本复现目录。prediction 中按平均 pocket distance 排名前八且小于 5 Å 的待审候选如下。

| 历史顺位 | model/seed | distance Å | global pLDDT | 14-residue pLDDT | pTM |
|---:|---|---:|---:|---:|---:|
| 28 | model 1 / seed 2 | 3.7815 | 50.78 | 47.32 | 0.400 |
| 34 | model 5 / seed 7 | 3.8720 | 49.24 | 48.08 | 0.350 |
| 18 | model 5 / seed 1 | 4.4450 | 53.47 | 53.78 | 0.430 |
| 8 | model 3 / seed 4 | 4.6570 | 58.53 | 53.19 | 0.480 |
| 33 | model 3 / seed 7 | 4.8155 | 49.74 | 48.99 | 0.320 |
| 14 | model 4 / seed 3 | 4.9100 | 54.77 | 51.16 | 0.450 |
| 32 | model 5 / seed 6 | 4.9940 | 50.18 | 51.37 | 0.360 |
| 40 | model 5 / seed 0 | 4.9995 | 46.61 | 43.57 | 0.300 |

前两名的局部 pLDDT 很低，不能仅凭距离称为可信构象。若在现有结果中优先人工检查，rank 18 和 rank 8 在距离与置信度之间相对更平衡，但仍只是待审候选。

历史 prediction 的均值约 5.923 Å、中位数约 5.928 Å、8/40 小于 5 Å；control 的均值约 6.143 Å、中位数约 6.248 Å、7/40 小于 5 Å。探索性的单侧 Mann–Whitney 检验约为 p=0.204，而且 40 个模型不是独立生物学重复。因此当前证据没有显示强的 prediction/control 分离。

最终交付至少应生成：

- final_candidate_conformations.csv；
- candidates/ 下的代表性 PDB；
- 每个 PDB 的 SHA-256；
- ColabFold rank/model/seed；
- distance、fpocket score、druggability、volume；
- global/local pLDDT、pTM、PAE；
- 对 apo/holo 参考的 RMSD/TM-score；
- 构象聚类 ID 和代表选择规则；
- prediction/control 统计和限制说明；
- 专家最终 approve/reject/rationale。

## 10. 当前代码的完整性风险

以下问题可能导致命令成功退出但结果不完整或被旧文件污染：

- 缺失 PDB、fpocket 输出或 CSV 时多处只打印 SKIP。
- 未设置 RUN_FPOCKET=1 时会 dry-run 后继续消费可能存在的旧输出。
- combine-sampling-metrics 只找到一个 sampling CSV 也可成功。
- copy-pdbs、cluster-residues、recompile 不清理旧文件。
- 如果本次无 rows，旧 CSV 可能保留。
- residue lookup 只按整数 resseq，不限制 chain 或 icode。
- cluster 目录没有 residue-set fingerprint。
- M-fold voting 扫描所有 round_*，可混入旧实验。
- recompile 在 combined source MSA 缺失时可静默回退原始 A3M。
- write-colabfold 的 stage all 不含 final。
- group A3M 目录中的 .shuf 会被 ColabFold 报为非 FASTA/A3M 文件。

Reviewer 版本必须改为 fail-closed：

- stage 启动前校验空目录或匹配 run_id；
- 所有 expected counts 不满足即非零退出；
- 每个输入和输出写 SHA-256；
- 原子写 stage_done.json；
- 内容包括命令、代码 commit、环境、模型、GPU、输入输出、计数和时间；
- selection 或配置 hash 改变时不得复用旧输出。

## 11. Golden checks

建议随包放置小型测试和完整 reference manifest。

### 11.1 历史文件 SHA-256

| 文件 | SHA-256 |
|---|---|
| filtered_sequences.a3m | b6bc27658a8173d77283236523649e5876891de51eb7757aa8a378fbf2f6595d |
| combined Iteration 1 | eafac04e5b6d88a1ecacd972668ef2330afd370155602619b4c9644174a3e47a |
| combined Iteration 2 | 009fc6fdf6bbeb7ca0dc831c98bf4ca2d32740f909da4f7d5e5cd95ddf3ac0e2 |
| combined Iteration 3 | 8129c06fdf98d9f794e3d0c39d3a9869dbd3e74da0bfddf4d8861b7bd14c7d34 |
| combined Iteration 4 | d2bfd9615bdeb2e3706db17c54ab33a13de5745fe8c9299df0982154813f12cc |
| combined Iteration 5 | 9d30e7017bd624a1158710bd9f732bd9db0258da732f808ac962388f5dd83a9f |
| combined Iteration 6 | e161065c8db5a0fcbe1be306cbc1439b457c3ec42eb6e5fc5ee2958618cb1693 |
| combined Iteration 7 | bcf3e106489ac3c4667cf8df116fc6bd25a39e432605afbced27eef6f2ef435d |
| combined all 759 | 0ca6d392238a1380e489cc95b4ac7284708a1684d6b4bba34c05570484a121f6 |

这些 hash 只适用于 historical_replay 的历史 metric 和浮点结果。

### 11.2 必需测试

- 输入 A3M 重复 header 和 last-write-wins；
- PDB/A3M query equality；
- 2,190 个 Iteration group manifest；
- 37 initial 和 1,333 sampling group manifest；
- 119 positives、9,843 candidates、7,641 filtered candidates；
- 14 residues 的 chain-aware fingerprint；
- clean round_1 的 759 行 voting；
- fpocket fixture 的 pocket center、cluster center 和距离；
- group_2 与 group_24 的 legacy/corrected 双模式；
- bin 最小值、最大值和边界；
- 缺任一 sampling/PDB/CSV 必须失败；
- selection 变化、重跑和 stale-output 隔离；
- final 40 prediction 与 40 control 完整性。

## 12. 仍需补充的 reviewer-ready 清单

### P0：阻断交付

- 自包含 historical Step 3 evidence 或可运行 corrected Step 3。
- 明确 historical_replay/corrected_rerun 模式。
- 实现或明确隔离group substring的legacy/corrected模式，并阻止旧输出复用。
- 严格完整性 barrier。
- 锁定 ColabFold、fpocket 和 core environment。
- canonical sequence 与残基 mapping。
- expert_decision.yaml 和 bin_decision.yaml。
- final candidates 表、代表 PDB 和选择规则。
- SHA256SUMS、代码 commit/tag、许可证和第三方 notices。

### P1：科学可信度

- pLDDT/pTM/PAE 和结构完整性过滤。
- fpocket score、volume、druggability。
- 构象去冗余、聚类、RMSD/TM-score。
- prediction/control 的预注册统计。
- 阈值、量化和动态 bin 的敏感性分析。
- holo-guided 先验可能造成循环评价的限制说明。

### P2：工程质量

- conda-lock 或容器 digest。
- pytest、CI 和小型 golden fixture。
- SLURM 模板、资源与时长估计。
- 数据仓库 DOI、下载脚本和离线校验。
- 每阶段日志、provenance 和恢复说明。

## 13. 可删除、可归档和必须保留

本次自包含整理移动了最小必需文件，没有删除科学输入。父级legacy/provenance仍原地保留。

### 13.1 可直接删除或从交付包排除

| 路径 | 理由 | 恢复方式 |
|---|---|---|
| 父级legacy_generated_commands/*.sh | 11份迁移前临时产物嵌原服务器绝对路径，已移出运行包 | 如需溯源可保留，目标机重新生成 |
| scripts/__pycache__/ | Python缓存 | 自动重建 |
| src下各__pycache__/ | Python缓存 | 自动重建 |
| 父级inputs/6x18_chianR_covert_apo.pdb | 与父级ref文件字节相同，且未移入自包含包 | 若整理父级，仅保留ref文件 |

上述重复 PDB 的 SHA-256 均为 0ee56c821af690e95b1864239ecc3c032f045d548e7fd22a95dda13c0381b038。

### 13.2 提取 provenance 后可移出正式运行包

- commands/99_historical_project_glp1_colabfold.sh；
- source_snapshot/project_colabfold_batch.sh。

二者属于历史命令证据，与正式执行链重复。归档前应记录源路径、代码版本、文件 hash 和历史 config.json。

### 13.3 建议归入 legacy_provenance.tar.zst

- 包内 `source_snapshot/` 下与正式 runner 已有等价实现的其他一次性 Python；
- 父级legacy_case_scripts和figures；
- 父级configs/original及legacy configs；
- 父级full-pipeline scripts；
- 父级agent_task_spec.yaml，如审稿人不需要agent调度。

在新的参数化 Step 3 实现通过 golden test 之前，以下历史处理代码不能直接列入
“可删除”清单：`4_postgrasp_*_step3.py`、`5_calculte_*_step3.py`、`6_inference_*`、
`6.1_calculate_*deepallo*`、`7_plb_*` 和 `7.1_calculate_*plb*`。它们可以留在
`source_snapshot/`，也可以进入随交付提供的 provenance archive，但必须保留逐文件
hash、来源和职责说明；否则将丢失 Step 3 计算方法的直接代码证据。

这些脚本当前激活的仍可能是 PCKS9、CB1R 或 1HZB 路径，DeepAllo/PLB 脚本还
混用 GLP1 与 PCKS9。它们是算法与历史执行的 provenance，不是可直接运行的正式
入口，不能放在 reviewer runnable 命令区中冒充已参数化实现。

归档而非直接删除的原因是这些文件仍有 provenance 价值。建议同时生成 archive SHA-256 和逐文件 manifest。

### 13.4 必须保留

- scripts/run_stepwise_allo.py；
- commands/00_check_environment.sh、00_plan.sh和01–13；
- configs/stepwise_glp1_allo.yaml和configs/stepwise；
- 核心 A3M、PDB、三张当前证据 CSV；
- src/af_claseq/pipeline/sequence_recompile.py；
- src/af_claseq/utils/sequence_processing.py；
- src/af_claseq/utils/logging_utils.py；
- README、MANIFEST、environment.yml、commands/README和docs；
- evidence/step3_historical/README.md。

未来补齐后也必须保留lock、SHA256SUMS、LICENSE、NOTICE、tests和reference outputs。

## 14. 推荐交付目录

    allo_stepwise/
    ├── README.md
    ├── MANIFEST.md
    ├── environment.yml
    ├── LICENSE
    ├── NOTICE
    ├── CITATION.cff
    ├── SHA256SUMS
    ├── CODE_VERSION
    ├── commands/
    ├── configs/
    ├── inputs/
    │   ├── canonical.fasta
    │   ├── construct_mapping.csv
    │   ├── 6x18_chianR_R.a3m
    │   └── 6x18_MODEL_0.pdb
    ├── evidence/
    │   └── step3_historical/
    ├── scripts/
    ├── src/
    ├── docs/
    ├── decisions/
    │   ├── expert_decision.yaml
    │   └── bin_decision.yaml
    ├── locks/
    │   ├── core-eval.lock
    │   ├── colabfold-gpu.lock
    │   └── step3-corrected.lock
    ├── models/
    │   └── MODEL_MANIFEST.json
    ├── tests/
    ├── reference_outputs/
    ├── final_candidates/
    ├── generated/
    ├── workdir/
    └── legacy_provenance.tar.zst

大体积模型和 PDB 结果可放入 Zenodo、OSF 或机构仓库，交付包中保存 DOI、下载脚本、许可和 SHA-256。

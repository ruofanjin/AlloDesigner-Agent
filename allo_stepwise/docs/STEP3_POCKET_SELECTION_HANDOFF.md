# GLP1 Step 3 变构口袋选择交接规范

## 1. 文档目的

Step 3 位于 Iteration 1 构象生成之后、Iteration 1 的最终口袋距离评价和
Iteration 2 输入生成之前。它的职责不是继续筛选 MSA，而是从 Iteration 1
构象中形成候选变构口袋证据，供专家确认最终残基集合。确认后的集合随后固定
用于 Iteration 1 重评、Iteration 2-7、M-fold、sequence voting、recompile 和
最终 prediction/control 评价。

本文件只整理已经存在于原 GLP1 案例中的事实、数据契约和未来 agent 的实现
边界。当前复现 runner 不重新运行 DeepAllo、PLB、fpocket 或历史一次性脚本，
也不把专家判断改写成未经确认的自动打分公式。

## 2. 当前结论

原 GLP1 案例已经保存 Step 3 的计算性阶段：AlloDesigner 阳性残基、Iteration 1
候选残基簇、最近 fpocket 距离、DeepAllo 簇分数、PLB 簇分数，以及两种分数各自
按 group 取 top-k 后的残基出现频率。

此前 `run_stepwise_allo.py` 没有显式描述这条链，只直接读取 14 个历史残基做
后续几何评价。DeepAllo 和 PLB CSV 只是两个互斥的备选残基集，不能代表联合
排序或专家确认。现在 runner 新增的 `step3-audit` 只验证历史证据和下游 handoff；
它仍不执行 Step 3 计算。

专家选择属于人工 gate。原工程保存了 14-residue handoff 文件
`binding_sites_prediction/pocketminer_cluster/5vex/eps6/holo_cluster_for_msa.csv`，
但没有找到生成该文件的脚本、专家 rationale 或签署 manifest。其簇级证据表显示
5VEX clusters 8、9、14 是 16 个候选中仅有的 `DCC < 10 A` 集合；三簇 PLB 分别
为 6.367、3.492、13.282。Iteration 1 DeepAllo/PLB 频率表对这 14 个残基均有
支持，但精确的人工权重/排除理由没有记录，不能反推成纯数值公式的自动输出。

## 3. 只读证据根目录

原 GLP1 Iteration 1：

```text
/root/data1/data/move/ZYY/zyy/works/AF_ClaSeq/case/GPL1/6x18_chianR_R/
└── run/01_iterative_shuffling/Iteration_1/
```

AlloDesigner 阳性残基：

```text
/root/data1/data/move/ZYY/zyy/works2/AlloDesigner/Allo-PocketMiner/
└── case/GLP1/AlloDesigner_residue_probabilities_averge_0.7.csv
```

该 CSV 是 0/1 标签表。连续的 50-model PocketMiner 分数仍保存在：

```text
/root/data1/data/move/ZYY/zyy/works/PocketMiner-gvp/case/GLP1/5vex/
└── every_apo_predict/5vex_0_pred.npy ... 5vex_49_pred.npy

/root/data1/data/move/ZYY/zyy/works2/AlloDesigner/Allo-PocketMiner/data/case/GLP1/
└── 5vex_apo_model.npy
```

50 个 `(491,)` 分数数组取均值并按 `>= 0.7` 阈值化，可重建上述 491 行标签。
因此文件名中的 `probabilities` 不能解释为 CSV 内仍保存连续模型概率。

原脚本快照：

```text
allo_stepwise/source_snapshot/
```

这些位置均为溯源输入。自动 agent 不得向原案例或 `source_snapshot/` 写入结果，
也不得直接执行含硬编码路径的一次性脚本。

## 4. 历史执行链

| 阶段 | 历史脚本/产物 | 真实语义 |
|---|---|---|
| AlloDesigner 阳性预测 | `works2/AlloDesigner/Allo-PocketMiner/case_predict.py` | 对 50 个模型分数取均值并以阈值 0.7 二值化，写出 `residue,probability`。GLP1 共 491 行，CSV 中只有 0/1，`probability == 1` 有 119 个残基。 |
| Iteration 1 构象与 fpocket | `Iteration_1/shuffle_*_fpocket/` | 10 个 shuffle，共 620 个预测 PDB、620 个 `pocket_centers.csv`。 |
| 阳性残基空间聚类 | `4_postgrasp_clustering_pocketminer_apo_dir_step3.py` | 在每个 Iteration 1 构象中提取 119 个阳性残基的 CA，使用 DBSCAN `eps=6`、`min_samples=2`。 |
| 候选簇与 pocket 距离 | `5_calculte_group_cluster_fpocket_dcc_all_shuffle_step3.py` | 每个残基簇匹配同一构象中最近的 fpocket pocket；10 个 CSV 共 9,843 行。 |
| DeepAllo 簇评分 | `6_inference_case_pocketminer_cluster_to_deepallo_run.py` | 仅保留 `min_distance < 10` 的候选，结合 ProtBERT pocket residue embedding 和 19 个 fpocket 特征，得到 `deepallo_score`。10 个 CSV 共 7,641 行。 |
| DeepAllo 残基频率 | `6.1_calculate_apo_pocketminer_cluster_deepallo_score.py` | 在每个 shuffle 的每个 group 内按 `deepallo_score` 降序取 7 个簇，再统计残基出现频率；输出覆盖 114 个残基。 |
| PLB 簇评分 | `7_plb_calculation_pocketminer_apo_dir_step3.py` | 对同一批 7,641 个候选簇按 Soga RA 值求和，得到 `plb_score`。 |
| PLB 残基频率 | `7.1_calculate_apo_pocketminer_cluster_plb_score.py` | 在每个 shuffle 的每个 group 内按 `plb_score` 降序取 7 个簇，再统计残基出现频率；输出覆盖 108 个残基。 |
| 重复残基集合审查 | `8_cluster_residues.py` | 统计相同残基组成的候选簇出现次数，为人工查看提供辅助表；它不执行最终选择。 |
| 专家 handoff | `binding_sites_prediction/pocketminer_cluster/5vex/eps6/holo_cluster_for_msa.csv` | 可核实的最终交接是 clusters 8、9、14 对应的 14 个 apo residues；两类排名和 5VEX 结构表均提供支持，但精确人工决策公式缺失。 |

`min_distance < 10` 的历史过滤关系可由文件逐行核实：9,843 条距离记录中恰有
7,641 条满足条件，与 DeepAllo 和 PLB 的行数一致。

历史聚合脚本同时保存 top 3/5/7：DeepAllo 表分别覆盖 85/106/114 个残基，PLB
表分别覆盖 100/106/108 个残基。Iteration 1 每个 shuffle 有 62 个 group，10 个
shuffle 共 620 个 group；top-7 频率的分母是 `620 * 7 = 4,340` 个入选簇实例。

## 5. 历史文件契约

### 5.1 候选簇距离

```text
group_cluster,closest_pocket,min_distance
```

路径模板：

```text
Iteration_1/pocketminer_predict_residues_cluster/
└── shuffle_N_group_cluster_fpocket_distance_results.csv
```

### 5.2 DeepAllo 簇级分数

```text
group_cluster,closest_pocket,min_distance,deepallo_score
```

路径模板：

```text
Iteration_1/pocketminer_cluster_deepallo_score/
└── pocketminer_cluster_deepallo_score_shuffle_N_filtered.csv
```

### 5.3 PLB 簇级分数

```text
group_cluster,closest_pocket,min_distance,deepallo_score,group,cluster,plb_score,pdb_path
```

路径模板：

```text
Iteration_1/pocketminer_cluster_deepallo_score/plb_score/
└── pocketminer_cluster_deepallo_plb_shuffle_N.csv
```

### 5.4 Top-k 残基频率

两个历史文件均使用：

```text
residue_number,probability
```

复现包内只读副本：

```text
inputs/glp1-deepallo-score-residue_probabilities_top_7.csv  # 114 rows
inputs/glp1-plb-score-residue_probabilities_top_7.csv       # 108 rows
```

这两份文件是计算性 Step 3 的最终指标产物；候选cluster、DCC和簇级DeepAllo/PLB
CSV是生成它们所需的可审核中间产物。专家选择不属于这两个指标的计算。

这里的 `probability` 不是 DeepAllo 模型概率，也不是 PLB 概率。它表示“每个 group
分别取 top 7 候选簇后，该残基在全部入选簇实例中的出现频率”。后续实现应把列名
明确改为 `deepallo_topk_frequency` 和 `plb_topk_frequency`，同时保留原列以便追溯。

`top_7` 指每个 group 选择 7 个候选簇，不是最终只选择 7 个残基。

包内副本与历史原文件逐字节一致，但历史行序不是按 `probability` 降序。若将其作为
“排序文档”交付，必须在不覆盖冻结副本的前提下生成确定性排名视图：先按
`probability` 降序，再按 `residue_number` 升序解决相同频率的行序；排名规则及
输入hash写入provenance manifest。

关键 handoff 输入的固定 hash：

| 文件 | SHA-256 |
|---|---|
| AlloDesigner 491-residue CSV | `d5ebbd12f15d651c9cad1eb800143f89fef705513c308843909e44dc26cf8a26` |
| DeepAllo top-7 frequency CSV | `c4d5cdedb3ccd42ec7737b987500329d4141a9a6a00b1fedf707e00fb3e6edc0` |
| PLB top-7 frequency CSV | `6f3fb69adc352e99cbc09b6b85525141e78fc31779728314658ffbb79568d67a` |
| 原始 `holo_cluster_for_msa.csv` | `c3863db8c95ace60caa2e4af17e55e38ea1b3b2825a6de405c1950831edd6617` |
| 5VEX `plb_scores_dcc_dvo.csv` | `2bc8eb85573d846bdb3c7aed8ad47c22a6fed8709649027b3bc285abeb8fd2bf` |
| 14-residue expert handoff CSV | `0213fabe2b7eb965b4756ab8f0278bc76164e3458c20ede97028066030305354` |

### 5.5 DeepAllo 历史兼容性说明

GLP1 历史推理快照使用 `token_emb[int(residue_number)]`。Iteration 1 的 AF PDB
为 chain A、1-491 连续编号，而 ProtBERT 去除 CLS 后 `token_emb[0]` 才对应残基
1。因此现存 7,641 条 DeepAllo 分数以及由它们汇总的 top-7 frequency 继承了
一个 `+1` token shift。

这不妨碍对历史流程做逐字节复现，但这些值不能冒充“修正编号后的 DeepAllo
结果”。本地没有保存历史 pocket embedding，修正后的重新排序必须重新运行 MTL
ProtBERT 和 AutoGluon。未来 agent 必须同时标记：

- `historical_compatibility`：保留旧索引行为，只用于复现历史结论；
- `corrected_mapping`：按 `(chain, resseq, insertion_code) -> token position` 显式
  映射，用于新的科学分析。

两种模式的结果不得覆盖、合并或使用同一 selection fingerprint。

本地模型资产仅供未来实现引用：

```text
/root/data1/data/move/ZYY/zyy/works/deepallo-main/models/
├── Rostlab/prot_bert_bfd/             # tokenizer + 1024-d encoder
├── prot-bert-deepallo-mtl.bin         # MTL checkpoint
└── autogluon/                         # complete 1043-feature predictor bundle
```

AutoGluon 输入为 1024 维 pocket residue embedding 均值加按 fpocket info 原顺序
读取的 19 个描述符。旧脚本中的 pocket 坐标不是模型特征，只被间接用于截断长度。

未来 agent 应默认读取现有 7,641 条 precomputed score 以复现历史。只有明确要求
修正评分时，才通过 `/root/miniconda3/envs/deepallo/bin/python` 启动隔离子进程，
并把模型和 predictor 各加载一次。历史脚本不是可导入 API：它们有顶层执行和
硬编码路径，不能直接 `import` 到 runner。

## 6. 专家选择与当前 GLP1 结论

当前冻结的 14 个下游评价残基为：

```text
354, 355, 357, 358, 365, 369, 410, 411, 412, 413, 414, 415, 416, 417
```

对应 apo 残基组成为：

```text
I354, K355, R357, L358, L365, L369, L410, Y411,
C412, F413, V414, N415, N416, E417
```

三簇证据为：

| 5VEX cluster | apo residues | PLB | DCC |
|---|---|---:|---:|
| 8 | 354, 355, 357, 358 | 6.367 | 8.61 A |
| 9 | 365, 369 | 3.492 | 9.48 A |
| 14 | 410-417 | 13.282 | 9.29 A |

原始 handoff 与复现包副本：

```text
/root/data1/data/move/ZYY/zyy/works/binding_sites_prediction/
└── pocketminer_cluster/5vex/eps6/holo_cluster_for_msa.csv

inputs/glp1_historical_holo_cluster_mapped_residues.csv
```

两个 CSV 的 14 行映射内容相同；字节 hash 的差别仅来自复现包副本补了文件末尾
换行。原始簇级证据表为同目录的 `plb_scores_dcc_dvo.csv`：clusters 8、9、14
是唯一 `dcc < 10` 的三行，其残基并集正好等于 handoff。

这 14 个残基：

- 全部属于 119 个 AlloDesigner 阳性残基；
- 全部出现在 DeepAllo top-7 残基频率表；
- 全部出现在 PLB top-7 残基频率表；
- 同时保留 5VEX holo 口袋映射的结构先验。

它们并不是把两列频率简单相加后截取 top-N 得到的结果。专家先验改变了纯模型
排序，因此未来 agent 必须把“模型证据排名”和“专家最终选择”保存为两个独立
产物。

原 AlloDesigner 后续脚本已有明确的人工交接先例：
`4.3_postgrasp_clustering_pocketminer_apo_dir.py` 读取单列
`final_select_cluster_residues.csv`。PCSK9 历史实例的列名是 `residues`。GLP1
复现 runner 的标准列统一为 `residue_number`，必要时由适配层导出旧列名。

## 7. 下游数据流

当前 runner 通过以下配置消费最终残基：

```yaml
residue_selection:
  active_set: historical_holo_cluster
  sets:
    historical_holo_cluster:
      csv: "{root}/inputs/glp1_historical_holo_cluster_mapped_residues.csv"
      residue_column: "apo_residues_id"
```

`load_binding_residues()` 只读取残基号、去重和排序。它不会读取排名、DeepAllo
分数、PLB 分数、选择标志或专家理由。因此：

- 完整候选排名表不能直接作为下游 residue CSV；否则所有候选都会被加载。
- 最终 handoff 必须是独立的 selection-only CSV。
- 后续 iteration、M-fold、voting 和 recompile 不直接读取残基列表。
- 残基集合先决定构象的残基簇和 `min_distance`，再通过这些指标间接影响所有
  MSA 选择、投票和重编译结果。

历史消费者 `case/4.2_postgrasp_clustering_pocketminer_apo_dir.py`、
`case/4.3_02_postgrasp_clustering_pocketminer_apo_dir_glp1.py` 和 recompile 对应脚本
直接读取 `holo_cluster_for_msa.csv` 的 `holo_residue`，再通过
`6x18_seqres_to_atom_mapping.pkl` 映射成 apo 编号。当前 runner 为避免每次重复
映射，直接读取同一文件已冻结的 `apo_residues_id` 副本。两种入口必须得到完全
相同的 14-residue 集合。

正确顺序应为：

```text
Iteration 1 prediction/fpocket
  -> Step 3 candidate evidence
  -> expert approval and frozen residue fingerprint
  -> rerun/finalize Iteration 1 pocket-distance metric with approved residues
  -> select Iteration 1 MSA
  -> Iteration 2-7
  -> combine Iteration 1-5 for M-fold
  -> M-fold / sequence voting / recompile / final evaluation
```

## 8. 未来 agent 的必需产物

未来实现只能写入：

```text
{work_dir}/01_iterative_shuffling/Iteration_1/
└── step3_select_pocket_cluster_residues/
```

至少生成：

| 文件 | 最低内容要求 |
|---|---|
| `candidate_cluster_scores.csv` | shuffle、group、cluster、残基集合、cluster size、closest pocket、min distance、DeepAllo raw score/status、PLB raw/size-normalized score。 |
| `deepallo_topk_residue_frequency.csv` | residue number、计数、分母、频率、top-k 和 score direction。 |
| `plb_topk_residue_frequency.csv` | residue number、计数、分母、频率、top-k、PLB 口径。 |
| `residue_evidence_table.csv` | residue、氨基酸、AlloDesigner raw/label、DeepAllo/PLB frequency、expert prior、selected、selection reason。 |
| `ranked_pocket_candidates.csv` | 空间候选簇或稳定残基集合、两类独立排名、重复支持数、结构位置和专家审查状态。 |
| `expert_decision.yaml` | decision ID、include/exclude、专家姓名或角色、日期、rationale、证据文件 hash；不得由模型自动伪造。 |
| `final_selected_residues.csv` | 仅包含已批准残基；标准列名 `residue_number`，每行一个唯一整数。 |
| `provenance_manifest.json` | 所有输入/输出 SHA-256、参数、模型路径/版本、代码版本、chain/numbering 映射和 residue-set fingerprint。 |

专家批准后，agent 只能把 `final_selected_residues.csv` 注册为新的
`residue_selection.sets.step3_approved`，列名固定为 `residue_number`；
`ranked_pocket_candidates.csv` 或 `residue_evidence_table.csv` 都不是 selection-only
输入。激活新集合后必须先用新的 selection fingerprint 重做 Iteration 1 指标，
再允许后续 iteration/M-fold/voting/recompile 继续。

## 9. 自动化护栏

未来 agent 实现 Step 3 时必须满足：

1. 原 GLP1 case 和 `source_snapshot/` 始终只读。
2. Step 3 只接受 Iteration 1；非 Iteration 1 discovery 必须失败。
3. AlloDesigner 阳性筛选必须显式记录阈值和值，不能把 491 个残基全部带入。
4. DeepAllo 和 PLB 必须在每个 `shuffle + group` 内分别取 top-k，不能全局取 top-k。
5. DeepAllo residue number 到 ProtBERT token 的映射必须基于 `(chain, resseq, icode)`
   和实际序列位置，不能直接使用 `token_emb[int(residue_number)]`。
6. 每条 DeepAllo 记录必须保留 `status/error`；缺失分数不能通过缩短 list 静默跳过。
7. PLB raw sum 天然偏向大 cluster；必须同时记录 cluster size 和 size-normalized
   口径，专家表中注明实际使用哪一种。
8. 专家 handoff 未批准时，Iteration 1 选择及后续阶段必须停止，不能静默回退。
9. 对最终残基列表计算 SHA-256/selection ID；Iteration 1 重评、Iteration 2-7、
   M-fold、sampling 和 final metric 必须校验同一 fingerprint。
10. 当前 metric 输出路径只包含 `eps`，旧 cluster PDB 不会自动清理。残基集合改变时
    必须按 selection ID/hash 隔离目录，或拒绝复用，防止旧簇混入新结果。
11. 当前 residue loader 只按 `residue.id[1]` 匹配。正式通用化前必须显式限制 chain，
    并处理 insertion code 和多链重复编号。
12. 排名 tie-break 必须确定性，并写入 manifest。
13. 默认历史复现读取 precomputed score CSV；可选实推必须作为独立适配器运行，且
    `legacy_indexing` 与 `corrected_mapping` 的产物、hash 和 selection ID 完全隔离。

## 10. 只读检查命令

```bash
./commands/01_audit_step3_handoff.sh
```

该命令只检查路径、CSV schema、历史计数、119 个阳性残基、两张 top-k 频率表、
14 个专家残基的集合关系和下游 active set。它不会加载 DeepAllo 模型，不会运行
fpocket/DBSCAN/PLB，不会创建 future-agent 输出目录，也不会修改原案例。

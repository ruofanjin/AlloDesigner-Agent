# GLP1 历史案例核对记录

只读参考目录：

```text
/root/data1/data/move/ZYY/zyy/works/AF_ClaSeq/case/GPL1/6x18_chianR_R
```

该目录只用于确认实际执行方式，agent 不向其中写入文件。

## MSA 处理

对历史输入 `default/6x18_chianR_R.a3m` 按原 AF-ClaSeq 读取规则去除小写插入、按 header 去重后有 7392 条序列。coverage 阈值 0.8 后保留 985 个唯一 header；写入 PDB query 后，历史 `filtered_sequences.a3m` 共 986 条记录。

每次 iteration 使用 seed 42 重新开始随机序列，10 个 shuffle、每组 16 条。用该规则重建的 `Iteration_1/shuffle_1/group_1.a3m` header 顺序与历史文件完全一致。

历史每轮合并规则由现有指标 CSV 与 A3M 反向核对：

| Iteration | 选择规则 | 与历史 `combined_filtered_iteration_N.a3m` |
|---|---:|---|
| 1 | 每个 shuffle 最低 20% `min_distance` | 完全一致，852 条唯一序列 |
| 2 | 每个 shuffle 最低 20% `min_distance` | 完全一致，723 条唯一序列 |
| 3 | 每个 shuffle 最低 10% `min_distance` | 完全一致，446 条唯一序列 |
| 4 | 每个 shuffle 最低 10% `min_distance` | 完全一致，234 条唯一序列 |
| 5 | 每个 shuffle 最低 10% `min_distance` | 完全一致，119 条唯一序列 |
| 6 | 每个 shuffle 最低 10% `min_distance` | 完全一致，82 条唯一序列 |

M-fold 的输入不是这些轮次文件的简单拼接。历史 `combined_filtered_all_iterations.a3m` 等价于：Iteration 1–5 中所有 `min_distance < 5.0` 的 group A3M 按序列去重，结果为 759 条唯一序列。该规则已写入 `configs/stepwise/01_iterative_shuffling.yaml`。

## M-fold sampling

历史 M-fold 参数为 coverage 0.8、group size 20、round 1 seed 43。759 条输入经过写入 query 和 coverage 处理后，产生：

- `filtered_sequences.a3m`：760 条记录；
- `02_init_random_split`：37 个 group，前 36 组各 20 个候选序列，最后一组 39 个候选序列；
- `02_sampling`：37 个 leave-one-out sampling 目录；
- `sampling_1/group_1.a3m` 的 header 顺序与 seed 43 的重建结果完全一致。

## 序列投票

历史 `pocket_distance` 使用 20 个 focused bins，边界由 1333 条 sampling-group `min_distance` 的实际最小值和最大值生成。并列最高票时，原实现通过排序后的 `np.unique` 选择较小 bin；该规则不能替换为依赖首次出现顺序的 `Counter.most_common()`。

按上述规则从历史 M-fold A3M 和合并指标 CSV 只读重建，759 条序列的 `Bin_Assignment`、`Vote_Count` 和 `Total_Votes` 均与历史 `run/03_voting/pocket_distance/voting_results.csv` 逐行一致。最终仍重编译历史使用的 `bin_3_4`。

## Iteration 1 Step 3 证据

历史 Step 3 的计算产物已在 Iteration 1 下核实：AlloDesigner 输入包含 491 个
残基，其中 119 个为阳性；10 个 shuffle 共产生 620 个预测 PDB/fpocket 结果、
9,843 条候选残基簇到最近 pocket 的距离。`min_distance < 10` 后保留 7,641 条，
与 10 个 DeepAllo CSV 和 10 个 PLB CSV 的总行数完全一致。

DeepAllo 与 PLB 分别在每个 shuffle 的每个 group 内按分数降序取 7 个候选簇，
再统计残基出现频率。对应表覆盖 114 和 108 个残基；`probability` 是 top-k
cluster frequency，不是模型概率，也不是最终专家选择概率。

历史 DeepAllo 推理使用 `token_emb[int(residue_number)]`。GLP1 AF PDB 是 1-491
连续编号，正确的残基 1 位置应为 `token_emb[0]`，因此历史分数继承一个 `+1`
token shift。现有 CSV 只用于忠实复现历史；修正编号后必须重新运行模型，结果应
使用不同的 provenance 和 residue-set fingerprint。

完整脚本映射、文件 schema、hash、人工 handoff 边界和 future-agent 护栏见
`STEP3_POCKET_SELECTION_HANDOFF.md`。

## 评价残基与结构指标

历史 GLP1 sampling/final clustering 脚本读取 5VEX holo cluster，并通过 `6x18_seqres_to_atom_mapping.pkl` 映射到预测结构编号。映射后的 14 个残基为：

```text
354, 355, 357, 358, 365, 369, 410, 411, 412, 413, 414, 415, 416, 417
```

原始映射 CSV 的 SHA-256 为 `c3863db8c95ace60caa2e4af17e55e38ea1b3b2825a6de405c1950831edd6617`。agent 内保存了只含必要映射的 CSV，并将其作为冻结的 Step 3 专家 handoff 使用。这 14 个残基均属于 AlloDesigner 阳性集合，也均出现在 DeepAllo 和 PLB top-7 频率表；但历史目录没有机器可读的专家 rationale/签署 manifest，因此不能把该结论描述为自动 score fusion。

结构评价沿用历史 `eps=6`、`min_samples=2`：候选残基 CA 坐标 DBSCAN 聚类后，计算每个残基簇几何中心到对应 fpocket pocket center 的最短距离，并对同一 group 或最终同一 PDB 的多个残基簇取平均。

## 最终阶段

项目级 `colabfold_batch.sh` 记录的 GLP1 参数为：前期 iteration/M-fold 使用 `3 recycles, 1 model, 1 seed, random seed 42`；最终 `prediction/bin_3_4` 与 `control_prediction/bin_3_4` 使用 `3 recycles, 5 models, 8 seeds`。最终 prediction/control 的 fpocket 评价已由 `13_final_metric_stack.sh` 参数化，不再依赖 PCKS9 的 `bin_7` 或 `bin_12_13_14_15` 硬编码。

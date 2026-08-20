# AlloDesigner source snapshot

本目录保存 `/root/data1/data/move/ZYY/zyy/works2/AlloDesigner/Allo_af_claseq` 的原始一次性脚本，以及项目级 `colabfold_batch.sh` 的快照。它只承担溯源功能，不属于 agent 可执行区。

原脚本中的 PCKS9、CB1R、1HZB、旧 DeepAllo 路径和 `case/GPL1/.../run` 路径均是历史上下文。为了不把“原始证据”伪装成“改写后代码”，这些文件保留原样；常规评价链已在 `../scripts/run_stepwise_allo.py` 与 `../commands/` 中参数化，Step 3 则只在 `../docs/STEP3_POCKET_SELECTION_HANDOFF.md` 中完成证据提取和 future-agent 适配。任何自动 agent 都不得直接运行本目录文件。

## 适配关系

| 原始脚本类别 | GLP1 参数化入口 |
|---|---|
| `1_*exact_pdb*` | `copy-pdbs` |
| `2_*fpocket*` | `run-fpocket` |
| `3_*fpocket_center*` | `pocket-centers` |
| `4_*clustering*`、`8_cluster_residues.py` | `cluster-residues` |
| `5_*distance*` | `cluster-pocket-distance` |
| Step 3 的 `4_*`、`5_*`、`6*`、`7*`、`8_cluster_residues.py` | `step3-audit`（只读检查）及 `../docs/STEP3_POCKET_SELECTION_HANDOFF.md`（未来实现契约） |
| `9_*average*`、`13_*average*` | `average-distances` |
| `10.3_combined_all_sample.py` | `combine-sampling-metrics` |
| `11_sequence_voting.py` | `sequence-voting` |
| `12_recompile.py` | `recompile` |
| `combined_a3m.py` | `select-iteration-msa`、`combine-iterations` |
| M-fold 拆分逻辑 | `generate-mfold-msas` |
| `project_colabfold_batch.sh` | `write-colabfold-commands --stage iteration|mfold|final` |

DeepAllo/PLB 推理脚本不进入默认执行链。GLP1 历史执行已经产生簇级分数和
top-k 残基频率；默认评价直接消费冻结的
`glp1_historical_holo_cluster_mapped_residues.csv`。`step3-audit` 只验证这条证据链，
不会导入或执行这些脚本。

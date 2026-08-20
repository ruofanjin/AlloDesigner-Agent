# GLP1 stepwise 命令顺序

本目录只包含参数化 GLP1 执行入口。先运行 strict preflight，再按 `00_plan -> 02..13` 执行；`01` 是需要完整历史证据的可选审计，`99` 是永久禁用记录。

## 顺序总览

| 编号 | 命令 | 前置条件与作用 | 并行说明 |
|---:|---|---|---|
| preflight | `00_check_environment.sh` | 严格检查核心环境、外部程序、输入 hash 和路径 | 缺项时非零退出；审计模式可加 `--allow-missing-external` |
| 00 | `00_plan.sh` | 自包含路径审计和流程预览 | 默认不要求未打包的完整 Step 3 evidence |
| 01 | `01_audit_step3_handoff.sh` | 可选的冻结历史证据与专家 handoff 只读审计；不重算 Step 3 | 先按 evidence/step3_historical/README.md 补齐证据 |
| 02 | `02_prepare_iteration_input.sh` | 一次性生成 coverage 过滤输入 | 必须在 iteration 循环前串行完成 |
| 03 | `03_generate_iteration_msas.sh N` | 为 Iteration `N` 生成 10 个 shuffle | 为保持历史 RNG 顺序，本步骤本身不得按 shuffle 并行 |
| 04 | `04_write_iteration_colabfold_commands.sh N` | 生成当前轮 ColabFold 清单 | 清单中的 10 个 shuffle 目录互相独立，可并行预测 |
| 05 | `05_iteration_metric_stack.sh N` | 当前轮 fpocket 与 `pocket_min_distance` 评价 | 当前 wrapper 遍历全部 shuffle，应单实例执行 |
| 06 | `06_select_iteration_msa.sh N` | 汇总当前轮，产生下一轮输入 | 必须等待当前轮 10 个 shuffle 指标全部完成 |
| 07 | `07_combine_iterations.sh` | 从 Iteration 1-5 汇总 759 条 M-fold 输入 | Iteration 5 完成后可与 Iteration 6-7 分支并行 |
| 08 | `08_prepare_mfold_msas.sh` | 生成 37 个 initial groups 和 37 个 sampling | 随机拆分必须串行，随后才可并行预测 |
| 09 | `09_write_mfold_colabfold_commands.sh` | 生成 M-fold ColabFold 清单 | 1 个 initial split 加 37 个 sampling，共 38 个目录可并行 |
| 10 | `10_sampling_metric_stack.sh` | 评价全部 sampling 并合并指标 | 当前 wrapper 遍历 37 个 sampling，应单实例执行 |
| 11 | `11_vote_and_recompile.sh` | 序列投票后重编译 `bin_3_4` | 投票和重编译存在直接依赖，必须保持顺序 |
| 12 | `12_write_final_colabfold_commands.sh` | 生成最终 prediction/control 清单 | prediction 与 control 两个目录可并行预测 |
| 13 | `13_final_metric_stack.sh` | 最终 prediction/control 评价 | 两个 scope 独立；当前 wrapper 默认串行执行 |
| 99 | `99_historical_project_glp1_colabfold.sh` | 原目录命令记录 | 永久禁用，不得执行 |

## Iteration 循环

`02` 只运行一次。随后对每个 `N=1..7` 依次执行 `03 -> 04 -> ColabFold -> 05 -> 06`：

```bash
./commands/02_prepare_iteration_input.sh

./commands/03_generate_iteration_msas.sh 1
./commands/04_write_iteration_colabfold_commands.sh 1
# 并行或串行完成 generated/iteration_1_colabfold_commands.sh 中的 10 个预测单元
RUN_FPOCKET=1 ./commands/05_iteration_metric_stack.sh 1
./commands/06_select_iteration_msa.sh 1
```

下一轮必须等待上一轮 `06` 结束，因为 Iteration `N+1` 默认读取 `combined_filtered_iteration_N.a3m`。

## 可并行分支

Iteration 5 的 `06_select_iteration_msa.sh 5` 完成后可拆成两个分支：

| 分支 A | 分支 B |
|---|---|
| 继续执行 Iteration 6-7 的 `03-06` | 执行 M-fold 的 `07-10` |

M-fold 分支只读取 Iteration 1-5，因此两个分支没有写目录冲突。必须等待 `10_sampling_metric_stack.sh` 完成后才能执行 `11_vote_and_recompile.sh`。

## 并行安全边界

1. 只并行不同输出目录；同一个 shuffle、sampling、prediction 或 control 目录不得重复提交。
2. ColabFold 可并行单元来自 `generated/*_colabfold_commands.sh`，生成命令本身不运行预测。
3. `05` 和 `10` 当前是全范围 wrapper，不要通过启动多个相同 wrapper 来模拟并行。
4. 每个下游汇总步骤都是 barrier，必须确认其全部上游任务成功后再执行。
5. 所有活动命令只允许写入包内 `workdir/` 与 `generated/`。

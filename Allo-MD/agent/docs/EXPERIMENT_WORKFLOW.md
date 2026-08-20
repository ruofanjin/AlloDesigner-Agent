# GLP1 iteration1 主实验工作流


## 1. 三个证据层必须分开

### 冻结模拟与历史过程复核

尽可能保留已归档的 MDP、DAT、起点关系和可由产物确认的历史语义，包括：

- 已执行的 eq1–eq6 逐段以上一段 GRO 为位置约束参考；实际 TPR 的 position-restraint reference 与前一段坐标吻合；
- 10、50、100 ns 常规 MD 是 eq6 起点的独立分支；
- 200 ns 常规 MD 从 100 ns 末态启动，但新段时间轴归零；
- 距离偏置的 100 ns 后段从 50 ns 末态启动，但建立新的 HILLS；
- SASA DAT 原样保留 `METAD` 与 `BIASVALUE ARG=sasa`。

该历史行为可通过 `RESTRAINT_REFERENCE_MODE=historical_previous` 复核；它与原始 CHARMM-GUI README 始终使用 `step5_input.gro` 的配方不同。模拟阶段统一标为 `frozen-simulation`，不使用会暗示字节级复现的 `legacy-exact`。这用于复核历史过程，不表示所有设置都是推荐的新研究设计。

### 标准化分析扩展

本版把可以比较的分析协议显式扩展到 SASA site 10 ns、pocket 10 ns 和正式 pocket 100 ns：

- 完整性/PBC 检查与蛋白轨迹对齐；
- 5 类 RMSD；
- 7 套预先固定 cutoff 的 Gromos 聚类与 5VEX site 比较；
- 原始完整体系轨迹上的 `gmx sasa`：`SOLU_MEMB` 为全部非溶剂 surface，变构位点为 output；
- 每 100 ps 拆帧、MDpocket density/selected pocket、体积 CSV 与 non-finite QC。

这些 stage 的 `protocol_class=standardized-analysis`。原项目只证明 site/pocket 10 ns 各有 4 条 RMSD 和 101 帧 MDpocket，且没有 SASA 聚类；正式 pocket 100 ns 没有对应历史分析。因此标准化结果是可审计的新增再分析，不是历史已有产物。

### 推荐的新研究设计

推荐设计的实质变化必须使用新的 profile、run-id、MDP/DAT 文件名和 provenance 记录，不能原地修改冻结输入。平衡位置约束的推荐默认值为：

```text
RESTRAINT_REFERENCE_MODE=charmm_gui_initial
```

该值遵循原始 CHARMM-GUI 配方，但会偏离已执行历史 TPR；因此 `prepare` 会把实际选择冻结到 run provenance。若目标是复核历史已执行平衡过程，应显式改为 `historical_previous` 并使用不同 run-id。profile 名描述冻结输入/DAG，运行态的平衡变体以 site snapshot 为准。

真正连续的生产时间轴、PLUMED HILLS restart、移除 SASA `BIASVALUE`、按无偏波动校准偏置、replica/reweighting/收敛标准等变更尚未作为可执行 profile 固化。若要采用，先按 [科学决策](SCIENTIFIC_DECISIONS.md) 建立新方案并验证。本版不会为未决科研参数提供看似可运行的默认值。

## 2. 不可变输入

`inputs/` 保存从当前复现流程提取的阶段性冻结输入快照：

- 完整体系坐标、蛋白参考 PDB、拓扑、index 和项目本地 `toppar/`；
- 最小化、六段平衡、常规 MD、距离和 SASA 的 MDP；
- χ 角、48 距离、SPIB 二维距离偏置和两个 SASA 定义；
- 聚类和 5VEX 比较使用的 NDX/PDB。

PLUMED 原子编号从 1 开始且与拓扑原子顺序绑定。任何重建拓扑、删除原子、重排分子或修改 `step5_input3.pdb` 的操作都会使冻结 DAT 失效。若输入摘要变化，应创建新的实验版本，不能继续称为冻结流程复现。

`prepare` 会把整个 `inputs/` 快照复制到新 run；阶段脚本只在该 run 中创建链接、TPR 和输出，不在 bundle 或原项目中运行。未来全流程 Agent 应从上游建模/拓扑/选择步骤规划这些 artifact；该功能尚未实现，本版不能自动重建或替换它们，详见 [未来全流程接入提醒](FUTURE_FULL_FLOW.md)。

## 3. 已定义 profile

用下列命令查看部署包中的实际清单：

```bash
./agentctl list
```

主要 profile：

| profile | 内容 |
|---|---|
| `validate-only` | 仅用于列出空模拟计划；实际环境检查请使用 `doctor` |
| `historical-distance-main` | 最小化→平衡→常规 100 ns→距离监测 50 ns→距离 metad 50 ns→后处理→MDpocket |
| `distance-simulation-only` | 与上面相同，但停在距离 metad 50 ns，不要求 MDpocket |
| `distance-new-bias-100ns` | 在距离 metad 50 ns 后从末态建立新的 100 ns 偏置历史 |
| `historical-normal-controls` | eq6 起点的独立 10/50/100 ns，对 100 ns 末态再加 200 ns |
| `historical-sasa-site` | 常规 100 ns 后的变构位点 10 ns SASA 历史分支 |
| `historical-sasa-pocket` | 常规 100 ns 后的 8 Å pocket 10 ns 短程对照 |
| `historical-sasa-pocket-100ns` | 常规 100 ns 后的 8 Å pocket 100 ns 正式长分支 |
| `historical-sasa-biased-main` | 位点 10 ns 与 pocket 100 ns 两条独立 SASA biased MD 的审计合集 |
| `standardized-sasa-site-10ns-full` | site 10 ns 历史模拟 + 标准化结构/SASA/MDpocket 分析 |
| `standardized-sasa-pocket-10ns-full` | pocket 10 ns 对照 + 同一分析矩阵 |
| `standardized-sasa-pocket-100ns-full` | 正式 pocket 100 ns + 新增标准分析 |
| `standardized-sasa-biased-main` | 同一 parent 的 site 10 ns/pocket 100 ns 与全部标准分析 |
| `all-traceable` | 当前可追溯正确分支的合集；计算量很大，不是默认建议 |

`historical-distance-main` 和所有 `*-full` SASA profile 包含 MDpocket。目标机没有 `mdpocket` 时，应使用 simulation-only 的历史 profile，不能绕过 doctor 后伪报完整 profile 成功。

## 4. 两个同级主实验族

```text
minimization
  ↓
equilibration: eq1 → eq2 → eq3 → eq4 → eq5 → eq6
  ↓
normal_100ns                 （eq6 起点）
  ├─ distance_monitor_50ns   （48 个距离，仅记录，无偏置、无 SASA）
  │    └─ distance_metad_50ns（SPIB sigma1/sigma2 二维 metadynamics）
  │         ├─ postprocess_distance_50ns → mdpocket_distance_50ns
  │         └─ distance_metad_100ns_new_bias（新 HILLS）
  ├─ sasa_site_10ns          （254 原子，直接 SASA biased MD）
  │    └─ postprocess_sasa_site_10ns → mdpocket_sasa_site_10ns
  └─ sasa_pocket_100ns       （8 Å/648 原子，直接 SASA biased MD）
       └─ postprocess_sasa_pocket_100ns → mdpocket_sasa_pocket_100ns
```

常规对照分支：

```text
eq6 ─┬─ normal_10ns
     ├─ normal_50ns
     └─ normal_100ns → normal_200ns_from_100ns
```

因此不得把 10、50、100、200 ns 四份轨迹拼成连续 360 ns。历史上最长的常规构象链是 100 ns 加后续 200 ns，但两个磁盘时间轴均从 0 开始。

两个 SASA 阶段都从同一 run 内的 `normal_100ns.gro/.cpt` 直接构建新 TPR，时间轴从 0 开始，各自创建独立 HILLS/COLVAR。它们不依赖 distance monitor/metad，也不互相接续。`historical-sasa-biased-main` 按 manifest 顺序调用二者，保证共享同一父态。不要用两个 run-id 冒充并行历史分叉：eq1 的 `gen-seed=-1` 会让它们形成不同 normal100 父态。真正的同父态并发需要未来的只读 seed artifact fan-out 与调度依赖机制，本版未实现。

标准化分析不会复用 50 ns 的固定终点：site/pocket 10 ns 严格要求 101 帧和 10000 ps，pocket 100 ns 严格要求 1001 帧和 100000 ps。分析选择/cutoff 被写进 manifest 与协议 TSV；输出按 `protocol_class` 与历史模拟分层。两个来源不闭合的 SASA 50 ns 分析树不进入 profile。

## 5. 跨膜体系上游边界

当前 run 使用冻结的 CHARMM-GUI 膜体系。本版不会从任意 PDB 猜测膜方向、脂质组成或力场。新体系默认采用 CHARMM-GUI Membrane Builder；GROMACS-native 仅作为已有定向结构、预平衡膜片和兼容 topology 时的专家路线。完整上游 artifact contract、QC 和命令边界见 [GLP1 跨膜体系构建](MEMBRANE_SYSTEM_BUILDING.md)。在新上游通过验收前，旧 48 距离与 254/648 SASA 原子映射绝不能复用。

## 6. 部署和执行顺序

假设：

```bash
export BUNDLE=/path/to/agent
export SITE=/data/config/glp1-agent.site.env
export WORK=/data/runs/glp1
```

### 6.1 静态和环境检查

```bash
cd "$BUNDLE"
./agentctl verify-bundle
./agentctl --site-config "$SITE" doctor --strict --require-mdpocket
./agentctl plan --profile standardized-sasa-biased-main
```

这些步骤不得启动长模拟。检查失败时先处理 [故障排查](TROUBLESHOOTING.md)。

### 6.2 创建隔离运行目录

```bash
./agentctl \
  --site-config "$SITE" \
  --work-root "$WORK" \
  prepare --run-id distance-main-001
```

run-id 只能包含字母、数字、点、下划线和连字符。若目标路径已存在但不是由本 Agent 创建，程序会拒绝使用。站点配置在这里被快照；资源和环境设置应在 prepare 前确认。

### 6.3 再做一次 dry-run

```bash
./agentctl \
  --site-config "$SITE" \
  --work-root "$WORK" \
  run --profile historical-distance-main \
  --run-id distance-main-001
```

没有 `--execute` 时只打印依赖展开后的计划，不执行外部命令。

### 6.4 明确开启长任务

```bash
./agentctl \
  --site-config "$SITE" \
  --work-root "$WORK" \
  run --profile historical-distance-main \
  --run-id distance-main-001 \
  --execute --allow-long-md
```

`--execute` 和 `--allow-long-md` 是两个独立门闩，缺少任意一个都不能启动计算。开始前还应确认：

- 调度资源已经分配，MPI ranks × OpenMP threads 不超配；
- work 目录空间足够容纳长轨迹；
- 站点配置为 `GMX_DEVICE_MODE=gpu`，CUDA GPU 已由调度器分配且日志映射正确；
- 当前 profile 的科学语义已经批准；
- 长任务由终端直接运行还是应提交给 Slurm。

当前 `agentctl` 直接调用阶段脚本；在批处理系统中应从已分配的作业环境内调用，或先生成并人工审阅站点作业脚本。不要在登录节点直接启动长期 MD。

Slurm 用户可先渲染模板（默认不提交）：

```bash
./scheduler/slurm_profile.sh \
  --mode gpu --profile distance-simulation-only \
  --run-id distance-main-001 \
  --work-root /scratch/glp1-agent-runs \
  --site-config "$SITE" \
  --partition gpu --time 2-00:00:00 \
  --ntasks 1 --cpus-per-task 8 --gpus 1 \
  --allow-long-md
```

只有追加 `--execute` 才调用 `sbatch`。长 profile 提交还必须显式给出 `--time`；模板中的 24 小时只是 dry-run 展示值。历史 RTX 3090 上常规 100 ns 约 13.2 小时；pocket SASA 100 ns 约 44.6 小时，site SASA 10 ns 约 4.25 小时，因此 SASA 合集连同平衡已超过 60 小时。distance 完整主线也很可能超过 24 小时。目标 GPU 必须重新基准测试，必要时用同一参数多次提交 `resume`；终点校验会阻止优雅提前停止被误判为完成。

可给提交包装器增加 `--maxh-per-mdrun HOURS`，让每次 MD integrator 的 GROMACS 调用在该时限附近主动写 checkpoint；该选项不会加到能量最小化。它只作为受控运行参数加入 `-maxh`，不改变 TPR 的 `nsteps`；当次调用会因尚未达到 TPR 终点而以阶段失败结束，下次用同一 run-id 执行 `resume`。

`--maxh-per-mdrun` 是每次 `mdrun` 的计时器，不是整个 Slurm 作业的 deadline 保证；一个 profile 可能在同一作业里连续启动多段。仅当站点能保证每次新调用的剩余墙钟都大于该值加上安全余量时才使用它；否则应按阶段分作业、配置站点预终止信号，或在已验证的调度包装层中动态计算剩余时间。必须为 checkpoint、PLUMED 输出刷新和调度退出预留余量。自由形式的 `GMX_MDRUN_EXTRA_ARGS` 只允许空值或 `-v`，不能注入 `-nsteps`。

模板通过非交互环境直接 source 安装栈，并在首次 `prepare` 时冻结合并后的有效站点参数、安装 `env.sh` 路径及其 SHA-256；任何包含 MDpocket 的完整 profile 还冻结其二进制与 BUILDINFO 摘要。同一 run-id 后续提交若使用不同参数或已冻结文件漂移，会被拒绝。不要同时提交同一 run-id，运行锁会拒绝第二个执行者。仅剩 postprocess/MDpocket 时，Agent 不要求节点上有可见 GPU，但仍验证冻结的 GROMACS 是 CUDA build；动力学阶段绝不降级。

单 rank 默认使用 `direct`。若站点改为 `srun` 或 `mpirun`，必须先在真实 allocation 内用相同 launcher 和 rank 数执行 `tests/smoke_gmx_plumed.sh`，验证 Slurm PMI/PMIx、OpenMPI ABI 与 PLUMED MPI 链路。多节点时，bundle、安装前缀和 work-root 还必须在所有节点上是同一个可见共享路径。`--sbatch-arg` 不允许覆盖由包装器管理的墙钟、rank、CPU、GPU、输出或数组参数。

## 7. SASA 平行 profile 与标准分析的额外确认

历史 DAT 同时施加 metadynamics 与 `BIASVALUE ARG=sasa`。SASA profile 除双门闩外还要求科学 ACK。只运行模拟产物时使用 `historical-sasa-biased-main`；执行完整标准分析时使用：

```bash
./agentctl \
  --site-config "$SITE" \
  --work-root "$WORK" \
  run --profile standardized-sasa-biased-main \
  --run-id sasa-biased-main-001 \
  --execute --allow-long-md --ack-sasa-biasvalue
```

该 run 必须先 `prepare`。若只需要其中一条分支，可使用独立 profile；但不同 run-id 的独立 profile 将重跑随机上游，不能再声称两条轨迹共享历史父态。

该参数表示操作者已经理解并接受历史势能定义，不表示 Agent 判断它在科学上合理。也可在 site 配置中设置 `ACK_SASA_BIASVALUE=yes`，但命令行确认更容易关联到具体 run。

完整 profile 还要求在 `prepare` 前安装固定 fpocket，并冻结其绝对二进制、BUILDINFO 和 SHA-256。SASA full profile 输出包括 `analysis_protocol.tsv`、`analysis_qc.tsv`、`cluster_qc.tsv`、`mdpocket_analysis_protocol.tsv` 与 `pocket_volume_qc.json`；distance 路线沿用其原有结构分析产物并同样输出 pocket-volume QC。辅助 descriptor 列的 NaN/Inf 会报告但不插值；`snapshot` 或 `pock_volume` 非有限、帧数/终点错误仍是硬失败。

当前聚类/RMSD 的 fit group 沿用包含 4 个蛋白组分的冻结 `Protein Backbone`；MDpocket 则为每条分支独立 discovery 后形成 branch-specific ROI。这是历史兼容的探索性分析，不能自动泛化到新 GPCR 复合物，也不能把不同 ROI 的体积直接作为严格条件间定量比较。全流程上游应创建 receptor/TM-core、chain-aware selection 和跨分支公共冻结 ROI。偏置轨迹的 cluster size 与 pocket volume 是描述性结果，未做总偏置 reweighting 时不得称为平衡布居。

使用 `scheduler/slurm_profile.sh` 时，即使 site 文件已有 ACK，提交包装器仍要求显式 `--ack-sasa-biasvalue`，以便把这次高风险决策直接留在提交命令中。

## 8. 状态、失败与续跑

每个 run 的关键目录：

```text
<work-root>/<run-id>/
├── .agent/run.json
├── .agent/site.env
├── .agent/state/<stage>.json
├── inputs/
├── stages/<stage>/
├── commands/<stage>.commands.log
└── logs/<stage>.console.log
```

查看状态：

```bash
./agentctl --work-root "$WORK" status \
  --profile historical-distance-main --run-id distance-main-001
```

中断后续跑：

```bash
./agentctl --work-root "$WORK" resume \
  --profile historical-distance-main --run-id distance-main-001 \
  --execute --allow-long-md
```

阶段只会在完整 manifest 产物存在、日志有完成标记，且当次执行已证明 checkpoint 达到 TPR 计划终点后记为 `complete`。后续 `status`/跳过会重新检查状态、完整产物集、索引帧集与记录的文件大小，但不会在每次查询时重新解析 TPR/CPT。优雅 walltime 停止也可能写出 `Finished mdrun`，因此该字符串本身不是完成证据。非 PLUMED 阶段已有本阶段 CPT 时使用 `-cpi ... -append`；若存在部分输出但没有 CPT，会停止而不是覆盖。

GROMACS checkpoint 不包含磁盘上 PLUMED 文本历史本身。偏置/监测阶段恢复前，Agent 会验证同目录 HILLS/COLVAR 从预期时刻开始、严格按 PACE/STRIDE 单调递增、行数和末尾均与 CPT 时间匹配；任一缺口、重复或“输出领先 checkpoint”都会阻断自动恢复。不要手工拼接或自动截断。

## 9. 运行完成的含义

阶段成功至少要求：

- 能量最小化日志明确报告 `Steepest Descents converged to Fmax`；仅到达最大步数、机器精度停止或只有 `Finished mdrun` 不会被接受；

- 命令退出码为 0；
- manifest 声明的输出存在且非空；
- MD 阶段日志含 `Finished mdrun`，且 checkpoint 时间达到 TPR 的计划终点；
- 没有被忽略的 fatal error、NaN、LINCS/SETTLE 或缺参数问题；
- PLUMED 阶段的 DAT、HILLS、COLVAR 位于本阶段目录；
- 标准分析的终点/帧数、RMSD/SASA 序列、完整 cluster artifact、MDpocket 42 列 schema 和 volume/QC 均通过；
- 实际步数、时间长度、温压和资源映射经过人工或自动解析复核。

这些条件证明任务按计划结束，但不自动证明采样充分、偏置定义正确或科学结论可重复。

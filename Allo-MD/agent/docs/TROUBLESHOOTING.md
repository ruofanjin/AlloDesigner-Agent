# 部署与运行故障排查

排障原则：先停止下游阶段，保存命令、console log、GROMACS log 和 state JSON；不要在原项目或冻结输入上试错，也不要用 `-maxwarn`、`GMX_MAXCONSTRWARN=-1` 或删除 checkpoint 来强行继续。

## 1. 推荐排查顺序

```bash
./agentctl verify-bundle
./agentctl --site-config /path/to/site.env doctor --strict
./agentctl plan --profile <profile>
./agentctl --work-root /path/to/runs status \
  --profile <profile> --run-id <run-id>
```

然后检查：

```text
<run>/logs/<stage>.console.log
<run>/commands/<stage>.commands.log
<run>/.agent/state/<stage>.json
<run>/stages/<stage>/<deffnm>.log
```

全局参数 `--site-config` 和 `--work-root` 必须写在子命令之前。

## 2. `gmx` 或 `gmx_mpi` 找不到

原因通常是只在交互 `.bashrc` 中定义了 alias，或批处理 shell 没有加载 GMXRC。

```bash
source /absolute/path/to/gmx-stack/env.sh
command -v gmx_mpi
gmx_mpi --version
```

在 site 配置中设置真实入口：

```text
GMX_ENV_SCRIPT=/absolute/path/to/gmx-stack/env.sh
GMX_BIN=gmx_mpi
```

不要把 `GMX_BIN` 设置为交互 alias `gmx`。

若打包安装器在构建或验证中失败，当前 prefix 是半安装证据，不是可恢复会话。不要 source `.env.sh.candidate` 或在非空 work-root 上强行重跑；保留日志和旧树供审计，修复原因后选择全新的 prefix/work-root。

## 3. GROMACS 版本、MPI、OpenMP 或 PLUMED 检查失败

执行：

```bash
gmx_mpi --version
gmx_mpi mdrun -h | grep -- '-plumed'
plumed info --long-version
plumed config show | grep 'module sasa on'
plumed gentemplate --action SASA_HASEL >/dev/null
plumed --has-mpi
```

目标应为 GROMACS 2024.3、PLUMED 2.9.3、external MPI、OpenMP 和 SASA module。常见原因是：

- GROMACS 源码在 PLUMED patch 前已经配置；
- 使用了 internal thread-MPI；
- PLUMED 未加 `--enable-modules=sasa`；
- PLUMED 增量构建残留旧对象；
- PATH 指向另一套安装。

解决方法是从干净源码按 [安装指南](INSTALL.md) 完整重建，而不是复制旧 build tree。

## 4. `libmpi.so`、`libplumed.so` 或 CUDA 库找不到

```bash
ldd "$(command -v gmx_mpi)"
gmx_mpi --version
mpicxx --showme
```

检查 `LD_LIBRARY_PATH`、RUNPATH、安装前缀和实际加载的 MPI/PLUMED。PLUMED 与 GROMACS 必须链接同一 MPI ABI。shared patch 通常不需要 `PLUMED_KERNEL`；不要用错误路径掩盖动态链接问题。

## 5. CUDA 失败、GPU 不可见或性能异常

```bash
nvidia-smi
nvcc --version
gmx_mpi --version
```

依次核对：驱动与 Toolkit、host compiler、GPU compute capability、调度器是否分配 GPU、`CUDA_VISIBLE_DEVICES`、日志中的 task mapping，以及 MPI ranks × OpenMP threads。

单 GPU 从 1 rank 开始测试。PLUMED 存在时不要强制 `-update gpu`。本包生产阶段不允许自动降级到 CPU；若目标没有 GPU，只能进行 CPU 安装诊断/零步测试，不能执行冻结生产 profile。

## 6. `MPI_RANKS × OMP_THREADS exceeds ...`

Agent 以 `nproc` 可见值检查超配。容器和集群中应以 cgroup/调度器配额为准：

```text
MPI_RANKS=<实际 rank 数>
OMP_THREADS=<每 rank 实际 CPU 数>
```

不要同时使用 `mpirun` 和 `srun`，也不要对 external MPI 构建传 `-ntmpi`。

## 7. `prepare` 拒绝已有目录

Agent 只接管由自身创建、含 `.agent/run.json` 的目录。若目标目录已存在且不是 Agent run，请选择新的 run-id。不要删除或覆盖未知目录。

site 配置在 prepare 时快照到 `<run>/.agent/site.env`，之后该快照优先。若要更改编译环境、资源模式或科学开关，最清晰的做法是创建新 run-id 并记录差异。

## 8. 未开启长任务门闩

实际执行同时要求：

```text
--execute --allow-long-md
```

缺少任一参数时不应绕过保护。先运行无 `--execute` 的 dry-run，核对 profile、路径、资源和预计计算量。

## 9. SASA gate 被拒绝

历史 SASA DAT 同时含 `METAD` 和 `BIASVALUE ARG=sasa`。阅读 [科学决策](SCIENTIFIC_DECISIONS.md) 后，只有确实要复现该势能定义时才传：

```text
--ack-sasa-biasvalue
```

不要为了让命令通过而盲目设置 ACK。若科学方案只需要 METAD，应建立新的 DAT/profile/run-id。

## 10. SASA action unknown、原子数不符或缺参数

检查：

1. PLUMED 2.9.3 是否以 `--enable-modules=sasa` 干净重建；
2. GROMACS 是否加载目标 PLUMED；
3. DAT 原子编号是否仍对应同一拓扑；
4. `step5_input3.pdb` 与 TPR 原子顺序是否一致；
5. 是否包含 `OXT`、非标准残基、配体或无 HASEL 参数的原子；
6. site/pocket 展开数是否分别为 254/648。

错误的 `*_atoms_wrong` 分支不能作为修复来源。

## 11. `toppar/...: No such file or directory`

每个阶段目录应具有：

```text
topol.top -> ../../inputs/system/topol.top
toppar    -> ../../inputs/system/toppar
index.ndx -> ../../inputs/system/index.ndx
```

检查链接目标、大小写和 run 输入快照是否完整。不要把 `toppar` 复制进全局 GROMACS 数据目录，也不要用其他项目的同名文件替换。

## 12. `grompp` warning 或失败

默认不应通过 `-maxwarn` 自动忽略 warning。查看阶段 console log 和生成的预处理信息，重点核对：

- MDP 与阶段坐标/checkpoint 是否匹配；
- index 中 MDP 引用的组名是否存在；
- topology include 能否解析；
- 温压耦合、continuation 和约束设置；
- `RESTRAINT_REFERENCE_MODE` 是否符合所选历史/修正版协议。

修改科学输入后必须创建新版本和 run-id。

## 13. 中断、部分输出与 checkpoint

`resume` 会跳过重新验证为完整的阶段；未完成阶段若存在本阶段 CPT，则使用：

```text
-cpi <本阶段>.cpt -append
```

若已有 LOG/EDR/XTC 但没有 CPT，Agent 会拒绝覆盖。`Finished mdrun` 也可能来自优雅 walltime 提前停止；Agent 会比较 CPT 与 TPR 终点，未到终点时继续恢复而不会标为完成。保留现场，检查是否能恢复；不确定时使用新 run-id。

不要把上游阶段 CPT 当成同一 deffnm 的中断恢复点。上游 CPT 只可在生成下游 TPR 时按已定义 DAG 使用。

## 14. HILLS/COLVAR 不连续或被覆盖

每个 PLUMED 阶段必须在自己的目录运行。GROMACS CPT 不会自动恢复另一目录的 HILLS。

- `distance_metad_100ns_new_bias` 按历史定义就是新的 HILLS，不应期待与 50 ns 文件连续；
- 同阶段 restart 由 patched GROMACS 在 `-cpi` 时通知 PLUMED；仍必须保留匹配的 HILLS/COLVAR 和 CPT/TPR；Agent 要求时间序列从预期起点按 PACE/STRIDE 完整延伸至 CPT，不能只凭文件非空；
- SASA、距离和 χ 分支不能共享 HILLS/COLVAR 路径。

发现覆盖或时间倒退时停止，不要拼接文件后继续。

## 15. LINCS/SETTLE、NaN 或约束警告

不要设置 `GMX_MAXCONSTRWARN=-1`。检查：

- 初始结构是否有碰撞；
- 步长、约束算法和迭代设置；
- 温度/压力耦合是否稳定；
- checkpoint 是否与 TPR、输出和拓扑匹配；
- PLUMED 偏置力和 CV 是否异常；
- GPU/CPU 模式切换是否暴露数值问题。

修复根因后从明确的健康 checkpoint 或新 run 开始。

## 16. MDpocket profile 无法启动

MDpocket 是 fpocket 套件中的 CPU 后处理程序，不包含在 GROMACS/PLUMED 软件栈中。使用 `install/install_fpocket.sh` 从官方 GitHub 部署固定的 4.2.3/commit，并应用 SHA-256 锁定的 argv 分配修复；当前主实验 profile 要求它时，doctor 会阻断缺少必需 CLI、精确 source/patch provenance、功能 smoke 记录或二进制摘要不一致的安装。provenance 字符串仍应与安装器的 `BUILDINFO.tsv` 一并审核，不能手抄后替代来源验证。

可先运行：

```text
distance-simulation-only
historical-sasa-site
historical-sasa-pocket-100ns
```

先按 [安装指南](INSTALL.md) 第 8 节运行安装器 plan/execute，再把其 `env.sh` 中的绝对 `MDPOCKET_BIN` 和完整 provenance 复制到 site 配置。不要相信帮助横幅中的旧 `fpocket 4.0` 文本，以 Git commit 和 `BUILDINFO.tsv` 为准。

若准备稍后在同一 run-id 补分析，必须在最初 `prepare` 前完成 fpocket 安装，并把绝对 MDpocket 路径与上述 pinned provenance 写入 site 配置；`prepare` 会冻结二进制与 `BUILDINFO.tsv` 的 SHA-256。若最初快照为 `UNRESOLVED`、相对命令名或缺少已安装文件，不可事后修改该 run 的站点快照；应建立新 run-id 或设计经审计的数据导入流程。不能把未执行 MDpocket 的结果标记为 distance/SASA full profile 完成。

## 17. 标准化 SASA 分析失败或结果含 NaN

先区分模拟与分析：`sasa_*` 是受门闩保护的历史偏置模拟；`postprocess_sasa_*`/`mdpocket_sasa_*` 是新增 `standardized-analysis`，不会更改轨迹或偏置。

- `gmx sasa` selection 失败：确认输入是含 237383 原子的原始完整体系 XTC，`sasa_analysis.ndx` 中有 `SOLU_MEMB` 与其子集 `Allosteric_Site`；不能拿只含 7952 个蛋白原子的 `aligned.xtc` 计算含膜 surface。
- 终点/帧数失败：site/pocket 10 ns 必须为 0–10000 ps、101 帧；pocket 100 ns 必须为 0–100000 ps、1001 帧，间隔均为 100 ps。不要把来源歧义的 50 ns 文件塞入这些 stage。
- 聚类存在部分文件但无 receipt：保留现场并换新 run-id；不要把截断的 XPM/PDB 当完成结果。
- descriptor 辅助列含 NaN/Inf：查看 `pocket_volume_qc.json`。只要 `snapshot` 连续且 `pock_volume` 有限非负，稀疏口袋导致的辅助非有限值会被保留和计数；禁止静默置零/插值。关键列非有限仍会失败。
- site/pocket 各自 discovery 后产生的 ROI 可能不同，不能只凭 volume 直接横向归因。新研究应由上游预注册一个 chain-aware 公共 ROI；本版 0.5/1 Å 参数用于历史可比的探索性分析。

这些输出来自 biased trajectory。cluster population、RMSD 或 pocket volume 异常不等于平衡自由能变化；先检查偏置、reweighting、block/replica 收敛及 selection 定义。

## 18. 状态显示 complete 但科学结果可疑

`complete` 表示程序退出、完整产物集合存在、记录大小未改变，且 MD checkpoint 已达到 TPR 终点；还需人工或扩展验证：

- 日志达到预期步数；
- 无 fatal、NaN、LINCS/SETTLE 和参数警告；
- GPU/MPI/OMP 映射合理；
- CV、HILLS、COLVAR 时间轴符合所选分支；
- 若项目另行建立了版本化 golden 基线，则在其预先规定的容差内一致；本 bundle 当前未附 numerical golden。

不要把调度完成等同于科学验收。

# 历史过程复核与推荐设计决策记录

本文件列出自动执行前必须明确的科学语义。原则是：

1. 历史输入保持冻结，用于回答“可追溯过程怎样运行”；
2. 推荐设计使用新文件、新 profile、新 run-id，回答“现在认为怎样运行更合理”；
3. 不允许在同一结果目录中混合两者，也不能把历史笔记、原始生成器协议和新增分析混称为“精确复现”。

## 1. 平衡阶段的位置约束参考

原始 CHARMM-GUI README 让 eq1–eq6 始终使用初始 `step5_input.gro` 作为 `-r`；这是本包推荐默认值：

```text
RESTRAINT_REFERENCE_MODE=charmm_gui_initial
```

已执行历史 TPR 与后来的 `GLP1_gmx_comand.sh` 命令笔记则逐段把上一阶段 GRO 同时作为 `-c` 和 `-r`：

```text
RESTRAINT_REFERENCE_MODE=historical_previous
```

这会不断更新约束参考；对原目录 eq1–eq6 TPR 的 `gmx dump` 检查确认 1189 个位置约束原子的 reference 去平移后均匹配各自上一段 GRO（最大 RMS 差小于 `4×10⁻⁶ nm`）。因此 `historical_previous` 用于复核实际历史，`charmm_gui_initial` 是遵循原始 builder recipe 的有意修正。选择必须写入 site 配置和 run provenance，两种模式不得共用 run-id。

## 2. 常规 MD 的时间关系

审计现有 TPR/日志得到：

- `step7_1`、`step7_2`、`step7_3` 的 x/v/box 起点一致，均从 eq6 独立启动；
- 它们各自记录 10、50、100 ns，时间从 0 开始；
- `step7_4` 从 100 ns 末态启动，再运行 200 ns，但新 TPR 的 `init-step` 和时间仍从 0 开始。

因此：

- 历史复现不得执行陈旧笔记中的 10→50→100 串联；
- 不得把四份轨迹称为连续 360 ns；
- 若新研究要求单一连续时间轴，应另建 MDP/TPR 方案，核对 `tinit`、`init-step`、`nsteps`、`simulation-part`、`continuation` 和 checkpoint，不能修改当前 profile。

## 3. 距离监测阶段不是偏置或 SASA

历史文件名含 `biased_sasa`，但正确 DAT 只定义 48 个 `DISTANCE` 和 `PRINT`：

- 没有 `METAD`；
- 没有 `SASA_HASEL`；
- 该阶段应称为 `distance_monitor_50ns`。

错误命名不能作为科学含义依据。

## 4. SPIB 距离偏置输入被冻结

`distance_metad.dat` 保存 48 个距离、`sigma1/sigma2` 线性系数及二维 metadynamics 参数。原始 SPIB 项目、训练权重和部分生成路径位于本项目之外，旧生成脚本还漂移到 AF2-rank1 数据。

所以历史复现以冻结 DAT 为权威，不自动重新训练或重建系数。若要重新训练，必须同时版本化：

- 输入距离轨迹及摘要；
- 数据切分、lag、随机种子和软件环境；
- 模型权重；
- 生成后的 DAT 与旧 DAT 的差异。

## 5. 距离偏置 50→100 ns 不是严格 restart

历史 100 ns 后段使用偏置 50 ns 的末态坐标和 checkpoint，但新目录中的 HILLS 从头开始，DAT 也没有继承旧 HILLS 的明确 restart 语义。

因此当前阶段名为：

```text
distance_metad_100ns_new_bias
```

它是“从旧末态启动的新偏置历史”，不是连续的 150 ns metadynamics。科学修正版若要真正续接，必须使用匹配的 biased TPR/CPT、原 HILLS/COLVAR、PLUMED `RESTART`，并验证 step/time、高斯编号和偏置能连续；应创建新阶段，不能重用当前名称。

## 6. SASA 原子选择与拓扑绑定

PLUMED `ATOMS` 是从 1 开始的全局原子编号，不是残基号或 index 组编号。当前冻结选择仅适用于包内这套拓扑和原子顺序：

| 选择 | 预期原子数 |
|---|---:|
| allosteric site | 254 |
| 参考口袋 8 Å 集合 | 648 |

当前正确列表排除了缺少 HASEL 参数的终端 `OXT`。新体系若增加配体、端基、非标准残基或重排分子，必须重新生成并验证选择；不能继续使用旧数字。

开始生产前至少要验证：

- TPR、`step5_input3.pdb`、topology 和 DAT 的原子顺序一致；
- 展开的原子数符合上表；
- PLUMED 日志没有 unknown atom 或缺少 SASA 参数；
- 若目标团队建立了固定帧 golden 基线，则新系统上的 CV 应在预先规定的容差内一致。

## 7. SASA 的 `BIASVALUE` 科学门闩

两个历史 SASA DAT 都同时包含（参见 PLUMED 2.9 的 [SASA 模块](https://www.plumed.org/doc-v2.9/user-doc/html/_s_a_s_a_m_o_d.html)与 [`BIASVALUE`](https://www.plumed.org/doc-v2.9/user-doc/html/_b_i_a_s_v_a_l_u_e.html) 文档）：

```text
METAD ARG=sasa ...
bias: BIASVALUE ARG=sasa
```

`BIASVALUE` 不是变量别名或仅用于输出，而是把 SASA 数值本身作为额外偏置势；它会与 metadynamics 同时作用。PLUMED 默认单位下 SASA 为 nm²，而偏置能为 kJ/mol，这一线性尺度需要明确物理依据。

因此历史 SASA profile 必须额外传入：

```text
--ack-sasa-biasvalue
```

或设置 `ACK_SASA_BIASVALUE=yes`。ACK 只表示知情接受历史定义，不代表科学审查通过。

若修正版只需要 metadynamics，应复制 DAT 到新的文件、删除 `BIASVALUE`、调整 `PRINT`，建立新 profile 并做短程数值验证。禁止原地修改 `inputs/plumed/sasa_*/*.dat`。

## 8. SASA 的物理定义

`SASA_HASEL TYPE=TOTAL ATOMS=<pocket>` 只把所列原子作为计算对象和相互遮挡体。它不自动等于“完整蛋白表面环境中口袋原子的 SASA 贡献”。

若研究问题需要完整蛋白作为遮挡 surface、口袋作为 output 子集，应重新确认方法，或在轨迹后处理中使用具有独立 `surface`/`output` selection 的 [`gmx sasa`](https://manual.gromacs.org/documentation/2024.3/onlinehelp/gmx-sasa.html)。不能在报告中把两种定义混称为同一 SASA。

本包的标准化 SASA 后处理另行运行 GROMACS 原生算法，固定为：

```text
surface = SOLU_MEMB（本体系全部非溶剂原子）
output  = 变构位点全原子子集
probe   = 0.14 nm
ndots   = 24
```

该输出描述完整非溶剂 surface 中位点子集的暴露，是对轨迹的诊断；它既不等于 PLUMED `SASA_HASEL ATOMS=<subset>` 的在线 CV，也不会改变已经施加的偏置。

## 9. 可追溯 SASA 路径和长度边界

当前可安全进入历史执行 manifest 的是：

- allosteric-site 10 ns：254 原子，从 `normal_100ns` 末态独立启动；
- 8 Å pocket 10 ns：648 原子的短程对照；
- 8 Å pocket 100 ns：与 10 ns 使用同一冻结 DAT，从 `normal_100ns` 末态独立启动的正式长分支。

site 10 ns 的历史产物到 10000 ps 完整，pocket 100 ns 的历史产物到 100000 ps 完整；每条分支的 TPR 时间轴都从 0 开始并各自建立 HILLS/COLVAR。它们与 distance 主线科学上并列，不能描述为 distance 的后续分析。

项目中的 SASA 50 ns 标签/分析来源存在歧义，正确目录没有足够配置证明；错误原子号目录也含相似时长。部署 Agent 不得根据目录名猜测 site/pocket 50 ns，也不得简单延长 MDP 后宣称复现了缺失实验。

这两条正式 SASA 路径都只有单轨迹历史证据，没有重复轨迹或收敛证明；site 与 pocket 的初始 SASA 尺度不同却共用 `SIGMA/HEIGHT`，不能把二者直接解释为等强扰动比较。

## 10. SASA 分析的证据等级

原项目可确认：site 10 ns 和 pocket 10 ns 各做过 4 条 RMSD 与 101 帧 MDpocket；没有 SASA 支线的历史聚类。正式 pocket 100 ns 有完整 biased MD，却没有可追溯的 RMSD、聚类或 MDpocket 目录。两个标作 50 ns 的分析树缺少对应 PLUMED DAT/运行日志且名称相互混淆，不能证明用了正确的 254/648 原子 CV，故不进入 DAG。

本版增加的统一 PBC、RMSD、Gromos cutoff 矩阵、原生 `gmx sasa` 和 MDpocket，均标为 `standardized-analysis`：

- 复用冻结 NDX 便于同一体系内比较，但不声称是历史字节复现；
- pocket 100 ns 是新增分析，不是补录历史完成状态；
- fpocket 4.2.3 是新的固定部署版本，不能期待与未知历史版本逐字节一致；
- 0.5 density isovalue、1 Å ROI 和聚类 cutoff 是预注册的比较参数，不是从结果中挑选的最优值，也不保证适用于新体系；
- 新体系应由上游生成 chain-aware receptor/TM-core fit group 和公共 ROI，不能照搬残基号或全复合物对齐策略。

当前实现为历史兼容的探索性再分析：轨迹按包含 4 个蛋白组分的全 `Protein Backbone` 拟合，每个分支先独立生成 density，再取该分支 grid 与目标残基邻域的交集作为 selected ROI。不同分支的 ROI 因而可能不同，体积序列不能直接当作同一固定几何区域上的条件间定量比较。新研究必须预先注册 receptor/TM-core fit group，并让所有配对分支使用同一个冻结 shared ROI；分支 discovery 只用于探索。

五条 RMSD 曲线都以各自 SASA 分支 TPR 的 t=0（即该分支所继承的 normal100 parent state）为参考，并再次用各自的测量 selection 做最小二乘拟合；它们不是相对 5VEX 的 RMSD。只有另行命名的 `rmsd_5vex_vs_clusters_*` 才把 60 原子代表构象与 5VEX 位点比较。selection、原子数和参考语义均写入 `analysis_protocol.tsv`。

RMSD、cluster size 和 pocket volume 只能描述被偏置轨迹。未做针对**总偏置**的正确 reweighting、block/replica 收敛和不确定度分析时，cluster population 不能解释为平衡构象布居或自由能概率，SASA 增大也不能直接等同真实配体口袋开放或可成药性增强。

MDpocket descriptor 中，稀疏/零口袋帧的某些非关键派生列可能为 NaN。本包只把 `snapshot` 或 `pock_volume` 非有限视为硬失败；其他列保留原值、不插值，并在 QC 中逐列报告 non-finite/zero 比例。

## 11. 推荐的新研究设计（尚未自动化生产）

冻结 `historical-*` profile 继续回答“原过程怎样运行”。新的研究设计应至少完成下列预注册后，另建 DAT/MDP/profile/run-id：

1. 先在无偏轨迹上定义并表征 CV；明确需要 subset 自遮挡还是完整蛋白/膜环境下的暴露。
2. 默认不继承 `BIASVALUE ARG=sasa`；若保留，必须给出额外线性势的单位、系数和物理依据。
3. site 与 pocket 分别由无偏波动/短程校准确定 `SIGMA`、`HEIGHT`、PACE 和边界，不能因为历史共用参数就照搬。
4. 从开始就建立目标总长度的连续协议；同一偏置 run 用匹配 TPR/CPT/HILLS/COLVAR 严格 restart，不能重置 HILLS 后称为连续。
5. 每个条件预先固定整数 seed 和独立 parent replica；建议从至少 3 个独立 parent 起步，但是否充分仍由预注册收敛指标决定。每个 parent 内的 distance/site/pocket fan-out 是配对条件，不是独立重复。
6. 预先规定 block、跨 replica 一致性、CV 覆盖、HILLS/偏置收敛、reweighting 和停止标准；结果后延长不能替代设计。

当前包没有凭空选择这些科研参数，因此不提供会被误认为已批准的 `recommended-sasa-production` profile。

## 12. 明确排除的错误和失败分支

以下内容永远不进入可执行 DAG：

```text
plumed_distance_atoms_wrong/
plumed_sasa_atoms_wrong/
plumed_sasa/ce/
```

前两者把残基号误当 PLUMED 原子号；`ce/` 是失败/调试分支。`bck.*`、`#...#`、`* copy.*`、空 HILLS 和自动备份也不是独立实验输入。

## 13. 约束警告不能被全局屏蔽

禁止设置：

```bash
GMX_MAXCONSTRWARN=-1
```

它可能掩盖 LINCS/SETTLE 不稳定。出现约束警告时应检查初始结构、步长、约束、温压耦合、GPU/CPU 数值行为和 checkpoint 连续性；修复原因后重新建立 run。

## 14. 版本和计算平台差异

历史目标软件栈是 GROMACS 2024.3 + PLUMED 2.9.3 SASA、mixed precision、external MPI。不同 SIMD、GPU、MPI rank/OpenMP thread 或驱动可能产生浮点级差异，不能期待长轨迹逐位相同。

可复现性应分层报告：

1. 输入和 DAT 摘要一致；
2. 软件功能和回归测试通过；
3. 若另行建立了版本化 golden，短程 CV/能量在预定容差内相符；
4. 长程统计结论在合理误差和重复实验中一致。

仅有 `gmx_mpi --version` 正常不等于上述四层均已满足。

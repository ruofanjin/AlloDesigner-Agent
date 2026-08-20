# 部署包来源与变更记录

## 1. 范围

本部署包整理自：

```text
/root/data1/data/move/ZYY/zyy/works/GPCRs_MD
```

重点实验来源：

```text
GLP1/interation1_shuffle8_group37/
```

主要审计依据：

- `项目快速导览.md`；
- `GROMACS_PLUMED_SASA_安装配置指南.md`；
- `GLP1/gmx_comand.sh`；
- iteration1 的 MDP、DAT、topology、index、日志、TPR/CPT 和已有分析目录；
- 当前主机的软件版本、动态链接和 PLUMED SASA 功能检查。
- 用户指定的[膜蛋白体系教程](https://zhuanlan.zhihu.com/p/553850783)作为二级操作参考；本次环境无法稳定抓取其全文，因此命令和科学边界实际以 [CHARMM-GUI Membrane Builder](https://charmm-gui.org/?doc=tutorial&project=membrane) 与 [GROMACS 官方膜蛋白教程](https://tutorials.gromacs.org/docs/membrane-protein.html)核对。

整理基准日期为 2026-08-12。这里记录的是当时可审计状态，不证明目标系统已经构建或测试成功。

## 2. 软件源码来源

部署归档来自当前主机 `/root/lnq/md/`，复制到 `install/sources/`。固定 SHA-256：

```text
bbda056ee59390be7d58d84c13a9ec0d4e3635617adf2eb747034922cba1f029  gromacs-2024.3.tar.gz
0abf3098d11a8720d6f8d0b65df6a8da5ccd013c7b4a8ddbbc86229066d7d640  plumed2-2.9.3.tar.gz
56c932549852cddcfafdab3820b0200c7742675be92179e59e6215b340e26467  fftw-3.3.10.tar.gz
e357043e65fd1b956a47d0dae6156a90cf0e378df759364936c1781f1a25ef80  openmpi-5.0.1.tar.bz2
2984e70515ff60c5e4a41922b5d715a8168a696a89721e3b114e36f453244f72  cmake-3.31.5-linux-x86_64.tar.gz
```

CUDA runfile、已安装二进制、当前 build tree 和 `.bashrc` 没有进入部署包。CUDA 驱动/Toolkit 必须按目标系统重新选择；虽然安装介质不打包，冻结生产 MD 阶段明确要求 CUDA GPU。

MDpocket 的历史 commit 不可恢复。本版选定的可审计部署来源是官方 `https://github.com/Discngine/fpocket.git`，tag 4.2.3、commit `4bb0d8447f62fee77e2c3c29f54b5fcaf5e2c066`；源码由独立安装器执行时获取，不属于上述离线归档，也不冒充历史原版本。固定上游 `mdparams.c` 的 argv 分配会越界，因此实际部署还包含包内最小修复，补丁 SHA-256 为 `6ed7a0e8280f10ae0d42c42d771b4a3083e7891d007898bc19f7148bb433481d`。

## 3. 冻结体系输入

以下内容从 iteration1 的当前复现过程提取为阶段性冻结快照，运行时不应修改：

| 打包路径 | 历史来源/含义 |
|---|---|
| `inputs/system/step5_input.gro` | CHARMM-GUI 构建后的完整膜、水、离子体系 |
| `inputs/system/step5_input3.pdb` | PLUMED `MOLINFO` 使用的蛋白参考 PDB |
| `inputs/system/topol.top` | 主 topology，使用相对 `toppar/...` include |
| `inputs/system/index.ndx` | 项目原始 index |
| `inputs/system/toppar/*.itp` | 四个蛋白组分、POPC、离子和 TP3 参数 |
| `inputs/mdp/equilibration/*` | 最小化和 eq1–eq6 MDP |
| `inputs/mdp/normal/*` | 10/50/100/200 ns 常规 MDP |

`prepare` 会为每个 run 创建输入快照。阶段输出不会写回这些文件。未来全流程 Agent 应从上游建模、拓扑和原子选择步骤规划或生成同类输入；当前版本没有这项能力，不能把本快照当作新体系模板。

当前 topology/README 还能确认 CHARMM-GUI 3.7、`AMBER FF in GROMACS format`、4 个蛋白组分、383 POPC、161 K⁺、162 Cl⁻ 和 59,262 TP3。没有足够 metadata 证明精确的 AMBER 蛋白/脂质子版本，也不能声称教程示例的力场就是本项目力场。未来构建约束见 `docs/MEMBRANE_SYSTEM_BUILDING.md` 和 `manifests/membrane_build_contract.json`。

## 4. PLUMED 与增强采样输入

打包时使用语义化文件名，但冻结内容源自现有正确分支：

| 打包路径 | 历史来源/说明 |
|---|---|
| `inputs/plumed/chi/chi_monitor.dat` | iteration1 χ1–χ5 监测定义 |
| `inputs/plumed/chi/chi_metad.dat` | 已归档 χ 降维偏置定义 |
| `inputs/plumed/distance_monitor/distance_monitor.dat` | 正确原子索引的 48 距离 DAT；仅 DISTANCE+PRINT |
| `inputs/plumed/distance_metad/distance_metad.dat` | 48 距离、冻结 SPIB 系数和二维 METAD |
| `inputs/plumed/sasa_site/sasa_site.dat` | 正确 allosteric-site SASA，254 个原子 |
| `inputs/plumed/sasa_pocket_8A/sasa_pocket_8A.dat` | 正确 8 Å pocket SASA，648 个原子 |

文件重命名是为了消除历史名称中的 `biased_sasa` 等误导；科学内容没有因重命名而改变。`manifests/input_checksums.sha256` 记录每个冻结文件的摘要，验证工具同时检查关键 DAT 结构和原子计数。

SPIB 原始训练项目与权重不完整地位于本项目之外，因此部署包不宣称能够重新训练得到相同系数。历史执行以冻结的 `distance_metad.dat` 为权威。

## 5. 已核实的历史阶段关系

审计 TPR/日志与输入状态后，将工作流解释为：

```text
minimization → eq1 → ... → eq6
eq6 → 独立 normal 10 ns
eq6 → 独立 normal 50 ns
eq6 → 独立 normal 100 ns
normal 100 ns 末态 → 新的 200 ns 常规段，时间轴归零
normal 100 ns 末态 → distance monitor 50 ns
distance monitor 50 ns 末态 → distance metad 50 ns
distance metad 50 ns 末态 → 新 HILLS 的 distance metad 100 ns
normal 100 ns 末态 → SASA site 10 ns 独立分支
normal 100 ns 末态 → SASA 8 Å pocket 100 ns 独立分支（另保留 10 ns 对照）
```

这纠正了旧 `gmx_comand.sh` 所暗示的 10→50→100 串联，但没有重写历史科学参数。

## 6. 分析输入来源

`inputs/analysis/` 汇集主距离偏置 50 ns 后处理所需的小型选择和参考文件：

- protein backbone；
- TM6–TM7 与 TM6–ECL3–TM7 backbone；
- 变构位点全原子和 backbone；
- `5vex_holo_convert_apo_id_allosteric_site_2A.pdb`。

原分析脚本中的绝对路径、交互组号和裸中文标题没有进入可执行脚本。原件保存在 `reference/original_scripts/`，仅供追溯。

SASA 分析的历史证据经单独审计：site 10 ns 与 pocket 10 ns 各有 101 帧（0–10000 ps、100 ps 间隔）的 4 条 RMSD 和 MDpocket 结果；两者都没有聚类。正式 pocket 100 ns 轨迹有 1001 帧（0–100000 ps），但没有相应分析目录。两个 50 ns 树缺少能证明正确 SASA DAT/原子集合的 provenance，故隔离而不进入 manifest。

证据路径和生产轨迹摘要如下；这些大文件仅在原项目中审计，没有复制进 bundle：

| 证据 | 原项目相对路径 | SHA-256/结论 |
|---|---|---|
| site 10 ns TPR/XTC | `gromacs/plumed_sasa/10ns/biased_sasa_allosteric_site_10ns_from_step7_3.{tpr,xtc}` | TPR `0ba6e61d7e4001ef99720549b04d3255646ae5add14be31c02e1f30cda172914`；XTC `308f62ffd62921be743976a884f61ac20af8bedc8413d2549c80c3bad82b5d4b`；101 帧 |
| site 10 ns RMSD | `deal_md/sasa_allosteric_site/10ns/` | 4 条 101 点 XVG；无 cluster |
| site 10 ns MDpocket | `mdpocket/plumed_sasa/10ns/` | 101 帧、42 列 descriptor |
| pocket 10 ns TPR/XTC | `gromacs/plumed_sasa/8.0A_pocket/10ns/` | TPR `85fd1594ae67415341582f23fbc5c75708be1b364d811a466ccda4b0a6abb169`；XTC `8a276413c0472987232d1c160738eb863ae8a267d2e2ce7bcc21170127336030`；101 帧 |
| pocket 10 ns RMSD/MDpocket | `deal_md/sasa_holo_8A_pocket/10ns/`、`mdpocket/plumed_sasa/8.0A_pocket/10ns/` | 4 条 RMSD、101 帧 descriptor；无 cluster |
| pocket 100 ns TPR/XTC | `gromacs/plumed_sasa/8.0A_pocket/100ns/` | TPR `742f9d0b47d2b7f4563e0ce441d6842e23431f6293055709e287fd7c92a775a4`；XTC `002fd21555e54373f01ababefe9f5ee048179e4083366b929c7b8468394102eb`；1001 帧；无对应分析树 |

这些历史大产物的摘要用于来源审计，不会被 Agent 当作当前 run 的完成标志。机器执行仍以本包输入 manifest 和运行时产物 QC 为准。

本版统一添加的 RMSD、聚类、原生 `gmx sasa` 与 MDpocket 被标为 `standardized-analysis`。它重放已确认的 10 ns 分析意图并把同一预注册矩阵扩展到 100 ns；这不等于历史分析已经完成，也不保证使用当前固定 fpocket 版本会得到历史未知版本的字节相同结果。

## 7. 明确排除的内容

`manifests/exclusions.txt` 记录不可执行内容，主要包括：

- `plumed_distance_atoms_wrong/`：残基号误作 PLUMED 原子号；
- `plumed_sasa_atoms_wrong/`：相同类型错误；
- `plumed_sasa/ce/`：失败/调试分支；
- 来源无法闭合的两个 SASA 50 ns 分析树；
- `bck.*`、`#...#`、`* copy.*` 和 lock；
- `mdout.mdp` 等生成物；
- TPR/CPT/XTC/TRR/EDR/LOG/HILLS/COLVAR 等历史输出。

这些排除项可以在原项目中用于审计，但不能被 Agent 当作输入或成功证据。

## 8. 冻结流程与推荐设计边界

部署包的模拟阶段标为 `frozen-simulation`，表达冻结输入和可追溯分支关系，不承诺位级复现。站点示例的推荐默认行为包括：

- `RESTRAINT_REFERENCE_MODE=charmm_gui_initial`，与原始 CHARMM-GUI README 一致；
- 常规独立分支及时间归零；
- 距离 100 ns 后段使用新的 HILLS；
- SASA DAT 同时保留 METAD 与 BIASVALUE，并设置显式 ACK 门闩。

已执行历史 TPR 与后来的命令笔记行为可用下列显式开关复核：

```text
RESTRAINT_REFERENCE_MODE=historical_previous
```

该模式逐段更新 `-r`；原目录 eq1–eq6 TPR 中 1189 个约束原子的 reference 去平移后均匹配各自上一段 GRO（最大 RMS 差小于 `4×10⁻⁶ nm`）。它与 CHARMM-GUI 原始 README 冲突，说明历史执行偏离了 builder recipe，而非说明历史未发生。运行态语义以 `prepare` 时冻结的 site snapshot 为准；推荐默认值不能声称复现历史平衡 TPR。

连续时间轴、严格 PLUMED restart、移除 SASA BIASVALUE 或重定义完整蛋白遮挡 SASA，都需要新 DAT/MDP、profile、run-id 和 provenance；不能覆盖冻结输入。

标准化分析不是对历史偏置势的静默修正：它只读取已完成轨迹，输出统一结构/口袋诊断和 QC。新的推荐生产设计仍必须先校准 CV/偏置、确定 replica/reweighting/收敛策略，再创建新的可执行输入。

## 9. 环境基线与可移植性

审计主机基线包括 Ubuntu 20.04 x86_64、GROMACS 2024.3、PLUMED 2.9.3、OpenMPI 5.0.1、FFTW 3.3.10、CUDA 12.2 和 RTX 3090。该表只用于比较，不要求目标主机硬件完全相同。

目标主机必须重新构建并记录：

- OS、CPU/SIMD、GPU、驱动、Toolkit 和 compiler；
- OpenMPI/FFTW/PLUMED configure 参数；
- GROMACS CMakeCache 和 ctest；
- PLUMED SASA regtest；
- `gmx_mpi --version`、动态库解析和 smoke test；
- MPI ranks、OpenMP threads、GPU mapping 和调度资源。

不同硬件上的长轨迹通常不会逐位相同。验收应以输入摘要、功能测试，以及未来另行建立的短程数值基线和长程统计一致性分层判断；本版本没有附带 numerical golden。

## 10. 测试声明

整理时（2026-08-12）在来源主机以 1 MPI rank/CPU 模式真实执行了包内 0-step 联调：`grompp` 成功，patched `mdrun` 初始化 `SASA_HASEL`、正常结束并写出含有限数值数据行的 `COLVAR_smoke`。该测试不推进生产采样，临时目录已清理；它不能代替目标机验收。来源主机现有 PLUMED 可执行文件本身未报告 MPI 支持，因此这次结果也不能作为多 rank 证据。CPU 联调不改变本版生产阶段要求 CUDA 的部署政策。

fpocket 4.2.3 固定 commit + 固定补丁的安装器已在全新隔离临时前缀完成 clone、补丁集核对、串行 build、用户前缀 staging、help/XTC CLI 声明与动态链接测试。还真实执行了官方 10-PDB discovery 和 selected-pocket 样例：生成非空有效 DX，以及 10 行连续 snapshot、严格 42 列且全有限数的 descriptors。安装器记录补丁、MDpocket 二进制 SHA-256 和 BUILDINFO。该小样例不等于实际读取 XTC、目标系统安装成功或本实验 501 帧的 stage 验收。

本 provenance 记录的是文件审计、整理依据和预期验证方式。它不声称：

- 目标系统上的源码已经成功编译；
- ctest 或 PLUMED regtest 已在目标系统通过；
- 任一长模拟已由本部署包重新运行；
- MDpocket 已在目标系统安装或验证；
- 历史参数已经获得新的科学合理性审查。

实际结果必须写入各 run 的 `.agent/state/`、commands、logs 和独立环境记录后，才能形成该次部署的验收证据。

# 部署 Agent 操作契约

你正在操作一个具有昂贵计算、固定科研输入和历史协议歧义的分子动力学工作流。以本文件为最高层执行约束，具体命令见 `README.md` 与 `docs/`。

## 不可跳过的顺序

1. 读取 `README.md`、`docs/SCIENTIFIC_DECISIONS.md`、`docs/FUTURE_FULL_FLOW.md`、`docs/MEMBRANE_SYSTEM_BUILDING.md`、`manifests/stages.json`。
2. 执行 `./agentctl verify-bundle`；失败时停止，不修补冻结输入来绕过检查。
3. 准备站点配置，并执行 `./agentctl --site-config ... doctor`。
4. 用 `agentctl plan` 展示选择的 profile、依赖、长任务和科学门闩。
5. 确认作业配额、scratch 容量、GPU/CPU 和墙钟时间后才 `prepare`。
6. 先执行不带门闩的 dry-run。未经操作者明确授权，不添加 `--execute --allow-long-md`。
7. 真正执行只通过 `agentctl run/resume`，不直接调用阶段脚本；阶段入口会拒绝缺少编排器标记或不满足 per-stage CUDA 要求的调用。
8. 每个阶段结束后检查 `.agent/state/`、`logs/`、GROMACS 日志中的 `Finished mdrun`、GPU 映射和 PLUMED 动作。

## 安全与数据规则

- 包目录是只读部署物；运行输出只能写入显式 `--work-root/RUN_ID`。
- 不覆盖已有非 Agent 目录，不删除旧轨迹，不把不同 run-id 的 checkpoint/HILLS 混用。
- 不依赖 `alias gmx`；使用安装环境中的 `gmx_mpi`。批处理脚本 source 独立 `env.sh`，不依赖 `.bashrc`。
- 不设置 `GMX_MAXCONSTRWARN=-1`，不以提高警告上限掩盖拓扑或约束问题。
- 不执行 `reference/original_scripts/`；其中含旧绝对路径、交互输入、过时文件名和已证伪顺序。
- 不导入 `manifests/exclusions.txt` 中列出的错误/失败分支，尤其 `*_atoms_wrong` 和 `plumed_sasa/ce`。
- 不把大轨迹、HILLS、COLVAR、拆帧 PDB 或 MDpocket 网格复制回部署包。

## 科学不变量

- 系统必须为 237383 个原子，蛋白 `SOLU` 为系统前 7952 个原子；PDB、TPR、NDX、轨迹和 PLUMED DAT 的顺序必须一致。
- PLUMED 原子号是 1-based 全局原子序号，不是残基号。
- 距离主线的 48 个 CV 与二维 SPIB 权重以冻结 DAT 为准。缺失的训练权重不是可自动推断的数据。
- `normal_10ns/50ns/100ns` 是同一 eq6 起点的独立分支。只有 200 ns 常规段继承 100 ns 末态，且它的输出时间轴重置。
- 距离 100 ns 偏置支线继承 50 ns 末态的坐标/速度但不继承其 HILLS。不得把它描述为严格连续偏置。
- SASA site 10 ns 与 pocket 100 ns 是从 `normal_100ns` 独立分叉、与 distance 同级的 biased MD 实验；不得串联。它们保留历史 `METAD + BIASVALUE` 行为，在得到科研确认前不运行，确认后仍需显式门闩并记录决策。
- SASA 后处理的 RMSD、聚类、完整非溶剂 surface `gmx sasa` 和 MDpocket 属于 `standardized-analysis`，不是历史模拟输入的静默修改。不得把 biased trajectory 的 cluster/volume 当作未加权平衡布居；辅助 descriptor NaN 只能记录到 QC，不得插值。
- `RESTRAINT_REFERENCE_MODE=charmm_gui_initial` 是推荐默认值，也与原始 CHARMM-GUI README 一致；`historical_previous` 对应已执行历史 TPR 与后来的命令笔记。两种模式都必须记录，且不得混用同一 run-id；使用推荐默认值时不可声称重现了历史平衡 TPR。
- 当前 `inputs/` 是从本次复现过程提取的冻结快照。未来全流程 Agent 应由上游规划/生成这些输入；本版未实现该能力，不得擅自替换、外推原子号或绕过哈希。
- 跨膜体系默认由可审计的 CHARMM-GUI Membrane Builder 上游生成；纯 GROMACS 路线只允许在已有定向结构、预平衡膜片和兼容 topology 的专家流程中使用。未满足 `manifests/membrane_build_contract.json` 时不得交付新体系。
- 平衡与所有冻结生产 MD 阶段要求 `GMX_DEVICE_MODE=gpu`。CUDA 驱动/Toolkit 由站点提供且不在 bundle 中；`steep` 最小化自动选择受支持的路径，CPU 其余用途只限诊断或零步 smoke，不能静默降级动力学生产段。

## 失败处理

- 环境、哈希、原子数、依赖或科学门闩任一检查失败：停止并报告证据，不自动降级。
- 有本阶段 checkpoint：使用 `agentctl resume`；非 PLUMED 阶段会对同一 TPR 执行 `-cpi -append`。PLUMED 阶段只有在 HILLS/COLVAR 时间序列与 checkpoint 可严格对齐时才自动续跑，否则保留现场并停止。
- 有部分输出但无 checkpoint：保留现场，换新 run-id；不得覆盖或猜测恢复状态。
- `SASA_HASEL unknown`、`mdrun` 无 `-plumed`、共享库 `not found`、MPI 工具链混用或 GPU kernel 不兼容：回到安装验收，不靠调整实验输入规避。
- MDpocket 暂不可用时可使用 `distance-simulation-only` 或历史 SASA simulation-only profile。标准部署入口是固定官方 tag/commit 的 `install/install_fpocket.sh`；若计划稍后在同一 run-id 补分析，必须在 `prepare` 前完成安装并冻结其绝对 `MDPOCKET_BIN`、二进制/BUILDINFO 哈希与 provenance，站点快照不能事后修改。未预先冻结时使用新 run-id/经审计的数据导入方案，不得偷偷换环境。

## 结果报告最低要求

报告 bundle 版本、run-id、profile、每阶段 `protocol_class`、站点配置快照、GROMACS/PLUMED/MPI/CUDA/fpocket 版本、ranks×threads、GPU 映射、每阶段状态、随机种子语义和所有偏离历史协议的改动。不得把“命令成功启动”表述为“科学复现成功”，也不得把本包的静态自检表述为目标机完整测试通过。

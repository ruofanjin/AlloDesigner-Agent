# GLP1 主实验 Agent 部署包

本包把 `interation1_shuffle8_group37/` 中可追溯的实验整理成可迁移、可审计、可续跑的 Agent 工作流。`normal_100ns` 后有两个同级实验族：二维 distance metadynamics，以及直接以 SASA 为 CV 的 biased MD。

## 已确认的实验关系

```text
minimization → eq1…eq6 → normal_100ns
                              ├→ distance_monitor_50ns
                              │     └→ distance_metad_50ns
                              │            └→ postprocess → MDpocket
                              ├→ sasa_site_10ns
                              │     └→ standardized postprocess → MDpocket
                              └→ sasa_pocket_100ns (8 Å)
                                    └→ standardized postprocess → MDpocket
```

- 两条 SASA 路径直接从 `normal_100ns.gro/.cpt` 独立分叉，不依赖 distance 路径，也不互相续接。
- `sasa_site_10ns` 是 254 原子的可追溯正式位点实验。
- `sasa_pocket_100ns` 是 8 Å/648 原子的可追溯正式长实验；10 ns 版本保留为短程对照。
- SASA DAT 同时含 `METAD` 与 `BIASVALUE ARG=sasa`。后者是额外直接势，不是输出别名；执行必须显式确认 `--ack-sasa-biasvalue`。
- SASA biased MD 后现已接入统一的 PBC、5 类 RMSD、7 套预注册 Gromos cutoff、5VEX 比较、原生 `gmx sasa` 和 MDpocket。它们标为 `standardized-analysis`，不是伪装成历史已完成的结果。
- 历史只证明 site/pocket 10 ns 各做过 4 条 RMSD 与 101 帧 MDpocket；没有 SASA 历史聚类。正式 pocket 100 ns 的上述分析是本版新增扩展；来源不闭合的 50 ns 树仍被排除。

`normal_10ns/50ns/100ns` 都从相同 eq6 状态独立开始。`normal_200ns_from_100ns` 才从 100 ns 末态接续，但新 TPR 时间轴归零。distance 的历史 100 ns 后段从 50 ns 偏置末态起步，却新建 HILLS，因此不是严格 metadynamics restart。

## 从这里开始

1. 阅读 [Agent 操作契约](AGENTS.md)、[实验工作流](docs/EXPERIMENT_WORKFLOW.md)、[科学决策](docs/SCIENTIFIC_DECISIONS.md)和[膜体系构建指南](docs/MEMBRANE_SYSTEM_BUILDING.md)。
2. 在包根执行完整性检查：

   ```bash
   ./agentctl verify-bundle
   ```

3. 按[安装指南](docs/INSTALL.md)部署软件：

   ```bash
   # 默认只输出 GPU 构建计划；不会安装 CUDA，也不会写目录
   ./install/install_gmx_stack.sh \
     --cuda-prefix /usr/local/cuda \
     --prefix /data/apps/gmx-stack \
     --work-root /data/build/gmx-stack

   # 默认只输出官方 fpocket 4.2.3 + 固定修复补丁的安装计划
   ./install/install_fpocket.sh \
     --prefix /data/apps/fpocket-4.2.3 \
     --work-root /data/build/fpocket-4.2.3
   ```

   两个安装器都只有追加 `--execute` 才会执行。GROMACS 栈所需源码归档已离线打包；fpocket 安装器执行时从官方 GitHub 获取固定 tag/commit，再校验并应用包内固定 SHA-256 的最小内存分配修复。CUDA 驱动和 Toolkit 不在包中，必须由目标系统预先提供。本包的生产 MD profile 强制使用 NVIDIA CUDA 加速；CPU 仅用于诊断或零步联调。

4. 把 `config/site.env.example` 复制到包外并定稿。使用真实 `gmx_mpi`，不要依赖交互 alias。把 fpocket 安装器生成的 `MDPOCKET_BIN` 和 `MDPOCKET_PROVENANCE` 写入 site 配置。
5. 检查目标环境并查看精确计划：

   ```bash
   ./agentctl --site-config /data/config/glp1.site.env doctor --strict --require-mdpocket
   ./agentctl plan --profile historical-distance-main
   ./agentctl plan --profile standardized-sasa-biased-main
   ```

   仅部署模拟层时可暂时不加 `--require-mdpocket`；执行 `historical-distance-main` 前必须带该选项通过检查。

## 运行 profile

主要 profile：

`historical-*` 是为兼容既有命名而保留的分支标签，不等于所有运行态参数都自动采用历史值。site 示例现在默认 `RESTRAINT_REFERENCE_MODE=charmm_gui_initial`，这是与原始 CHARMM-GUI README 一致的推荐修正；若要复核实际归档 eq1–eq6 TPR，必须在 `prepare` 前显式改为 `historical_previous`。两种选择都会冻结并由 `doctor` 报告，必须在结果中注明。

- `historical-distance-main`：distance 模拟、后处理和 MDpocket 全路径。
- `distance-simulation-only`：停在 distance biased MD，不要求 MDpocket。
- `historical-sasa-site`：位点 SASA 10 ns。
- `historical-sasa-pocket-100ns`：8 Å pocket SASA 100 ns。
- `historical-sasa-biased-main`：在一个 run 中依次调度上述两条独立 SASA 分支，便于完整审计；科学依赖仍是并列。
- `historical-sasa-pocket`：保留的 pocket 10 ns 短程对照。
- `standardized-sasa-site-10ns-full`：site 10 ns biased MD 加统一结构/SASA/MDpocket 分析。
- `standardized-sasa-pocket-10ns-full`：pocket 10 ns 短程对照加同一分析矩阵。
- `standardized-sasa-pocket-100ns-full`：正式 pocket 100 ns biased MD 加新增标准分析。
- `standardized-sasa-biased-main`：共享一个 `normal_100ns` 父态的 site 10 ns 与 pocket 100 ns 两支及全部标准分析；这是当前完整 SASA 入口。

只需要模拟产物时使用 `historical-sasa-biased-main`；需要结构、原生 SASA 与 MDpocket 全分析时使用 `standardized-sasa-biased-main`。两者都在同一 run 中顺序调度两条 SASA 分支，以保证共享同一个 `normal_100ns` 父态。两个独立 run-id 会因 `gen-seed=-1` 各自产生不同父态，只能视为独立 replica，不能称为历史同父态并行复现。真正并发且共享同一父态需要未来实现只读 seed artifact fan-out，本版尚未提供。

准备和 dry-run 示例：

```bash
./agentctl \
  --site-config /data/config/glp1.site.env \
  --work-root /scratch/glp1-agent-runs \
  prepare --run-id distance-001

./agentctl \
  --site-config /data/config/glp1.site.env \
  --work-root /scratch/glp1-agent-runs \
  run --profile historical-distance-main --run-id distance-001
```

只有获得计算资源并审阅计划后，才同时打开执行门闩：

```bash
./agentctl \
  --site-config /data/config/glp1.site.env \
  --work-root /scratch/glp1-agent-runs \
  run --profile historical-distance-main --run-id distance-001 \
  --execute --allow-long-md
```

SASA 命令还必须增加 `--ack-sasa-biasvalue`；带 MDpocket 的标准化完整 profile 要在 `prepare` 前部署并冻结 fpocket。中断后以相同参数把 `run` 换为 `resume`。详细恢复约束见[实验工作流](docs/EXPERIMENT_WORKFLOW.md)。

## 目录与输入边界

- `agentctl`：唯一推荐的编排入口；默认 dry-run。
- `inputs/`：从当前复现过程提取的、约 19 MiB 的冻结输入快照。
- `stages/`：无交互阶段脚本；输出只写包外 `--work-root/RUN_ID`。
- `manifests/`：DAG、输入与整包 SHA-256、来源和排除项。
- `install/`：GROMACS 栈离线源码、校验和、安装器，以及联网获取固定 fpocket 提交的安装器；不含 CUDA 安装包。
- `scheduler/`：默认 GPU 的 Slurm 渲染/提交包装器。
- `reference/original_scripts/`：只供溯源，禁止执行。

当前 `inputs/` 不是通用于任意新体系的永久模板，而是为本次阶段性复现提取的冻结快照。未来接入从建模、拓扑、选择到模拟的全流程 Agent 后，应让上游步骤规划或生成坐标、拓扑、NDX、MDP 与 PLUMED 原子映射，并通过明确的 artifact contract 交给本工作流。该能力当前尚未实现；本版 Agent 不得擅自重建或替换冻结输入。详见[未来全流程接入提醒](docs/FUTURE_FULL_FLOW.md)及[CHARMM-GUI/GROMACS 膜体系构建路线](docs/MEMBRANE_SYSTEM_BUILDING.md)。

## 复现边界

这是协议和执行顺序复现，不承诺长轨迹位级一致。随机种子、硬件、MPI 分解与 GPU 数值路径都会影响结果。冻结 distance DAT 的 SPIB 训练资产已不在项目内，不能用现存漂移脚本重建。任何新拓扑、PDB 原子重排或选择变化都必须重新规划并验证原子映射。

本包没有重跑长时间 MD。静态自检和本机零步耦合 smoke 不能替代目标系统验收，也不能证明采样收敛或科学结论重复。

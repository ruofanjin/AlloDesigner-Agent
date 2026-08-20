# GLP1 跨膜体系构建与上游交付契约

## 1. 本版能力边界

当前可执行 DAG 从冻结的 `inputs/system/step5_input.gro`、topology 和 index 开始，**不自动重建膜体系**。本文件为后续全流程 Agent 规定上游流程、人工决策点和交付物；只有新的体系版本通过全部契约后，才能生成新的 NDX、PLUMED DAT 和实验 DAG。

用户给出的[膜蛋白 GROMACS 教程](https://zhuanlan.zhihu.com/p/553850783)可作为操作参考。部署时以 CHARMM-GUI 和 GROMACS 官方文档、所选力场文档及项目实际 provenance 为准，不能把教程示例的 PDB、脂质组成或力场版本直接套到本项目。

本项目现有文件只能确认：CHARMM-GUI 3.7、GROMACS 格式的 AMBER 力场、4 个蛋白组分、383 个 POPC、161 个 K⁺、162 个 Cl⁻ 和 59,262 个 TP3。现有 metadata 不足以证明具体的 AMBER 蛋白/脂质子版本，也不能逐位重建原 CHARMM-GUI job。

## 2. 推荐路线：CHARMM-GUI Membrane Builder

对于 GLP1 GPCR 复合体系，默认采用 [CHARMM-GUI Membrane Builder](https://charmm-gui.org/?doc=tutorial&project=membrane)；[GROMACS 官方膜蛋白教程](https://tutorials.gromacs.org/docs/membrane-protein.html)也采用 CHARMM-GUI 生成膜体系，再用 GROMACS 做最小化、平衡和生产模拟。

建议顺序：

1. 确认 PDB/model、biological assembly、保留的链以及受体、G 蛋白、配体等角色。
2. 逐项审查缺失残基、突变、末端、二硫键、质子化、结构水、离子、辅因子、PTM 和配体；不得无条件删除全部结构水。
3. 确认跨膜区、膜法向和胞外/胞内方向。优先使用 OPM/PPM、实验拓扑和已知 TM 残基；整个多链复合物的第一主轴不能单独证明 GPCR 方向。
4. 选择相互兼容且有完整来源的蛋白、脂质、配体、离子和水模型。膜组成、上下叶比例、温度和盐浓度由研究问题决定；当前纯 POPC 只是历史简化模型。
5. 在 Membrane Builder 中生成膜、水、离子和 GROMACS 输入，保存 job ID、网页选项、下载包和 SHA-256。
6. 把 `topol.top` 与 `toppar/` 作为项目局部文件保留相对 include；不要复制到全局 GROMACS 数据目录。
7. 用 GROMACS 执行 EM 和逐步释放约束的 eq1–eq6。推荐所有平衡段保持初始构建结构作为 `-r`，逐段更新 `-c` 和 `-t`；生产 `grompp` 明确读取最终 `eq6.cpt`。
8. 完成无约束短验证和膜体系 QC 后冻结 parent state，再生成本项目所需的 index、残基映射、距离 CV 与 SASA 原子映射。

推荐的平衡命令关系是：

```bash
GMX_BIN=gmx_mpi

"$GMX_BIN" grompp -f eq1.mdp -c em.gro \
  -r step5_input.gro -p topol.top -n index.ndx -o eq1.tpr
"$GMX_BIN" mdrun -deffnm eq1

# eq2…eq6：-c 使用上一段 GRO，-t 使用上一段 CPT，-r 仍为初始构建结构
"$GMX_BIN" grompp -f production.mdp -c eq6.gro -t eq6.cpt \
  -p topol.top -n index.ndx -o production.tpr
```

示例只表达 artifact 关系；资源、GPU offload、MDP 和实际文件名必须由新实验版本给出，不能绕开本包的编排与验收门闩。

## 3. GROMACS-native 专家路线

GROMACS 可以组合已有部件，但不是从任意 GPCR PDB 自动设计生物学膜的工具。native 路线必须预先具备：

- 已审查且按明确矩阵定向的蛋白结构；
- 预平衡膜片或外部生成的脂质坐标；
- 与蛋白相容的脂质、配体、水和离子 topology；
- 明确的上下叶组成、面积、重叠删除规则和随机种子；
- 可重放的 selection 与辅助脚本。

可用原语及边界：

| 任务 | 官方命令 | 不能替代的科学决策 |
|---|---|---|
| 标准蛋白 topology | [`gmx pdb2gmx`](https://manual.gromacs.org/documentation/2024.3/onlinehelp/gmx-pdb2gmx.html) | 任意配体、PTM、金属、缺失环和不受力场支持的残基参数化 |
| 已决定的平移/旋转/盒子 | [`gmx editconf`](https://manual.gromacs.org/documentation/2024.3/onlinehelp/gmx-editconf.html) | GPCR 的膜方向、胞外侧和膜厚 |
| 按位置或随机放置分子 | [`gmx insert-molecules`](https://manual.gromacs.org/documentation/2024.3/onlinehelp/gmx-insert-molecules.html) | 混合/非对称叶层设计；该命令不是 bilayer planner |
| 嵌入预平衡膜 | [`gmx mdrun -membed`](https://manual.gromacs.org/documentation/2024.3/onlinehelp/gmx-mdrun.html) | 膜片、嵌入参数、index、topology 和删除脂质规则仍需外部准备 |
| 加水 | [`gmx solvate`](https://manual.gromacs.org/documentation/2024.3/onlinehelp/gmx-solvate.html) | 必须检查膜疏水核心中的误插水和排斥半径 |
| 单原子离子替换 | [`gmx genion`](https://manual.gromacs.org/documentation/2024.3/onlinehelp/gmx-genion.html) | 仅随机替换溶剂，不能自动处理多原子盐或特定位点离子 |

native 流程至少包括：蛋白 topology → 已验证取向和盒子 → 与预平衡膜片合并/嵌入并删除重叠脂质 → topology 计数同步 → 加水 → `grompp` 生成加离子 TPR → `genion` → EM/分段平衡。每一步都应在隔离工作目录中记录命令、seed、输入输出摘要和可视化 QC。

下面只是让上游 Agent 规划依赖的命令骨架，不是可直接粘贴运行的 GLP1 配方：

```bash
GMX_BIN=gmx_mpi

# 1) 仅在所选力场已支持全部蛋白残基时建立蛋白 topology。
"$GMX_BIN" pdb2gmx -f protein_oriented.pdb -o protein.gro -p topol.top \
  -ff FORCEFIELD -water WATERMODEL

# 2) 只执行 orientation.json 已批准的变换和盒尺寸，不能在这里猜方向。
"$GMX_BIN" editconf -f protein.gro -o protein_box.gro -box LX LY LZ

# 3A) 用版本化脚本把蛋白与预平衡膜片合并、删重叠脂质并同步 topology；或
# 3B) 为 mdrun -membed 准备 membed.mdp/dat、membed.ndx 和 membed.top。
# 若 MDP 启用位置约束，-r 必须是与 assembled.gro/topology 原子数和
# 原子顺序一致的完整体系参考；无位置约束时可省略 -r。
"$GMX_BIN" grompp -f membed.mdp -c assembled.gro -r assembled.gro \
  -n membed.ndx -p membed.top -o membed.tpr
"$GMX_BIN" mdrun -deffnm membed -membed membed.dat \
  -mn membed.ndx -mp membed.top

# 4) 加水后必须检查疏水核心误插水，并审核 topology 自动更新。
"$GMX_BIN" solvate -cp membrane_protein.gro -cs WATER_BOX.gro \
  -o solvated.gro -p topol.top

# 5) 先用专用 ions.mdp 生成 TPR，再明确选择可替换的溶剂组。
"$GMX_BIN" grompp -f ions.mdp -c solvated.gro -p topol.top \
  -n index.ndx -o ions.tpr
printf '%s\n' WATER_GROUP | "$GMX_BIN" genion -s ions.tpr -o ionized.gro \
  -p topol.top -pname K -nname CL -conc TARGET_MOLAR -neutral -seed FIXED_SEED
```

`LX/LY/LZ`、水模型、离子名、selection 和 seed 都必须由 `build_spec.json`/力场给出。若自动更新 topology 后的分子数与坐标不一致、膜心水未解释或 `grompp` 有 warning，流程必须停止。

## 4. 上游 Agent 必须交付的 artifact

机器可读要求见 `manifests/membrane_build_contract.json`。最低交付包括：

- `build_spec.json`：研究目的、pH、温度、盒子、膜组成/上下叶、盐浓度和各组分力场；
- `source_structures/` 与摘要：来源、assembly、链角色和获取日期；
- `chain_map.tsv`、`residue_map.tsv`：原始 chain/residue/insertion code 到最终残基和全局原子号；
- `structure_decisions.json`：缺失结构、质子化、二硫键、结构水、辅因子、PTM 和配体处理；
- `orientation.json`：膜法向、胞外方向、TM 范围、完整旋转/平移矩阵和依据；
- `membrane_composition.tsv`：计划/实际上下叶计数、膜片来源和被删除脂质；
- 自包含的 pre-EM GRO/PDB/NDX、`topol.top`、局部 `toppar/` 和 `grompp -pp` 展开 topology；
- 实际执行的 minimization/eq MDP，以及验收后的 parent GRO/CPT/TPR；三者的原子顺序、时间和 checkpoint 一致性必须证明；
- `system_summary.json`：原子数、分子顺序/数量、净电荷、盒向量、离子数和实际浓度；
- `commands.log`、`versions.json` 及所有 artifact 的 SHA-256；
- `validation/`：冲突、膜心水、叶层、膜厚/面积、EM Fmax、温度/压力/盒面积、约束告警和人工可视化结论。

契约把上游边界放在“已完成并验收膜专用平衡的 parent state”。未来编排器应从该 parent 分叉生产与 CV 表征，不能再无条件重跑本包冻结的 step5→eq1…eq6；若选择从 pre-EM state 接管，则必须声明另一种 contract 版本，避免重复平衡。

## 5. 硬门槛

出现任一情形，上游 Agent 必须停止，不能把体系交给当前 DAG：

- 坐标、topology、TPR、PDB/轨迹的原子数或顺序无法证明一致；
- 膜方向、链身份、净电荷、叶层组成或力场兼容性未决；
- 有未解释的 `grompp` warning、非有限能量、未收敛 EM 或持续 LINCS/SETTLE 问题；
- 未检查蛋白–脂质冲突、疏水核心中的水、叶层计数和盒子稳定性；
- 新体系试图复用本包冻结的 48 距离、254/648 SASA 原子号或旧 index；
- 缺少从残基选择到 1-based 全局原子号的可重放映射；
- 缺少 provenance、完整命令或校验和。

通过后也必须创建新的输入版本、profile 和 run-id；不得覆盖本包 `inputs/` 或继续声称是当前 237383 原子冻结体系的复现。

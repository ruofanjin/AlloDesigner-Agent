# 未来全流程 Agent 接入提醒

## 当前状态

本版本采用“冻结输入快照”模式：`inputs/` 是从现有 GLP1 复现过程提取的坐标、拓扑、index、MDP、PLUMED DAT 和分析选择。它们用于复现当前体系，必须按 SHA-256 只读使用。

当前编排器从这些输入开始执行，不负责重新完成 CHARMM-GUI 建模、质子化、膜/溶剂构建、拓扑生成、残基到原子的映射、CV 选择或 SPIB 训练。

GLP1 跨膜体系的推荐构建路线、GROMACS-native 专家替代路线和机器可读交付契约见 [膜体系构建指南](MEMBRANE_SYSTEM_BUILDING.md) 与 `manifests/membrane_build_contract.json`。它们是未来上游规范，不是本版已实现 stage。

## 后续全流程集成要求

全流程 Agent 接入后，应由前置步骤根据目标体系自主规划并产出后续输入，而不是复制本目录中的固定原子号。上游至少要交付一个可审计的 artifact contract：

- 坐标、拓扑、项目局部 include 与力场来源；
- 原始结构 assembly、链角色、结构水/辅因子/配体处理、质子化与二硫键决策；
- 膜法向、胞外方向、完整取向矩阵、上下叶组成、膜片来源、盐浓度和盒子；
- 原子总数、分子顺序、蛋白范围及 PDB/TPR/轨迹的原子顺序证明；
- index 组的 selection 表达式、成员数和生成工具版本；
- 每个 MDP 的来源、科学目的、计划步数/时间及随机种子策略；
- 膜专用 EM/平衡的实际 MDP、验收后的 parent GRO/CPT/TPR，以及三者原子顺序/时间/checkpoint 一致性；未来 DAG 默认从该 parent 接管，不能再次无条件执行本包冻结 eq1–eq6；
- PLUMED CV 的残基选择、展开后的 1-based 全局原子号、参数覆盖情况和短程数值验证；
- 若重建 distance SPIB 偏置，训练数据、切分、lag、种子、模型权重和生成 DAT；
- 每个 artifact 的 SHA-256、生产者版本、生成命令和依赖关系。
- 蛋白–脂质冲突、膜心水、叶层计数、膜厚/面积、EM 和平衡稳定性的 QC。

## 规划门槛

未来 Agent 只有在证明上述 contract 自洽后，才能生成新的实验版本和 DAG。以下情形必须停止并请求科研判断：

- 拓扑或原子顺序与冻结体系不同，却试图复用现有 PLUMED `ATOMS`；
- 膜方向、链身份、叶层组成或各组分力场兼容性尚未确定；
- 试图把 `gmx insert-molecules` 等装配原语当作无需预平衡膜片和 topology 的完整膜构建器；
- 无法从选择规则重建 254/648 原子集合；
- 缺少 SPIB 权重却试图近似生成 distance DAT；
- SASA 完整蛋白遮挡、subset 自遮挡或 `BIASVALUE` 势能定义尚未选择；
- 上游输入没有 provenance、校验和或可重放生成记录。

本文件只是后续集成提醒，不表示本版已经具备自动规划能力。当前运行仍以 `inputs/` 冻结快照和 `tools/validate_inputs.py` 为权威。

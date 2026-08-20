# 自主变构口袋发现、多分支 MSA 与构象富集 Agent Prompt

版本：0.1（2026-08-10）  
状态：设计规范与可复制 Prompt；尚未接入当前 runner

## 1. 需求理解与边界

当前计算性 Step 3 对 PocketMiner/AlloDesigner 给出的阳性残基进行空间聚类，并分别
生成 DeepAllo 和 PLB 的 top-7 残基频率排名表。传统流程再由人类专家结合结构和
领域先验，选择一个残基集合用于后续 MSA 富集和构象生成。

本规范把人工 gate 扩展成一个可审计的自主探索 agent：

1. 保留 DeepAllo 与 PLB 两张独立排名表，不把两者伪装成同一种概率。
2. 将单残基证据重新组织成空间连续、跨构象可追踪的候选口袋家族。
3. 自主检索靶点、同源蛋白、配体、突变、功能和构象文献，并保留检索式与证据等级。
4. 引入独立或半独立的口袋、动态、进化和配体可结合性评价。
5. 以 2–3 个非冗余候选口袋残基集合为探索目标；若证据不足，允许输出 0–1 个，
   而不是强制输出一个“唯一正确”口袋。
6. 为每个候选口袋创建独立 residue fingerprint 和运行分支，分别执行后续 MSA、
   构象富集和 final evaluation。
7. 根据预先登记的继续、停止或升级标准，判断每个分支是否值得增加计算或实验验证。

这里的 agent gate 是计算性研究决策，不是人类专家意见，也不能被记录为
`expert_decision`。正式产物必须命名为 `agent_decision.yaml`，并明确说明候选口袋仍需
实验验证。

## 2. 总体数据流

```text
Iteration 1 structures + fpocket + PocketMiner positives
  -> spatial residue clusters + fpocket DCC
       ├── DeepAllo cluster score -> DeepAllo top-7 frequency table
       └── PLB cluster score      -> PLB top-7 frequency table
  -> cross-conformation candidate-pocket families
  -> target identity / literature / homolog evidence
  -> independent pocket and allostery tool evidence
  -> transparent multi-objective ranking + critic audit
  -> 0–3 non-redundant candidate residue sets
       ├── pocket_01 -> branch-specific Iteration 1 metric -> MSA -> conformations
       ├── pocket_02 -> branch-specific Iteration 1 metric -> MSA -> conformations
       └── pocket_03 -> branch-specific Iteration 1 metric -> MSA -> conformations
  -> branch comparison
  -> CONTINUE / STOP / ESCALATE
```

候选簇、DCC、原始 DeepAllo/PLB 分数和工具原始输出必须保留为中间证据；最终 agent
gate 的直接输出是 0–3 个 selection-only residue CSV 及其决策记录。只有候选通过
预注册的硬 gate 时才物化分支，不得为凑够数量强行输出。

## 3. 运行模式

Agent 必须在开始前选择并记录一种模式，不能在看到结果后切换：

| 模式 | 允许使用的先验 | 适用场景 |
|---|---|---|
| `target_informed_exploration` | 允许检索本靶点、同源体、配体、突变和功能文献 | 未知或低先验靶点的真实探索；默认 |
| `blind_benchmark` | 候选锁定前禁止读取已知变构口袋、holo 残基或目标答案 | 方法学盲测，避免5VEX式答案泄漏 |
| `historical_replay` | 只验证既有人工 handoff，不做自主选择 | GLP1历史结果复现 |

在 `blind_benchmark` 中，已知口袋只能在 `agent_decision.yaml` 写入并冻结 hash 后用于
回顾性评价，不能参与候选生成或排序。

模式对执行阶段的约束如下；该表优先级高于后文的通用 Prompt：

| 模式 | 计算候选 | 目标/家族allostery文献 | 自主排名 | 下游分支 |
|---|---|---|---|---|
| `target_informed_exploration` | 执行并先冻结family hash | family冻结后允许 | 执行 | 只对授权候选执行 |
| `blind_benchmark` | 执行 | 决策hash冻结前禁止 | 只用未embargo证据 | 可执行，已知答案只作事后评价 |
| `historical_replay` | 不重建，只hash/schema验证 | 不执行 | 不执行 | 不由本Agent物化 |

`blind_benchmark` 必须在运行前冻结 `embargo_manifest.yaml`，列出禁止的 PDB、配体、
残基、文献和本地文件。候选决策冻结前，不可进行靶点/家族的 allostery、
ligand、holo、mutation 或机制文献搜索。`historical_replay` 在验证预期 hash 后就停止；
不得继续通用 Prompt 的候选、搜索或分支阶段。

## 4. 输入契约

### 4.1 必需输入

| 输入 | 最低要求 |
|---|---|
| Target identity | 名称、物种、UniProt/PDB ID（如有）、同义词；身份不明确时以 sequence hash 为主键 |
| Canonical/construct sequence | canonical FASTA、实际建模 construct FASTA、二者映射 |
| Structure mapping | `chain, resseq, insertion_code, construct_index, canonical_index`；所有候选残基必须可回映 |
| Iteration 1 ensemble | 每个 shuffle/group 的 PDB、fpocket pockets、info 和 pocket centers |
| PocketMiner evidence | 连续分数优先；至少提供阈值化阳性残基及阈值 |
| DeepAllo table | `residue_number, probability`，另记录 denominator、top-k、索引模式和 hash |
| PLB table | `residue_number, probability`，另记录 denominator、top-k、PLB 公式和 hash |
| Candidate intermediates | cluster manifest、residue set、DCC/closest-pocket、簇级 DeepAllo、簇级 PLB 四类表 |
| Output root | 必须是新的可写目录，不能是原始 case、`inputs/` 或 `source_snapshot/` |

所有候选表必须共用稳定 `candidate_key`，并以显式列保存
`target_id,shuffle_id,group_id,model_id,seed,structure_sha256,cluster_id`。不得再从
`group_cluster` 字符串或模糊文件名子串解析主键。历史表必须先经可审计 adapter
转成此 schema。`expected_keys_by_stage.json` 要为每个阶段分别定义 key set：例如全部
cluster/DCC keys 与经 `DCC < threshold` 生成的 DeepAllo/PLB eligible keys 本来就可以不同。
必须记录可重放的集合转换规则，不能要求不同阶段拥有错误的相同行数。

### 4.2 条件必需输入

| 条件 | 还必须提供 |
|---|---|
| `target_informed_exploration` | 可搜索的数据库/服务清单、时间与查询预算、禁止来源 |
| `blind_benchmark` | `embargo_manifest.yaml`、答案保管人或事后解封路径 |
| `historical_replay` | historical selection、evidence manifest、每个预期输出的SHA-256/schema/count |
| `branching.enabled=true` | Iteration 1 group-A3M manifest、base pipeline/selection config、runner path+hash、环境/模型manifest、seed/scheduler/计算预算 |

### 4.3 可选输入

- 已知 orthosteric site、活性位点、跨膜区、signal peptide、无序区和关键功能残基；
- AlphaFold PAE、pLDDT、实验分辨率或局部质量信息；
- 已有 MSA、家族 profile、结构同源体和配体结构；
- 允许使用的本地工具、数据库快照、容器 digest 和计算预算；
- 禁止使用的先验、付费服务或不可公开数据。

缺少可选输入不能被静默解释为零分。必须在 `missing_evidence` 和
`evidence_coverage` 中显式记录。

### 4.4 Preflight

在搜索或评分前必须完成：

1. 校验 sequence、PDB chain 和 residue mapping 一致；无法唯一映射时停止。
2. 对所有输入计算 SHA-256，并冻结 `discovery_run_id`。
3. 确认 DeepAllo/PLB 的 `probability` 是 top-k residue frequency，不是原始模型概率。
4. 从 expected manifest 生成每个 stage 的 key set，并对 cluster、DCC、DeepAllo、PLB
   各自做 exact-key 校验；再按预注册的资格转换规则连接。任一阶段缺失、重复或多余
   key 都必须停止。
5. 区分 DeepAllo `legacy_indexing` 与 `corrected_mapping`，不同模式不能混用输出。
6. 检查输出目录为空，或与同一个 `discovery_run_id` 完全一致。
7. 验证所选模式的 embargo/historical/search 条件输入；模式不符时不得降级到另一模式。
8. 若启用 branching，校验 group A3M 与 Iteration 1 PDB 的 group key 一一对应，并要求
   pipeline config、runner/environment/model manifest、seed/scheduler 和计算预算均已冻结。
9. 若进入多证据排名，验证 `metric_registry.yaml` 中每个使用中指标均有版本化
   的转换、可靠度和缺失规则。

## 5. 候选口袋生成

不能直接把两张残基表中分数最高的若干残基拼成口袋。Agent 必须先形成空间候选：

1. 在每个 Iteration 1 构象中，对 PocketMiner 阳性残基进行空间聚类。
2. 为每个 cluster 保存 chain-aware residue set、cluster center、大小、最近 fpocket、DCC
   和构象标识。
3. 对同一 construct 的构象先做结构对齐，再依据 residue-set Jaccard、中心距离和空间
   重叠，将单构象 cluster 归并成跨构象 pocket family。
4. 计算 family 在 group、shuffle、模型和 seed 层面的支持数；不能把同一结构中的多个
   相似 cluster 当成独立重复。
5. 对 DeepAllo 和 PLB 分别计算 pocket-level 支持：推荐使用成员残基的 rank percentile
   中位数、支持残基比例和 ensemble support，避免直接求和造成大口袋偏置。
6. 保留原始 DeepAllo 与 PLB 两个轴；任何 composite score 只能作为 agent gate 的派生
   决策量，不能覆盖两张原始排名表。
7. 在读取本靶点特异文献前，先冻结纯计算候选 family 及其 hash。文献可以
   改变排名或支持/反对判断，但不得不留版本地移动候选边界。
8. 每个分支的最终 residue set 必须由该 family 的空间成员和跨 shuffle/group 支持
   派生。为每个残基保存 `family_support_fraction`、排名和证据 ID；用预注册阈值
   选空间 core，并对阈值做敏感性分析。只在文献出现但不在计算 family 中的残基
   可作为注释或新版本候选，不得静默塞入已冻结的 selection。

跨构象归并阈值必须写入配置并做敏感性分析。默认起点可使用：

```yaml
candidate_family_defaults:
  minimum_residue_count: 2
  maximum_selected_pairwise_jaccard: 0.50
  require_chain_aware_mapping: true
  require_detectable_cavity_association: true
  minimum_independence_groups: 2
  minimum_evidence_coverage: 0.70
```

这些是工程起始值，不是普适生物学定律。Agent 必须报告阈值扰动后候选是否稳定。
两个空间相邻残基只能称为 residue patch；只有与可检测 cavity/fpocket family
存在稳定空间关联的 family 才能进入“candidate pocket” gate。

## 6. 自主证据探索

### 6.1 文献与数据库路径

Agent 应先解析靶点身份和同义词，再依次搜索：

1. 精确靶点：`target AND (allosteric OR pocket OR ligand OR modulator OR mutation OR HDX
   OR cryo-EM OR conformational change)`；
2. 蛋白家族或近同源体：同样关键词，并记录序列一致性、覆盖度和结构比对；
3. RCSB PDB 的序列相似、结构相似和结构 motif 搜索；
4. 已结合配体结构中的接触残基、功能突变、疾病变体、交联、HDX-MS 和状态特异结构；
5. 若直接文献稀少，转向家族机制和结构同源证据，不得编造“专家常识”。

每条证据至少保存：检索数据库、查询式、检索日期、标题、DOI/PMID/PDB/UniProt、
靶点或同源体、实验类型、原始 residue numbering、映射质量、支持/反对结论和来源URL。

证据等级：

| 等级 | 含义 | 排名用途 |
|---|---|---|
| A | 本靶点直接实验：配体结构、定点突变功能、HDX、状态结构等 | 强证据 |
| B | 近同源体直接实验，且 residue/structure mapping 可靠 | 中强证据 |
| C | 本靶点或同源体计算研究、数据库注释 | 辅助证据 |
| D | 综述、推测、无可核对残基映射的描述 | 只作背景，不得单独提高排名 |

文献不足不是失败，但必须降低 evidence coverage。Agent 不得把没有检索到反对证据
解释为支持证据。

文献搜索达到任一预注册终点即可停止：连续两轮查询没有新增 A–C 级证据；已覆盖
正式名称、同义词、家族和结构域查询；或达到时间/查询预算。停止原因必须写入
`search_strategy.yaml`。

### 6.2 推荐的工具适配器

工具必须锁定版本、命令、参数、数据库日期和容器/二进制 hash。一个工具的重评分
结果不能被误计为两个独立证据。例如 P2Rank 对 fpocket 的 rescore 与原 fpocket
共享输入和候选，依赖关系必须写入 `tool_dependencies.yaml`。

| 证据维度 | 首选或可选工具 | 目标输出 |
|---|---|---|
| 几何与 ligandability | fpocket；P2Rank 作为独立预测或明确标注的 fpocket rescore | pocket score、druggability、volume、中心、邻近残基、方法一致性 |
| Ensemble persistence | aligned Iteration 1 ensemble；可选 mdpocket | model-ensemble detection frequency、体积稳定性、瞬时/持续性 |
| 动态与变构通信 | ProDy PRS/ESSA、elastic network 或 residue interaction network | candidate 到功能位点的 communication/sensor/effector 证据 |
| 同源结构 | RCSB PDB sequence/3D search；可选 Foldseek | 同源结构、覆盖度、TM-score/identity、配体位置映射 |
| 已知配体接触 | PLIP 或等价可复现 contact profiler | 映射后的配体接触残基与相互作用类型 |
| 进化支持 | 当前 MSA 的 conservation、entropy、可选 coevolution | 每残基保守性、共同变化、有效序列数和缺失率 |
| 结构质量 | pLDDT、PAE、实验分辨率、缺失原子/残基 | 局部可信度和 artifact flags |
| 后期升级 | 短程 MD、fragment/docking、自由能或增强采样 | 只用于边界候选，不能单独证明变构性 |

Docking 或单一 pocket predictor 不得单独触发下游高成本分支。

术语和证据边界必须保持严格：

- Iteration 1 是预测模型集合，其口袋检出频率不是热力学 occupancy 或 Boltzmann 概率；
- PLB 是当前组成启发式分数，不是结合自由能、亲和力或可成药性概率；
- docking score 不是 `Kd`、`Ki` 或实验 `ΔG`，不得把自对接重复当作独立生物重复；
- PLIP 只描述已有 complex 中的接触，不能单独证明该位点存在变构效应；
- Foldseek/RCSB 的全局结构命中必须经局部口袋对齐和残基映射才能转移先验；
- `Q_structure_quality` 只是证据可信度调节量，高 pLDDT/高分辨率不是口袋价值奖励。

### 6.3 单Agent与多Agent编排

若运行环境支持多Agent，建议由 orchestrator 并行委派以下独立角色：

1. Data/Mapping Agent：只负责身份、序列、chain和编号映射；
2. Residue-to-Pocket Agent：只负责空间candidate family；
3. Literature Agent：只负责检索、证据分级和冲突证据；
4. Structural Consensus Agent：只负责额外口袋、ensemble和ligandability工具；
5. Mechanism Agent：只负责动态、网络、进化和功能耦联；
6. Skeptical Critic：在不知道预期答案的前提下尝试推翻候选；
7. Branch Builder/Evaluator：只在决策冻结后生成分支并评价。

Literature、Structural和Mechanism报告必须先各自冻结hash，再由orchestrator整合，
避免相互锚定。单Agent模式也必须依次保存这些中间报告，且不得跳过Skeptical Critic。

## 7. 多证据决策体系

### 7.1 独立证据域

每个 candidate pocket 必须保留以下原始维度：

- `G1_model_prior`：保留独立的DeepAllo、PLB和PocketMiner子字段；
- `G2_geometry_ligandability`；
- `G3_ensemble_behavior`；
- `G4_allosteric_communication`；
- `G5_external_structure_experiment`；
- `G6_evolution_function`；
- `Q_structure_quality`：只调节证据可靠度，不作为口袋价值奖励；
- `evidence_coverage`、`uncertainty` 和所有反对证据。

DeepAllo、PLB、PocketMiner和fpocket共享候选池或特征，不能被解释成四份完全独立
证据。尤其DeepAllo使用fpocket descriptors，fpocket几何信息不能在G1和G2中完整
重复加分。原始DeepAllo和PLB表始终独立保存，但在“独立证据家族”计数中二者同属
G1。每个原子指标只能登记到一个 `independence_group`。

任何综合分数前必须冻结 `metric_registry.yaml`。对每个原子指标记录：原始列、
方向、单位、所属 `independence_group`、转换函数、校准集/参考分布、截断、缺失策略和
版本。转为0–1支持度的优先级为：外部benchmark校准 > 预注册的机制阈值 > 冻结
候选集的within-target ECDF。使用ECDF时必须标记 `relative_only=true`，不得跨靶点解释。
一个域内多个相关指标默认取预注册的加权中位数，不得以指标数量堆高得分。

令 `s[i,d]` 为候选i在证据域d的0–1支持度，`q[i,d]`为该证据可靠度，`w[d]`为预先
冻结且总和为1的域权重。`q` 必须由输入完整性、mapping质量、结构质量和证据等级的
显式规则计算，规则在候选排名前冻结：

```text
coverage[i] = sum_d(w[d] * q[i,d])
support_penalized[i] = sum_d(w[d] * q[i,d] * s[i,d])
support_covered[i] = support_penalized[i] / coverage[i]
support_lower_bound[i] = support_penalized[i]
support_upper_bound[i] = support_penalized[i] + (1 - coverage[i])
```

`coverage[i] = 0` 时 `support_covered` 必须为NA并停止该候选的排名。若
`metric_registry.yaml` 不存在、未版本化或某个使用中指标缺转换/可靠度规则，
Agent 必须 `BLOCKED`，不得自行发明分数。

默认平衡profile仅作为操作性gate分数，不能命名为“变构概率”：

```yaml
balanced_gate_weights:
  G1_model_prior: 0.15
  G2_geometry_ligandability: 0.20
  G3_ensemble_behavior: 0.20
  G4_allosteric_communication: 0.20
  G5_external_structure_experiment: 0.15
  G6_evolution_function: 0.10
```

缺失维度保持NA，不得静默当作0或重分配权重。`support_covered` 只描述“已覆盖
证据中的支持度”，不能用于绕过coverage gate；排名辅助分使用不重归一的
`support_penalized`，并同时报告 `support_covered`、上下界、区间和 `evidence_coverage`。
若没有外部benchmark，只能做靶点内percentile比较，不能跨靶点解释绝对分数。

### 7.2 选择规则

1. 先应用不可降级的硬 gate：mapping 正确、空间连续并关联可检测 cavity、输入/输出
   和 candidate-key join 完整、无旧输出污染、结构质量没有灾难性问题、至少
   两个不同 `independence_group` 支持。
2. 在通过硬 gate 的候选上做 Pareto 排序；不能只依据一个加权总分。
3. 对权重和 pocket-family 阈值进行敏感性分析。至少覆盖top-k 3/5/7/10、DBSCAN
   eps 5/6/7 Å、DCC 8/10/12 Å和family center 4/6/8 Å；对非零权重做±25%扰动。
4. 使用shuffle为一级、group为二级的分层bootstrap，不能把620个预测构象当作完全
   独立重复。建议固定种子运行1,000次，并保存 `P(rank <= 3)`、q10/q90、
   leave-one-evidence-family-out最差排名和参数存活率。
5. 从稳定的 Pareto 候选中以选取 2–3 个空间和 residue-set 非冗余的候选为目标。
   优先覆盖不同证据模式，例如 consensus、dynamic/allosteric、
   homolog-supported alternative。
6. 如果只有 0 或 1 个候选通过硬 gate，必须如实输出 0 或 1 个，不得为了满足数量要求
   放宽规则或生成虚假口袋。
7. 每个候选必须同时给出支持理由、反对理由、缺失证据和最小追加验证建议。

可用作尚未校准系统的工程默认gate（不是普适生物学阈值）：

- `ADVANCE`：mapping 100%明确；G2不低于0.60；G4或本靶点直接G5至少一项不低于0.60；
  coverage不低于0.70；`P(rank <= 3)`不低于0.80；无硬性否决项。
- `ADVANCE_EXPLORATORY`：无可靠功能anchor时不伪造G4，而要求G2不低于0.70、G3不低于
  0.70、G6不低于0.60、至少3个不同independence group；coverage不低于0.70、
  `P(rank <= 3)`不低于0.80。允许进入计算分支，但只能称为结构/进化支持的
  exploratory pocket，不得声称已有机制变构证据。
- `ESCALATE_DISCOVERY`：硬 gate 通过，但coverage介于0.55和0.70之间或稳定性不足。
  只允许获取下一项最能降低不确定性的证据，不授权高成本MSA/构象分支。
- `HOLD`：候选可解释，但覆盖、质量或稳定性不足。
- `STOP`：mapping失败、低质量结构驱动、与orthosteric site混淆、仅由G1驱动或对
  参数轻微变化即消失。

## 8. Agent 决策输出

建议目录：

```text
workdir/autonomous_pocket_discovery/<target_id>/<discovery_run_id>/
├── target_identity.yaml
├── input_manifest.json
├── input_validation_report.json
├── mode_policy.yaml
├── embargo_manifest.yaml
├── search_strategy.yaml
├── literature_evidence.csv
├── structural_homolog_evidence.csv
├── tool_registry.yaml
├── tool_dependencies.yaml
├── metric_registry.yaml
├── candidate_family_freeze.json
├── candidate_pocket_families.csv
├── pocket_evidence_matrix.csv
├── pocket_ranking.csv
├── sensitivity_analysis.csv
├── all_candidate_decisions.csv
├── critic_report.md
├── agent_decision.yaml
├── provenance_manifest.json
├── raw_search_responses/
├── agent_reports/
├── tool_runs/                       # command/stdout/stderr/status/raw outputs
└── candidate_pockets/
    ├── pocket_01/
    │   ├── selected_residues.csv
    │   ├── rationale.md
    │   ├── selection_manifest.json
    │   └── branch_config.yaml
    ├── pocket_02/
    └── pocket_03/
```

`selected_residues.csv` 必须是 selection-only 文件，至少包含：

```text
chain,resseq,insertion_code,residue_name,construct_index,canonical_index,pocket_id,selection_reason,evidence_ids,mapping_status
```

`evidence_ids` 必须能回指 `literature_evidence.csv` 或工具原始输出；不允许只写
“agent judgement”。运行当前单链 runner 时，还要生成只含 construct integer residue
number 的 adapter 文件，但 chain/icode-aware 的 canonical CSV 始终是唯一真实来源。

`agent_decision.yaml` 至少包含：

```yaml
decision_id: "..."
mode: "target_informed_exploration | blind_benchmark | historical_replay"
target_id: "..."
input_manifest_sha256: "..."
run_status: "SUCCESS | BLOCKED | FAILED"
discovery_outcome: "NO_CANDIDATE | ONE_CANDIDATE | MULTI_CANDIDATE | HISTORICAL_VERIFIED"
evidence_completeness: "COMPLETE | PARTIAL"
candidate_decisions:
  - pocket_id: "pocket_01"
    status: "ADVANCE"
    selected_for_branch: true
    residue_set_sha256: "..."
    support_penalized: 0.00
    support_covered: 0.00
    evidence_coverage: 0.00
    evidence_ids: []
  - pocket_id: "pocket_02"
    status: "ADVANCE_EXPLORATORY"
    selected_for_branch: true
    residue_set_sha256: "..."
    support_penalized: 0.00
    support_covered: 0.00
    evidence_coverage: 0.00
    evidence_ids: []
  - pocket_id: "pocket_04"
    status: "HOLD"
    selected_for_branch: false
    residue_set_sha256: "..."
    reason: "..."
evidence_policy_version: "..."
uncertainties: []
contradictory_evidence: []
human_expert_approval: null
```

不得填写虚构的专家姓名、签名或批准。
其中 `ADVANCE/ADVANCE_EXPLORATORY/ESCALATE_DISCOVERY/HOLD/STOP` 是口袋发现阶段的状态；
只有前两者授权分支物化。
分支完成后的 `CONTINUE/ESCALATE/STOP` 是下游构象证据决策，两者不得混用。

## 9. 每个口袋的独立 MSA/构象分支

### 9.1 分叉位置

Iteration 1 的 group A3M、ColabFold PDB 和 fpocket 输出可作为所有 pocket branch 的
只读共享输入。不同口袋必须从 Iteration 1 的 residue clustering、distance metric 和
MSA selection 开始分叉；一旦 Iteration 1 combined MSA 不同，Iteration 2–7、M-fold、
voting、recompile 和 final 全部必须隔离。

```text
shared read-only:
  filtered MSA -> Iteration 1 group A3M -> Iteration 1 PDB/fpocket

branch-specific:
  selected residue set -> Iteration 1 metric/select -> Iteration 2..7
  -> M-fold -> voting -> recompile -> final prediction/control
```

### 9.2 分支隔离

每个 branch 的稳定 ID 应由下列内容计算：

```text
SHA256(target sequence hash + mapping hash + sorted chain/resseq/icode residue set
       + discovery decision hash + branch config hash)
```

建议输出：

```text
workdir/pocket_branches/<target_id>/<decision_id>/<pocket_id>_<fingerprint>/
```

discovery run 根目录还必须写 `branch_index.csv`，记录 pocket ID、fingerprint、
授权状态、配置 hash、workdir 和当前 stage；每个 branch 在查看 final 输出前冻结
`branch_decision_policy.yaml`。

不同分支不得共享可写目录、metric CSV、combined MSA、sampling、voting 或 final PDB。
只有 input hash 完全一致的 Iteration 1 prediction/fpocket 才可只读复用。

当前 runner 支持 `--config`，但现有 `commands/*.sh` wrapper 默认不透传 branch config。
在 branch adapter 完成前，Agent 不得声称可直接用原 wrapper 执行多分支。应生成每个
pocket 的完整配置，并显式调用：

```text
python scripts/run_stepwise_allo.py <command> --config <pocket_branch_config.yaml> ...
```

或先改造 wrapper，使其读取已审计的 `CONFIG` 环境变量。任何一种方式都必须先通过
路径、selection fingerprint 和空输出目录检查。

现 runner 的 residue loader 只消费整数 residue number，不能表达 chain 或 insertion code。
在正式增加 chain-aware loader 前，仅允许对“单链、无 insertion code、映射唯一”的
分支生成 integer adapter；其他情况必须 `HOLD`。

每个 stage 必须先写 expected manifest，完成后核验 observed count、hash、selection
fingerprint 和上游 config hash。未知靶点的 expected count 必须从当次输入派生，不得
沿用 GLP1 历史常数 `759`、`37` 或固定 `bin_3_4`。generated 脚本名也必须包含
`pocket_id + fingerprint`，防止分支间覆盖。

### 9.3 对照设计

每个 pocket branch 都保留现有 prediction/control 配对，并用同一评价代码和计算预算处理。
若预算允许，再在看到分支结果前生成至少一个 matched residue-set negative control：
匹配残基数、chain/拓扑区域、溶剂暴露和二级结构，但不与候选或已知功能位点重叠。
该对照用于检查“任意残基集是否也会被当前算法富集”，不是候选生物学的替代品。

## 10. 分支后评价与继续/停止标准

`pocket_min_distance` 只能作为一个富集指标。每个候选分支至少评价：

由于下游 MSA 本身就是按 selected-residue 距离富集，再在同一批结构上报告距离
下降存在目标函数循环，只是 in-sample optimization，不是独立变构验证。正式判断必须
使用没有参与候选形成/阈值选择的 held-out model/seed 或新计算，并依赖下表的
非距离证据判断口袋价值。若没有 holdout，只能标记为 exploratory/in-sample。

| 维度 | 最低输出 |
|---|---|
| 完整性 | expected/observed PDB、fpocket、CSV、MSA计数和hash |
| 富集效果 | prediction与control的距离分布、效应量、bootstrap CI；注明模型并非独立生物重复 |
| 局部可信度 | 候选残基局部pLDDT、PAE、缺失和构象冲突 |
| 口袋质量 | fpocket/P2Rank分数、druggability、volume、enclosure、极性/疏水性 |
| 持续性 | 跨shuffle/model/seed/构象簇的model-ensemble detection frequency和指标稳定性 |
| 构象多样性 | RMSD/TM-score或等价聚类；代表构象与重复比例 |
| 变构通信 | PRS/ESSA/network或等价证据，及其到功能位点的关系 |
| 可复现性 | 不同seed/profile重跑的一致性和阈值敏感性 |
| 新颖性与风险 | 已知orthosteric重叠、跨膜/无序暴露、holo先验循环性、工具依赖 |

Agent 必须在查看 final branch 结果前写入 `branch_decision_policy.yaml`。建议状态：

- `CONTINUE`：所有硬 barrier 通过；相对control有一致方向的富集；局部结构可信；口袋在
  多个构象/seed中持续；至少一个非DeepAllo/PLB证据维度支持；敏感性分析稳定。
- `STOP`：mapping或完整性失败；优势只来自单一工具/单一构象；低可信区域驱动结果；
  相对control无稳定富集；结果对阈值、seed或旧输出极敏感。
- `ESCALATE`：证据互相矛盾或统计不确定，但候选有独特机制价值。只为此类候选增加
  seeds、MD、fragment/docking或实验设计，不对所有候选无差别扩算。

阈值必须依据目标、结构类型和预先观察到的基线分布登记，不能在看到候选胜负后修改。

每个完成的分支至少产出：

```text
branch_evaluation.csv          # 每个PDB的原子指标及quality flags
preferred_conformations.csv    # 去冗余后的排名、cluster、代表PDB和选择理由
preferred_conformations/       # 与上表一致的PDB、PAE/质量文件或可校验链接
branch_decision.yaml           # CONTINUE/ESCALATE/STOP、阈值、对照和不确定性
branch_provenance.json         # 输入、工具、配置和输出hash
```

`preferred_conformations.csv` 不得只按最小距离排序；必须先做构象去冗余/聚类，
再在每个可靠簇中依据预注册的多指标规则选代表构象。

## 11. 可直接复制给 Agent 的 Prompt 脚本

下面的内容可作为 system/task prompt。运行时用真实值替换 `{...}`。

```text
你是 Autonomous Allosteric Pocket Discovery and Branching Agent。

目标
----
从 PocketMiner/AlloDesigner 阳性残基、Iteration 1 构象集合、DeepAllo top-7 残基
频率表和 PLB top-7 残基频率表出发，自主形成、评价并以选择 2–3 个空间非冗余的
候选变构口袋残基集合。随后为每个候选建立相互隔离的 MSA/构象富集分支，并给出
CONTINUE、STOP 或 ESCALATE 决策。若不足 2 个通过硬 gate，允许输出 0–1 个。你不能
伪造人类专家批准，也不能把计算候选称为
已验证变构口袋。

模式特异规则优先于上述通用目标：historical_replay只hash/schema/count审计后停止，
不执行B–F；blind_benchmark在候选决策hash冻结前禁止靶点/家族allostery、ligand、
holo、mutation和机制文献搜索。

运行参数
--------
mode: {target_informed_exploration|blind_benchmark|historical_replay}
target_name: {target_name}
organism: {organism}
target_accessions: {ids_or_empty}
canonical_fasta: {path}
construct_fasta: {path}
structure_mapping_csv: {path}
iteration1_root: {read_only_path}
iteration1_group_msa_manifest: {path_or_null}
pocketminer_scores: {path}
deepallo_top7_csv: {path}
plb_top7_csv: {path}
candidate_cluster_manifest: {path}
dcc_scores: {path}
deepallo_cluster_scores: {path}
plb_cluster_scores: {path}
functional_or_orthosteric_residues: {path_or_null}
mode_control_manifest: {embargo_or_historical_manifest_or_null}
base_pipeline_config: {path_or_null}
runner_path: {path_or_null}
environment_manifest: {path_or_null}
model_manifest: {path_or_null}
tool_config: {path}
output_root: {new_writable_path}
compute_budget: {budget_and_scheduler_constraints}

不可违反的规则
--------------
1. 原始case、inputs和source_snapshot只读；所有输出写入新的output_root。
2. 首先校验target identity、sequence、chain、resseq、icode和construct/canonical mapping；
   不能唯一映射时停止。
3. 对每个输入、输出、工具、模型和配置记录SHA-256、版本、命令和参数。
4. DeepAllo与PLB保持为两个分开的原始排名轴；其probability是top-k residue
   frequency，不是原始模型概率。两者共享PocketMiner候选池，因此在独立证据
   计数中同属G1；禁止在原始表中合并或覆盖。
5. 先由Iteration 1中的空间cluster形成跨构象pocket family，再做排名；不得把排名靠前
   但空间不连续的残基直接拼接成口袋；无可检测cavity关联的只能称residue patch。
6. 缺文件、缺评分、mapping失败、candidate key不一致或旧输出污染时fail closed。
7. 文献结论必须附DOI/PMID/PDB/UniProt和URL；保存查询式与日期；不能检索到不等于反对。
8. 不得将相关工具输出重复计算成独立证据；记录tool dependency。
9. 目标是2–3个候选，上限为3。如果不足2个通过硬gate，如实输出更少，不得放宽标准凑数。
10. 不得生成虚构的expert_decision、专家姓名、签名或实验结论。
11. 不得把预测构象集的检出频率写成热力学occupancy；PLB不是自由能；
    docking score不是Kd/Ki/ΔG；PLIP接触和全局结构相似性都不能单独证明变构。
12. 任何结构、文献或工具证据缺失都保持NA；禁止以0代替，也禁止在看到
    候选排名后重分配权重。
13. 候选主键必须是显式target/shuffle/group/model/seed/structure-hash/cluster字段；
    禁止使用子串文件名匹配。
14. 冻结metric_registry后才能打分；排名辅助分使用support_penalized，
    support_covered不能绕过coverage gate。

执行步骤
--------
A. Preflight
- 冻结input_manifest和discovery_run_id。
- 从expected manifest生成每个stage的candidate key set，各表独立验exact keys，再按
  预注册的DCC/资格规则生成下一阶段key set；不要求所有阶段行数相同。
- 声明使用legacy_indexing还是corrected_mapping；两者输出完全隔离。
- historical_replay验证historical selection/evidence/expected hash后立即停止。
- blind_benchmark验证embargo_manifest已冻结，并屏蔽禁止的本地文件和远程查询。

B. 候选口袋家族
- 在每个构象中对阳性残基形成chain-aware空间cluster。
- 结构对齐后，依据residue Jaccard、中心距离、空间重叠和ensemble support归并pocket family。
- 保存每个family的残基、中心、DCC、closest pocket、group/shuffle支持和不确定性。
- 分别计算DeepAllo和PLB的pocket-level rank support，使用size-normalized聚合。
- 在查阅本靶点特异文献前冻结candidate-family manifest和hash；若后续改边界，
  必须生成新版本并保留变更理由。

C. 自主证据探索
- 解析靶点同义词并执行目标、家族、同源结构、配体、突变、HDX和状态结构检索。
- 只在target_informed模式的决策前使用目标/家族特异文献；blind_benchmark必须跳过
  这些查询，直到agent_decision hash冻结后才作回顾性评价。
- 优先使用可复现的fpocket/P2Rank、ensemble persistence、ProDy PRS/ESSA、RCSB/Foldseek、
  PLIP和MSA conservation/co-evolution适配器。
- 为每条证据分配A/B/C/D等级，并保存支持、反对、映射质量和来源。
- 连续两轮无新A–C证据、已覆盖正式名/同义词/家族/结构域，或达到预算时停止；
  保存停止原因，不得无限搜索到得到预期答案。

D. 多目标决策
- 为每个pocket输出DeepAllo、PLB、geometry/persistence、ligandability、allosteric
  communication、evolution、literature/homolog、structure quality和evidence coverage。
- 先应用mapping、空间连续、完整性、质量和至少两个不同independence group的硬gate。
- 在通过者上做Pareto排序、默认balanced-weight辅助评分和±25%权重/阈值敏感性分析。
- 从冻结metric_registry生成每个域的s/q，同时报告support_penalized、support_covered、
  evidence coverage和上下界；缺失域不重分配权重。
- 以选择2–3个空间和残基集合非冗余、对敏感性分析稳定的候选为目标；
  未达到数量时不放宽硬gate。
- 每个候选同时写支持理由、反对理由、缺失证据、置信度和最小追加验证。
- 让一个独立critic检查答案泄漏、重复计分、映射错误、过度解释和选择后改阈值。
- 支持多Agent时，Data/Mapping、Literature、Structural、Mechanism和Critic独立产出报告；
  前四者各自冻结hash后orchestrator才能整合，Critic不能接收预期答案。

E. 决策与分支物化
- 写agent_decision.yaml、pocket_evidence_matrix.csv、pocket_ranking.csv和完整provenance。
- 为全部候选保留status、score/coverage、residue-set hash和证据引用；只有
  ADVANCE或ADVANCE_EXPLORATORY可写selection-only selected_residues.csv并物化分支。
- 只读复用相同的Iteration 1 PDB/fpocket；从Iteration 1 residue metric和MSA selection开始
  为每个pocket建立独立workdir/config。Iteration 2–7、M-fold、voting、recompile和final
  不得跨分支共享可写结果。
- 当前commands wrapper不透传branch config；必须显式调用runner --config或先提供经过审计
  的CONFIG适配器，不能假装原wrapper已支持多分支。
- 单链integer residue adapter必须从chain-aware selection CSV生成；多链或icode冲突时HOLD。
- 计数和voting bin由当次输入派生，不得沿用GLP1的759/37/bin_3_4常数。
- 每个分支保留prediction/control；预算允许时增加预注册的matched residue-set
  negative control，以检验非特异富集。

F. 分支评价
- 在看final结果前冻结branch_decision_policy.yaml。
- 用未参与candidate/threshold选择的held-out model/seed评价；无holdout时显式标记
  exploratory/in-sample，不得把同一距离目标的改善当作独立验证。
- 除pocket_min_distance外，比较prediction/control效应量与CI、local pLDDT/PAE、
  fpocket/P2Rank ligandability、pocket persistence、构象多样性、allosteric communication、
  seed稳定性和artifact flags。
- 对每个分支给出CONTINUE、STOP或ESCALATE及可审核理由。
- 写branch_evaluation.csv、preferred_conformations.csv/目录、branch_decision.yaml和
  branch_provenance.json；先聚类去冗余，不得只按最小pocket distance选构象。

最终响应
--------
先给结论和选出的0–3个pocket；随后列出每个pocket的chain-aware residues、证据矩阵、
反对证据、置信度、分支路径和决策。最后列出所有缺失输入、未运行工具、假设、搜索式、
hash、版本和不能据此声称的结论。不要只输出自然语言；必须实际生成规定的CSV/YAML/JSON。
```

## 12. Task payload 模板

```yaml
schema_version: "autonomous-allosteric-pocket-agent/v1"
mode: "target_informed_exploration"

mode_controls:
  embargo_manifest: null
  historical_evidence_manifest: null
  historical_selection: null
  historical_expected_outputs: null

target:
  name: null
  organism: null
  accessions: []
  canonical_fasta: null
  construct_fasta: null
  structure_mapping_csv: null

inputs:
  iteration1_root: null
  iteration1_group_msa_manifest: null
  pocketminer_scores: null
  deepallo_top7_csv: null
  plb_top7_csv: null
  candidate_cluster_manifest: null
  expected_keys_by_stage: null
  dcc_scores: null
  deepallo_cluster_scores: null
  plb_cluster_scores: null
  functional_or_orthosteric_residues: null

candidate_key:
  fields: [target_id, shuffle_id, group_id, model_id, seed, structure_sha256, cluster_id]
  require_exact_join: true

tools:
  config: null
  metric_registry: null
  allow_web_literature_search: true
  allow_remote_structure_databases: true
  allow_heavy_md_or_docking_without_escalation: false

search:
  allowed_sources: []
  forbidden_sources: []
  maximum_queries: null
  maximum_minutes: null
  stop_after_consecutive_no_new_A_to_C_rounds: 2

geometry:
  atom_selection: "CA"
  dbscan_min_samples: 2
  dbscan_eps_angstrom: 6.0
  dcc_threshold_angstrom: 10.0
  family_center_threshold_angstrom: 6.0
  minimum_family_support_fraction: null
  require_detectable_cavity_association: true

selection_policy:
  maximum_candidate_pockets: 3
  minimum_residue_count: 2
  maximum_selected_pairwise_jaccard: 0.50
  minimum_independence_groups: 2
  minimum_evidence_coverage: 0.70
  weight_sensitivity_fraction: 0.25
  force_candidate_count: false
  domain_weights:
    G1_model_prior: 0.15
    G2_geometry_ligandability: 0.20
    G3_ensemble_behavior: 0.20
    G4_allosteric_communication: 0.20
    G5_external_structure_experiment: 0.15
    G6_evolution_function: 0.10
  sensitivity:
    top_k: [3, 5, 7, 10]
    dbscan_eps_angstrom: [5.0, 6.0, 7.0]
    dcc_angstrom: [8.0, 10.0, 12.0]
    family_center_angstrom: [4.0, 6.0, 8.0]
  bootstrap:
    replicates: 1000
    seed: 42
    primary_unit: "shuffle"
    secondary_unit: "group"

branching:
  enabled: true
  runner_path: null
  runner_sha256: null
  base_pipeline_config: null
  environment_manifest: null
  model_manifest: null
  scheduler_profile: null
  compute_budget: null
  share_iteration1_predictions_read_only: true
  fork_from_iteration1_metric: true
  require_selection_fingerprint: true
  require_empty_or_matching_output: true

evaluation:
  require_held_out_models_or_seeds: true
  allow_in_sample_result_as_validation: false
  require_non_distance_evidence: true
  write_preferred_conformations: true

outputs:
  root: null
  write_machine_readable_artifacts: true
  write_ranked_report: true
  preserve_all_raw_evidence: true
```

模板中与所选模式/启用阶段相关的 `null` 值必须在冻结 task payload 前填写；
不相关阶段必须显式 `enabled: false`，不得由 Agent 猜测。

## 13. 成功、阻断与降级条件

不得用一个状态同时表示“流程是否正常结束”和“发现了几个口袋”。必须正交报告：

- `run_status = SUCCESS | BLOCKED | FAILED`：只表示流程完整性。mapping不唯一、exact-key join
  不完整或输出可能覆盖其他run时为 `BLOCKED`；绕过hard gate、伪造引用或blind泄漏时为
  `FAILED`。
- `discovery_outcome = NO_CANDIDATE | ONE_CANDIDATE | MULTI_CANDIDATE | HISTORICAL_VERIFIED`：
  只表示科学输出。0或1个候选不会自动降低 `run_status`。
- `evidence_completeness = COMPLETE | PARTIAL`：表示预注册的非必需证据是否齐全。目标直接
  文献稀少本身不是故障；它只会降低coverage、扩大不确定性或使单个候选进入
  `ESCALATE_DISCOVERY/HOLD`。

## 14. 实施前仍需开发的接口

本文件定义的是 agent 任务和验收契约。当前 `allo_stepwise` 尚需实现：

1. 参数化 Step 3 scoring 和 pocket-family builder；
2. literature/structure/tool adapter registry；
3. `agent_decision.yaml` schema validator；
4. selection fingerprint 和 branch config generator；
5. wrapper 的 branch config 透传，或直接 runner orchestration；
6. 多分支 expected-count barrier、stage manifest 和 stale-output 隔离；
7. final branch comparison 与 CONTINUE/STOP/ESCALATE evaluator；
8. 小型 blind benchmark、GLP1 historical replay 和至少一个未知靶点的 golden test。

在这些接口完成前，该 Prompt 可用于生成审计计划和候选证据，但不能宣称已经实现了
全自主端到端运行。

## 15. 推荐工具的主要来源

- [fpocket 官方仓库](https://github.com/Discngine/fpocket)：包含 fpocket、dpocket、
  tpocket 和用于构象集合/轨迹的 mdpocket。
- [P2Rank 官方仓库](https://github.com/rdk/p2rank)：独立命令行口袋预测，并支持
  fpocket rescore；两种模式必须在证据依赖图中区分。
- [MDpocket 原始论文](https://academic.oup.com/bioinformatics/article/27/23/3276/234086)：
  用于构象集合中的瞬时口袋检测和描述。
- [ProDy 2.0](https://pmc.ncbi.nlm.nih.gov/articles/PMC8545336/)及
  [PRS教程](https://www.bahargroup.org/prody/tutorials/prs_tutorial/prs_tutorial.pdf)：
  用于弹性网络、扰动响应和潜在变构通信分析。
- [RCSB PDB Search API](https://search.rcsb.org/)：支持metadata、sequence和structure
  搜索；命中后必须用Data API核对结构、配体和实验信息。
- [Foldseek 官方仓库](https://github.com/steineggerlab/foldseek)：快速结构相似性搜索。
- [PLIP 官方仓库](https://github.com/pharmai/plip)：对已结合配体的PDB结构生成可追溯
  的蛋白–配体接触证据。

工具输出均是计算证据，不等价于实验验证。任何“最具价值”“可成药”或“变构”结论
都必须与证据等级、不确定性和验证建议一起报告。

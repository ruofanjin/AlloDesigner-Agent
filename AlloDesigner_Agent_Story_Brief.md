# AlloDesigner Agent 故事包装 Brief

**版本**：v1.1  
**定位**：对内科学/产品 brief（可直接用于一作方法学包装与对外精简 pitch）  
**素材来源**：`allodesigner5.1(1).docx`、`allodesigner-SI5.0.docx`、`cryptic pocket.pptx`、`AlloDesigner_Agent.docx`、本仓库代码  
**口径冻结**：固定生物学问题分解、阶段目标与科学约束；开放每个环节内的工具选择与组合。  
**工程落地**：[`AlloDesigner_MultiAgent/`](AlloDesigner_MultiAgent/)（阶段合同 + 多智能体编排 + 论文流程串接）

### 与 `.cursor/plans/allodesigner_agent_story_*.plan.md` 的关系

| 产物 | 角色 | 是否还要大改 |
| --- | --- | --- |
| `allodesigner_agent_story_*.plan.md` | **叙事包装计划**（讲什么、边界是什么） | **不必重写**；它已完成使命 |
| 本文 `AlloDesigner_Agent_Story_Brief.md` | 计划落地后的故事稿 | 仅补“工程映射/状态” |
| `AlloDesigner_MultiAgent/` | 按故事口径实现的**多智能体系统** | 持续迭代的工程主线 |

一句话：plan 是“为什么这样讲 Agent”；MultiAgent 是“怎样按这个口径跑起来”。两者不是竞争文档，而是 **故事层 → 工程层**。

---

## 1. 一句话定位与非目标

### 一句话定位

**AlloDesigner Agent：把隐匿变构口袋发现从专家隐性流程，升级为阶段合同驱动、工具可替换、证据可审计的受控科研 Agent。**

### 它解决什么

一作团队已经用 AlloDesigner 证明：隐匿变构口袋不是“单点预测”问题，而是一条必须串联的科学主线——残基级结构先验 → 偏好构象富集 → 物理约束下的定向采样 → 开放样口袋评价 → 候选物排序。Agent 化的目标，不是重写这条主线，而是把它变成机器可读、可执行、可版本化、可比较的阶段任务系统。

### 明确非目标

| 非目标 | 原因 |
| --- | --- |
| 通用“蛋白科学家 Agent”自由拆题 | 隐匿变构口袋领域理解不足时，自由拆题会放大搜索空间、工具错配与答案泄漏 |
| 宣称 Agent 可独立作出最终科学结论 | Agent 输出可复核决策材料；最终科学判断留给专家 |
| 把 AlloDesigner 写成无需比较的唯一赢家 | AlloDesigner 是参考主路径与内部基线，进入同一工具池接受替换/补充/对照 |
| 把知情恢复包装成盲法发现 | 回溯轨与探索轨必须在输入、缓存、日志与报告上隔离 |
| 把未经验证的口袋/配体直接称为“真实/有效” | 探索轨只产生待验证假设 |

---

## 2. 为什么不是通用 Agent

### 2.1 问题本身不是单一工具任务

隐匿变构口袋（cryptic allosteric pocket）通常在实验结构中不可见或仅瞬时出现。现有工具各自只覆盖局部：

- 结构生成 / AlphaFlow / AFCluster：给构象，不自动给出功能导向的口袋定义
- PocketMiner / PLM / 共折叠：给残基或口袋线索，不自动完成物理可达的开放态采样
- MD / metadynamics：给物理真实性，但缺高质量初始构象与可解释 CV 时成本极高
- docking / 虚筛：给候选排序，但口袋几何与开放态不可靠时结果无意义

因此，真正稀缺的不是“再多一个模型”，而是**正确的问题分解、信息边界与评价合同**。

### 2.2 当前不把全局科学规划交给 Agent

如果允许 Agent 从“研究某蛋白的隐匿口袋”直接自由拆解，容易出现：

1. 搜索空间过大，效率下降  
2. 工具语义错配（把共折叠结果当成已验证口袋）  
3. 隐含答案泄漏（HOLO/配体/已知残基混入盲态运行）  
4. 人工选残基、选构象、选帧不可追溯  

**现阶段分工**：

- **人类专家**：冻结问题如何拆分、每阶段回答什么、允许使用什么信息、什么结果算完成  
- **Agent**：只在固定环节内搜索、判断、调用、比较工具，整理文献先验，执行获批任务，记录全部依据与人工干预  

### 2.3 AlloDesigner 的双重定位

| 层面 | 定位 |
| --- | --- |
| 方法学层面 | 专家团队综合科学能力、成本、解释性与物理约束后形成的**参考主路径** |
| 模块/工具层面 | 预先登记的自研工具选项、内部基线与参考实现，可与外部工具公平比较 |

核心口径再强调一次：

> **固定的是生物学问题分解、阶段目标和科学约束；开放的是每个环节内的工具选择与组合。**

---

## 3. 专家冻结的六阶段合同

下列阶段用于传达现有方法学逻辑方向；正式阶段名称、数量与依赖仍可由科学专家再冻结版本号。Agent 不得改写阶段目标，只能在合同内选择执行器。

```mermaid
flowchart LR
  S1[Stage1_Boundary] --> S2[Stage2_ResiduePrior]
  S2 --> S3[Stage3_EnsembleEnrichment]
  S3 --> S4[Stage4_PhysicsSampling]
  S4 --> S5[Stage5_PocketEvaluation]
  S5 --> S6[Stage6_CandidateRanking]
```

### Stage 1｜目标与信息边界定义

- **人类冻结**：靶点、任务类型（回溯/探索）、盲态或知情用途、可用先验清单、禁止信息清单  
- **Agent 可做**：文献检索、先验草案整理、泄漏风险标注、案例协议生成  
- **完成标准**：形成经审批的《信息边界与先验冻结单》  
- **AlloDesigner 默认选项**：案例协议模板（GLP-1R / PCSK9 / CB1R 等）

### Stage 2｜残基级或区域级结构先验

- **人类冻结**：标签定义（如 LIGSITE 动态标签）、阈值、评价指标（PR-AUC/Recall 等）  
- **Agent 可做**：在工具池中比较 PocketMiner、PLM、共折叠残基线索等，选定或组合执行器  
- **完成标准**：残基/区域概率图 + 阈值化候选集合 + 工具比较记录  
- **AlloDesigner 默认选项**：Allo-PocketMiner（GVP，Dice+BCE fine-tune）  
- **论文锚点**：独立测试集 PR-AUC 0.701 vs PocketMiner 0.582

### Stage 3｜候选构象生成与富集

- **人类冻结**：偏好构象定义（如关键残基簇中心与 fpocket 中心距离）、迭代轮次、保留比例、随机种子策略  
- **Agent 可做**：比较 AlphaFlow、AFCluster、MSA 子采样/投票等策略，执行富集并报告对照  
- **完成标准**：纯化 MSA / 偏好构象集合 + 对照随机 MSA 结果  
- **AlloDesigner 默认选项**：AlphaFlow apo 集成 + AF-ClaSeq（迭代 shuffle、cross-group sampling、sequence voting）

### Stage 4｜物理约束下的定向构象采样

- **人类冻结**：CV 定义（SASA / 残基对距离等）、模拟预算、膜体系设定、停止准则  
- **Agent 可做**：比较 unbiased MD、metadynamics、RAVE/SPIB 类方案，执行获批采样  
- **完成标准**：开放样构象轨迹/代表帧 + 相对消融对照  
- **AlloDesigner 默认选项**：AI-prior guided metadynamics（论文主路径；PPT 中亦有 AF-RAVE/biased MD 叙述）

### Stage 5｜开放样构象与口袋评价

- **人类冻结**：成药性/变构评分合同、聚类参数、共识规则（如 top-k）  
- **Agent 可做**：组合 fpocket、DeepAllo、PLB 等，报告一致与分歧  
- **完成标准**：口袋簇排序表、残基共识列表、不确定性说明  
- **AlloDesigner 默认选项**：DBSCAN 空间聚类 + DeepAllo + PLB 共识

### Stage 6｜配体或候选物排序

- **人类冻结**：化合物库范围、对接协议、Top-N 与再评分规则  
- **Agent 可做**：执行虚筛流水线，输出可复核排序包，不宣布“有效配体”  
- **完成标准**：候选排序、姿态、分数分布、协议版本  
- **AlloDesigner 默认选项**：GLP-1R 案例虚筛流程（KarmaDock / Glide / Vina 等，按获批协议）

### 工具允许角色（适用于所有阶段）

| 角色 | 含义 | 对主流程影响 |
| --- | --- | --- |
| 直接复用 | 无需改变科学语义即可满足合同 | 可作为执行器候选 |
| 适配后复用 | 科学问题一致，需接口/格式转换 | 适配验证后再进入执行 |
| 替代候选 | 可完成与自研模块相同阶段任务 | 进入模块级公平比较 |
| 补充工具 | 提供正交信息或质控 | 不替代主输出，可增强证据 |
| Benchmark 对照 | 验证边界、失败模式或相对性能 | 与主执行结果分开报告 |
| 不适用 | 输入输出、信息权限或科学约束不匹配 | 记录排除依据，不进入该环节 |

---

## 4. AlloDesigner 作为参考主路径与工具基线

### 4.1 专家主路径（论文证据层）

AlloDesigner 主文主张的端到端链路：

1. 低成本构象集成（HOLO–APO 线性插值/能量最小化用于训练；推理侧可用 AlphaFlow apo）  
2. GVP 学习 LIGSITE 动态标签，输出残基级 cryptic 概率  
3. 以预测残基为空间先验，做 MSA 纯化与序列–构象投票，得到功能导向初始构象  
4. 将残基先验自动转译为可解释 CV，驱动 metadynamics  
5. DeepAllo / PLB 共识评价口袋；必要时进入结构基虚筛  

这条路径证明了“问题分解有效”，因此成为 Agent 的**参考主路径**。

### 4.2 关键结果锚点（讲故事时可用，但要带边界）

| 证据 | 用途 | 边界提醒 |
| --- | --- | --- |
| PR-AUC 0.701 vs PocketMiner 0.582（40 蛋白测试） | Stage 2 基线优势 | 是残基先验阶段指标，不是端到端药物有效性 |
| GLP-1R extra-helical 口袋与候选配体 | Stage 3–6 故事样板 | 若用于回溯，必须区分盲态运行与知情评价 |
| PCSK9 loop/hinge/β-sheet 覆盖与 open 态采样 | 泛化叙事 | “未解析 open 态”是计算假设，需实验验证口径 |
| 消融：无纯化 MSA / 无 CV / 仅 AlphaFlow 均弱于完整链路 | 证明阶段协同必要 | 用于说明合同不可随意删阶段 |

### 4.3 Agent 化跃迁（产品故事层）

论文/案例中曾经隐含的人工选择——选残基、选构象、选帧、使用 HOLO/配体知识——必须改造成：

**文献先验生成 → 人工审批 → 冻结使用 → 全过程记录**

Agent 的产品价值因此不是“更会猜”，而是：

1. 在固定环节内发现可复用、可替换、可补充或可 benchmark 的外部工具  
2. 外部工具不满足合同时，有依据地回退到 AlloDesigner 自研模块  
3. 为专家输出可复核决策包，而不是替代专家宣布结论  
4. **在冻结合同内自主生成推理链与执行图**（`ReasoningOrchestrator` / `docs/reasoning_orchestrator.md`），随产物与预算改写 DAG，并由 Critic 守宣称边界  

---

## 5. GLP-1R：回溯故事样板（可讲，但标明答案边界）

### 5.1 为什么适合做样板

GLP-1R 同时具备：

- 高难度 GPCR / 膜蛋白设定  
- 已知 NAM 相关 HOLO 参考（如 5VEX）  
- 从序列到虚筛的完整演示链（PPT + SI）  
- 仓库内已有 case 数据与部分脚本  

因此它适合讲**回溯轨**：检验方法能否恢复已知或近已知结果，并比较工具边界。

### 5.2 样板叙事（对外可压缩为 90 秒）

1. **边界冻结**：任务设为回溯验证；HOLO/配体信息只进入评价端或知情上限轨，不默认进入盲态执行。  
2. **残基先验**：AlphaFlow 生成 apo 集成 → Allo-PocketMiner 输出残基概率 → 多构象均值，阈值约 0.7。  
3. **口袋共识**：DBSCAN 聚类 + DeepAllo/PLB，聚焦 TM6/TM7 螺旋外膜脂质区，形成关键残基集合。  
4. **构象富集**：MSA 迭代纯化与序列投票，使关键残基簇中心与 fpocket 中心距离下降到更口袋样的构象。  
5. **物理采样**：以偏好构象为起点，用 SASA/距离等 CV 做定向采样，富集开放口袋。  
6. **候选排序**：对代表性开放构象做虚筛，输出排序包供专家复核。  

### 5.3 必须同时讲清的“答案边界”

| 轨道 | 允许 | 禁止 |
| --- | --- | --- |
| 答案盲态运行 | 只用实际应用可获得且经审批的非答案先验 | 把 5VEX 关键残基、配体坐标、人工选定帧偷偷喂给执行 Agent |
| 知情上限/评价 | 用 HOLO/配体评估恢复能力、设性能上限 | 把知情恢复写成“未知问题上的盲法发现” |
| 报告层 | 分栏报告盲态结果与知情对照 | 混写进同一“发现”结论而不标注 |

**关键原则：存在答案，不等于运行时允许看到答案。**

---

## 6. 探索轨：如何防止过度宣称

探索轨用于无现成 HOLO/配体答案的新靶点。目标是产生**值得后续验证的假设**，不是宣布发现。

### 6.1 允许输出

- 待验证口袋假设（残基集合、几何描述、支撑证据）  
- 候选构象与开放样指标（体积、SASA、距离、稳定性）  
- 计算候选物排序（明确协议与不确定性）  
- 工具比较与失败模式记录  

### 6.2 禁止措辞 / 禁止结论

- 无独立验证时，不得称“真实口袋”“已证实机制”“有效配体/抑制剂”  
- 不得把补充工具的正交信号写成主结论  
- 不得把文献中对同源蛋白的口袋知识，未经审批地当作本靶点答案  

### 6.3 探索轨最小治理清单

1. 先验来源是否全部可公开追溯且已审批  
2. 是否存在隐蔽的结构答案泄漏（如用 HOLO 做靶点准备却未标注）  
3. 每个阶段是否有完成合同与否决条件  
4. 最终报告是否使用“假设 / 候选 / 待验证”语义  
5. 是否保留可复现的随机种子、阈值、工具版本与人工干预日志  

---

## 7. Agent 输出物：决策包、工具比较表、审计日志

Agent 每个阶段结束后，不交付“最终真相”，而交付标准输出包。

### 7.1 阶段决策包（Decision Packet）

建议字段：

- `stage_id` / `stage_contract_version`  
- `task_track`：`retrospective_blind` / `retrospective_informed` / `exploratory`  
- `inputs_frozen`：输入清单与哈希  
- `priors_approved`：审批通过的先验及审批人/时间  
- `tools_considered`：候选工具列表  
- `tool_selected`：最终执行器与选择理由  
- `outputs`：主输出路径与摘要指标  
- `qc_flags`：失败、警告、不确定性  
- `human_interventions`：人工改阈值、改残基、改 CV 等  
- `claims_allowed`：本阶段允许的表述边界  

### 7.2 工具比较表（Tool Comparison Sheet）

每阶段至少保留：

| 工具 | 角色 | 是否满足合同 | 关键指标 | 成本/耗时 | 决策 | 排除/入选依据 |
| --- | --- | --- | --- | --- | --- | --- |

AlloDesigner 自研模块与外部工具使用同一表格，避免“自研免审”。

### 7.3 审计日志（Audit Log）

最低要求：

- 全部提示、工具调用、参数、环境与版本  
- 文献先验引用与审批状态  
- 盲态/知情上下文隔离记录（分库或分命名空间）  
- 随机性控制（seed、MSA 分组、采样帧）  
- 任何人工覆盖必须带理由，不能静默改写  

### 7.4 对专家的最终交付物

一次完整任务结束时，专家拿到的是：

1. 六阶段决策包合集  
2. 主路径结果与替代工具对照  
3. 可发表/可答辩口径的“允许宣称清单”  
4. 下一步实验或计算验证建议  

而不是一句“Agent 已发现某某口袋”。

---

## 8. 与现有代码仓库的映射与缺口

### 8.1 阶段 ↔ 论文 ↔ 仓库映射

| 阶段 | 论文/SI/PPT 证据 | 仓库现状 | 成熟度 |
| --- | --- | --- | --- |
| Stage 1 边界与先验 | Agent brief；案例中隐含 HOLO/配体使用 | 无正式协议模块；仅文档口径 | 文档级 |
| Stage 2 残基先验 | 主文 Table 1；GVP/LIGSITE；SI 标签设计 | `Allo-PocketMiner/`：`models.py` `gvp.py` `train_DiceBCELoss.py` `test.py` `case_predict.py` + `model_weight/` + case `.npy` | 可运行原型（需 Zenodo 全量训练数据） |
| Stage 3 构象生成与富集 | 主文 Fig.3；SI GLP1/PCSK9 迭代与投票；PPT Step3–4 | `AlphaFlow/` helper；`Allo_af_claseq/` 1–13 编号脚本、`11_sequence_voting.py` `12_recompile.py` | 案例脚本级（大量硬编码路径） |
| Stage 4 物理采样 | 主文 metadynamics/SPIB；PPT AF-RAVE/biased MD；SI 膜体系与消融 | `Allo-MD/` agentctl；本地 **1 ns demo 已完成**（`distance-simulation-1ns-demo` / `glp1r_distance_1ns_demo_001`）；证据见 `AlloDesigner_MultiAgent/docs/stage4_demo_glp1r_1ns.md` | **partial/demo**（非论文级 ~200 ns 冻结复现） |
| Stage 5 口袋评价 | DeepAllo + PLB；DBSCAN；fpocket 距离 | `allo_stepwise` historical_replay + **Stage4 帧 fpocket 对照 demo**（`stage5_glp1r_pocket_eval_demo`）；证据见 `AlloDesigner_MultiAgent/docs/stage5_demo_glp1r_pocket_eval.md` | **partial/demo**（非全栈 DeepAllo/MDpocket 重算） |
| Stage 6 候选排序 | 主文 Fig.5 虚筛；PPT KarmaDock/Glide/Vina | **作业单 + Vina/Glide 回传 schema 已 seeded**（`job_packs/stage6_candidate_ranking_glp1r_seeded`）；证据见 `AlloDesigner_MultiAgent/docs/stage6_seeded_job_pack.md` | **partial/seeded**（非真实全库/论文 cascade） |

### 8.2 仓库模块速览

```text
AlloDesigner/
├── AlphaFlow/                 # Stage3 入口：MSA + ESMFlow/AlphaFlow 预测 helper
├── Allo-PocketMiner/          # Stage2：GVP 残基级口袋预测
├── Allo_af_claseq/            # Stage3+5：fpocket/聚类/DeepAllo/PLB/MSA voting
├── README.md                  # 三模块工作流说明
├── AlloDesigner_Agent.docx    # Agent 化需求口径
└── AlloDesigner_Agent_Story_Brief.md  # 本故事包装 brief
```

### 8.3 已实现与缺口（对 Agent 产品化的诚实清单）

**已具备**

- Stage 2 模型架构、权重与 case 推理入口  
- Stage 3/5 的研究型脚本链与 GLP1 示例输出  
- 清晰的科学主线文档（主文 + SI + Agent 需求）  

**缺口**

- 无统一 CLI / 阶段合同配置 / 决策包 schema  
- 无 Stage 1 先验审批与盲态隔离机制  
- Stage 4：Allo-MD 已接入；GLP1 **1 ns demo** 端到端完成（成熟度 partial/demo）。正式 ~200 ns 冻结协议为可选，非当前叙事必需  
- Stage 5：historical_replay + Stage4 帧 fpocket↔pocket_01 对照 demo 已完成（partial/demo）；全栈 DeepAllo/DBSCAN/MDpocket 重算与 MultiAgent 自动回传仍待产品化  
- Stage 6：作业单 + Vina/Glide 回传接口已 seeded（partial/seeded）；真实对接与论文 cascade 仍外站执行  
- `Allo_af_claseq` 路径硬编码（`AF_ClaSeq/case/...`、本机 fpocket 路径）  
- 缺 `requirements.txt` / 环境锁定；依赖 AlphaFlow、PocketMiner、DeepAllo、ColabFold、AutoGluon 等外部栈  
- 训练全量 `.npy` 需 Zenodo（`https://zenodo.org/records/19234183`）  

### 8.4 建议的产品化顺序（服务故事可信度）

1. **先固化合同**：把六阶段做成 YAML/JSON schema + 决策包模板  
2. **先打通可演示闭环**：Stage 1–3–5 以 GLP-1R 回溯盲态 demo 为主（仓库最接近）  
3. **重计算**：Stage 4 已用 Allo-MD 完成 1 ns demo；Stage 5 已做口袋对照 demo；Stage 6 以「作业单 + Vina/Glide 回传审计」接入（seeded），真实对接在外站执行  
4. **同步工具池**：为每阶段登记 AlloDesigner 模块与至少 1 个外部对照工具  

---

## 9. 对外可直接使用的故事文本（精简版）

> 隐匿变构口袋是药物发现里的“暗态”：实验结构里看不见，常规 MD 又太贵，单点 AI 往往只能给出局部线索。  
>  
> AlloDesigner 一作团队的贡献，首先不是又一个口袋模型，而是把这个问题拆成可审计的科学阶段：先得到残基级结构先验，再富集功能导向构象，再落到物理采样与候选排序。论文证明这条分解有效——在 40 个变构蛋白上残基识别 PR-AUC 达到 0.701，并在 GLP-1R、PCSK9 等难点靶标上打通案例。  
>  
> AlloDesigner Agent 要做的，是把这条专家主路径变成受控工作流：人类冻结阶段合同与信息边界；Agent 只在合同内搜索、调用和比较工具，并把 AlloDesigner 自研模块作为可替换基线，而不是无需检验的唯一答案。系统同时支持有答案的回溯验证与无答案的探索发现，且严格防止答案泄漏与过度宣称。  
>  
> 最终，Agent 交付的不是一句“发现了口袋”，而是给领域专家的可复核决策包。

---

## 10. 收束

AlloDesigner Agent 的故事主角，不是“更强的自治”，而是**把一作已经验证的方法学，转成可比较、可替换、可审计的执行系统**。

- 对科学：守住隐匿变构口袋问题的正确分解  
- 对工程：把论文模块登记进工具池，并诚实标注成熟度  
- 对治理：用双轨隔离与决策包，防止把计算假设说成已证实发现  

这就是可对外包装、也对内可执行的 AlloDesigner Agent 故事。

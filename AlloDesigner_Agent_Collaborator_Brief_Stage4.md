# AlloDesigner Agent — Stage4 状态快报（合作者）

**日期**：2026-08-14（UTC）  
**结论**：Stage4（physics_sampling）本地 **1 ns demo 已完成**，成熟度标为 **`partial / demo`**。不宣称论文级 ~200 ns 冻结协议复现。

## 跑通了什么

Profile `distance-simulation-1ns-demo`，run `glp1r_distance_1ns_demo_001`：

1. minimization  
2. equilibration（~1.875 ns）  
3. normal **1 ns**（235.3 ns/day）  
4. distance monitor **1 ns**（110.8 ns/day）  
5. distance metad **1 ns**（104.3 ns/day）  

硬件：单卡 H100；GMX 2024.3 + PLUMED 2.9.3（SASA）。

## 产物位置

`/home/ubuntu/work/allo-md/runs/glp1r_distance_1ns_demo_001/`

关键回传物：`eq6.gro`、`normal_1ns.xtc`、`colvar_distance`、`HILLS`、`COLVAR_biased.dat`、`distance_metad_1ns.xtc/.gro`。

完整表：[`AlloDesigner_MultiAgent/docs/stage4_demo_glp1r_1ns.md`](AlloDesigner_MultiAgent/docs/stage4_demo_glp1r_1ns.md)  
机器可读：[`AlloDesigner_MultiAgent/runs/stage4_demo_glp1r_distance_1ns/stage_result.json`](AlloDesigner_MultiAgent/runs/stage4_demo_glp1r_distance_1ns/stage_result.json)

## 对合作者的口径

| 可说 | 不可说 |
|---|---|
| Allo-MD Stage4 后端在本站点可执行 | 论文历史 100+50+50 ns 已复现 |
| 缩短预算下已采到 CV/偏置轨迹 | 机制已证实 / 口袋已实验确认 |
| Agent 编排可进入 Stage5 对接 | 端到端自主发现已完成 |

## 下一步（产品）

Stage4 仿真侧可收口；优先 Stage5 口袋评价对接本次帧/CV，Stage6 虚筛仍外接。

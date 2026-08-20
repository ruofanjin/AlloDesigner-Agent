# Stage6 seeded record — job pack + Vina/Glide return

**Status**: `partial / seeded`  
**Completed (UTC)**: 2026-08-14  
**Job pack**: `/home/ubuntu/file2/jrf/AlloDesigner/AlloDesigner_MultiAgent/job_packs/stage6_candidate_ranking_glp1r_seeded`  
**Run**: `/home/ubuntu/file2/jrf/AlloDesigner/AlloDesigner_MultiAgent/runs/stage6_glp1r_ranking_seeded_demo`

## What this is

Stage6 (`candidate_ranking`) is wired as an **external docking job sheet** with a fixed **return schema**.  
Vina and Glide are both first-class return engines. This site does **not** ship Glide; Vina binary was not available at seed time — interface demo uses schema-conformant **seeded example returns** (`score_type=seeded_example_not_docking`).

## Consumes (Stage5 handoff)

| Field | Value |
|---|---|
| pocket_id | `pocket_01` |
| residues | 354,355,357,358,365,369,410–417 |
| receptor | Stage5 `t0250.pdb` (Protein from Stage4 metad) |
| box center | CA centroid (53.564, 58.499, 108.802), size 22³ Å |
| continue_gate | `CONTINUE` |
| library_scope (frozen) | `seed_demo_n15` |

## Delivered artifacts

| Artifact | Path |
|---|---|
| Request / job sheet | `job_packs/.../request.yaml`, `job_sheet.json` |
| Vina operator pack | `external/vina/` (`vina.conf`, `run_vina.sh`) |
| Glide operator pack | `external/glide/` (`grid_box.txt`) |
| Return schema | `schemas/stage6_vs_return.schema.json` |
| Ingest | `scripts/ingest_return.py` |
| Example Vina return | `runs/.../returns/vina_seeded_example/` |
| Example Glide return | `runs/.../returns/glide_seeded_example/` |
| Promoted stage_result | `runs/.../stage_result.json` (`engines_returned.vina` + `.glide`) |

## How a real site returns

1. Dock with Vina and/or Glide using the job pack inputs.  
2. Write `return.json` + `ranked_candidates.csv` (+ `poses/`).  
3. `python3 scripts/ingest_return.py --pack-dir <pack> --return-dir <dir> --promote-run-dir <run>`.

## Consistency口径

| 可说 | 不可说 |
|---|---|
| Stage6 作业单 + Vina/Glide 回传接口已 seeded | 论文级 KarmaDock/Glide/Vina cascade 已复现 |
| 外部站可按 schema 回传排序包 | 本机 seeded 分数 = 真实对接 |
| 消费 Stage5 `pocket_01` + `t0250` | 有效配体已证实 / 全库虚筛完成 |
| 成熟度 **partial/seeded** | Stage6 科学虚筛结果已完成 |

## Gaps

- No on-box Vina/Glide execution in this seed.  
- Seed library ≠ production library (`human_freezes.library_scope` must be updated).  
- MultiAgent `RankingAgent` / `_ranking` `.py` still missing; job pack is the operable contract.

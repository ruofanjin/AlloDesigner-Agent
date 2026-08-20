# Stage4 demo record — GLP1R distance 1 ns

**Status**: `demo_completed` (local shortened protocol; **not** frozen historical 200 ns reproduction)  
**Date (UTC)**: 2026-08-14  
**Maturity claim**: `partial / demo` — Allo-MD backend exercised end-to-end; paper-scale sampling deferred by product choice.

## Run identity

| Field | Value |
| --- | --- |
| Profile | `distance-simulation-1ns-demo` |
| Run ID | `glp1r_distance_1ns_demo_001` |
| Work root | `/home/ubuntu/work/allo-md/runs` |
| Absolute run dir | `/home/ubuntu/work/allo-md/runs/glp1r_distance_1ns_demo_001` |
| Resume log | `/home/ubuntu/work/allo-md/execute_1ns_demo_resume.log` |
| Site config | `/home/ubuntu/work/allo-md/site.env` |
| GMX stack | `/home/ubuntu/opt/gmx-stack/env.sh` |
| Hardware | 1× NVIDIA H100 80GB; OMP=16; `-nb gpu -pme gpu -bonded gpu` |

## Stage outcomes

| Stage | Status | Wall time (UTC) | Performance |
| --- | --- | --- | --- |
| minimization | complete | 15:05:34 → 15:06:26 | — |
| equilibration (eq1–eq6, ~1.875 ns) | complete | 15:06:26 → 15:21:15 | ~127–241 ns/day (eq segments) |
| normal_1ns | complete | 15:53:42 → 16:00:05 | **235.329 ns/day** |
| distance_monitor_1ns | complete | 16:00:05 → 16:13:22 | **110.820 ns/day** |
| distance_metad_1ns | complete | 16:13:22 → 16:27:28 | **104.332 ns/day** |

All five stages recorded `complete` under `.agent/state/*.json`.

## Key artifacts (callback contract)

| Role | Path |
| --- | --- |
| Minimized structure | `.../stages/minimization/em.gro` |
| Equilibrated seed | `.../stages/equilibration/eq6.gro` |
| Unbiased 1 ns trajectory | `.../stages/normal_1ns/normal_1ns.xtc` |
| Distance monitor COLVAR | `.../stages/distance_monitor_1ns/colvar_distance` |
| Metadynamics HILLS | `.../stages/distance_metad_1ns/HILLS` |
| Biased COLVAR | `.../stages/distance_metad_1ns/COLVAR_biased.dat` |
| Biased 1 ns trajectory / last frame | `.../stages/distance_metad_1ns/distance_metad_1ns.xtc` / `.gro` |
| Agent state freeze | `.../.agent/state/` |

Run size ≈ **756 MB**.

## Allowed / forbidden claims

**Allowed**
- Stage4 Allo-MD backend is wired and operator-executable on this site.
- A shortened GLP1 distance pipeline (min → eq → 1 ns normal → 1 ns monitor → 1 ns metad) completed successfully.
- Open-like / CV-sampled frames exist under the run directory for Stage5 handoff experiments.

**Forbidden**
- “Paper-scale / frozen historical 100+50+50 ns protocol reproduced.”
- “Cryptic pocket mechanism experimentally confirmed.”
- “Full MultiAgent autonomous discovery finished.”

## Relation to MultiAgent maturity

- Tool `ai_prior_metadynamics`: maturity remains **`scripted`** with **demo evidence**.
- Stage `physics_sampling`: product status **`demo_completed`** (1 ns). Formal `distance-simulation-only` (~200 ns) is optional and not required for current agent-loop narrative.

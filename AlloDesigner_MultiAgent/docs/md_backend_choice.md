# Stage4 MD backend choice

## Decision

**Primary backend: collaborator `Allo-MD/` (`agentctl`).**

Generic public MD agents (MDCrow, DynaMate-style) do not replace Allo-MD for GLP1 Stage4 (frozen membrane system, SPIB distance DAT, SASA profiles, MDpocket DAG).

## Current maturity (2026-08-14)

| Layer | Status |
| --- | --- |
| MultiAgent ↔ Allo-MD job pack / site wiring | Done |
| Local **1 ns demo** (`distance-simulation-1ns-demo`) | **Completed** — see [stage4_demo_glp1r_1ns.md](stage4_demo_glp1r_1ns.md) |
| Formal frozen ~200 ns `distance-simulation-only` | Optional; **not required** for current agent-loop narrative |

## Demo performance (H100)

- normal_1ns: **235.3 ns/day**
- distance_monitor_1ns: **110.8 ns/day**
- distance_metad_1ns: **104.3 ns/day**

## Claim boundary

Mark Stage4 as **`partial / demo`**. Do not claim paper-scale historical protocol reproduction unless the full frozen profile is executed and audited.

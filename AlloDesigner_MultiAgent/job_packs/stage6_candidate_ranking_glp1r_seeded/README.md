# Stage6 job pack — GLP1R candidate ranking (seeded)

**Maturity**: `partial/seeded`  
**Request id**: `stage6_glp1r_ranking_seeded_v1`

This pack is the MultiAgent **external job sheet** for Stage6 virtual screening.
It consumes Stage5 `pocket_01` + Stage4/5 receptor frame `t0250`, and accepts
**Vina** and/or **Glide** returns through a fixed schema.

## Layout

```text
request.yaml / job_sheet.json / protocol_version.json
inputs/          receptor, pocket_definition, library_seed.smi, Stage5 handoff
external/vina/   vina.conf + run helper
external/glide/  grid box + operator README
scripts/         ingest_return.py, make_seeded_return_example.py
```

## Quick start (interface demo, no docking binary required)

```bash
cd /home/ubuntu/file2/jrf/AlloDesigner/AlloDesigner_MultiAgent/job_packs/stage6_candidate_ranking_glp1r_seeded
python3 scripts/make_seeded_return_example.py
python3 scripts/ingest_return.py --pack-dir . \
  --return-dir ../../runs/stage6_glp1r_ranking_seeded_demo/returns/vina_seeded_example \
  --promote-run-dir ../../runs/stage6_glp1r_ranking_seeded_demo
python3 scripts/ingest_return.py --pack-dir . \
  --return-dir ../../runs/stage6_glp1r_ranking_seeded_demo/returns/glide_seeded_example \
  --promote-run-dir ../../runs/stage6_glp1r_ranking_seeded_demo
```

## Real external docking

1. Follow `external/vina/README.md` and/or `external/glide/README.md`.
2. Emit `return.json` + `ranked_candidates.csv` (+ poses).
3. Ingest with `scripts/ingest_return.py`.
4. Update `human_freezes.library_scope` before claiming anything beyond the seed library.

## Claim boundary

| Allowed | Forbidden |
|---|---|
| Job pack + return schema ready | Experimental potency |
| Seeded interface demo completed | Full-library VS completed |
| Real Vina/Glide scores **if** returned and ingested | Paper cascade reproduced without audit |

# Reasoning narrative

- For target GLP1R on track retrospective_blind, pursue cryptic allosteric pocket discovery via the frozen six-stage decomposition; tool choices and replay/reuse adapt to available artifacts and budget (max_md_ns=1.0, prefer_recompute=False).
- [boundary] Human-approved boundary must precede any scientific tool use.
- [residue_prior] Retrospective artifacts exist; replay residue prior to keep blind demo auditable without re-running PocketMiner.
- [ensemble_enrichment] Reuse retrospective ensemble_enrichment; full AF-ClaSeq recompute out of demo budget.
-   uncertainty: Stage3 not recomputed; uncertainty carried to pocket evaluation.
- [physics_sampling] 1 ns Allo-MD demo artifact present and budget<=1ns; reuse rather than relaunch MD (not paper 200ns).
- [pocket_evaluation] Combine historical_replay pocket_01 handoff with Stage4-frame fpocket consistency check when frames exist.
- [candidate_ranking] Stage6 is external: emit Vina/Glide job pack and ingest returns; seeded returns remain partial/seeded.

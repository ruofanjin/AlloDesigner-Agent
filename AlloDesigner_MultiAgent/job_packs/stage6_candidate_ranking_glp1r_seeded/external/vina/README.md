# External runner — AutoDock Vina

## Inputs (from this job pack)

| File | Role |
|---|---|
| `../../inputs/receptor.pdb` | Protein receptor (Stage5 t0250) |
| `../../inputs/library_seed.smi` | Ligand SMILES (seed demo) |
| `../../inputs/pocket_definition.json` | Box + pocket_01 residues |
| `vina.conf` | Search box (copied from pocket box) |

## Operator steps

1. Prepare receptor PDBQT (e.g. Meeko / ADFR `prepare_receptor` / OpenBabel).
2. Enumerate ligands from `library_seed.smi` → PDBQT.
3. Run Vina with `vina.conf` (or equivalent CLI flags).
4. Collect poses under `poses/` and build `ranked_candidates.csv`.
5. Fill `return.json` using `../../../../schemas/stage6_vs_return.schema.json`.
6. Ingest:

```bash
python3 ../../scripts/ingest_return.py \
  --pack-dir ../.. \
  --return-dir /path/to/returns/vina_<site> \
  --promote-run-dir /home/ubuntu/file2/jrf/AlloDesigner/AlloDesigner_MultiAgent/runs/stage6_glp1r_ranking_seeded_demo
```

## Claim boundary

- Allowed: Vina docking scores on the declared library_scope.
- Forbidden: experimental potency; full-library VS; silent upgrade to paper cascade complete.

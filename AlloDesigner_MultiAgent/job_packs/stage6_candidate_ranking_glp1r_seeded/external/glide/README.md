# External runner — Schrödinger Glide

## Inputs

| File | Role |
|---|---|
| `../../inputs/receptor.pdb` | Import as receptor |
| `../../inputs/library_seed.smi` | LigPrep input (seed) |
| `../../inputs/pocket_definition.json` | Grid center / inner box |
| `grid_box.txt` | Center/size for Grid Generation |

## Operator steps (site-specific Maestro / CLI)

1. Import receptor; optionally restrain / preprocess per site SOP.
2. Generate Glide grid centered on pocket_01 box (`grid_box.txt`).
3. LigPrep `library_seed.smi` (or replace with approved library after updating `library_scope`).
4. Dock Glide SP (default freeze) or XP if human-approved.
5. Export poses + CSV scores.
6. Map to `ranked_candidates.csv` columns (see return template).
7. Write `return.json` with `"engine": "glide"`.
8. Ingest via `scripts/ingest_return.py`.

## Claim boundary

- Allowed: Glide docking scores under declared precision and library_scope.
- Forbidden: experimental IC50/EC50 claims; claiming paper KarmaDock/Glide/Vina cascade complete unless that cascade was actually run and audited.

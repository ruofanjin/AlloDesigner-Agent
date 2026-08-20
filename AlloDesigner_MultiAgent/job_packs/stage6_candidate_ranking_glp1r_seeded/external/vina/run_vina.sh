#!/usr/bin/env bash
# External-site helper. Requires: vina, and pre-prepared *.pdbqt files.
set -Eeuo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
work="${1:-"$here/work"}"
mkdir -p "$work/poses" "$work/logs"
cp "$here/vina.conf" "$work/vina.conf"
if [[ ! -f "$work/receptor.pdbqt" ]]; then
  echo "Place prepared receptor.pdbqt in $work (from ../../inputs/receptor.pdb)" >&2
  exit 2
fi
if [[ ! -d "$work/ligands_pdbqt" ]]; then
  echo "Place ligand PDBQTs in $work/ligands_pdbqt/*.pdbqt" >&2
  exit 2
fi
command -v vina >/dev/null || { echo "vina not on PATH" >&2; exit 3; }
shopt -s nullglob
for lig in "$work"/ligands_pdbqt/*.pdbqt; do
  id="$(basename "$lig" .pdbqt)"
  vina --config "$work/vina.conf" --receptor "$work/receptor.pdbqt" --ligand "$lig" \
    --out "$work/poses/${id}_out.pdbqt" >"$work/logs/${id}.log" 2>&1 || true
done
echo "Done. Parse logs into ranked_candidates.csv + return.json, then ingest_return.py"

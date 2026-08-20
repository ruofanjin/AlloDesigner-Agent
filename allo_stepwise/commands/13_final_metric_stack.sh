#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
RUNNER="${ROOT}/scripts/run_stepwise_allo.py"

# final-prediction and final-control are independent evaluation branches. This
# convenience wrapper runs them serially; a scheduler may submit one scope per job.
for SCOPE in final-prediction final-control; do
  "${PYTHON_BIN}" "${RUNNER}" copy-pdbs --scope "${SCOPE}"
  if [[ "${RUN_FPOCKET:-0}" == "1" ]]; then
    "${PYTHON_BIN}" "${RUNNER}" run-fpocket --scope "${SCOPE}"
  else
    echo "Dry-run fpocket commands for ${SCOPE}. Set RUN_FPOCKET=1 to execute fpocket."
    "${PYTHON_BIN}" "${RUNNER}" run-fpocket --scope "${SCOPE}" --dry-run
  fi
  "${PYTHON_BIN}" "${RUNNER}" pocket-centers --scope "${SCOPE}"
  "${PYTHON_BIN}" "${RUNNER}" cluster-residues --scope "${SCOPE}"
  "${PYTHON_BIN}" "${RUNNER}" cluster-pocket-distance --scope "${SCOPE}"
  "${PYTHON_BIN}" "${RUNNER}" average-distances --scope "${SCOPE}"
done

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
RUNNER="${ROOT}/scripts/run_stepwise_allo.py"

# Run after all M-fold sampling ColabFold predictions exist under workdir/run.
# Sampling evaluations are conceptually independent, but this wrapper traverses
# sampling_1..37 and performs the final merge. Do not run duplicate wrappers.
"${PYTHON_BIN}" "${RUNNER}" copy-pdbs --scope sampling

if [[ "${RUN_FPOCKET:-0}" == "1" ]]; then
  "${PYTHON_BIN}" "${RUNNER}" run-fpocket --scope sampling
else
  echo "Dry-run fpocket commands. Set RUN_FPOCKET=1 to execute fpocket."
  "${PYTHON_BIN}" "${RUNNER}" run-fpocket --scope sampling --dry-run
fi

"${PYTHON_BIN}" "${RUNNER}" pocket-centers --scope sampling
"${PYTHON_BIN}" "${RUNNER}" cluster-residues --scope sampling
"${PYTHON_BIN}" "${RUNNER}" cluster-pocket-distance --scope sampling
"${PYTHON_BIN}" "${RUNNER}" average-distances --scope sampling
"${PYTHON_BIN}" "${RUNNER}" combine-sampling-metrics

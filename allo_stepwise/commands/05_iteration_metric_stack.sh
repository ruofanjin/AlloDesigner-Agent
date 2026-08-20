#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
RUNNER="${ROOT}/scripts/run_stepwise_allo.py"
ITERATION="${1:-1}"

# Run after all ColabFold predictions for Iteration_${ITERATION}/shuffle_* exist.
# Shuffle evaluations are conceptually independent, but this wrapper traverses
# all ten shuffles. Do not launch duplicate copies for the same iteration.
"${PYTHON_BIN}" "${RUNNER}" copy-pdbs --scope iteration --iteration "${ITERATION}"

if [[ "${RUN_FPOCKET:-0}" == "1" ]]; then
  "${PYTHON_BIN}" "${RUNNER}" run-fpocket --scope iteration --iteration "${ITERATION}"
else
  echo "Dry-run fpocket commands. Set RUN_FPOCKET=1 to execute fpocket."
  "${PYTHON_BIN}" "${RUNNER}" run-fpocket --scope iteration --iteration "${ITERATION}" --dry-run
fi

"${PYTHON_BIN}" "${RUNNER}" pocket-centers --scope iteration --iteration "${ITERATION}"
"${PYTHON_BIN}" "${RUNNER}" cluster-residues --scope iteration --iteration "${ITERATION}"
"${PYTHON_BIN}" "${RUNNER}" cluster-pocket-distance --scope iteration --iteration "${ITERATION}"
"${PYTHON_BIN}" "${RUNNER}" average-distances --scope iteration --iteration "${ITERATION}"

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
OUT="${ROOT}/generated/final_colabfold_commands.sh"

# Parallel units: final prediction and control_prediction use separate folders
# and their two generated ColabFold commands may run at the same time.
"${PYTHON_BIN}" "${ROOT}/scripts/run_stepwise_allo.py" \
  write-colabfold-commands --stage final --expected --output "${OUT}"

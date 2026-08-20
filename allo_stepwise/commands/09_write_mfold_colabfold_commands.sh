#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
OUT="${ROOT}/generated/mfold_colabfold_commands.sh"

# Parallel units: 02_init_random_split and sampling_1..37 use separate output
# directories. Their 38 generated ColabFold commands may be scheduled independently.
"${PYTHON_BIN}" "${ROOT}/scripts/run_stepwise_allo.py" \
  write-colabfold-commands --stage mfold --expected --output "${OUT}"

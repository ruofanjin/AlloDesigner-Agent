#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

ARGS=(write-colabfold-commands --stage iteration --expected)
if [[ -n "${1:-}" ]]; then
  ARGS+=(--iteration "$1")
  OUT="${ROOT}/generated/iteration_${1}_colabfold_commands.sh"
else
  OUT="${ROOT}/generated/iteration_colabfold_commands.sh"
fi
ARGS+=(--output "${OUT}")

# Parallel unit: each generated shuffle command has a separate input/output
# directory and may be submitted independently. Never submit the same shuffle
# directory twice at the same time.
"${PYTHON_BIN}" "${ROOT}/scripts/run_stepwise_allo.py" "${ARGS[@]}"

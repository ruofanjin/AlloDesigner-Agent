#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

ARGS=(generate-iteration-msas --iteration "${1:-1}")
if [[ "${OVERWRITE:-0}" == "1" ]]; then
  ARGS+=(--overwrite)
fi

# Iteration 1 consumes the coverage-filtered MSA prepared by
# 02_prepare_iteration_input.sh. Later iterations consume the previous
# combined_filtered_iteration_N.a3m. Keep this generation step serial: the
# ten shuffles share one deterministic RNG stream needed for historical parity.
"${PYTHON_BIN}" "${ROOT}/scripts/run_stepwise_allo.py" "${ARGS[@]}"

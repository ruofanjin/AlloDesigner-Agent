#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

ARGS=(generate-mfold-msas)
if [[ "${OVERWRITE:-0}" == "1" ]]; then
  ARGS+=(--overwrite)
fi
# Keep deterministic M-fold splitting serial. Parallelism begins with the
# generated ColabFold commands in the next stage.
"${PYTHON_BIN}" "${ROOT}/scripts/run_stepwise_allo.py" "${ARGS[@]}"

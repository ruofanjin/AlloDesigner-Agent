#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

RUNNER="${ROOT}/scripts/run_stepwise_allo.py"
"${PYTHON_BIN}" "${RUNNER}" audit-paths
"${PYTHON_BIN}" "${RUNNER}" plan

if [[ "${RUN_STEP3_AUDIT:-0}" == "1" ]]; then
  "${PYTHON_BIN}" "${RUNNER}" step3-audit
else
  echo "Step 3 full evidence audit skipped; set RUN_STEP3_AUDIT=1 after populating evidence/step3_historical/."
fi

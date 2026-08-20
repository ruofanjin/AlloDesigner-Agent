#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

# Requires completed metrics for Iterations 1-5 only. After Iteration 5, the
# M-fold branch may start while the optional Iteration 6-7 branch continues.
"${PYTHON_BIN}" "${ROOT}/scripts/run_stepwise_allo.py" combine-iterations

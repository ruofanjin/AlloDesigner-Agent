#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

# Serial barrier: requires metrics from all ten shuffles in this iteration and
# produces the only default input for the next iteration.
"${PYTHON_BIN}" "${ROOT}/scripts/run_stepwise_allo.py" \
  select-iteration-msa --iteration "${1:-1}"

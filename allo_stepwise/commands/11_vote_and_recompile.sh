#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
RUNNER="${ROOT}/scripts/run_stepwise_allo.py"

# Serial dependency: recompile consumes the voting outputs produced immediately
# before it, so these two commands must retain this order.
"${PYTHON_BIN}" "${RUNNER}" sequence-voting
"${PYTHON_BIN}" "${RUNNER}" recompile

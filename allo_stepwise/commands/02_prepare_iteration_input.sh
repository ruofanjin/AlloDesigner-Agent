#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

# One-time prerequisite for the iteration loop. Do not run concurrently with
# iteration MSA generation because both use the same iteration input tree.
"${PYTHON_BIN}" "${ROOT}/scripts/run_stepwise_allo.py" prepare-iteration-input

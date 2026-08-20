#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

# Read-only provenance/schema audit. It can run alongside environment review,
# but it never runs DeepAllo, PLB, fpocket, clustering, or historical scripts.
"${PYTHON_BIN}" "${ROOT}/scripts/run_stepwise_allo.py" step3-audit

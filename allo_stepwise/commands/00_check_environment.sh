#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
COLABFOLD_BIN="${COLABFOLD_BIN:-colabfold_batch}"
FPOCKET_BIN="${FPOCKET_BIN:-fpocket}"
STRICT=1
if [[ "${1:-}" == "--allow-missing-external" ]]; then
  STRICT=0
elif [[ -n "${1:-}" ]]; then
  echo "Usage: $0 [--allow-missing-external]" >&2
  exit 2
fi

failures=0

check_executable() {
  local label="$1"
  local executable="$2"
  if [[ "${executable}" == */* ]]; then
    if [[ -x "${executable}" ]]; then
      echo "OK   ${label}: ${executable}"
    else
      echo "MISS ${label}: ${executable}"
      failures=$((failures + 1))
    fi
  elif command -v "${executable}" >/dev/null 2>&1; then
    echo "OK   ${label}: $(command -v "${executable}")"
  else
    echo "MISS ${label}: ${executable}"
    failures=$((failures + 1))
  fi
}

check_sha256() {
  local relative_path="$1"
  local expected="$2"
  local path="${ROOT}/${relative_path}"
  if [[ ! -f "${path}" ]]; then
    echo "MISS input: ${relative_path}"
    failures=$((failures + 1))
    return
  fi
  local actual
  actual="$(sha256sum "${path}" | awk '{print $1}')"
  if [[ "${actual}" == "${expected}" ]]; then
    echo "OK   SHA256 ${relative_path}"
  else
    echo "FAIL SHA256 ${relative_path}: ${actual}"
    failures=$((failures + 1))
  fi
}

echo "Bundle root: ${ROOT}"
check_executable "Python" "${PYTHON_BIN}"
if [[ ${failures} -eq 0 ]]; then
  "${PYTHON_BIN}" --version
  for module in numpy pandas Bio yaml sklearn matplotlib scipy; do
    if "${PYTHON_BIN}" -c "import ${module}" >/dev/null 2>&1; then
      echo "OK   Python import: ${module}"
    else
      echo "MISS Python import: ${module}"
      failures=$((failures + 1))
    fi
  done
fi

check_executable "ColabFold" "${COLABFOLD_BIN}"
check_executable "fpocket" "${FPOCKET_BIN}"

check_sha256 "inputs/6x18_chianR_R.a3m" "27deb4e6de2eb2311912a29918af7d88043096d603edd589f662fda5f4b8028a"
check_sha256 "inputs/6x18_MODEL_0.pdb" "dd4ad9e7d23dcdb38fdf790157c2f522e20e00fb7baf35eee228fb7463e0c999"
check_sha256 "inputs/glp1_historical_holo_cluster_mapped_residues.csv" "0213fabe2b7eb965b4756ab8f0278bc76164e3458c20ede97028066030305354"
check_sha256 "inputs/glp1-deepallo-score-residue_probabilities_top_7.csv" "c4d5cdedb3ccd42ec7737b987500329d4141a9a6a00b1fedf707e00fb3e6edc0"
check_sha256 "inputs/glp1-plb-score-residue_probabilities_top_7.csv" "6f3fb69adc352e99cbc09b6b85525141e78fc31779728314658ffbb79568d67a"

if [[ ${failures} -eq 0 || ${STRICT} -eq 0 ]]; then
  "${PYTHON_BIN}" "${ROOT}/scripts/run_stepwise_allo.py" audit-paths || failures=$((failures + 1))
  "${PYTHON_BIN}" "${ROOT}/scripts/run_stepwise_allo.py" plan || failures=$((failures + 1))
fi

if [[ ${failures} -gt 0 ]]; then
  if [[ ${STRICT} -eq 1 ]]; then
    echo "Preflight failed with ${failures} missing or invalid requirements." >&2
    exit 1
  fi
  echo "Preflight completed with ${failures} missing external/runtime requirements (allowed for audit only)."
else
  echo "Preflight OK."
fi

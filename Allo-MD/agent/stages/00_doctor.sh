#!/usr/bin/env bash
set -Eeuo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/common.sh
source "$script_dir/lib/common.sh"

: "${AGENT_STRICT:=0}"
: "${AGENT_REQUIRE_MDPOCKET:=0}"
: "${AGENT_REQUIRE_GPU_RUNTIME:=auto}"
failures=0
warnings=0

ok() { printf 'OK: %s\n' "$*"; }
info() { printf 'INFO: %s\n' "$*"; }
warn() { printf 'WARN: %s\n' "$*" >&2; warnings=$((warnings + 1)); }
fail() { printf 'FAIL: %s\n' "$*" >&2; failures=$((failures + 1)); }

if command -v "$PYTHON_BIN" >/dev/null 2>&1 \
   && "$PYTHON_BIN" -c 'import sys; raise SystemExit(sys.version_info < (3, 8))'; then
    ok "Python 3.8+ found: $($PYTHON_BIN --version 2>&1)"
else
    fail "PYTHON_BIN must resolve to Python 3.8 or newer: $PYTHON_BIN"
fi

case "$GMX_DEVICE_MODE" in
    auto|cpu|gpu) ok "device mode is valid: $GMX_DEVICE_MODE" ;;
    *) fail "GMX_DEVICE_MODE must be auto, cpu, or gpu" ;;
esac
case "$AGENT_REQUIRE_GPU_RUNTIME" in
    auto|0|1) ;;
    *) fail "AGENT_REQUIRE_GPU_RUNTIME must be auto, 0, or 1" ;;
esac
case "$RESTRAINT_REFERENCE_MODE" in
    historical_previous|charmm_gui_initial) ok "restraint-reference mode is valid: $RESTRAINT_REFERENCE_MODE" ;;
    *) fail "RESTRAINT_REFERENCE_MODE must be historical_previous or charmm_gui_initial" ;;
esac
case "$GMX_MDRUN_EXTRA_ARGS" in
    ""|-v) ok "mdrun extra arguments cannot change protocol length" ;;
    *) fail "GMX_MDRUN_EXTRA_ARGS is restricted to an empty value or -v" ;;
esac
if [[ -n "$GMX_MDRUN_MAXH" ]] \
   && { [[ ! "$GMX_MDRUN_MAXH" =~ ^[0-9]+([.][0-9]+)?$ ]] \
        || ! awk -v value="$GMX_MDRUN_MAXH" 'BEGIN {exit !(value>0)}'; }; then
    fail "GMX_MDRUN_MAXH must be a positive number of hours"
elif [[ -n "$GMX_MDRUN_MAXH" ]]; then
    ok "controlled mdrun walltime checkpoint: ${GMX_MDRUN_MAXH} h"
fi

if [[ -n "${GMX_MAXCONSTRWARN:-}" ]]; then
    fail "GMX_MAXCONSTRWARN is inherited ($GMX_MAXCONSTRWARN); remove it rather than suppressing constraint warnings"
else
    ok "no GMX_MAXCONSTRWARN bypass is inherited"
fi
if [[ -n "${PLUMED_KERNEL:-}" ]]; then
    fail "PLUMED_KERNEL is set in a shared-patch workflow: $PLUMED_KERNEL"
else
    ok "no runtime PLUMED_KERNEL override is inherited"
fi

if command -v "$GMX_BIN" >/dev/null 2>&1; then
    gmx_path="$(command -v "$GMX_BIN")"
    gmx_version="$($GMX_BIN --version 2>&1)"
    grep -q 'GROMACS version:.*2024\.3' <<< "$gmx_version" && ok "GROMACS 2024.3 found at $gmx_path" || fail "Expected GROMACS 2024.3"
    grep -q 'Precision:.*mixed' <<< "$gmx_version" && ok "mixed precision build detected" || fail "Expected mixed precision GROMACS"
    grep -q 'MPI library:.*MPI' <<< "$gmx_version" && ok "external MPI build detected" || fail "GROMACS external MPI build not detected"
    grep -q 'MPI library version:.*Open MPI.*5\.0\.1' <<< "$gmx_version" \
        && ok "GROMACS uses Open MPI 5.0.1" \
        || fail "Expected GROMACS linked to Open MPI 5.0.1"
    grep -q 'OpenMP support:.*enabled' <<< "$gmx_version" && ok "OpenMP enabled" || fail "OpenMP is not enabled"
    mdrun_help="$($GMX_BIN mdrun -h 2>&1 || true)"
    if grep -q -- '-plumed' <<< "$mdrun_help"; then
        ok "GROMACS mdrun exposes -plumed"
    else
        fail "GROMACS is not patched with PLUMED"
    fi
    sasa_help="$($GMX_BIN sasa -h 2>&1 || true)"
    if grep -q -- '-surface' <<< "$sasa_help" && grep -q -- '-output' <<< "$sasa_help"; then
        ok "GROMACS exposes surface/output selections for standardized SASA analysis"
    else
        fail "GROMACS sasa lacks the required -surface/-output interface"
    fi
    if ldd "$gmx_path" 2>&1 | grep -q 'not found'; then
        fail "gmx_mpi has unresolved shared libraries"
        ldd "$gmx_path" 2>&1 | grep 'not found' >&2 || true
    else
        ok "gmx_mpi shared libraries resolve"
    fi
else
    fail "Cannot find $GMX_BIN; source the installed GMXRC through GMX_ENV_SCRIPT"
fi

if command -v "$PLUMED_BIN" >/dev/null 2>&1; then
    plumed_version="$($PLUMED_BIN info --long-version 2>&1 || true)"
    [[ "$plumed_version" == *"2.9.3"* ]] && ok "PLUMED 2.9.3 detected" || fail "Expected PLUMED 2.9.3, got: $plumed_version"
    "$PLUMED_BIN" config module sasa >/dev/null 2>&1 && ok "PLUMED SASA module enabled" || fail "PLUMED SASA module is unavailable"
    "$PLUMED_BIN" gentemplate --action SASA_HASEL >/dev/null 2>&1 && ok "SASA_HASEL action registered" || fail "SASA_HASEL action is unavailable"
    if "$PLUMED_BIN" --has-mpi >/dev/null 2>&1; then
        ok "PLUMED reports MPI support"
    elif (( MPI_RANKS > 1 )); then
        fail "PLUMED lacks MPI support but MPI_RANKS=$MPI_RANKS"
    else
        info "PLUMED does not report MPI support; permitted only because MPI_RANKS=1"
    fi
else
    fail "Cannot find $PLUMED_BIN"
fi

if [[ "$GMX_DEVICE_MODE" == "gpu" ]]; then
    if [[ ${gmx_version:-} == *"GPU support:"* ]] \
       && grep -q 'GPU support:.*CUDA' <<< "$gmx_version"; then
        ok "GROMACS CUDA backend is enabled"
    else
        fail "GPU mode requested but GROMACS does not report CUDA support"
    fi
    if [[ "$AGENT_REQUIRE_GPU_RUNTIME" == "0" ]]; then
        info "No pending MD stage requires a live GPU; CUDA build validation retained for analysis-only resume"
    else
        command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1 && ok "NVIDIA GPU is visible" || fail "GPU mode requested but nvidia-smi cannot see a GPU"
    fi
elif command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1; then
    ok "NVIDIA GPU visible; task placement remains $GMX_DEVICE_MODE"
else
    info "No NVIDIA GPU detected; CPU/auto operation remains possible"
fi

case "$GMX_LAUNCHER" in
    direct)
        (( MPI_RANKS == 1 )) && ok "direct launcher is consistent with one MPI rank" \
            || fail "direct launcher cannot realize MPI_RANKS=$MPI_RANKS; use mpirun/srun or set one rank"
        ;;
    mpirun)
        command -v "$MPIEXEC_BIN" >/dev/null 2>&1 && ok "MPI launcher found: $MPIEXEC_BIN" || fail "Missing MPI launcher: $MPIEXEC_BIN"
        ;;
    srun)
        command -v srun >/dev/null 2>&1 && ok "Slurm launcher found: srun" || fail "GMX_LAUNCHER=srun but srun is unavailable"
        ;;
    *)
        fail "GMX_LAUNCHER must be direct, mpirun, or srun"
        ;;
esac

if command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    ok "Python found: $(command -v "$PYTHON_BIN")"
    "$PYTHON_BIN" "$AGENT_BUNDLE_ROOT/tools/validate_inputs.py" --bundle-root "$AGENT_BUNDLE_ROOT" || fail "Frozen scientific inputs failed validation"
else
    fail "Cannot find $PYTHON_BIN"
fi

if [[ "$AGENT_REQUIRE_MDPOCKET" == "1" ]]; then
    if [[ "$MDPOCKET_BIN" != /* ]]; then
        fail "Full MDpocket validation requires an absolute MDPOCKET_BIN from install/install_fpocket.sh"
    elif [[ -x "$MDPOCKET_BIN" ]]; then
        mdpocket_path="$MDPOCKET_BIN"
        ok "MDpocket found at absolute path: $mdpocket_path"
        mdpocket_help="$($MDPOCKET_BIN --help 2>&1 || true)"
        grep -q -- '--pdb_list' <<< "$mdpocket_help" \
            && grep -q -- '--selected_pocket' <<< "$mdpocket_help" \
            && ok "MDpocket exposes the required PDB-list and selected-pocket interfaces" \
            || fail "MDpocket help lacks --pdb_list or --selected_pocket"
        expected_fpocket_provenance="Discngine/fpocket tag 4.2.3 commit 4bb0d8447f62fee77e2c3c29f54b5fcaf5e2c066 bundle-patch-sha256 6ed7a0e8280f10ae0d42c42d771b4a3083e7891d007898bc19f7148bb433481d"
        [[ "$MDPOCKET_PROVENANCE" == "$expected_fpocket_provenance" ]] \
            && ok "pinned MDpocket provenance recorded: $MDPOCKET_PROVENANCE" \
            || fail "Profile requires fpocket 4.2.3 pinned provenance from install/install_fpocket.sh"
        fpocket_prefix="$(cd -- "$(dirname -- "$mdpocket_path")/.." && pwd -P)"
        fpocket_buildinfo="$fpocket_prefix/share/fpocket/BUILDINFO.tsv"
        if [[ -s "$fpocket_buildinfo" ]]; then
            grep -Fqx $'repository\thttps://github.com/Discngine/fpocket.git' "$fpocket_buildinfo" \
                && grep -Fqx $'tag\t4.2.3' "$fpocket_buildinfo" \
                && grep -Fqx $'commit\t4bb0d8447f62fee77e2c3c29f54b5fcaf5e2c066' "$fpocket_buildinfo" \
                && grep -Fqx $'patch_name\tfpocket-4.2.3-mdparams-argv-allocation.patch' "$fpocket_buildinfo" \
                && grep -Fqx $'patch_sha256\t6ed7a0e8280f10ae0d42c42d771b4a3083e7891d007898bc19f7148bb433481d' "$fpocket_buildinfo" \
                && grep -Fqx $'patched_mdparams_sha256\te2bff1096c833083567fd626319161f2b6e06e7d7878dc9c073c77ba4ea1d8c8' "$fpocket_buildinfo" \
                && grep -Fqx $'functional_smoke\t10-PDB discovery DX and selected-pocket 42-column descriptors passed' "$fpocket_buildinfo" \
                && ok "fpocket BUILDINFO records the pinned source, patch, and functional smoke" \
                || fail "fpocket BUILDINFO source/patch/smoke does not match the deployment pin"
            recorded_mdpocket_sha="$(awk -F '\t' '$1=="mdpocket_sha256" {print $2; exit}' "$fpocket_buildinfo")"
            actual_mdpocket_sha="$(sha256sum "$mdpocket_path")"
            actual_mdpocket_sha="${actual_mdpocket_sha%% *}"
            [[ "$recorded_mdpocket_sha" =~ ^[0-9a-f]{64}$ && "$recorded_mdpocket_sha" == "$actual_mdpocket_sha" ]] \
                && ok "MDpocket binary matches its installer BUILDINFO SHA-256" \
                || fail "MDpocket binary hash does not match BUILDINFO"
        else
            fail "Missing installer BUILDINFO beside MDpocket: $fpocket_buildinfo"
        fi
    else
        fail "Profile requires MDpocket, but $MDPOCKET_BIN is unavailable"
    fi
elif command -v "$MDPOCKET_BIN" >/dev/null 2>&1; then
    ok "Optional MDpocket found"
else
    info "Optional MDpocket is not installed"
fi

visible_cpus="$(nproc 2>/dev/null || printf 'unknown')"
printf 'INFO: launcher=%s ranks=%s OMP=%s visible_cpus=%s device=%s\n' "$GMX_LAUNCHER" "$MPI_RANKS" "$OMP_THREADS" "$visible_cpus" "$GMX_DEVICE_MODE"
if [[ "$visible_cpus" =~ ^[0-9]+$ ]] && (( MPI_RANKS * OMP_THREADS > visible_cpus )); then
    fail "MPI_RANKS × OMP_THREADS exceeds nproc-visible CPUs"
fi

printf 'Doctor summary: failures=%d warnings=%d\n' "$failures" "$warnings"
if (( failures > 0 )); then
    exit 1
fi
if [[ "$AGENT_STRICT" == "1" ]] && (( warnings > 0 )); then
    exit 1
fi

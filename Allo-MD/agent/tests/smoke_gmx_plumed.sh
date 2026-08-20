#!/usr/bin/env bash
# Zero-step single-point smoke for GROMACS -> patched PLUMED -> SASA_HASEL.
# Default mode only prints a plan.  --execute writes a new, empty work dir.

set -Eeuo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly BUNDLE_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"

execute=0
mode="cpu"
launcher=""
mpi_ranks=""
site_config=""
work_dir="${GMX_SMOKE_WORK_DIR:-}"

usage() {
    cat <<'EOF'
Usage: tests/smoke_gmx_plumed.sh [options]

Default: print the zero-step integration plan and make no changes.

  --execute             Create the work directory and run the smoke
  --mode cpu|gpu        Explicit task mode (cpu)
  --launcher direct|mpirun|srun
                        Coupled mdrun launcher (direct)
  --mpi-ranks N         MPI ranks; direct requires 1 (1)
  --site-config PATH    Trusted site.env to source
  --work-dir PATH       New empty output directory (required with --execute)
  -h, --help            Show help
EOF
}

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
need_arg() { [[ $# -ge 2 && -n ${2:-} ]] || die "$1 requires a value"; }

while (($#)); do
    case "$1" in
        --execute) execute=1 ;;
        --plan|--dry-run) execute=0 ;;
        --mode) need_arg "$@"; mode="$2"; shift ;;
        --launcher) need_arg "$@"; launcher="$2"; shift ;;
        --mpi-ranks) need_arg "$@"; mpi_ranks="$2"; shift ;;
        --site-config) need_arg "$@"; site_config="$2"; shift ;;
        --work-dir) need_arg "$@"; work_dir="$2"; shift ;;
        -h|--help) usage; exit 0 ;;
        *) die "unknown option: $1" ;;
    esac
    shift
done

[[ $mode == cpu || $mode == gpu ]] || die "--mode must be cpu or gpu"

if [[ -n $site_config ]]; then
    site_config="$(realpath -m -- "$site_config")"
    [[ -r $site_config ]] || die "site config is not readable: $site_config"
    # Explicitly trusted deployment input.
    # shellcheck source=/dev/null
    source "$site_config"
fi
if [[ -n ${GMX_ENV_SCRIPT:-} ]]; then
    [[ -r $GMX_ENV_SCRIPT ]] || die "GMX_ENV_SCRIPT is not readable: $GMX_ENV_SCRIPT"
    # shellcheck source=/dev/null
    source "$GMX_ENV_SCRIPT"
fi
# Keep explicit site choices authoritative over defaults exported by env.sh.
if [[ -n $site_config ]]; then
    # shellcheck source=/dev/null
    source "$site_config"
fi

: "${GMX_BIN:=gmx_mpi}"
: "${PLUMED_BIN:=plumed}"
: "${PYTHON_BIN:=python3}"
: "${MPIEXEC_BIN:=mpirun}"
: "${OMP_THREADS:=1}"
launcher="${launcher:-${GMX_LAUNCHER:-direct}}"
mpi_ranks="${mpi_ranks:-${MPI_RANKS:-1}}"
[[ -z "${GMX_MAXCONSTRWARN:-}" ]] || die "refusing inherited GMX_MAXCONSTRWARN"
[[ -z "${PLUMED_KERNEL:-}" ]] || die "refusing PLUMED_KERNEL in the shared-patch smoke"
[[ $launcher == direct || $launcher == mpirun || $launcher == srun ]] ||
    die "--launcher must be direct, mpirun, or srun"
[[ $mpi_ranks =~ ^[1-9][0-9]*$ ]] || die "--mpi-ranks must be a positive integer"
[[ $OMP_THREADS =~ ^[1-9][0-9]*$ ]] || die "OMP_THREADS must be a positive integer"
[[ $launcher != direct || $mpi_ranks == 1 ]] || die "direct launcher requires --mpi-ranks 1"
export OMP_NUM_THREADS="$OMP_THREADS"

if [[ -z $work_dir ]]; then
    if ((execute)); then
        die "--work-dir is required with --execute"
    fi
    work_dir="/NEW/EMPTY/PATH/gmx-plumed-sasa-smoke"
else
    work_dir="$(realpath -m -- "$work_dir")"
fi
[[ $work_dir == /* && $work_dir != / ]] || die "work dir must be a non-root absolute path"
[[ $work_dir != *[$'\n\r\t ']* ]] || die "work dir must not contain whitespace"
[[ $work_dir != "$BUNDLE_ROOT" && $work_dir != "$BUNDLE_ROOT"/* ]] ||
    die "work dir must be outside the read-only deployment bundle: $BUNDLE_ROOT"

device_args=(-nb cpu -pme cpu -bonded cpu -update cpu)
if [[ $mode == gpu ]]; then
    device_args=(-nb gpu -pme gpu -bonded gpu -update cpu)
fi
mdrun_prefix=()
case "$launcher" in
    direct) mdrun_prefix=("$GMX_BIN" mdrun) ;;
    mpirun) mdrun_prefix=("$MPIEXEC_BIN" -np "$mpi_ranks" "$GMX_BIN" mdrun) ;;
    srun) mdrun_prefix=(srun --ntasks="$mpi_ranks" "$GMX_BIN" mdrun) ;;
esac

print_command() { printf '  '; printf '%q ' "$@"; printf '\n'; }
run_cmd() {
    print_command "$@"
    if ((execute)); then
        "$@"
    fi
}

printf 'GROMACS/PLUMED/SASA zero-step smoke: %s\n' "$([[ $execute == 1 ]] && printf EXECUTE || printf PLAN)"
printf '  work dir: %s\n  mode: %s\n  launcher: %s (%s rank(s), %s thread(s)/rank)\n  gmx: %s\n  plumed: %s\n' \
    "$work_dir" "$mode" "$launcher" "$mpi_ranks" "$OMP_THREADS" "$GMX_BIN" "$PLUMED_BIN"

if ((execute)); then
    command -v "$GMX_BIN" >/dev/null 2>&1 || die "cannot find $GMX_BIN"
    command -v "$PLUMED_BIN" >/dev/null 2>&1 || die "cannot find $PLUMED_BIN"
    command -v "$PYTHON_BIN" >/dev/null 2>&1 || die "cannot find $PYTHON_BIN"
    [[ $launcher != mpirun ]] || command -v "$MPIEXEC_BIN" >/dev/null 2>&1 || die "cannot find $MPIEXEC_BIN"
    [[ $launcher != srun ]] || command -v srun >/dev/null 2>&1 || die "cannot find srun"
    [[ ! -e $work_dir ]] || die "refusing existing smoke directory: $work_dir"
fi

run_cmd mkdir -p -- "$work_dir"
run_cmd cp -a -- "$BUNDLE_ROOT/inputs/system/." "$work_dir/"
run_cmd cp -p -- "$SCRIPT_DIR/fixtures/smoke.mdp" "$work_dir/smoke.mdp"
run_cmd cp -p -- "$SCRIPT_DIR/fixtures/plumed_sasa_smoke.dat" "$work_dir/plumed.dat"

if ((!execute)); then
    print_command "$GMX_BIN" grompp -f "$work_dir/smoke.mdp" \
        -c "$work_dir/step5_input.gro" -p "$work_dir/topol.top" \
        -r "$work_dir/step5_input.gro" -n "$work_dir/index.ndx" \
        -o "$work_dir/smoke.tpr"
    print_command "${mdrun_prefix[@]}" -s "$work_dir/smoke.tpr" \
        -deffnm "$work_dir/smoke" -plumed "$work_dir/plumed.dat" "${device_args[@]}"
    printf 'PLAN complete: no directory or external calculation was started.\n'
    exit 0
fi

(
    cd -- "$work_dir"
    "$GMX_BIN" grompp -f smoke.mdp -c step5_input.gro -p topol.top \
        -r step5_input.gro -n index.ndx -o smoke.tpr
    "${mdrun_prefix[@]}" -s smoke.tpr -deffnm smoke -plumed plumed.dat "${device_args[@]}"
)

[[ -s $work_dir/smoke.tpr ]] || die "smoke TPR was not created"
[[ -s $work_dir/smoke.log ]] || die "smoke log was not created"
grep -q 'Finished mdrun' "$work_dir/smoke.log" || die "GROMACS did not finish the zero-step run"
grep -q 'SASA_HASEL' "$work_dir/smoke.log" || die "PLUMED SASA_HASEL did not initialize"
[[ -s $work_dir/COLVAR_smoke ]] || die "SASA smoke COLVAR was not created"
"$PYTHON_BIN" - "$work_dir/COLVAR_smoke" <<'PY' || die "SASA smoke COLVAR has no finite data row"
import math
from pathlib import Path
import sys

rows = []
for raw in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if line and not line.startswith("#"):
        rows.append(line.split())
if not rows or len(rows[-1]) < 2:
    raise SystemExit(1)
try:
    values = [float(value) for value in rows[-1]]
except ValueError:
    raise SystemExit(1)
if not all(math.isfinite(value) for value in values):
    raise SystemExit(1)
PY

printf 'OK: coupled zero-step smoke passed; evidence retained at %s\n' "$work_dir"

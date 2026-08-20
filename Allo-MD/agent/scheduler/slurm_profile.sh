#!/usr/bin/env bash
# Render or submit a Slurm job for the packaged GPCR workflow.
# No job is submitted unless --execute is present.

set -Eeuo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly BUNDLE_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"

execute=0
mode="gpu"
profile="historical-distance-main"
run_id=""
work_root="${GMX_AGENT_WORK_ROOT:-${HOME:?HOME is not set}/gmx-agent-runs}"
prefix="${GMX_STACK_PREFIX:-${HOME:?HOME is not set}/opt/gmx-stack}"
env_script=""
site_config=""
launcher="direct"
partition=""
account=""
qos=""
walltime="24:00:00"
walltime_explicit=0
nodes=1
ntasks=1
cpus_per_task=8
gpus=1
memory=""
job_name="gmx-agent"
output=""
allow_long_md=0
ack_sasa_biasvalue=0
mdrun_maxh=""
extra_sbatch=()

usage() {
  cat <<'EOF'
Usage:
  scheduler/slurm_profile.sh [options]

Default behavior is a dry-run: print the sbatch command and complete job
script.  Only --execute submits it.  The compute job sources PREFIX/env.sh
directly and never relies on .bashrc aliases or interactive shell startup.

Workflow options:
  --execute                  Submit with sbatch (the only submission gate)
  --plan, --dry-run          Render only (default)
  --mode cpu|gpu             Agent execution mode (gpu; production requirement)
  --profile NAME             Packaged profile (historical-distance-main)
  --run-id ID                Stable run identifier (required with --execute)
  --work-root PATH           Agent run root ($HOME/gmx-agent-runs)
  --prefix PATH              Installed stack root ($HOME/opt/gmx-stack)
  --env-script PATH          Explicit generated env.sh (PREFIX/env.sh)
  --site-config PATH         Optional shell config sourced before overrides
  --launcher direct|srun|mpirun
                             Runtime launcher exported to the agent (direct)
  --allow-long-md            Open agentctl's independent long-stage gate
  --maxh-per-mdrun HOURS     Controlled GROMACS -maxh checkpoint interval;
                             endpoint checks prevent early completion
  --ack-sasa-biasvalue       Acknowledge preserved METAD+BIASVALUE SASA setup

Slurm resources:
  --partition NAME           Partition/queue
  --account NAME             Account
  --qos NAME                 QoS
  --time D-HH:MM:SS          Wall time; required explicitly for long execution
                             (dry-run illustration: 24:00:00)
  --nodes N                  Nodes (1)
  --ntasks N                 MPI ranks (1; recommended for this workflow)
  --cpus-per-task N          OpenMP threads per rank (8)
  --gpus N                   GPUs per node in GPU mode (1)
  --mem SIZE                 Memory, e.g. 32G
  --job-name NAME            Slurm job name (gmx-agent)
  --output PATH              Slurm output pattern (WORK_ROOT/slurm-%x-%j.out)
  --sbatch-arg ARG           Extra single sbatch argument; repeatable
  -h, --help                 Show this help

The submitted job performs `agentctl prepare`, then `agentctl run --execute`.
The wrapper itself does not install CUDA/GROMACS or create a site configuration.
EOF
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

warn() {
  printf 'WARNING: %s\n' "$*" >&2
}

need_arg() {
  [[ $# -ge 2 && -n ${2:-} ]] || die "$1 requires a value"
}

while (($#)); do
  case "$1" in
    --execute) execute=1 ;;
    --plan|--dry-run) execute=0 ;;
    --mode) need_arg "$@"; mode="$2"; shift ;;
    --profile) need_arg "$@"; profile="$2"; shift ;;
    --run-id) need_arg "$@"; run_id="$2"; shift ;;
    --work-root) need_arg "$@"; work_root="$2"; shift ;;
    --prefix) need_arg "$@"; prefix="$2"; shift ;;
    --env-script) need_arg "$@"; env_script="$2"; shift ;;
    --site-config) need_arg "$@"; site_config="$2"; shift ;;
    --launcher) need_arg "$@"; launcher="$2"; shift ;;
    --partition) need_arg "$@"; partition="$2"; shift ;;
    --account) need_arg "$@"; account="$2"; shift ;;
    --qos) need_arg "$@"; qos="$2"; shift ;;
    --time) need_arg "$@"; walltime="$2"; walltime_explicit=1; shift ;;
    --nodes) need_arg "$@"; nodes="$2"; shift ;;
    --ntasks) need_arg "$@"; ntasks="$2"; shift ;;
    --cpus-per-task) need_arg "$@"; cpus_per_task="$2"; shift ;;
    --gpus) need_arg "$@"; gpus="$2"; shift ;;
    --mem) need_arg "$@"; memory="$2"; shift ;;
    --job-name) need_arg "$@"; job_name="$2"; shift ;;
    --output) need_arg "$@"; output="$2"; shift ;;
    --sbatch-arg) need_arg "$@"; extra_sbatch+=("$2"); shift ;;
    --allow-long-md) allow_long_md=1 ;;
    --maxh-per-mdrun) need_arg "$@"; mdrun_maxh="$2"; shift ;;
    --ack-sasa-biasvalue) ack_sasa_biasvalue=1 ;;
    -h|--help) usage; exit 0 ;;
    --)
      shift
      (($# == 0)) || die "unexpected positional arguments: $*"
      break
      ;;
    *) die "unknown option: $1 (use --help)" ;;
  esac
  shift
done

[[ $mode == cpu || $mode == gpu ]] || die "--mode must be cpu or gpu"
case "$profile" in
  validate-only|historical-distance-main|distance-simulation-only|distance-new-bias-100ns|historical-normal-controls|historical-sasa-site|historical-sasa-pocket|historical-sasa-pocket-100ns|historical-sasa-biased-main|standardized-sasa-site-10ns-full|standardized-sasa-pocket-10ns-full|standardized-sasa-pocket-100ns-full|standardized-sasa-biased-main|all-traceable)
    ;;
  *) die "invalid --profile: $profile (run agentctl list for packaged profiles)" ;;
esac
case "$launcher" in srun|mpirun|direct) ;; *) die "invalid --launcher: $launcher" ;; esac
for pair in "nodes:$nodes" "ntasks:$ntasks" "cpus-per-task:$cpus_per_task"; do
  label=${pair%%:*}; value=${pair#*:}
  [[ $value =~ ^[1-9][0-9]*$ ]] || die "--$label must be a positive integer"
done
[[ $gpus =~ ^[1-9][0-9]*$ ]] || die "--gpus must be a positive integer"
[[ $launcher != direct || $ntasks == 1 ]] ||
  die "--launcher direct requires --ntasks 1; use a validated MPI launcher for multiple ranks"
if [[ -n $mdrun_maxh ]]; then
  [[ $mdrun_maxh =~ ^[0-9]+([.][0-9]+)?$ ]] \
    && awk -v value="$mdrun_maxh" 'BEGIN {exit !(value>0)}' \
    || die "--maxh-per-mdrun must be a positive number of hours"
fi
[[ $walltime =~ ^([0-9]+-)?[0-9]{1,2}:[0-9]{2}:[0-9]{2}$ ]] ||
  die "--time must use unambiguous HH:MM:SS or D-HH:MM:SS"
[[ -z $run_id || $run_id =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$ ]] ||
  die "--run-id must start alphanumeric and use at most 128 letters, digits, dot, underscore, or hyphen"
[[ $job_name =~ ^[A-Za-z0-9._-]+$ ]] ||
  die "--job-name may contain only letters, digits, dot, underscore, and hyphen"
for argument in "${extra_sbatch[@]}"; do
  case "$argument" in
    --job-name|--job-name=*|-J|-J*|--nodes|--nodes=*|-N|-N*|\
    --ntasks|--ntasks=*|-n|-n*|--cpus-per-task|--cpus-per-task=*|-c|-c*|\
    --time|--time=*|-t|-t*|--output|--output=*|-o|-o*|\
    --partition|--partition=*|-p|-p*|--account|--account=*|-A|-A*|\
    --qos|--qos=*|--mem|--mem=*|--gpus|--gpus=*|--gpus-per-node|--gpus-per-node=*|\
    --array|--array=*|--wrap|--wrap=*)
      die "--sbatch-arg may not override a managed/concurrency option: $argument"
      ;;
  esac
done

absolute_path() {
  command -v realpath >/dev/null 2>&1 || die "realpath is required"
  realpath -m -- "$1"
}

prefix="$(absolute_path "$prefix")"
work_root="$(absolute_path "$work_root")"
env_script="$(absolute_path "${env_script:-$prefix/env.sh}")"
[[ -z $site_config ]] || site_config="$(absolute_path "$site_config")"
output="$(absolute_path "${output:-$work_root/slurm-%x-%j.out}")"
paths_overlap() {
  local left=${1%/} right=${2%/}
  [[ $left == "$right" || $left == "$right"/* || $right == "$left"/* ]]
}
[[ $work_root != / ]] || die "--work-root must not be /"
paths_overlap "$work_root" "$BUNDLE_ROOT" &&
  die "--work-root must be outside the immutable bundle"
[[ $output != "$BUNDLE_ROOT" && $output != "$BUNDLE_ROOT"/* ]] ||
  die "--output must be outside the immutable bundle"

if [[ -z $run_id ]]; then
  if ((execute)); then
    die "--run-id is required with --execute (choose a stable, auditable ID)"
  fi
  run_id="EXAMPLE_RUN_ID"
fi

if ((ntasks > 1)); then
  warn "this workflow was validated primarily with one MPI rank; verify SASA behavior before multi-rank production"
fi
profile_needs_long=1
[[ $profile == validate-only ]] && profile_needs_long=0
profile_needs_gpu=1
[[ $profile == validate-only ]] && profile_needs_gpu=0
profile_needs_sasa_ack=0
case "$profile" in
  historical-sasa-site|historical-sasa-pocket|historical-sasa-pocket-100ns|historical-sasa-biased-main|standardized-sasa-site-10ns-full|standardized-sasa-pocket-10ns-full|standardized-sasa-pocket-100ns-full|standardized-sasa-biased-main|all-traceable) profile_needs_sasa_ack=1 ;;
esac
if ((profile_needs_long && !allow_long_md)); then
  warn "$profile contains long MD stages; execution requires --allow-long-md"
fi
if ((profile_needs_gpu)) && [[ $mode != gpu ]]; then
  warn "$profile contains packaged production simulations and requires --mode gpu"
fi
if ((profile_needs_long && !walltime_explicit)); then
  warn "$profile is long; --time must be selected explicitly before submission"
fi
if ((profile_needs_sasa_ack && !ack_sasa_biasvalue)); then
  warn "$profile contains the preserved METAD+BIASVALUE SASA setup; review it and pass --ack-sasa-biasvalue"
fi

sbatch_args=(
  "--job-name=$job_name"
  "--nodes=$nodes"
  "--ntasks=$ntasks"
  "--cpus-per-task=$cpus_per_task"
  "--time=$walltime"
  "--output=$output"
)
[[ -z $partition ]] || sbatch_args+=("--partition=$partition")
[[ -z $account ]] || sbatch_args+=("--account=$account")
[[ -z $qos ]] || sbatch_args+=("--qos=$qos")
[[ -z $memory ]] || sbatch_args+=("--mem=$memory")
if [[ $mode == gpu ]]; then
  sbatch_args+=("--gpus-per-node=$gpus")
fi
sbatch_args+=("${extra_sbatch[@]}")

print_assignment() {
  local name=$1 value=$2
  printf 'export %s=%q\n' "$name" "$value"
}

render_job() {
  local agentctl="$BUNDLE_ROOT/agentctl"

  printf '%s\n' '#!/usr/bin/env bash'
  printf '%s\n' 'set -Eeuo pipefail'
  printf '\n'
  printf 'source %q\n' "$env_script"
  if [[ -n $site_config ]]; then
    # Export ordinary NAME=value entries while sourcing.  agentctl prepare
    # then captures the allowlisted effective values into the run snapshot.
    printf '%s\n' 'set -a'
    printf 'source %q\n' "$site_config"
    printf '%s\n' 'set +a'
  fi
  printf '\n'
  print_assignment GMX_ENV_SCRIPT "$env_script"
  print_assignment GMX_DEVICE_MODE "$mode"
  print_assignment GMX_LAUNCHER "$launcher"
  print_assignment MPI_RANKS "$ntasks"
  print_assignment OMP_THREADS "$cpus_per_task"
  [[ -z $mdrun_maxh ]] || print_assignment GMX_MDRUN_MAXH "$mdrun_maxh"
  printf 'export OMP_NUM_THREADS="$OMP_THREADS"\n'
  printf '\n'
  printf '%q --work-root %q prepare --run-id %q\n' \
    "$agentctl" "$work_root" "$run_id"
  printf '%q --work-root %q run --profile %q --run-id %q --execute' \
    "$agentctl" "$work_root" "$profile" "$run_id"
  if ((allow_long_md)); then
    printf ' --allow-long-md'
  fi
  if ((ack_sasa_biasvalue)); then
    printf ' --ack-sasa-biasvalue'
  fi
  printf '\n'
}

printf 'Slurm profile: %s\n' "$([[ $execute == 1 ]] && printf EXECUTE || printf PLAN)"
printf '  bundle:       %s\n' "$BUNDLE_ROOT"
printf '  stack env:    %s\n' "$env_script"
printf '  workflow:     mode=%s profile=%s run-id=%s\n' "$mode" "$profile" "$run_id"
printf '  resources:    nodes=%s ranks=%s threads/rank=%s' "$nodes" "$ntasks" "$cpus_per_task"
[[ $mode == gpu ]] && printf ' gpus/node=%s' "$gpus"
printf '\n'
printf '  launcher:     %s\n' "$launcher"
[[ -z $mdrun_maxh ]] || printf '  mdrun maxh:   %s h per invocation\n' "$mdrun_maxh"
printf '  Slurm output: %s\n' "$output"

if ((!execute)); then
  printf '\nNo job was submitted.  Planned submission command:\n  sbatch '
  printf '%q ' "${sbatch_args[@]}"
  printf '<<\x27SLURM_JOB\x27\n'
  render_job
  printf '%s\n' 'SLURM_JOB'
  printf '\nAdd --execute and a real --run-id to submit this exact job.\n'
  exit 0
fi

if ((profile_needs_gpu)) && [[ $mode != gpu ]]; then
  die "$profile requires CUDA production execution; use --mode gpu"
fi
command -v sbatch >/dev/null 2>&1 || die "sbatch is not available"
if ((profile_needs_long && !allow_long_md)); then
  die "$profile requires explicit --allow-long-md"
fi
if ((profile_needs_long && !walltime_explicit)); then
  die "$profile requires an explicit --time based on target-node benchmarks"
fi
if ((profile_needs_sasa_ack && !ack_sasa_biasvalue)); then
  die "$profile requires explicit --ack-sasa-biasvalue"
fi
[[ -r $env_script ]] || die "stack environment is not readable: $env_script"
[[ -x $BUNDLE_ROOT/agentctl ]] || die "agentctl is not executable: $BUNDLE_ROOT/agentctl"
[[ -z $site_config || -r $site_config ]] || die "site config is not readable: $site_config"
mkdir -p -- "$(dirname -- "$output")"

printf '\nSubmitting with:\n  sbatch '
printf '%q ' "${sbatch_args[@]}"
printf '\n'
render_job | sbatch "${sbatch_args[@]}"

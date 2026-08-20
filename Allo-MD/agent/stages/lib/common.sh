#!/usr/bin/env bash
set -Eeuo pipefail

if (( BASH_VERSINFO[0] < 4 || (BASH_VERSINFO[0] == 4 && BASH_VERSINFO[1] < 3) )); then
    echo "Bash 4.3 or newer is required (array nameref support)" >&2
    exit 2
fi

: "${AGENT_BUNDLE_ROOT:?AGENT_BUNDLE_ROOT is required}"

if [[ -n "${AGENT_SITE_CONFIG:-}" ]]; then
    [[ -f "$AGENT_SITE_CONFIG" ]] || { echo "Missing site config: $AGENT_SITE_CONFIG" >&2; exit 2; }
    # The site file is an explicit, trusted deployment input.
    # shellcheck source=/dev/null
    source "$AGENT_SITE_CONFIG"
fi

if [[ -n "${GMX_ENV_SCRIPT:-}" ]]; then
    [[ -f "$GMX_ENV_SCRIPT" ]] || { echo "Missing GMX environment script: $GMX_ENV_SCRIPT" >&2; exit 2; }
    # shellcheck source=/dev/null
    source "$GMX_ENV_SCRIPT"
fi

# The frozen site snapshot is the final authority.  The installation env.sh
# supplies paths and libraries, but must not silently replace an explicitly
# frozen binary/resource choice.
if [[ -n "${AGENT_SITE_CONFIG:-}" ]]; then
    # shellcheck source=/dev/null
    source "$AGENT_SITE_CONFIG"
fi

: "${GMX_BIN:=gmx_mpi}"
: "${PLUMED_BIN:=plumed}"
: "${MDPOCKET_BIN:=mdpocket}"
: "${MDPOCKET_PROVENANCE:=UNRESOLVED}"
: "${PYTHON_BIN:=python3}"
: "${GMX_LAUNCHER:=direct}"
: "${MPIEXEC_BIN:=mpirun}"
: "${MPI_RANKS:=1}"
: "${OMP_THREADS:=1}"
: "${GMX_DEVICE_MODE:=auto}"
: "${GMX_MDRUN_EXTRA_ARGS:=-v}"
: "${GMX_MDRUN_MAXH:=}"
: "${RESTRAINT_REFERENCE_MODE:=charmm_gui_initial}"

[[ "$MPI_RANKS" =~ ^[1-9][0-9]*$ ]] || { echo "MPI_RANKS must be a positive integer" >&2; exit 2; }
[[ "$OMP_THREADS" =~ ^[1-9][0-9]*$ ]] || { echo "OMP_THREADS must be a positive integer" >&2; exit 2; }
export OMP_NUM_THREADS="$OMP_THREADS"

quote_command() {
    printf '%q ' "$@"
    printf '\n'
}

record_command() {
    local command_file="${AGENT_COMMAND_FILE:-/dev/null}"
    {
        printf '# %s\n' "$(date --iso-8601=seconds)"
        quote_command "$@"
    } >> "$command_file"
}

run_cmd() {
    record_command "$@"
    quote_command "$@"
    "$@" 2>&1 | tee -a "${AGENT_CONSOLE_LOG:-/dev/null}"
}

run_with_input() {
    local input_text="$1"
    shift
    record_command "$@"
    printf '# stdin: %q\n' "$input_text" >> "${AGENT_COMMAND_FILE:-/dev/null}"
    quote_command "$@"
    printf '%s' "$input_text" | "$@" 2>&1 | tee -a "${AGENT_CONSOLE_LOG:-/dev/null}"
}

assert_file() {
    [[ -s "$1" ]] || { echo "Required file is missing or empty: $1" >&2; exit 3; }
}

stage_begin() {
    : "${AGENT_RUN_DIR:?AGENT_RUN_DIR is required}"
    : "${AGENT_STAGE_ID:?AGENT_STAGE_ID is required}"
    [[ "${AGENT_ORCHESTRATED:-0}" == "1" ]] || { echo "Stage entry is reserved for agentctl orchestration" >&2; exit 2; }
    [[ "${AGENT_EXECUTE:-0}" == "1" ]] || { echo "Stage scripts are dry by default; use agentctl with --execute" >&2; exit 2; }
    [[ "${AGENT_ALLOW_LONG_MD:-0}" == "1" ]] || { echo "Long-stage gate is closed" >&2; exit 2; }
    case "${AGENT_REQUIRED_DEVICE:-}" in
        "") ;;
        gpu)
            [[ "$GMX_DEVICE_MODE" == gpu ]] || {
                echo "This stage is orchestrator-marked as CUDA production MD; GMX_DEVICE_MODE must be gpu" >&2
                exit 2
            }
            ;;
        *)
            echo "Unsupported orchestrator device requirement: $AGENT_REQUIRED_DEVICE" >&2
            exit 2
            ;;
    esac
    [[ -z "${GMX_MAXCONSTRWARN:-}" ]] || {
        echo "Refusing inherited GMX_MAXCONSTRWARN=$GMX_MAXCONSTRWARN; fix constraint warnings instead" >&2
        exit 2
    }
    [[ -z "${PLUMED_KERNEL:-}" ]] || {
        echo "Refusing PLUMED_KERNEL in a shared-patch workflow: $PLUMED_KERNEL" >&2
        exit 2
    }
    case "$GMX_MDRUN_EXTRA_ARGS" in
        ""|-v) ;;
        *)
            echo "GMX_MDRUN_EXTRA_ARGS is restricted to an empty value or -v" >&2
            echo "Protocol-changing mdrun options (for example -nsteps or -maxh) are forbidden" >&2
            exit 2
            ;;
    esac
    if [[ -n "$GMX_MDRUN_MAXH" ]]; then
        [[ "$GMX_MDRUN_MAXH" =~ ^[0-9]+([.][0-9]+)?$ ]] \
            && awk -v value="$GMX_MDRUN_MAXH" 'BEGIN {exit !(value>0)}' || {
            echo "GMX_MDRUN_MAXH must be a positive number of hours" >&2
            exit 2
        }
    fi
    AGENT_STAGE_DIR="$AGENT_RUN_DIR/stages/$AGENT_STAGE_ID"
    AGENT_COMMAND_FILE="$AGENT_RUN_DIR/commands/$AGENT_STAGE_ID.commands.log"
    AGENT_CONSOLE_LOG="$AGENT_RUN_DIR/logs/$AGENT_STAGE_ID.console.log"
    export AGENT_STAGE_DIR AGENT_COMMAND_FILE AGENT_CONSOLE_LOG
    mkdir -p "$AGENT_STAGE_DIR" "$AGENT_RUN_DIR/commands" "$AGENT_RUN_DIR/logs"
    # Recheck the copied scientific inputs at every stage boundary.  This is
    # cheap relative to MD and prevents a mid-run edit from silently changing
    # topology, selections, MDPs, or frozen PLUMED coefficients.
    run_cmd "$PYTHON_BIN" "$AGENT_BUNDLE_ROOT/tools/validate_inputs.py" \
        --bundle-root "$AGENT_BUNDLE_ROOT" --inputs-root "$AGENT_RUN_DIR/inputs"
}

link_system_inputs() {
    local rel
    for rel in topol.top index.ndx step5_input.gro step5_input3.pdb; do
        if [[ ! -e "$AGENT_STAGE_DIR/$rel" ]]; then
            ln -s "../../inputs/system/$rel" "$AGENT_STAGE_DIR/$rel"
        fi
    done
    if [[ ! -e "$AGENT_STAGE_DIR/toppar" ]]; then
        ln -s "../../inputs/system/toppar" "$AGENT_STAGE_DIR/toppar"
    fi
}

copy_config_once() {
    local source_file="$1"
    local destination="$2"
    assert_file "$source_file"
    if [[ -e "$destination" ]]; then
        cmp -s "$source_file" "$destination" || {
            echo "Existing stage configuration differs from the frozen input: $destination" >&2
            echo "Use a new run-id; this package will not silently change a prepared stage." >&2
            exit 4
        }
    else
        cp -p "$source_file" "$destination"
    fi
}

log_finished() {
    [[ -s "$1" ]] && tail -c 524288 "$1" | grep -q 'Finished mdrun'
}

assert_checkpoint_reached_tpr_end() {
    local deffnm="$1"
    local tpr="$deffnm.tpr"
    local checkpoint="$deffnm.cpt"
    [[ -s "$tpr" ]] || {
        echo "Required TPR is missing or empty: $tpr" >&2
        return 1
    }

    local parameter_dump
    parameter_dump="$(mktemp --tmpdir=. ".${deffnm##*/}.tpr-parameters.XXXXXX.mdp")"
    record_command "$GMX_BIN" dump -s "$tpr" -om "$parameter_dump"
    if ! "$GMX_BIN" dump -s "$tpr" -om "$parameter_dump" \
            >/dev/null 2>>"${AGENT_CONSOLE_LOG:-/dev/null}"; then
        rm -f -- "$parameter_dump"
        echo "Cannot inspect TPR completion target: $tpr" >&2
        return 1
    fi

    local integrator tinit dt nsteps init_step
    integrator="$(awk -F= '$1 ~ /^[[:space:]]*integrator[[:space:]]*$/ {gsub(/[[:space:]]/, "", $2); print $2; exit}' "$parameter_dump")"
    if [[ "$integrator" == steep ]]; then
        local emtol em_nsteps summary convergence_re reported_emtol reported_steps
        emtol="$(awk -F= '$1 ~ /^[[:space:]]*emtol[[:space:]]*$/ {gsub(/[[:space:]]/, "", $2); print $2; exit}' "$parameter_dump")"
        em_nsteps="$(awk -F= '$1 ~ /^[[:space:]]*nsteps[[:space:]]*$/ {gsub(/[[:space:]]/, "", $2); print $2; exit}' "$parameter_dump")"
        rm -f -- "$parameter_dump"
        [[ -s "$deffnm.log" ]] || {
            echo "Energy-minimization log is missing: $deffnm.log" >&2
            return 1
        }
        summary="$(grep -E '^Steepest Descents (converged|did not converge)' "$deffnm.log" | tail -n 1 || true)"
        convergence_re='^Steepest Descents converged to Fmax < ([^ ]+) in ([0-9]+) steps$'
        if [[ "$summary" =~ $convergence_re ]]; then
            reported_emtol="${BASH_REMATCH[1]}"
            reported_steps="${BASH_REMATCH[2]}"
            if [[ "$emtol" =~ ^[0-9]+([.][0-9]+)?([eE][-+]?[0-9]+)?$ \
               && "$em_nsteps" =~ ^[0-9]+$ \
               && "$reported_emtol" =~ ^[0-9]+([.][0-9]+)?([eE][-+]?[0-9]+)?$ ]] \
               && awk -v expected="$emtol" -v reported="$reported_emtol" \
                    -v steps="$reported_steps" -v limit="$em_nsteps" 'BEGIN {
                        difference=expected-reported; if (difference<0) difference=-difference;
                        tolerance=expected*1e-9; if (tolerance<1e-9) tolerance=1e-9;
                        # GROMACS can report the final steepest-descent
                        # evaluation as nsteps+1 while still meeting Fmax.
                        exit !(difference<=tolerance && steps<=limit+1);
                    }'; then
                echo "Verified steepest-descent minimization reached Fmax < $reported_emtol in $reported_steps steps."
                return 0
            fi
        fi
        echo "Steepest-descent minimization did not reach the frozen Fmax convergence target" >&2
        [[ -z "$summary" ]] || echo "Last minimization summary: $summary" >&2
        echo "A finish marker, machine-precision stop, or maximum-step stop is not accepted." >&2
        return 1
    fi
    if [[ "$integrator" != md ]]; then
        rm -f -- "$parameter_dump"
        echo "Unsupported integrator for automatic completion proof: $integrator" >&2
        return 1
    fi
    tinit="$(awk -F= '$1 ~ /^[[:space:]]*tinit[[:space:]]*$/ {gsub(/[[:space:]]/, "", $2); print $2; exit}' "$parameter_dump")"
    dt="$(awk -F= '$1 ~ /^[[:space:]]*dt[[:space:]]*$/ {gsub(/[[:space:]]/, "", $2); print $2; exit}' "$parameter_dump")"
    nsteps="$(awk -F= '$1 ~ /^[[:space:]]*nsteps[[:space:]]*$/ {gsub(/[[:space:]]/, "", $2); print $2; exit}' "$parameter_dump")"
    init_step="$(awk -F= '$1 ~ /^[[:space:]]*init-step[[:space:]]*$/ {gsub(/[[:space:]]/, "", $2); print $2; exit}' "$parameter_dump")"
    rm -f -- "$parameter_dump"

    [[ -s "$checkpoint" ]] || {
        echo "Completed MD log has no checkpoint for final-step verification: $checkpoint" >&2
        return 1
    }
    [[ "$tinit" =~ ^-?[0-9]+([.][0-9]+)?([eE][-+]?[0-9]+)?$ \
       && "$dt" =~ ^[0-9]+([.][0-9]+)?([eE][-+]?[0-9]+)?$ \
       && "$nsteps" =~ ^[0-9]+$ && "$init_step" =~ ^-?[0-9]+$ ]] || {
        echo "Cannot parse TPR timing: tinit=$tinit dt=$dt nsteps=$nsteps init-step=$init_step" >&2
        return 1
    }

    local checkpoint_report checkpoint_time
    record_command "$GMX_BIN" check -f "$checkpoint"
    checkpoint_report="$("$GMX_BIN" check -f "$checkpoint" 2>&1)" || {
        printf '%s\n' "$checkpoint_report" >>"${AGENT_CONSOLE_LOG:-/dev/null}"
        echo "Cannot inspect checkpoint completion time: $checkpoint" >&2
        return 1
    }
    checkpoint_time="$(tr '\r' '\n' <<<"$checkpoint_report" \
        | awk '/Last frame/ {for (i=1; i<=NF; i++) if ($i=="time") {print $(i+1); exit}}')"
    [[ "$checkpoint_time" =~ ^-?[0-9]+([.][0-9]+)?([eE][-+]?[0-9]+)?$ ]] || {
        echo "Cannot parse final time from checkpoint: $checkpoint" >&2
        return 1
    }

    awk -v actual="$checkpoint_time" -v tinit="$tinit" -v dt="$dt" \
        -v nsteps="$nsteps" -v init_step="$init_step" 'BEGIN {
            expected=tinit+(init_step+nsteps)*dt;
            difference=actual-expected; if (difference<0) difference=-difference;
            tolerance=dt*0.51; if (tolerance<1e-6) tolerance=1e-6;
            if (difference>tolerance) exit 1;
        }' || {
        echo "Checkpoint stopped before the TPR endpoint: actual=${checkpoint_time} ps" >&2
        echo "Refusing to treat an early -maxh/-nsteps stop as a completed stage" >&2
        return 1
    }
    printf 'Verified checkpoint reached the TPR endpoint: %s ps\n' "$checkpoint_time"
}

grompp_if_needed() {
    local tpr="$1"
    shift
    if [[ -s "$tpr" ]]; then
        echo "Reuse existing TPR for resume: $tpr"
        return 0
    fi
    run_cmd "$GMX_BIN" grompp "$@" -o "$tpr"
}

build_mdrun_command() {
    local output_name="$1"
    shift
    local -n output_ref="$output_name"
    case "$GMX_LAUNCHER" in
        direct)
            output_ref=("$GMX_BIN" mdrun)
            ;;
        mpirun)
            output_ref=("$MPIEXEC_BIN" -np "$MPI_RANKS" "$GMX_BIN" mdrun)
            ;;
        srun)
            output_ref=(srun --ntasks="$MPI_RANKS" "$GMX_BIN" mdrun)
            ;;
        *)
            echo "Unknown GMX_LAUNCHER: $GMX_LAUNCHER" >&2
            exit 2
            ;;
    esac
    output_ref+=("$@")
}

append_mdrun_tuning() {
    local output_name="$1"
    local deffnm="$2"
    local -n output_ref="$output_name"
    case "$GMX_DEVICE_MODE" in
        auto)
            ;;
        gpu)
            output_ref+=(-nb gpu -pme gpu -bonded gpu)
            ;;
        cpu)
            output_ref+=(-nb cpu -pme cpu -bonded cpu -update cpu)
            ;;
        *)
            echo "GMX_DEVICE_MODE must be auto, gpu, or cpu" >&2
            exit 2
            ;;
    esac
    local extra=()
    if [[ -n "$GMX_MDRUN_EXTRA_ARGS" ]]; then
        read -r -a extra <<< "$GMX_MDRUN_EXTRA_ARGS"
        output_ref+=("${extra[@]}")
    fi
    if [[ -n "$GMX_MDRUN_MAXH" ]]; then
        local parameter_dump integrator
        parameter_dump="$(mktemp --tmpdir=. ".${deffnm##*/}.maxh-parameters.XXXXXX.mdp")"
        record_command "$GMX_BIN" dump -s "$deffnm.tpr" -om "$parameter_dump"
        if ! "$GMX_BIN" dump -s "$deffnm.tpr" -om "$parameter_dump" \
                >/dev/null 2>>"${AGENT_CONSOLE_LOG:-/dev/null}"; then
            rm -f -- "$parameter_dump"
            echo "Cannot inspect the TPR before applying GMX_MDRUN_MAXH: $deffnm.tpr" >&2
            exit 2
        fi
        integrator="$(awk -F= '$1 ~ /^[[:space:]]*integrator[[:space:]]*$/ {gsub(/[[:space:]]/, "", $2); print $2; exit}' "$parameter_dump")"
        rm -f -- "$parameter_dump"
        if [[ "$integrator" == md ]]; then
            output_ref+=(-maxh "$GMX_MDRUN_MAXH")
        else
            echo "GMX_MDRUN_MAXH is not applied to non-MD integrator: $integrator"
        fi
    fi
}

validate_plumed_checkpoint_series() {
    local deffnm="$1" plumed_file="$2"
    local checkpoint_report checkpoint_time timestep
    record_command "$GMX_BIN" check -f "$deffnm.cpt"
    checkpoint_report="$("$GMX_BIN" check -f "$deffnm.cpt" 2>&1)" || {
        echo "Cannot inspect PLUMED-stage checkpoint: $deffnm.cpt" >&2
        return 1
    }
    checkpoint_time="$(tr '\r' '\n' <<<"$checkpoint_report" \
        | awk '/Last frame/ {for (i=1; i<=NF; i++) if ($i=="time") {print $(i+1); exit}}')"
    [[ "$checkpoint_time" =~ ^-?[0-9]+([.][0-9]+)?([eE][-+]?[0-9]+)?$ ]] || {
        echo "Cannot parse checkpoint time for PLUMED validation" >&2
        return 1
    }
    timestep="$(awk -F= '$1 ~ /^[[:space:]]*dt[[:space:]]*$/ {
        value=$2; sub(/[;#].*$/, "", value); gsub(/[[:space:]]/, "", value);
        print value; exit
    }' "$deffnm.mdp")"
    [[ "$timestep" =~ ^[0-9]+([.][0-9]+)?([eE][-+]?[0-9]+)?$ ]] || {
        echo "Cannot parse dt from $deffnm.mdp for PLUMED validation" >&2
        return 1
    }
    run_cmd "$PYTHON_BIN" "$AGENT_BUNDLE_ROOT/tools/validate_plumed_restart.py" \
        --plumed "$plumed_file" --base-dir . \
        --checkpoint-time "$checkpoint_time" --dt "$timestep"
}

run_mdrun() {
    local deffnm="$1"
    local plumed_file="${2:-}"
    if log_finished "$deffnm.log"; then
        if assert_checkpoint_reached_tpr_end "$deffnm"; then
            if [[ -n "$plumed_file" ]]; then
                validate_plumed_checkpoint_series "$deffnm" "$plumed_file" || exit 5
            fi
            echo "Already finished: $deffnm"
            return 0
        fi
        echo "The log has a finish marker from an early stop; continuing from its checkpoint."
    fi
    local command=()
    build_mdrun_command command -deffnm "$deffnm"
    if [[ -s "$deffnm.cpt" ]]; then
        if [[ -n "$plumed_file" ]]; then
            # GROMACS tells the patched PLUMED interface to restart, but an
            # abrupt stop can leave text output ahead of the last checkpoint.
            # Never load hills/observations from the checkpoint's future.
            if ! validate_plumed_checkpoint_series "$deffnm" "$plumed_file"; then
                echo "Automatic PLUMED truncation is unsafe; preserve the run for expert recovery." >&2
                exit 4
            fi
        fi
        command+=(-cpi "$deffnm.cpt" -append)
    elif [[ -e "$deffnm.log" || -e "$deffnm.edr" || -e "$deffnm.xtc" ]]; then
        echo "Partial outputs exist but no checkpoint is available for $deffnm" >&2
        echo "Use a new run-id; this package will not overwrite uncertain state." >&2
        exit 4
    fi
    if [[ -n "$plumed_file" ]]; then
        assert_file "$plumed_file"
        command+=(-plumed "$plumed_file")
    fi
    append_mdrun_tuning command "$deffnm"
    run_cmd "${command[@]}"
    log_finished "$deffnm.log" || { echo "mdrun did not reach its planned final step: $deffnm" >&2; exit 5; }
    assert_checkpoint_reached_tpr_end "$deffnm" || exit 5
    if [[ -n "$plumed_file" ]]; then
        validate_plumed_checkpoint_series "$deffnm" "$plumed_file" || exit 5
    fi
}

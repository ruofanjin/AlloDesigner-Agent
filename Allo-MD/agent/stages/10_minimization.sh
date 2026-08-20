#!/usr/bin/env bash
set -Eeuo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/common.sh
source "$script_dir/lib/common.sh"
stage_begin
link_system_inputs
cd "$AGENT_STAGE_DIR"

copy_config_once "$AGENT_RUN_DIR/inputs/mdp/equilibration/step6.0_minimization.mdp" minimization.mdp
grompp_if_needed em.tpr \
    -f minimization.mdp \
    -c step5_input.gro \
    -r step5_input.gro \
    -p topol.top \
    -n index.ndx
# `steep` is a preparation integrator, not production molecular dynamics.
# Keep the run in the CUDA production profile, but let GROMACS choose its
# supported minimization path instead of forcing MD-only GPU task flags.
if [[ "$GMX_DEVICE_MODE" == gpu ]]; then
    printf '%s\n' 'Energy minimization uses automatic task placement; CUDA is enforced from equilibration onward.' \
        >> "$AGENT_CONSOLE_LOG"
    GMX_DEVICE_MODE=auto
fi
run_mdrun em
assert_file em.gro

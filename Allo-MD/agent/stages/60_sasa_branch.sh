#!/usr/bin/env bash
set -Eeuo pipefail

[[ $# -eq 3 ]] || { echo "Usage: $0 BRANCH MDP_FILE PLUMED_RELATIVE_PATH" >&2; exit 2; }
branch="$1"
mdp_name="$2"
plumed_rel="$3"

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/common.sh
source "$script_dir/lib/common.sh"
[[ "${AGENT_ACK_SASA_BIASVALUE:-no}" == "yes" ]] || {
    echo "SASA frozen-protocol gate is closed: DAT has both METAD and BIASVALUE ARG=sasa" >&2
    exit 6
}
stage_begin
link_system_inputs
cd "$AGENT_STAGE_DIR"

prefix="$AGENT_STAGE_ID"
start_dir="$AGENT_RUN_DIR/stages/normal_100ns"
assert_file "$start_dir/normal_100ns.gro"
assert_file "$start_dir/normal_100ns.cpt"
copy_config_once "$AGENT_RUN_DIR/inputs/mdp/sasa/$mdp_name" "$prefix.mdp"
copy_config_once "$AGENT_RUN_DIR/inputs/plumed/$plumed_rel" plumed.dat

printf 'Legacy-exact SASA branch acknowledged: %s\n' "$branch" >> "$AGENT_CONSOLE_LOG"
grompp_if_needed "$prefix.tpr" \
    -f "$prefix.mdp" \
    -c "$start_dir/normal_100ns.gro" \
    -t "$start_dir/normal_100ns.cpt" \
    -p topol.top \
    -n index.ndx
run_mdrun "$prefix" plumed.dat
assert_file "$prefix.gro"
assert_file "$prefix.cpt"
assert_file HILLS
assert_file COLVAR

#!/usr/bin/env bash
set -Eeuo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/common.sh
source "$script_dir/lib/common.sh"
stage_begin
link_system_inputs
cd "$AGENT_STAGE_DIR"

prefix="distance_metad_50ns"
start_dir="$AGENT_RUN_DIR/stages/distance_monitor_50ns"
assert_file "$start_dir/distance_monitor_50ns.gro"
assert_file "$start_dir/distance_monitor_50ns.cpt"
copy_config_once "$AGENT_RUN_DIR/inputs/mdp/distance/distance_metad_50ns.mdp" "$prefix.mdp"
copy_config_once "$AGENT_RUN_DIR/inputs/plumed/distance_metad/distance_metad.dat" plumed.dat

grompp_if_needed "$prefix.tpr" \
    -f "$prefix.mdp" \
    -c "$start_dir/distance_monitor_50ns.gro" \
    -t "$start_dir/distance_monitor_50ns.cpt" \
    -p topol.top \
    -n index.ndx
run_mdrun "$prefix" plumed.dat
assert_file "$prefix.gro"
assert_file "$prefix.cpt"
assert_file HILLS
assert_file COLVAR_biased.dat

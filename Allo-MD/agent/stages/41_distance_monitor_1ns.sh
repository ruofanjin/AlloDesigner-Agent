#!/usr/bin/env bash
set -Eeuo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
source "$script_dir/lib/common.sh"
stage_begin
link_system_inputs
cd "$AGENT_STAGE_DIR"
prefix="distance_monitor_1ns"
start_dir="$AGENT_RUN_DIR/stages/normal_1ns"
assert_file "$start_dir/normal_1ns.gro"
assert_file "$start_dir/normal_1ns.cpt"
copy_config_once "$AGENT_RUN_DIR/inputs/mdp/distance/distance_monitor_1ns_demo.mdp" "$prefix.mdp"
copy_config_once "$AGENT_RUN_DIR/inputs/plumed/distance_monitor/distance_monitor.dat" plumed.dat
grompp_if_needed "$prefix.tpr" \
    -f "$prefix.mdp" \
    -c "$start_dir/normal_1ns.gro" \
    -t "$start_dir/normal_1ns.cpt" \
    -p topol.top \
    -n index.ndx
run_mdrun "$prefix" plumed.dat
assert_file "$prefix.gro"
assert_file "$prefix.cpt"
assert_file colvar_distance

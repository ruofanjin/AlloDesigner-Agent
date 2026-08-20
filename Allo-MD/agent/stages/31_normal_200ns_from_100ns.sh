#!/usr/bin/env bash
set -Eeuo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/common.sh
source "$script_dir/lib/common.sh"
stage_begin
link_system_inputs
cd "$AGENT_STAGE_DIR"

prefix="normal_200ns_from_100ns"
start_dir="$AGENT_RUN_DIR/stages/normal_100ns"
assert_file "$start_dir/normal_100ns.gro"
assert_file "$start_dir/normal_100ns.cpt"
copy_config_once "$AGENT_RUN_DIR/inputs/mdp/normal/step7.4_production.mdp" "$prefix.mdp"

# Historical protocol: physical state continues from 100 ns, while the new TPR
# keeps tinit/init-step at zero. It is a 200 ns added segment, not a continuous
# on-disk time axis and not part of a 10+50+100+200 chain.
grompp_if_needed "$prefix.tpr" \
    -f "$prefix.mdp" \
    -c "$start_dir/normal_100ns.gro" \
    -t "$start_dir/normal_100ns.cpt" \
    -p topol.top \
    -n index.ndx
run_mdrun "$prefix"
assert_file "$prefix.gro"
assert_file "$prefix.cpt"

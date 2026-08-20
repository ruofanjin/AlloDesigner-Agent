#!/usr/bin/env bash
set -Eeuo pipefail

[[ $# -eq 2 ]] || { echo "Usage: $0 DURATION MDP_FILE" >&2; exit 2; }
duration="$1"
mdp_name="$2"
[[ "$duration" =~ ^(1ns|10ns|50ns|100ns)$ ]] || { echo "Unexpected duration: $duration" >&2; exit 2; }

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/common.sh
source "$script_dir/lib/common.sh"
stage_begin
link_system_inputs
cd "$AGENT_STAGE_DIR"

prefix="normal_${duration}"
start_gro="$AGENT_RUN_DIR/stages/equilibration/eq6.gro"
assert_file "$start_gro"
copy_config_once "$AGENT_RUN_DIR/inputs/mdp/normal/$mdp_name" "$prefix.mdp"

# The archived step7_1/2/3 TPRs have identical x/v/box. They are independent
# duration branches from eq6, despite the stale command notebook suggesting a
# 10 -> 50 -> 100 ns chain. Do not use another normal branch as this input.
grompp_if_needed "$prefix.tpr" \
    -f "$prefix.mdp" \
    -c "$start_gro" \
    -p topol.top \
    -n index.ndx
run_mdrun "$prefix"
assert_file "$prefix.gro"
assert_file "$prefix.cpt"

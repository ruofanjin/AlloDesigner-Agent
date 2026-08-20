#!/usr/bin/env bash
set -Eeuo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/common.sh
source "$script_dir/lib/common.sh"
stage_begin
link_system_inputs
cd "$AGENT_STAGE_DIR"

previous_gro="$AGENT_RUN_DIR/stages/minimization/em.gro"
assert_file "$previous_gro"

for number in 1 2 3 4 5 6; do
    prefix="eq${number}"
    mdp_source="$AGENT_RUN_DIR/inputs/mdp/equilibration/step6.${number}_equilibration.mdp"
    copy_config_once "$mdp_source" "$prefix.mdp"

    case "$RESTRAINT_REFERENCE_MODE" in
        historical_previous)
            restraint_gro="$previous_gro"
            ;;
        charmm_gui_initial)
            restraint_gro="$AGENT_RUN_DIR/inputs/system/step5_input.gro"
            ;;
        *)
            echo "Unknown RESTRAINT_REFERENCE_MODE: $RESTRAINT_REFERENCE_MODE" >&2
            exit 2
            ;;
    esac

    assert_file "$previous_gro"
    assert_file "$restraint_gro"
    grompp_if_needed "$prefix.tpr" \
        -f "$prefix.mdp" \
        -c "$previous_gro" \
        -r "$restraint_gro" \
        -p topol.top \
        -n index.ndx
    run_mdrun "$prefix"
    assert_file "$prefix.gro"
    assert_file "$prefix.cpt"
    previous_gro="$AGENT_STAGE_DIR/$prefix.gro"
done

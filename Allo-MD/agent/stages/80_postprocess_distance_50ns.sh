#!/usr/bin/env bash
set -Eeuo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=stages/lib/common.sh
source "$script_dir/lib/common.sh"

stage_begin

simulation_dir="$AGENT_RUN_DIR/stages/distance_metad_50ns"
tpr="$simulation_dir/distance_metad_50ns.tpr"
trajectory="$simulation_dir/distance_metad_50ns.xtc"
analysis_dir="$AGENT_RUN_DIR/inputs/analysis"
reference_5vex="$analysis_dir/5vex_holo_convert_apo_id_allosteric_site_2A.pdb"

assert_file "$tpr"
assert_file "$trajectory"
assert_file "$analysis_dir/protein_backbone.ndx"
assert_file "$analysis_dir/tm6_ecl3_tm7_backbone.ndx"
assert_file "$analysis_dir/tm6_tm7_backbone.ndx"
assert_file "$analysis_dir/allosteric_all_atoms_2A.ndx"
assert_file "$analysis_dir/allosteric_backbone_2A.ndx"
assert_file "$reference_5vex"

cd "$AGENT_STAGE_DIR"

assert_trajectory_endpoint() {
    local trajectory_file="$1" expected_ps="$2" report actual_ps
    record_command "$GMX_BIN" check -f "$trajectory_file"
    report="$("$GMX_BIN" check -f "$trajectory_file" 2>&1)" || {
        echo "Cannot inspect trajectory: $trajectory_file" >&2
        exit 5
    }
    actual_ps="$(tr '\r' '\n' <<<"$report" \
        | awk '/Last frame/ {for (i=1; i<=NF; i++) if ($i=="time") value=$(i+1)} END {print value}')"
    [[ "$actual_ps" =~ ^-?[0-9]+([.][0-9]+)?([eE][-+]?[0-9]+)?$ ]] || {
        echo "Cannot parse final trajectory time: $trajectory_file" >&2
        exit 5
    }
    awk -v actual="$actual_ps" -v expected="$expected_ps" \
        'BEGIN {difference=actual-expected; if (difference<0) difference=-difference; exit !(difference<=1e-3)}' || {
        echo "Trajectory $trajectory_file ends at $actual_ps ps, expected $expected_ps ps" >&2
        exit 5
    }
}

assert_xvg_endpoint() {
    local xvg_file="$1" expected_ns="$2" actual_ns
    actual_ns="$(awk '!/^[#@]/ && NF {value=$1} END {print value}' "$xvg_file")"
    [[ "$actual_ns" =~ ^-?[0-9]+([.][0-9]+)?([eE][-+]?[0-9]+)?$ ]] || {
        echo "Cannot parse final XVG time: $xvg_file" >&2
        exit 5
    }
    awk -v actual="$actual_ns" -v expected="$expected_ns" \
        'BEGIN {difference=actual-expected; if (difference<0) difference=-difference; exit !(difference<=1e-6)}' || {
        echo "RMSD $xvg_file ends at $actual_ns ns, expected $expected_ns ns" >&2
        exit 5
    }
}

assert_trajectory_endpoint "$trajectory" 50000

if [[ ! -s pbc_fixed.xtc ]]; then
    # trjconv prompts: centering group, then output group.
    run_with_input $'Protein\nProtein\n' \
        "$GMX_BIN" trjconv -s "$tpr" -f "$trajectory" -o pbc_fixed.xtc \
        -pbc mol -ur compact -center
fi
assert_trajectory_endpoint pbc_fixed.xtc 50000

if [[ ! -s aligned.xtc ]]; then
    # trjconv prompts: least-squares fit group, then output group.
    run_with_input $'Backbone\nProtein\n' \
        "$GMX_BIN" trjconv -s "$tpr" -f pbc_fixed.xtc -o aligned.xtc \
        -fit rot+trans
fi
assert_trajectory_endpoint aligned.xtc 50000

if [[ ! -s aligned_reference.pdb ]]; then
    run_with_input $'Protein\n' \
        "$GMX_BIN" trjconv -s "$tpr" -f aligned.xtc \
        -o aligned_reference.pdb -dump 0
fi
[[ $(grep -c '^ATOM' aligned_reference.pdb) -eq 7952 ]] || {
    echo "aligned_reference.pdb does not contain the expected 7952 protein atoms" >&2
    exit 5
}

run_rmsd() {
    local index_file="$1"
    local group_name="$2"
    local output_file="$3"
    if [[ ! -s "$output_file" ]]; then
        # gmx rms prompts: fit group, then RMSD calculation group.
        run_with_input "${group_name}"$'\n'"${group_name}"$'\n' \
            "$GMX_BIN" rms -s "$tpr" -f aligned.xtc -n "$index_file" \
            -o "$output_file" -tu ns
    fi
}

run_cluster() {
    local index_file="$1"
    local group_name="$2"
    local stem="$3"
    local cutoff="$4"
    local representatives="clusters_${stem}.pdb"
    local outputs=(
        "cluster_matrix_${stem}.xpm"
        "$representatives"
        "cluster_sizes_${stem}.xvg"
        "cluster_id_${stem}.xvg"
        "rmsd_distribution_${stem}.xvg"
        "cluster_${stem}.log"
    )
    local receipt=".cluster_${stem}.complete"
    local existing=0 output_file
    for output_file in "${outputs[@]}"; do
        [[ ! -e "$output_file" ]] || existing=$((existing + 1))
    done
    if [[ -e "$receipt" && ! -s "$receipt" ]]; then
        echo "Invalid cluster completion receipt for $stem" >&2
        exit 4
    fi
    if [[ ! -s "$receipt" && $existing -ne 0 ]]; then
        echo "Cluster outputs exist without a completion receipt for $stem" >&2
        echo "Preserve the partial analysis and use a new run-id." >&2
        exit 4
    fi
    if [[ ! -s "$receipt" ]]; then
        # The supplied index contains exactly one intentionally named group.
        # gmx cluster prompts for fit/RMSD atoms, then representative-output atoms.
        run_with_input "${group_name}"$'\n'"${group_name}"$'\n' \
            "$GMX_BIN" cluster -s "$tpr" -f aligned.xtc -n "$index_file" \
            -method gromos -cutoff "$cutoff" \
            -o "cluster_matrix_${stem}.xpm" \
            -cl "$representatives" \
            -sz "cluster_sizes_${stem}.xvg" \
            -clid "cluster_id_${stem}.xvg" \
            -dist "rmsd_distribution_${stem}.xvg" \
            -g "cluster_${stem}.log"
        for output_file in "${outputs[@]}"; do
            assert_file "$output_file"
        done
        run_cmd bash -c 'printf "complete\n" > "$1"' _ "$receipt"
    else
        (( existing == ${#outputs[@]} )) || {
            echo "Completed cluster set is now missing outputs for $stem" >&2
            exit 4
        }
    fi
    for output_file in "${outputs[@]}"; do
        assert_file "$output_file"
    done
}

run_5vex_cluster_rmsd() {
    local cutoff="$1"
    local representatives="clusters_allosteric_backbone_${cutoff}nm.pdb"
    local output_file="rmsd_5vex_vs_clusters_allosteric_backbone_${cutoff}nm.xvg"
    local receipt=".${output_file}.complete"
    assert_file "$representatives"
    if [[ -e "$output_file" && ! -s "$receipt" ]]; then
        echo "5VEX RMSD output exists without a completion receipt: $output_file" >&2
        exit 4
    fi
    if [[ ! -s "$receipt" ]]; then
        # Both the frozen 5VEX reference and these representatives expose one
        # unique 60-atom Backbone group; gmx rms prompts for fit, then RMSD.
        run_with_input $'Backbone\nBackbone\n' \
            "$GMX_BIN" rms -s "$reference_5vex" -f "$representatives" \
            -o "$output_file" -tu ps
        assert_file "$output_file"
        run_cmd bash -c 'printf "complete\n" > "$1"' _ "$receipt"
    fi
    assert_file "$output_file"
}

run_rmsd "$analysis_dir/protein_backbone.ndx" Backbone rmsd_backbone.xvg
run_rmsd "$analysis_dir/tm6_ecl3_tm7_backbone.ndx" Backbone rmsd_tm6_ecl3_tm7_backbone.xvg
run_rmsd "$analysis_dir/tm6_tm7_backbone.ndx" Backbone rmsd_tm6_tm7_backbone.xvg
run_rmsd "$analysis_dir/allosteric_all_atoms_2A.ndx" Protein rmsd_allosteric_all_atoms.xvg
run_rmsd "$analysis_dir/allosteric_backbone_2A.ndx" Backbone rmsd_allosteric_backbone.xvg

assert_xvg_endpoint rmsd_backbone.xvg 50
assert_xvg_endpoint rmsd_tm6_ecl3_tm7_backbone.xvg 50
assert_xvg_endpoint rmsd_tm6_tm7_backbone.xvg 50
assert_xvg_endpoint rmsd_allosteric_all_atoms.xvg 50
assert_xvg_endpoint rmsd_allosteric_backbone.xvg 50

# Historical analysis matrix: whole-backbone 0.2 nm; TM6/TM7 0.1/0.2 nm;
# allosteric all atoms 0.1 nm; allosteric backbone 0.1/0.2/0.3 nm.
run_cluster "$analysis_dir/protein_backbone.ndx" Backbone backbone_0.2nm 0.2
run_cluster "$analysis_dir/tm6_tm7_backbone.ndx" Backbone tm6_tm7_backbone_0.1nm 0.1
run_cluster "$analysis_dir/tm6_tm7_backbone.ndx" Backbone tm6_tm7_backbone_0.2nm 0.2
run_cluster "$analysis_dir/allosteric_all_atoms_2A.ndx" Protein allosteric_all_atoms_0.1nm 0.1
run_cluster "$analysis_dir/allosteric_backbone_2A.ndx" Backbone allosteric_backbone_0.1nm 0.1
run_cluster "$analysis_dir/allosteric_backbone_2A.ndx" Backbone allosteric_backbone_0.2nm 0.2
run_cluster "$analysis_dir/allosteric_backbone_2A.ndx" Backbone allosteric_backbone_0.3nm 0.3

run_5vex_cluster_rmsd 0.1
run_5vex_cluster_rmsd 0.2
run_5vex_cluster_rmsd 0.3

assert_file aligned.xtc
assert_file aligned_reference.pdb
assert_file rmsd_backbone.xvg
assert_file rmsd_allosteric_backbone.xvg
assert_file clusters_allosteric_backbone_0.1nm.pdb
assert_file rmsd_5vex_vs_clusters_allosteric_backbone_0.1nm.xvg
assert_file rmsd_5vex_vs_clusters_allosteric_backbone_0.2nm.xvg
assert_file rmsd_5vex_vs_clusters_allosteric_backbone_0.3nm.xvg

#!/usr/bin/env bash
set -Eeuo pipefail

[[ $# -eq 2 ]] || {
    echo "Usage: $0 SIMULATION_STAGE EXPECTED_ENDPOINT_PS" >&2
    exit 2
}
simulation_stage="$1"
expected_ps="$2"

case "$simulation_stage:$expected_ps" in
    sasa_site_10ns:10000|sasa_pocket_10ns:10000|sasa_pocket_100ns:100000) ;;
    *)
        echo "Unsupported SASA analysis target: $simulation_stage at $expected_ps ps" >&2
        exit 2
        ;;
esac

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=stages/lib/common.sh
source "$script_dir/lib/common.sh"

stage_begin

simulation_dir="$AGENT_RUN_DIR/stages/$simulation_stage"
tpr="$simulation_dir/$simulation_stage.tpr"
trajectory="$simulation_dir/$simulation_stage.xtc"
analysis_dir="$AGENT_RUN_DIR/inputs/analysis"
system_index="$AGENT_RUN_DIR/inputs/system/index.ndx"
reference_5vex="$analysis_dir/5vex_holo_convert_apo_id_allosteric_site_2A.pdb"
expected_ns="$(awk -v value="$expected_ps" 'BEGIN {printf "%.10g", value/1000}')"
expected_last_frame=$((expected_ps / 100))
expected_count=$((expected_last_frame + 1))

assert_file "$tpr"
assert_file "$trajectory"
assert_file "$system_index"
assert_file "$analysis_dir/protein_backbone.ndx"
assert_file "$analysis_dir/tm6_ecl3_tm7_backbone.ndx"
assert_file "$analysis_dir/tm6_tm7_backbone.ndx"
assert_file "$analysis_dir/allosteric_all_atoms_2A.ndx"
assert_file "$analysis_dir/allosteric_backbone_2A.ndx"
assert_file "$reference_5vex"

cd "$AGENT_STAGE_DIR"

trajectory_last_time=""
trajectory_last_frame=""
assert_trajectory_complete() {
    local trajectory_file="$1" expected_atoms="$2" report actual_atoms
    record_command "$GMX_BIN" check -f "$trajectory_file"
    report="$("$GMX_BIN" check -f "$trajectory_file" 2>&1)" || {
        printf '%s\n' "$report" >>"$AGENT_CONSOLE_LOG"
        echo "Cannot inspect trajectory: $trajectory_file" >&2
        exit 5
    }
    printf '%s\n' "$report" >>"$AGENT_CONSOLE_LOG"
    trajectory_last_time="$(tr '\r' '\n' <<<"$report" \
        | awk '/Last frame/ {for (i=1; i<=NF; i++) if ($i=="time") value=$(i+1)} END {print value}')"
    trajectory_last_frame="$(tr '\r' '\n' <<<"$report" \
        | awk '/Last frame/ {for (i=1; i<=NF; i++) if ($i=="frame") value=$(i+1)} END {print value}')"
    actual_atoms="$(tr '\r' '\n' <<<"$report" | awk '/^# Atoms/ {print $3; exit}')"
    [[ "$trajectory_last_time" =~ ^-?[0-9]+([.][0-9]+)?([eE][-+]?[0-9]+)?$ ]] || {
        echo "Cannot parse final trajectory time: $trajectory_file" >&2
        exit 5
    }
    [[ "$trajectory_last_frame" =~ ^[0-9]+$ ]] || {
        echo "Cannot parse final trajectory frame index: $trajectory_file" >&2
        exit 5
    }
    [[ "$actual_atoms" =~ ^[0-9]+$ && "$actual_atoms" -eq "$expected_atoms" ]] || {
        echo "Trajectory $trajectory_file has ${actual_atoms:-unknown} atoms, expected $expected_atoms" >&2
        exit 5
    }
    awk -v actual="$trajectory_last_time" -v expected="$expected_ps" \
        'BEGIN {difference=actual-expected; if (difference<0) difference=-difference; exit !(difference<=1e-3)}' || {
        echo "Trajectory $trajectory_file ends at $trajectory_last_time ps, expected $expected_ps ps" >&2
        exit 5
    }
    [[ "$trajectory_last_frame" -eq "$expected_last_frame" ]] || {
        echo "Trajectory $trajectory_file ends at frame $trajectory_last_frame, expected $expected_last_frame" >&2
        exit 5
    }
}

assert_xvg_complete() {
    local xvg_file="$1" count first last
    if ! awk '
        BEGIN {
            number = "^[-+]?(([0-9]+([.][0-9]*)?)|([.][0-9]+))([eE][-+]?[0-9]+)?$"
        }
        !/^[#@]/ && NF {
            rows++
            if (NF != 3) exit 1
            for (field = 1; field <= NF; field++) {
                if ($field !~ number) exit 1
            }
            expected_time=(rows-1)*0.1
            difference=$1-expected_time; if (difference<0) difference=-difference
            if (difference>1e-6 || $2 < 0 || $3 < 0 || $3 > $2+1e-6) exit 1
            previous_time = $1
        }
        END {if (rows == 0) exit 1}
    ' "$xvg_file"; then
        echo "$xvg_file contains an empty, non-numeric, non-finite, or non-monotonic data series" >&2
        exit 5
    fi
    read -r count first last < <(
        awk '!/^[#@]/ && NF {count++; if (count==1) first=$1; last=$1}
             END {print count+0, first, last}' "$xvg_file"
    )
    [[ "$count" -eq "$expected_count" ]] || {
        echo "$xvg_file has $count data rows, expected $expected_count" >&2
        exit 5
    }
    [[ "$first" =~ ^-?[0-9]+([.][0-9]+)?([eE][-+]?[0-9]+)?$ \
       && "$last" =~ ^-?[0-9]+([.][0-9]+)?([eE][-+]?[0-9]+)?$ ]] || {
        echo "Cannot parse XVG time range: $xvg_file" >&2
        exit 5
    }
    awk -v first="$first" -v last="$last" -v expected="$expected_ns" 'BEGIN {
        first_difference=first; if (first_difference<0) first_difference=-first_difference;
        last_difference=last-expected; if (last_difference<0) last_difference=-last_difference;
        exit !(first_difference<=1e-6 && last_difference<=1e-6);
    }' || {
        echo "$xvg_file covers $first..$last ns, expected 0..$expected_ns ns" >&2
        exit 5
    }
}

assert_xvg_finite_rows() {
    local xvg_file="$1" expected_rows="$2" actual_rows
    if ! awk '
        BEGIN {
            number = "^[-+]?(([0-9]+([.][0-9]*)?)|([.][0-9]+))([eE][-+]?[0-9]+)?$"
        }
        !/^[#@]/ && NF {
            rows++
            if (NF != 2 || $1 < 0 || $2 < 0) exit 1
            for (field = 1; field <= NF; field++) {
                if ($field !~ number) exit 1
            }
        }
        END {if (rows == 0) exit 1}
    ' "$xvg_file"; then
        echo "$xvg_file contains an empty, non-numeric, or non-finite data series" >&2
        exit 5
    fi
    actual_rows="$(awk '!/^[#@]/ && NF {rows++} END {print rows+0}' "$xvg_file")"
    [[ "$actual_rows" -eq "$expected_rows" ]] || {
        echo "$xvg_file has $actual_rows data rows, expected $expected_rows" >&2
        exit 5
    }
}

assert_rmsd_complete() {
    local xvg_file="$1" count first last
    if ! awk '
        BEGIN {number="^[-+]?(([0-9]+([.][0-9]*)?)|([.][0-9]+))([eE][-+]?[0-9]+)?$"}
        !/^[#@]/ && NF {
            rows++
            if (NF != 2 || $1 !~ number || $2 !~ number || $2 < 0) exit 1
            expected=(rows-1)*0.1
            difference=$1-expected; if (difference<0) difference=-difference
            if (difference>1e-6) exit 1
            if (rows==1) first=$1; last=$1
        }
        END {if (rows==0) exit 1; print rows, first, last}
    ' "$xvg_file" >.rmsd_validation.tmp; then
        rm -f -- .rmsd_validation.tmp
        echo "$xvg_file must contain finite, nonnegative RMSD at every 0.1 ns sample" >&2
        exit 5
    fi
    read -r count first last <.rmsd_validation.tmp
    rm -f -- .rmsd_validation.tmp
    [[ "$count" -eq "$expected_count" ]] || {
        echo "$xvg_file has $count rows, expected $expected_count" >&2
        exit 5
    }
    awk -v first="$first" -v last="$last" -v expected="$expected_ns" 'BEGIN {
        first_diff=first; if (first_diff<0) first_diff=-first_diff;
        last_diff=last-expected; if (last_diff<0) last_diff=-last_diff;
        exit !(first_diff<=1e-6 && last_diff<=1e-6)
    }' || {
        echo "$xvg_file covers $first..$last ns, expected 0..$expected_ns ns" >&2
        exit 5
    }
}

assert_cluster_outputs() {
    local stem="$1"
    local id_file="cluster_id_${stem}.xvg"
    local sizes_file="cluster_sizes_${stem}.xvg"
    local representatives="clusters_${stem}.pdb"
    local id_summary size_summary id_rows first_time last_time max_id unique_ids size_id size_value
    local -a id_fields
    local cluster_count size_sum model_count atom_count expected_atoms matrix_x matrix_y

    id_summary="$(awk '
        BEGIN {number="^[-+]?(([0-9]+([.][0-9]*)?)|([.][0-9]+))([eE][-+]?[0-9]+)?$"}
        !/^[#@]/ && NF {
            if (NF < 2 || $1 !~ number || $2 !~ /^[1-9][0-9]*$/) exit 1
            rows++; if (rows == 1) first=$1
            expected_time=(rows-1)*100
            difference=$1-expected_time; if (difference<0) difference=-difference
            if (difference>1e-3) exit 1
            previous=$1; last=$1; if ($2 > maximum) maximum=$2; seen[$2]=1
            counts[$2]++
        }
        END {
            if (rows == 0) exit 1
            for (id in seen) unique++
            printf "%d %s %s %d %d", rows, first, last, maximum, unique
            for (id=1; id<=maximum; id++) printf " %d", counts[id]+0
            printf "\n"
        }
    ' "$id_file")" || {
        echo "Invalid cluster-id series: $id_file" >&2
        exit 5
    }
    read -r -a id_fields <<<"$id_summary"
    id_rows="${id_fields[0]}"; first_time="${id_fields[1]}"; last_time="${id_fields[2]}"
    max_id="${id_fields[3]}"; unique_ids="${id_fields[4]}"
    [[ "$id_rows" -eq "$expected_count" ]] || {
        echo "$id_file has $id_rows rows, expected $expected_count" >&2
        exit 5
    }
    awk -v first="$first_time" -v last="$last_time" -v expected="$expected_ps" 'BEGIN {
        first_diff=first; if (first_diff<0) first_diff=-first_diff;
        last_diff=last-expected; if (last_diff<0) last_diff=-last_diff;
        exit !(first_diff<=1e-3 && last_diff<=1e-3)
    }' || {
        echo "$id_file covers $first_time..$last_time ps, expected 0..$expected_ps ps" >&2
        exit 5
    }

    size_summary="$(awk '
        !/^[#@]/ && NF {
            if (NF < 2 || $1 !~ /^[1-9][0-9]*$/ || $2 !~ /^[1-9][0-9]*$/) exit 1
            rows++; if ($1 != rows) exit 1; total += $2
        }
        END {if (rows == 0) exit 1; print rows, total}
    ' "$sizes_file")" || {
        echo "Invalid cluster-size series: $sizes_file" >&2
        exit 5
    }
    read -r cluster_count size_sum <<<"$size_summary"
    [[ "$size_sum" -eq "$expected_count" && "$max_id" -eq "$cluster_count" \
       && "$unique_ids" -eq "$cluster_count" ]] || {
        echo "$sizes_file sums to $size_sum frames across $cluster_count clusters; expected $expected_count with ids 1..$cluster_count (max=$max_id unique=$unique_ids)" >&2
        exit 5
    }
    while read -r size_id size_value; do
        [[ "$size_value" -eq "${id_fields[$((size_id + 4))]}" ]] || {
            echo "Cluster $size_id size $size_value disagrees with assignment count ${id_fields[$((size_id + 4))]}" >&2
            exit 5
        }
    done < <(awk '!/^[#@]/ && NF {print $1, $2}' "$sizes_file")
    model_count="$(awk '/^MODEL([[:space:]]|$)/ {count++} END {print count+0}' "$representatives")"
    [[ "$model_count" -eq "$cluster_count" ]] || {
        echo "$representatives contains $model_count models, expected $cluster_count" >&2
        exit 5
    }
    atom_count="$(awk '/^ATOM([[:space:]]|$)/ {count++} END {print count+0}' "$representatives")"
    expected_atoms="${CLUSTER_EXPECTED_ATOMS[$stem]:-0}"
    [[ "$expected_atoms" -gt 0 && "$atom_count" -eq $((cluster_count * expected_atoms)) ]] || {
        echo "$representatives has $atom_count atoms; expected $cluster_count models x $expected_atoms" >&2
        exit 5
    }
    read -r matrix_x matrix_y < <(awk -F'"' '/^"[0-9]+ [0-9]+/ {split($2, fields, /[[:space:]]+/); print fields[1], fields[2]; exit}' "cluster_matrix_${stem}.xpm")
    [[ "$matrix_x" -eq "$expected_count" && "$matrix_y" -eq "$expected_count" ]] || {
        echo "cluster_matrix_${stem}.xpm is ${matrix_x:-?}x${matrix_y:-?}; expected ${expected_count}x${expected_count}" >&2
        exit 5
    }
    assert_xvg_finite_rows "rmsd_distribution_${stem}.xvg" \
        "$(awk '!/^[#@]/ && NF {rows++} END {print rows+0}' "rmsd_distribution_${stem}.xvg")"
}

assert_trajectory_complete "$trajectory" 237383

if [[ ! -s pbc_fixed.xtc ]]; then
    # trjconv prompts: centering group, then output group.
    run_with_input $'Protein\nProtein\n' \
        "$GMX_BIN" trjconv -s "$tpr" -f "$trajectory" -o pbc_fixed.xtc \
        -pbc mol -ur compact -center
fi
assert_trajectory_complete pbc_fixed.xtc 7952

if [[ ! -s aligned.xtc ]]; then
    # trjconv prompts: least-squares fit group, then output group.
    run_with_input $'Backbone\nProtein\n' \
        "$GMX_BIN" trjconv -s "$tpr" -f pbc_fixed.xtc -o aligned.xtc \
        -fit rot+trans
fi
assert_trajectory_complete aligned.xtc 7952
aligned_last_time="$trajectory_last_time"
aligned_last_frame="$trajectory_last_frame"

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
    assert_rmsd_complete "$output_file"
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
        assert_cluster_outputs "$stem"
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
    assert_cluster_outputs "$stem"
}

run_5vex_cluster_rmsd() {
    local cutoff="$1"
    local cluster_count
    local representatives="clusters_allosteric_backbone_${cutoff}nm.pdb"
    local output_file="rmsd_5vex_vs_clusters_allosteric_backbone_${cutoff}nm.xvg"
    local receipt=".${output_file}.complete"
    assert_file "$representatives"
    if [[ -e "$output_file" && ! -s "$receipt" ]]; then
        echo "5VEX RMSD output exists without a completion receipt: $output_file" >&2
        exit 4
    fi
    if [[ ! -s "$receipt" ]]; then
        # Both structures expose one unique 60-atom Backbone group.
        run_with_input $'Backbone\nBackbone\n' \
            "$GMX_BIN" rms -s "$reference_5vex" -f "$representatives" \
            -o "$output_file" -tu ps
        assert_file "$output_file"
    fi
    assert_file "$output_file"
    cluster_count="$(awk '!/^[#@]/ && NF {rows++} END {print rows+0}' \
        "cluster_sizes_allosteric_backbone_${cutoff}nm.xvg")"
    assert_xvg_finite_rows "$output_file" "$cluster_count"
    if [[ ! -s "$receipt" ]]; then
        run_cmd bash -c 'printf "complete\n" > "$1"' _ "$receipt"
    fi
}

declare -A CLUSTER_EXPECTED_ATOMS=(
    [backbone_0.2nm]=1473
    [tm6_tm7_backbone_0.1nm]=144
    [tm6_tm7_backbone_0.2nm]=144
    [allosteric_all_atoms_0.1nm]=337
    [allosteric_backbone_0.1nm]=60
    [allosteric_backbone_0.2nm]=60
    [allosteric_backbone_0.3nm]=60
)

run_rmsd "$analysis_dir/protein_backbone.ndx" Backbone rmsd_backbone.xvg
run_rmsd "$analysis_dir/tm6_ecl3_tm7_backbone.ndx" Backbone rmsd_tm6_ecl3_tm7_backbone.xvg
run_rmsd "$analysis_dir/tm6_tm7_backbone.ndx" Backbone rmsd_tm6_tm7_backbone.xvg
run_rmsd "$analysis_dir/allosteric_all_atoms_2A.ndx" Protein rmsd_allosteric_all_atoms.xvg
run_rmsd "$analysis_dir/allosteric_backbone_2A.ndx" Backbone rmsd_allosteric_backbone.xvg

# Standardized cross-branch sensitivity matrix. These cutoffs reproduce the
# archived distance-analysis protocol; they are not estimates of state count.
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

cluster_qc_tmp="$(mktemp --tmpdir=. .cluster_qc.tsv.XXXXXX)"
{
    printf 'stem\tframes\tclusters\tsize_sum\tmodels\tatoms_per_model\tmatrix_x\tmatrix_y\tstatus\n'
    for cluster_stem in "${!CLUSTER_EXPECTED_ATOMS[@]}"; do
        read -r cluster_count size_sum < <(
            awk '!/^[#@]/ && NF {rows++; total += $2} END {print rows+0, total+0}' \
                "cluster_sizes_${cluster_stem}.xvg"
        )
        model_count="$(awk '/^MODEL([[:space:]]|$)/ {count++} END {print count+0}' \
            "clusters_${cluster_stem}.pdb")"
        read -r matrix_x matrix_y < <(
            awk -F'"' '/^"[0-9]+ [0-9]+/ {split($2, fields, /[[:space:]]+/); print fields[1], fields[2]; exit}' \
                "cluster_matrix_${cluster_stem}.xpm"
        )
        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\tpass\n' \
            "$cluster_stem" "$expected_count" "$cluster_count" "$size_sum" \
            "$model_count" "${CLUSTER_EXPECTED_ATOMS[$cluster_stem]}" "$matrix_x" "$matrix_y"
    done | sort
} >"$cluster_qc_tmp"
mv -- "$cluster_qc_tmp" cluster_qc.tsv

# gmx sasa lets all non-solvent atoms (protein + membrane) define occlusion
# while reporting only the allosteric-site atoms. Use the original full-system
# trajectory: aligned.xtc intentionally contains Protein only and therefore
# cannot provide membrane coordinates. SASA is rotation/translation invariant;
# gmx sasa makes molecules whole and handles PBC itself. This observable is not
# the PLUMED bias CV.
sasa_index_tmp="$(mktemp --tmpdir=. .sasa_analysis.ndx.XXXXXX)"
{
    cat "$system_index"
    awk '
        /^\[[[:space:]]*Protein[[:space:]]*\]$/ {print "[ Allosteric_Site ]"; next}
        {print}
    ' "$analysis_dir/allosteric_all_atoms_2A.ndx"
} >"$sasa_index_tmp"
if [[ -e sasa_analysis.ndx ]]; then
    cmp -s "$sasa_index_tmp" sasa_analysis.ndx || {
        rm -f -- "$sasa_index_tmp"
        echo "Existing sasa_analysis.ndx differs from frozen selections; use a new run-id" >&2
        exit 4
    }
    rm -f -- "$sasa_index_tmp"
else
    mv -- "$sasa_index_tmp" sasa_analysis.ndx
fi
assert_file sasa_analysis.ndx

if [[ ! -s sasa_allosteric_site_non_solvent_surface.xvg ]]; then
    run_cmd "$GMX_BIN" sasa -s "$tpr" -f "$trajectory" -n sasa_analysis.ndx \
        -surface 'group "SOLU_MEMB"' -output 'group "Allosteric_Site"' \
        -o sasa_allosteric_site_non_solvent_surface.xvg \
        -probe 0.14 -ndots 24 -rmpbc -pbc -tu ns
fi
assert_xvg_complete sasa_allosteric_site_non_solvent_surface.xvg

protocol_tmp="$(mktemp --tmpdir=. .analysis_protocol.tsv.XXXXXX)"
{
    printf 'key\tvalue\n'
    printf 'protocol_version\t1\n'
    printf 'analysis_class\tstandardized_extension_not_historical_exact\n'
    printf 'simulation_stage\t%s\n' "$simulation_stage"
    printf 'expected_endpoint_ps\t%s\n' "$expected_ps"
    printf 'expected_frame_interval_ps\t100\n'
    printf 'expected_frame_count\t%s\n' "$expected_count"
    printf 'pbc_protocol\tmol_compact_center_Protein\n'
    printf 'alignment_protocol\trot+trans_Backbone_output_Protein\n'
    printf 'rmsd_reference\tsimulation_tpr_t0_normal100_parent_state\n'
    printf 'rmsd_fit_measure_groups\tprotein_backbone:Backbone/1473;tm6_ecl3_tm7:Backbone/183;tm6_tm7:Backbone/144;allosteric_all_atoms:Protein/337;allosteric_backbone:Backbone/60\n'
    printf 'rmsd_fit_semantics\teach_curve_refits_its_own_measurement_group_after_common_prealignment\n'
    printf 'cluster_method\tgromos\n'
    printf 'cluster_cutoff_matrix_nm\tbackbone:0.2;tm6_tm7_backbone:0.1,0.2;allosteric_all_atoms:0.1;allosteric_backbone:0.1,0.2,0.3\n'
    printf 'external_reference\t5VEX_allosteric_backbone_60_atoms\n'
    printf 'sasa_surface\tSOLU_MEMB_all_non_solvent_atoms\n'
    printf 'sasa_output\tAllosteric_Site_all_atoms_337\n'
    printf 'sasa_trajectory\toriginal_full_system_xtc\n'
    printf 'sasa_pbc\trmpbc_yes,pbc_yes\n'
    printf 'sasa_probe_nm\t0.14\n'
    printf 'sasa_ndots\t24\n'
    printf 'interpretation\tbiased_trajectory_geometry_not_unbiased_population_or_free_energy\n'
} >"$protocol_tmp"
mv -- "$protocol_tmp" analysis_protocol.tsv

qc_tmp="$(mktemp --tmpdir=. .analysis_qc.tsv.XXXXXX)"
{
    printf 'artifact\tmetric\texpected\tactual\tstatus\n'
    printf 'aligned.xtc\tendpoint_ps\t%s\t%s\tpass\n' "$expected_ps" "$aligned_last_time"
    printf 'aligned.xtc\tlast_frame_index\t%s\t%s\tpass\n' "$expected_last_frame" "$aligned_last_frame"
    for xvg_file in \
        rmsd_backbone.xvg \
        rmsd_tm6_ecl3_tm7_backbone.xvg \
        rmsd_tm6_tm7_backbone.xvg \
        rmsd_allosteric_all_atoms.xvg \
        rmsd_allosteric_backbone.xvg \
        sasa_allosteric_site_non_solvent_surface.xvg; do
        data_count="$(awk '!/^[#@]/ && NF {count++} END {print count+0}' "$xvg_file")"
        printf '%s\tdata_rows\t%s\t%s\tpass\n' "$xvg_file" "$expected_count" "$data_count"
    done
    printf 'aligned_reference.pdb\tprotein_atom_count\t7952\t%s\tpass\n' \
        "$(grep -c '^ATOM' aligned_reference.pdb)"
    printf 'cluster_qc.tsv\tvalidated_cluster_sets\t7\t%s\tpass\n' \
        "$(awk 'NR>1 {rows++} END {print rows+0}' cluster_qc.tsv)"
} >"$qc_tmp"
mv -- "$qc_tmp" analysis_qc.tsv

assert_file aligned.xtc
assert_file aligned_reference.pdb
assert_file rmsd_backbone.xvg
assert_file rmsd_tm6_ecl3_tm7_backbone.xvg
assert_file rmsd_tm6_tm7_backbone.xvg
assert_file rmsd_allosteric_all_atoms.xvg
assert_file rmsd_allosteric_backbone.xvg
assert_file clusters_allosteric_backbone_0.1nm.pdb
assert_file rmsd_5vex_vs_clusters_allosteric_backbone_0.1nm.xvg
assert_file rmsd_5vex_vs_clusters_allosteric_backbone_0.2nm.xvg
assert_file rmsd_5vex_vs_clusters_allosteric_backbone_0.3nm.xvg
assert_file sasa_analysis.ndx
assert_file sasa_allosteric_site_non_solvent_surface.xvg
assert_file analysis_protocol.tsv
assert_file analysis_qc.tsv
assert_file cluster_qc.tsv

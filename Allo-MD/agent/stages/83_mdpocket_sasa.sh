#!/usr/bin/env bash
set -Eeuo pipefail

[[ $# -eq 3 ]] || {
    echo "Usage: $0 POSTPROCESS_STAGE SIMULATION_STAGE EXPECTED_SNAPSHOT_COUNT" >&2
    exit 2
}
postprocess_stage="$1"
simulation_stage="$2"
expected_count="$3"

case "$postprocess_stage:$simulation_stage:$expected_count" in
    postprocess_sasa_site_10ns:sasa_site_10ns:101 \
    |postprocess_sasa_pocket_10ns:sasa_pocket_10ns:101 \
    |postprocess_sasa_pocket_100ns:sasa_pocket_100ns:1001) ;;
    *)
        echo "Unsupported SASA MDpocket target: $postprocess_stage / $simulation_stage / $expected_count" >&2
        exit 2
        ;;
esac

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=stages/lib/common.sh
source "$script_dir/lib/common.sh"

stage_begin

postprocess_dir="$AGENT_RUN_DIR/stages/$postprocess_stage"
simulation_dir="$AGENT_RUN_DIR/stages/$simulation_stage"
tpr="$simulation_dir/$simulation_stage.tpr"
trajectory="$postprocess_dir/aligned.xtc"
reference="$postprocess_dir/aligned_reference.pdb"
tools_dir="$AGENT_BUNDLE_ROOT/tools"
expected_last_frame=$((expected_count - 1))
expected_endpoint_ps=$((expected_last_frame * 100))

assert_file "$tpr"
assert_file "$trajectory"
assert_file "$reference"
assert_file "$postprocess_dir/analysis_protocol.tsv"
assert_file "$postprocess_dir/analysis_qc.tsv"

cd "$AGENT_STAGE_DIR"
mkdir -p frames global selected

assert_trajectory_complete() {
    local trajectory_file="$1" report actual_ps actual_frame actual_atoms
    record_command "$GMX_BIN" check -f "$trajectory_file"
    report="$("$GMX_BIN" check -f "$trajectory_file" 2>&1)" || {
        printf '%s\n' "$report" >>"$AGENT_CONSOLE_LOG"
        echo "Cannot inspect trajectory: $trajectory_file" >&2
        exit 5
    }
    printf '%s\n' "$report" >>"$AGENT_CONSOLE_LOG"
    actual_ps="$(tr '\r' '\n' <<<"$report" \
        | awk '/Last frame/ {for (i=1; i<=NF; i++) if ($i=="time") value=$(i+1)} END {print value}')"
    actual_frame="$(tr '\r' '\n' <<<"$report" \
        | awk '/Last frame/ {for (i=1; i<=NF; i++) if ($i=="frame") value=$(i+1)} END {print value}')"
    actual_atoms="$(tr '\r' '\n' <<<"$report" | awk '/^# Atoms/ {print $3; exit}')"
    [[ "$actual_ps" =~ ^-?[0-9]+([.][0-9]+)?([eE][-+]?[0-9]+)?$ \
       && "$actual_frame" =~ ^[0-9]+$ ]] || {
        echo "Cannot parse trajectory endpoint/frame count: $trajectory_file" >&2
        exit 5
    }
    awk -v actual="$actual_ps" -v expected="$expected_endpoint_ps" \
        'BEGIN {difference=actual-expected; if (difference<0) difference=-difference; exit !(difference<=1e-3)}' \
        || {
            echo "Trajectory ends at $actual_ps ps, expected $expected_endpoint_ps ps" >&2
            exit 5
        }
    [[ "$actual_frame" -eq "$expected_last_frame" ]] || {
        echo "Trajectory ends at frame $actual_frame, expected $expected_last_frame" >&2
        exit 5
    }
    [[ "$actual_atoms" =~ ^[0-9]+$ && "$actual_atoms" -eq 7952 ]] || {
        echo "Trajectory has ${actual_atoms:-unknown} atoms, expected 7952 protein atoms" >&2
        exit 5
    }
}

assert_trajectory_complete "$trajectory"

shopt -s nullglob
existing_frames=(frames/frame*.pdb)
shopt -u nullglob
frames_receipt="frames/.frames.complete"
if [[ ! -s "$frames_receipt" && ${#existing_frames[@]} -ne 0 ]]; then
    echo "Partial PDB frames exist without a completion receipt." >&2
    echo "Preserve the partial extraction and use a new run-id." >&2
    exit 4
fi
if [[ ! -s "$frames_receipt" ]]; then
    # The frozen SASA trajectories have one frame every 100 ps, including t=0.
    run_with_input $'Protein\n' \
        "$GMX_BIN" trjconv -s "$tpr" -f "$trajectory" \
        -o frames/frame.pdb -sep -dt 100 -tu ps
fi

# Three lists deliberately use paths relative to each consumer directory.
run_cmd "$PYTHON_BIN" "$tools_dir/make_snapshot_list.py" \
    --frames-dir frames --output snapshot_list.txt \
    --relative-to . --expected-count "$expected_count" --expected-atoms 7952 \
    --frame-interval-ps 100
if [[ ! -s "$frames_receipt" ]]; then
    run_cmd bash -c 'printf "complete\n" > "$1"' _ "$frames_receipt"
fi
run_cmd "$PYTHON_BIN" "$tools_dir/make_snapshot_list.py" \
    --frames-dir frames --output global/snapshot_list.txt \
    --relative-to global --expected-count "$expected_count"
run_cmd "$PYTHON_BIN" "$tools_dir/make_snapshot_list.py" \
    --frames-dir frames --output selected/snapshot_list.txt \
    --relative-to selected --expected-count "$expected_count"

if [[ ! -s global/.mdpocket_discovery.complete ]]; then
    shopt -s nullglob
    partial_global=(global/mdpout_*)
    shopt -u nullglob
    if (( ${#partial_global[@]} != 0 )); then
        echo "Partial global MDpocket outputs exist without a completion receipt." >&2
        echo "Use a new run-id; uncertain state will not be overwritten." >&2
        exit 4
    fi
    (
        cd global
        run_cmd "$MDPOCKET_BIN" --pdb_list snapshot_list.txt
    )
    assert_file global/mdpout_dens_grid.dx
    run_cmd bash -c 'printf "complete\n" > "$1"' _ global/.mdpocket_discovery.complete
fi
assert_file global/mdpout_dens_grid.dx

if [[ ! -s global/mdpout_dens_iso_0.5.pdb ]]; then
    run_cmd "$PYTHON_BIN" "$tools_dir/extract_iso_pdb.py" \
        --input global/mdpout_dens_grid.dx \
        --output global/mdpout_dens_iso_0.5.pdb --iso 0.5
fi

if [[ ! -s selected_grid_iso_0.5_1A_pocket.pdb ]]; then
    run_cmd "$PYTHON_BIN" "$tools_dir/select_pocket_grid.py" \
        --grid global/mdpout_dens_iso_0.5.pdb \
        --reference "$reference" \
        --output selected_grid_iso_0.5_1A_pocket.pdb \
        --residues 354,355,357,358,365,369,410-417 --cutoff 1.0
fi

if [[ ! -s selected/.mdpocket_selected.complete ]]; then
    shopt -s nullglob
    partial_selected=(selected/mdpout_*)
    shopt -u nullglob
    if (( ${#partial_selected[@]} != 0 )); then
        echo "Partial selected-pocket MDpocket outputs exist without a completion receipt." >&2
        echo "Use a new run-id; uncertain state will not be overwritten." >&2
        exit 4
    fi
    (
        cd selected
        run_cmd "$MDPOCKET_BIN" --pdb_list snapshot_list.txt \
            --selected_pocket ../selected_grid_iso_0.5_1A_pocket.pdb
    )
    assert_file selected/mdpout_descriptors.txt
    # This receipt records MDpocket completion only; CSV/QC can be regenerated.
    run_cmd bash -c 'printf "complete\n" > "$1"' _ selected/.mdpocket_selected.complete
fi
assert_file selected/mdpout_descriptors.txt

# CSV and JSON QC are mandatory. PNG remains optional when matplotlib is absent.
# Auxiliary MDpocket descriptor NaN/Inf values are reported, never interpolated;
# snapshot and pocket volume remain strictly finite and validated.
run_cmd "$PYTHON_BIN" "$tools_dir/plot_pocket_volume.py" \
    --input selected/mdpout_descriptors.txt \
    --csv-output pocket_volume.csv \
    --qc-output pocket_volume_qc.json \
    --output pocket_volume.png \
    --frame-interval-ps 100 --expected-count "$expected_count" \
    --require-historical-schema

protocol_tmp="$(mktemp --tmpdir=. .mdpocket_analysis_protocol.tsv.XXXXXX)"
{
    printf 'key\tvalue\n'
    printf 'protocol_version\t1\n'
    printf 'analysis_class\tstandardized_extension_not_historical_exact\n'
    printf 'postprocess_stage\t%s\n' "$postprocess_stage"
    printf 'simulation_stage\t%s\n' "$simulation_stage"
    printf 'snapshot_interval_ps\t100\n'
    printf 'snapshot_count\t%s\n' "$expected_count"
    printf 'global_density_isovalue\t0.5\n'
    printf 'selected_grid_cutoff_A\t1.0\n'
    printf 'selected_residues\t354,355,357,358,365,369,410-417\n'
    printf 'descriptor_schema\thistorical_42_column\n'
    printf 'nonfinite_auxiliary_policy\treport_without_interpolation_or_imputation\n'
    printf 'required_finite_fields\tsnapshot,pock_volume\n'
    printf 'interpretation\tpocket_geometry_on_biased_trajectory_not_unbiased_population\n'
} >"$protocol_tmp"
mv -- "$protocol_tmp" mdpocket_analysis_protocol.tsv

assert_file snapshot_list.txt
assert_file global/snapshot_list.txt
assert_file selected/snapshot_list.txt
assert_file frames/frame0.pdb
assert_file "frames/frame${expected_last_frame}.pdb"
assert_file "$frames_receipt"
assert_file global/mdpout_dens_grid.dx
assert_file global/mdpout_dens_iso_0.5.pdb
assert_file selected_grid_iso_0.5_1A_pocket.pdb
assert_file selected/mdpout_descriptors.txt
assert_file pocket_volume.csv
assert_file pocket_volume_qc.json
assert_file mdpocket_analysis_protocol.tsv

#!/usr/bin/env bash
set -Eeuo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=stages/lib/common.sh
source "$script_dir/lib/common.sh"

stage_begin

postprocess_dir="$AGENT_RUN_DIR/stages/postprocess_distance_50ns"
simulation_dir="$AGENT_RUN_DIR/stages/distance_metad_50ns"
tpr="$simulation_dir/distance_metad_50ns.tpr"
trajectory="$postprocess_dir/aligned.xtc"
reference="$postprocess_dir/aligned_reference.pdb"
tools_dir="$AGENT_BUNDLE_ROOT/tools"

assert_file "$tpr"
assert_file "$trajectory"
assert_file "$reference"

cd "$AGENT_STAGE_DIR"
mkdir -p frames global selected

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
    # 50 ns / 100 ps + the t=0 frame = 501 snapshots, frame0..frame500.
    run_with_input $'Protein\n' \
        "$GMX_BIN" trjconv -s "$tpr" -f "$trajectory" \
        -o frames/frame.pdb -sep -dt 100 -tu ps
fi

# Three lists deliberately use paths relative to the directory in which each
# consumer runs.  This keeps the run directory relocatable.
run_cmd "$PYTHON_BIN" "$tools_dir/make_snapshot_list.py" \
    --frames-dir frames --output snapshot_list.txt \
    --relative-to . --expected-count 501 --expected-atoms 7952 \
    --frame-interval-ps 100
if [[ ! -s "$frames_receipt" ]]; then
    run_cmd bash -c 'printf "complete\n" > "$1"' _ "$frames_receipt"
fi
run_cmd "$PYTHON_BIN" "$tools_dir/make_snapshot_list.py" \
    --frames-dir frames --output global/snapshot_list.txt \
    --relative-to global --expected-count 501
run_cmd "$PYTHON_BIN" "$tools_dir/make_snapshot_list.py" \
    --frames-dir frames --output selected/snapshot_list.txt \
    --relative-to selected --expected-count 501

if [[ ! -s global/.mdpocket_discovery.complete ]]; then
    shopt -s nullglob
    partial_global=(global/mdpout_*)
    shopt -u nullglob
    if (( ${#partial_global[@]} != 0 )); then
        echo "Partial global MDpocket outputs exist without mdpout_dens_grid.dx." >&2
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
        echo "Partial selected-pocket MDpocket outputs exist without descriptors." >&2
        echo "Use a new run-id; uncertain state will not be overwritten." >&2
        exit 4
    fi
    (
        cd selected
        run_cmd "$MDPOCKET_BIN" --pdb_list snapshot_list.txt \
            --selected_pocket ../selected_grid_iso_0.5_1A_pocket.pdb
    )
fi
assert_file selected/mdpout_descriptors.txt

# CSV is always produced.  PNG is additionally produced when matplotlib is
# installed; plotting is not a scientific completion condition.
run_cmd "$PYTHON_BIN" "$tools_dir/plot_pocket_volume.py" \
    --input selected/mdpout_descriptors.txt \
    --csv-output pocket_volume.csv --qc-output pocket_volume_qc.json \
    --output pocket_volume.png \
    --frame-interval-ps 100 --expected-count 501 \
    --require-historical-schema
if [[ ! -s selected/.mdpocket_selected.complete ]]; then
    run_cmd bash -c 'printf "complete\n" > "$1"' _ selected/.mdpocket_selected.complete
fi

assert_file snapshot_list.txt
assert_file global/snapshot_list.txt
assert_file selected/snapshot_list.txt
assert_file frames/frame0.pdb
assert_file frames/frame500.pdb
assert_file "$frames_receipt"
assert_file global/mdpout_dens_grid.dx
assert_file global/mdpout_dens_iso_0.5.pdb
assert_file selected_grid_iso_0.5_1A_pocket.pdb
assert_file selected/mdpout_descriptors.txt
assert_file pocket_volume.csv
assert_file pocket_volume_qc.json

import os
import re
import numpy as np
import pandas as pd
from Bio import PDB

def calculate_center(coords):
    return np.mean(coords, axis=0)

def get_structure_center(pdb_path):
    parser = PDB.PDBParser(QUIET=True)
    structure = parser.get_structure("model", pdb_path)
    coords = []
    for model in structure:
        for chain in model:
            for residue in chain:
                for atom in residue:
                    coords.append(atom.coord)
    return calculate_center(np.array(coords)) if coords else None

def find_group_folder(group_id, search_root):
    for name in os.listdir(search_root):
        if group_id in name:
            full_path = os.path.join(search_root, name)
            if os.path.isdir(full_path):
                return full_path
    return None

def find_closest_pocket(center, pocket_csv_path):
    df = pd.read_csv(pocket_csv_path)
    pocket_coords = df[["center_x", "center_y", "center_z"]].values
    dists = np.linalg.norm(pocket_coords - center, axis=1)
    min_idx = np.argmin(dists)
    return df.iloc[min_idx]["pocket_name"], dists[min_idx]

base_path = "./AF_ClaSeq/case/GPL1/6x18_chianR_R/run/01_iterative_shuffling/Iteration_6"

for i in range(1, 11):

    pdb_folder = os.path.join(base_path, f"shuffle_{i}_pocketminer_holo_cluster/eps6_min_samples2")
    group_root_folder = os.path.join(base_path, f"shuffle_{i}_fpocket")
    output_csv = os.path.join(base_path, f"shuffle_{i}_group_cluster_fpocket_distance_results.csv")

    if not os.path.exists(pdb_folder):
        continue

    if not os.path.exists(group_root_folder):
        continue

    results = []

    for filename in os.listdir(pdb_folder):
        if not filename.endswith(".pdb") or "noise_residues" in filename:
            continue

        match = re.match(r"(group_\d+)_.*_cluster_(\d+)", filename)
        if not match:
            continue

        group_id, cluster_id = match.groups()
        pdb_path = os.path.join(pdb_folder, filename)
        center = get_structure_center(pdb_path)

        if center is None:
            continue

        group_folder = find_group_folder(group_id, group_root_folder)
        if not group_folder:
            continue

        pocket_csv_path = os.path.join(group_folder, "pocket_centers.csv")
        if not os.path.exists(pocket_csv_path):
            continue

        pocket_name, min_dist = find_closest_pocket(center, pocket_csv_path)

        results.append({
            "group_cluster": f"{group_id}_cluster_{cluster_id}",
            "closest_pocket": pocket_name,
            "min_distance": round(min_dist, 3)
        })

    if results:
        df_out = pd.DataFrame(results)
        df_out.to_csv(output_csv, index=False)


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

# def find_group_folder(group_id, search_root):
#     for name in os.listdir(search_root):
#         if group_id in name:
#             full_path = os.path.join(search_root, name)
#             if os.path.isdir(full_path):
#                 return full_path
#     return None

def find_group_folder(group_id, search_root):

    if not group_id.startswith('group_'):
        group_id = 'group_' + group_id
    
    for name in os.listdir(search_root):
        if name.startswith(group_id + '_'):
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


# base_path = "./AF_ClaSeq/case/GPL1/6x18_chianR_R/run/01_iterative_shuffling/Iteration_1"



pdb_folder = './AF_ClaSeq/case/PCKS9/4ne9/run/04_recompile/pocket_min_distance/prediction/bin_7_pocketminer_predict_residues_cluster/eps6_min_samples2'
group_root_folder = './AF_ClaSeq/case/PCKS9/4ne9/run/04_recompile/pocket_min_distance/prediction/bin_7_fpocket'
output_csv = os.path.join('./AF_ClaSeq/case/PCKS9/4ne9/run/04_recompile/pocket_min_distance/prediction/bin_7_pocketminer_predict_residues_cluster_eps6/group_cluster_fpocket_distance_results.csv')



results = []

for filename in os.listdir(pdb_folder):
    if not filename.endswith(".pdb") or "noise_residues" in filename:
        continue

    # if group_id != 'group_2':
    #     continue
    pdb_path = os.path.join(pdb_folder, filename)
    center = get_structure_center(pdb_path)

    if center is None:
        continue

    pocket_file =  filename.split("_cluster_")[0] + "_out"
    pdb_name = filename.split("_cluster_")[0]

    pocket_csv_path = os.path.join('./AF_ClaSeq/case/PCKS9/4ne9/run/04_recompile/pocket_min_distance/prediction/bin_7_fpocket',pocket_file, "pocket_centers.csv")
    if not os.path.exists(pocket_csv_path):
        continue

    pocket_name, min_dist = find_closest_pocket(center, pocket_csv_path)

    results.append({
        "pdb_file":pdb_name ,
        "closest_pocket": pocket_name,
        "min_distance": round(min_dist, 3)
    })

if results:
    df_out = pd.DataFrame(results)
    df_out.to_csv(output_csv, index=False)


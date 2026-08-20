import os
import numpy as np
import pandas as pd
from Bio import PDB

def calculate_center(coords):
    return np.mean(coords, axis=0)

def process_seed_folder(seed_folder):
    pockets_dir = os.path.join(seed_folder, "pockets")
    if not os.path.isdir(pockets_dir):
        return

    pocket_centers = []
    pdb_parser = PDB.PDBParser(QUIET=True)

    for file in os.listdir(pockets_dir):
        if file.endswith(".pdb"):
            pdb_path = os.path.join(pockets_dir, file)
            try:
                structure = pdb_parser.get_structure("pocket", pdb_path)
                coords = []
                for model in structure:
                    for chain in model:
                        for residue in chain:
                            for atom in residue:
                                coords.append(atom.coord)
                if coords:
                    coords = np.array(coords)
                    center = calculate_center(coords)
                    pocket_centers.append([file, *center])
            except Exception as e:
                 print(f" Wrong {pdb_path}: {e}")


    if pocket_centers:
        df = pd.DataFrame(pocket_centers, columns=["pocket_name", "center_x", "center_y", "center_z"])
        output_csv = os.path.join(seed_folder, "pocket_centers.csv")
        df.to_csv(output_csv, index=False)
    else:
        print(f"Wrong {seed_folder} no valid pocket flie")


parent_dir = './AF_ClaSeq/case/PCKS9/4ne9/run/04_recompile/pocket_min_distance/control_prediction/bin_7_fpocket'

for name in os.listdir(parent_dir):
    full_path = os.path.join(parent_dir, name)
    if os.path.isdir(full_path) and name.endswith("_out"):
        process_seed_folder(full_path)

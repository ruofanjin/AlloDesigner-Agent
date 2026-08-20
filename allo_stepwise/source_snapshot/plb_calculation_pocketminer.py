import os
import sys
import pandas as pd
from Bio.PDB import PDBParser

ra_values = {
    "ALA": 0.701, "CYS": 1.65, "ASP": 1.233, "GLU": 1.548, "PHE": 1.977,
    "GLY": 0.0, "HIS": 1.84, "ILE": 1.821, "LYS": 1.964, "LEU": 1.746,
    "MET": 1.936, "ASN": 1.517, "PRO": 1.221, "GLN": 1.678, "ARG": 2.099,
    "SER": 1.015, "THR": 1.239, "VAL": 1.655, "TRP": 2.146, "TYR": 1.672
}


def extract_residues_from_pdb(pdb_path):
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("structure", pdb_path)
    residue_names = []

    for model in structure:
        for chain in model:
            for residue in chain:
                hetfield, resnum, icode = residue.id
                if hetfield == ' ':
                    resname = residue.get_resname().upper()
                    residue_names.append(resname)
    return residue_names


def compute_plb_from_residues(residue_list):
    residue_counts = {}
    for resname in residue_list:
        if resname in ra_values:
            residue_counts[resname] = residue_counts.get(resname, 0) + 1

    plb = sum(count * ra_values[resname] for resname, count in residue_counts.items())
    return plb


def main(pdb_dir):
    results = []

    for filename in os.listdir(pdb_dir):
        if filename.endswith(".pdb"):
            pdb_path = os.path.join(pdb_dir, filename)
            try:
                residues = extract_residues_from_pdb(pdb_path)
                plb_score = compute_plb_from_residues(residues)
                results.append({"filename": filename, "plb_score": round(plb_score, 3)})
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    df = pd.DataFrame(results)
    df = df.sort_values(by="plb_score", ascending=False)
    output_csv = os.path.join(pdb_dir, "plb_scores2.csv")
    df.to_csv(output_csv, index=False)
    print(f"Saved PLB scores to {output_csv}")


if __name__ == "__main__":
    pdb_dir = './binding_sites_prediction/pocketminer_cluster/5vex/eps6_min_samples4'
    main(pdb_dir)

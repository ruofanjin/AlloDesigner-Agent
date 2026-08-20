import os
import pandas as pd
from Bio.PDB import PDBParser
from collections import defaultdict, Counter
import csv
def extract_residue_ids_from_pdb(pdb_path):
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("temp", pdb_path)
    residue_ids = []
    
    for model in structure:
        for chain in model:
            for residue in chain:
                hetfield, resnum, icode = residue.id
                if hetfield == ' ':
                    resname = residue.get_resname().strip().upper()

                    unique_id = f"{resname}-{resnum}"
                    residue_ids.append(unique_id)
    return tuple(sorted(residue_ids))

def find_frequent_residue_sets(base_dir, pdb_dir_template, threshold=2):
    residue_set_counter = Counter()
    
    for i in range(1, 11):
        input_csv = os.path.join(base_dir, f"pocketminer_cluster_deepallo_score_shuffle_{i}_filtered.csv")
        pdb_dir = pdb_dir_template.format(i=i)

        if not os.path.exists(input_csv):
            continue

        df = pd.read_csv(input_csv)
        df[['group', 'cluster']] = df['group_cluster'].str.extract(r'group_(\d+)_cluster_(\d+)')
        
        for _, row in df.iterrows():
            group = row['group']
            cluster = row['cluster']
            pdb_file = os.path.join(pdb_dir, f"group_{group}_unrelaxed_rank_001_alphafold2_ptm_model_1_seed_042_cluster_{cluster}.pdb")
            
            if not os.path.exists(pdb_file):
                continue
            
            try:
                residue_set = extract_residue_ids_from_pdb(pdb_file)
                if residue_set:
                    residue_set_counter[residue_set] += 1
            except Exception as e:
                print(f"wrong {pdb_file}: {e}")
    
    output_csv = os.path.join(base_dir, "frequent_residue_sets.csv")
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["count", "residues"])  
        
        for res_set, count in residue_set_counter.most_common():
            if count >= threshold:
                writer.writerow([count, ";".join(res_set)])

if __name__ == "__main__":
    base_dir = "./AF_ClaSeq/case/PCKS9/4ne9/run/01_iterative_shuffling/Iteration_1/pocketminer_cluster_deepallo_score_eps4.5"
    pdb_dir_template = "./AF_ClaSeq/case/PCKS9/4ne9/run/01_iterative_shuffling/Iteration_1/shuffle_{i}_pocketminer_predict_residues_cluster/eps4.5_min_samples2"

    find_frequent_residue_sets(base_dir, pdb_dir_template, threshold=1)

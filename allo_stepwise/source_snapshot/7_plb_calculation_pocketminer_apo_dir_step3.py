import os
import pandas as pd
from Bio.PDB import PDBParser
from collections import defaultdict

RA_VALUES = {
    "ALA": 0.701, "CYS": 1.65, "ASP": 1.233, "GLU": 1.548, "PHE": 1.977,
    "GLY": 0.0, "HIS": 1.84, "ILE": 1.821, "LYS": 1.964, "LEU": 1.746,
    "MET": 1.936, "ASN": 1.517, "PRO": 1.221, "GLN": 1.678, "ARG": 2.099,
    "SER": 1.015, "THR": 1.239, "VAL": 1.655, "TRP": 2.146, "TYR": 1.672
}

def extract_residues_from_pdb(pdb_path):
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("temp", pdb_path)
    residue_names = []
    
    for model in structure:
        for chain in model:
            for residue in chain:
                hetfield, resnum, icode = residue.id
                if hetfield == ' ':
                    resname = residue.get_resname().strip().upper()
                    if resname in RA_VALUES:
                        residue_names.append(resname)
    return residue_names

def compute_plb_score(residue_list):
    residue_counts = defaultdict(int)
    for resname in residue_list:
        residue_counts[resname] += 1
    
    plb = sum(count * RA_VALUES[resname] for resname, count in residue_counts.items())
    return round(plb, 3)

def process_shuffle_files(base_dir, output_dir):

    os.makedirs(output_dir, exist_ok=True)
    
    for i in range(1, 11):
        input_csv = os.path.join(base_dir, f"pocketminer_cluster_deepallo_score_shuffle_{i}_filtered.csv")
        output_csv = os.path.join(output_dir, f"pocketminer_cluster_deepallo_plb_shuffle_{i}.csv")
        
        if not os.path.exists(input_csv):
            continue
        
        df = pd.read_csv(input_csv)
        
        df[['group', 'cluster']] = df['group_cluster'].str.extract(r'group_(\d+)_cluster_(\d+)')
        df['group'] = df['group'].astype(int)
        df['cluster'] = df['cluster'].astype(int)
        
        df['plb_score'] = 0.0
        df['pdb_path'] = ""
        
        for index, row in df.iterrows():
            group_id = row['group']
            cluster_id = row['cluster']
            
            # pdb_file = os.path.join(f"./AF_ClaSeq/case/GPL1/6x18_chianR_R/run/01_iterative_shuffling/Iteration_1/shuffle_{i}_pocketminer_predict_residues_cluster/eps6_min_samples2"
            #         ,
            #         f"group_{group_id}_unrelaxed_rank_001_alphafold2_ptm_model_1_seed_042_cluster_{cluster_id}.pdb"
            #     )

            pdb_file = os.path.join(f"./AF_ClaSeq/case/PCKS9/4ne9/run/01_iterative_shuffling/Iteration_1/shuffle_{i}_pocketminer_predict_residues_cluster/eps4.5_min_samples2"
                ,
                f"group_{group_id}_unrelaxed_rank_001_alphafold2_ptm_model_1_seed_042_cluster_{cluster_id}.pdb"
            )
                
            if not os.path.exists(pdb_file):
                continue
            
            try:
                residues = extract_residues_from_pdb(pdb_file)
                plb_score = compute_plb_score(residues)
                
                df.at[index, 'plb_score'] = plb_score
                df.at[index, 'pdb_path'] = pdb_file
                
            except Exception as e:
                continue
    
        df.to_csv(output_csv, index=False)


if __name__ == "__main__":
    # base_directory = "./AF_ClaSeq/case/GPL1/6x18_chianR_R/run/01_iterative_shuffling/Iteration_1/pocketminer_cluster_deepallo_score/"
    #base_directory = "./AF_ClaSeq/case/PCKS9/4ne9/run/01_iterative_shuffling/Iteration_1/pocketminer_cluster_deepallo_score/"
    base_directory = './AF_ClaSeq/case/PCKS9/4ne9/run/01_iterative_shuffling/Iteration_1/pocketminer_cluster_deepallo_score_eps4.5'
    output_directory = os.path.join(base_directory, "plb_score")
    
    process_shuffle_files(base_directory, output_directory)
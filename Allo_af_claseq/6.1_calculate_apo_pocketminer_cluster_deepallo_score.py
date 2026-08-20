import os
import glob
import pandas as pd
from collections import defaultdict
from Bio.PDB import PDBParser

def extract_residues_from_pdb(pdb_file):
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure('temp', pdb_file)
    residues = set()
    
    for model in structure:
        for chain in model:
            for residue in chain:
                residues.add(residue.id[1]) 
    
    return residues

def process_shuffle_files(base_dir, top_k=3):

    residue_counts = defaultdict(int)
    total_structures = 0
    

    for i in range(1, 11):
        csv_file = os.path.join(base_dir, f"pocketminer_cluster_deepallo_score_shuffle_{i}_filtered.csv")
        
        if not os.path.exists(csv_file):
            continue
        
        df = pd.read_csv(csv_file)
        
        df[['group', 'cluster']] = df['group_cluster'].str.extract(r'group_(\d+)_cluster_(\d+)')
        df['group'] = df['group'].astype(int)
        df['cluster'] = df['cluster'].astype(int)
        
        grouped = df.groupby('group')
        
        for group_id, group_df in grouped:
            top_clusters = group_df.sort_values('deepallo_score', ascending=False).head(top_k)
            
            for _, row in top_clusters.iterrows():
                cluster_id = row['cluster']
                
                # pdb_file = os.path.join(f"./AF_ClaSeq/case/GPL1/6x18_chianR_R/run/01_iterative_shuffling/Iteration_1/shuffle_{i}_pocketminer_predict_residues_cluster/eps6_min_samples2"
                #     ,
                #     f"group_{group_id}_unrelaxed_rank_001_alphafold2_ptm_model_1_seed_042_cluster_{cluster_id}.pdb"
                # )
                
                pdb_file = os.path.join(f"./AF_ClaSeq/case/PCKS9/4ne9/run/01_iterative_shuffling/Iteration_1/shuffle_{i}_pocketminer_predict_residues_cluster/eps4.5_min_samples2"
                    ,
                    f"group_{group_id}_unrelaxed_rank_001_alphafold2_ptm_model_1_seed_042_cluster_{cluster_id}.pdb"
                )
                

                if not os.path.exists(pdb_file):
                    continue
                

                residues = extract_residues_from_pdb(pdb_file)
                total_structures += 1
                
                for res in residues:
                    residue_counts[res] += 1
    
    residue_prob = {}
    for res, count in residue_counts.items():
        residue_prob[res] = count / total_structures
    
    return residue_prob


if __name__ == "__main__":
    # base_directory = "./AF_ClaSeq/case/GPL1/6x18_chianR_R/run/01_iterative_shuffling/Iteration_1/pocketminer_cluster_deepallo_score"  
    base_directory = "./AF_ClaSeq/case/PCKS9/4ne9/run/01_iterative_shuffling/Iteration_1/pocketminer_cluster_deepallo_score_eps4.5"  
    top_k = 7  
    
    residue_probabilities = process_shuffle_files(base_directory, top_k)
    
    output_file = os.path.join(base_directory, f"residue_probabilities_top_{top_k }.csv")
    prob_df = pd.DataFrame.from_dict(residue_probabilities, orient='index', columns=['probability'])
    prob_df.index.name = 'residue_number'
    prob_df.to_csv(output_file)
    
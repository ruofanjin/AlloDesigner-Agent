import os
import pandas as pd
from glob import glob

def extract_a3m_sequences_with_headers(a3m_path):

    sequences = []
    with open(a3m_path, "r") as f:
        lines = f.readlines()
    
    for i in range(0, len(lines)):
        line = lines[i].strip()
        if line.startswith(">") and i + 1 < len(lines):
            header = line
            seq = lines[i + 1].strip()
            sequences.append((header, seq))
    return sequences

root_dir = "./AF_ClaSeq/case/1HZB/run/01_iterative_shuffling/Iteration_3"  

all_seq_dict = {}

for i in range(1, 11):
    csv_path = os.path.join(root_dir, f"selct_cluster_group_chi1_chi2_dist0.2/cluster_centers_shuffle{i}_chi1_chi2_dist0.2.csv")
    shuffle_dir = os.path.join(root_dir, f"shuffle_{i}")
    
    if not os.path.exists(csv_path):
        print(f"Missing CSV: {csv_path}")
        continue
    if not os.path.exists(shuffle_dir):
        print(f"Missing folder: {shuffle_dir}")
        continue

    df = pd.read_csv(csv_path)
    
    for pdb_file in df["PDB_File"]:
        group_id = pdb_file.split("_")[1]  # e.g., 1000 from group_1000...
        a3m_path = os.path.join(shuffle_dir, f"group_{group_id}.a3m")

        if not os.path.exists(a3m_path):
            continue
        
        for header, seq in extract_a3m_sequences_with_headers(a3m_path):
            if seq not in all_seq_dict:
                all_seq_dict[seq] = header 

output_path = os.path.join(root_dir, "combined_filtered_iteration_3_chi1_chi2_dist0.2.a3m")
with open(output_path, "w") as out:
    for seq, header in all_seq_dict.items():
        out.write(f"{header}\n{seq}\n")



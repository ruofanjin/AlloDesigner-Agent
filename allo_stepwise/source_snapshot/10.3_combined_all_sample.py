import os
import pandas as pd

base_path = "./AF_ClaSeq/case/PCKS9/4ne9/run/02_m_fold_sampling/round_1/02_sampling/pocketminer_predict_residues_cluster_eps6"
output_file = os.path.join(base_path, "all_sampling_avg_distance_combined.csv")

all_data = []

for i in range(1, 38):
    input_csv = os.path.join(base_path, f"sampling_{i}_same_group_fpocket_distance_results_avg_distance.csv")
    
    if not os.path.exists(input_csv):
        continue

    df = pd.read_csv(input_csv)
    
    if "group_id" not in df.columns or "min_distance" not in df.columns:
        continue

    df["sampling_group_id"] = df["group_id"].apply(lambda x: f"sampling_{i}_{x}")
    
    df = df[["sampling_group_id", "min_distance"]]
    all_data.append(df)

if all_data:
    final_df = pd.concat(all_data, ignore_index=True)
    final_df.to_csv(output_file, index=False)
 

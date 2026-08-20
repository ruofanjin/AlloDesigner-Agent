import pandas as pd
import re
import os

base_path = "./AF_ClaSeq/case/PCKS9/4ne9/run/02_m_fold_sampling/round_1/02_sampling/pocketminer_predict_residues_cluster_eps6"

for i in range(1, 38):
    input_csv = os.path.join(base_path, f"sampling_{i}_group_cluster_fpocket_distance_results.csv")
    output_csv = os.path.join(base_path, f"sampling_{i}_same_group_fpocket_distance_results_avg_distance.csv")

    if not os.path.exists(input_csv):
        continue

    df = pd.read_csv(input_csv)

    if "group_cluster" not in df.columns or "min_distance" not in df.columns:
        continue

    df["group_id"] = df["group_cluster"].apply(lambda x: re.match(r"(group_\d+)", x).group(1))

    df_avg = df.groupby("group_id")["min_distance"].mean().reset_index()

    df_avg.to_csv(output_csv, index=False)

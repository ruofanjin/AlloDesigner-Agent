import pandas as pd
import re


input_csv = "./AF_ClaSeq/case/GPL1/6x18_chianR_R/run/01_iterative_shuffling/Iteration_1/shuffle_4_group_cluster_fpocket_distance_results.csv"
output_csv = "./AF_ClaSeq/case/GPL1/6x18_chianR_R/run/01_iterative_shuffling/Iteration_1/shuffle_4_same_group_fpocket_distance_results_avg_distance.csv"

df = pd.read_csv(input_csv)

df["group_id"] = df["group_cluster"].apply(lambda x: re.match(r"(group_\d+)", x).group(1))

df_avg = df.groupby("group_id")["min_distance"].mean().reset_index()

df_avg.to_csv(output_csv, index=False)


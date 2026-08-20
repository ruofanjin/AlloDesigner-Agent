import pandas as pd

df = pd.read_csv("./AF_ClaSeq/case/PCKS9/4ne9/run/04_recompile/pocket_min_distance/prediction/bin_7_pocketminer_predict_residues_cluster_eps6/group_cluster_fpocket_distance_results.csv")

result = df.groupby("pdb_file", as_index=False)["min_distance"].mean()



result.to_csv("./AF_ClaSeq/case/PCKS9/4ne9/run/04_recompile/pocket_min_distance/prediction/bin_7_pocketminer_predict_residues_cluster_eps6/merge_same_pdb_cluster_fpocket_distance_results.csv.csv", index=False)  # 如需保存为新文件

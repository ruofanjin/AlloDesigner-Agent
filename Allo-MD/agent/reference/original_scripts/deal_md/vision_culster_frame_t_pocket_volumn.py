import pandas as pd
import matplotlib.pyplot as plt

# 1. 读取包含 frame_t 的 CSV 文件
cluster_csv = '/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/deal_md/distance/50ns_unbiased_md/biased_md/50ns/cluster_protein_backbone_allosteric_site_2A_cutoff0.1/cluster_frame_map.csv'  # 你的cluster frame_t文件
df_cluster = pd.read_csv(cluster_csv)

# 提取帧号（frame = frame_t / 100 并取整数）
df_cluster['frame'] = df_cluster['frame_t'].astype(float).div(100).astype(int)

# 2. 读取 pocket 数据的 txt 文件（含列名）
pocket_txt = '/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/mdpocket/plumed_distance/50ns_unbiased_md/biased_md/50ns/output/select_atoms/1A/mdpout_descriptors.txt'
df_pocket = pd.read_csv(pocket_txt, delim_whitespace=True)

# 3. 提取对应帧的 pock_volume
merged_df = df_cluster.merge(df_pocket[['snapshot', 'pock_volume']], left_on='frame', right_on='snapshot', how='left')

merged_df = merged_df.sort_values(by='snapshot').reset_index(drop=True)

# 4. 保存为新 CSV
merged_df[['frame', 'pock_volume']].to_csv('/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/deal_md/distance/50ns_unbiased_md/biased_md/50ns/cluster_protein_backbone_allosteric_site_2A_cutoff0.1/cluster_frame_map_pock_volume.csv', index=False)

# 5. 可视化保存为 PNG
plt.figure(figsize=(8, 5))
plt.plot(merged_df['frame'], merged_df['pock_volume'], marker='o', linestyle='-', color='teal')
plt.xlabel('Frame')
plt.ylabel('Pock Volume')
plt.title('Pock Volume over Cluster Representative Frames')
plt.grid(True)
plt.tight_layout()
plt.savefig('/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/deal_md/distance/50ns_unbiased_md/biased_md/50ns/cluster_protein_backbone_allosteric_site_2A_cutoff0.1/frame_pock_volume.png', dpi=300)
plt.close()


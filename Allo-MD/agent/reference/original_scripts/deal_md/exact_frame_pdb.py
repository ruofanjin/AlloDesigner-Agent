import pandas as pd
import subprocess

# 读取CSV
df = pd.read_csv("/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/deal_md/distance/50ns_unbiased_md/biased_md/50ns/cluster_protein_backbone_allosteric_site_2A_cutoff0.1/cluster_frame_map.csv")

# 转为整数帧号
df["frame_t"] = df["frame_t"].astype(int)

# 文件路径
tpr_file = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/deal_md/distance/50ns_unbiased_md/biased_md/50ns/cluster_protein_backbone_allosteric_site_2A_cutoff0.1/biased_50ns_from_unbiaed_50ns.tpr"
xtc_file = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/deal_md/distance/50ns_unbiased_md/biased_md/50ns/cluster_protein_backbone_allosteric_site_2A_cutoff0.1/biased_50ns_from_unbiaed_50ns_center.xtc"
index_flie = '/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/deal_md/distance/50ns_unbiased_md/biased_md/50ns/cluster_protein_backbone_allosteric_site_2A_cutoff0.1/protein.ndx'
# 遍历每个cluster
for idx, row in df.iterrows():
    cluster_id = row["cluster_id"]
    frame = row["frame_t"]

    output_pdb = f"cluster_{cluster_id}_frame_{frame}.pdb"

    # 构建GMX命令
    command = [
        "gmx_mpi", "trjconv",
        "-s", tpr_file,
        "-f", xtc_file,
        "-o", output_pdb,
        "-dump", str(frame),
        "-n", index_flie
    ]

    print(f"Extracting cluster {cluster_id} at frame {frame} → {output_pdb}")

    # 执行命令，自动输入 "System" (或其他 group number)，你可根据 index.ndx 自定义
    try:
        subprocess.run(command, input=b"0\n", check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error extracting frame {frame}: {e}")

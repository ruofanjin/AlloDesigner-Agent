import csv

input_pdb = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/deal_md/distance/50ns_unbiased_md/biased_md/50ns/cluster_protein_backbone_allosteric_site_2A_cutoff0.1/clusters.pdb"
output_csv = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/deal_md/distance/50ns_unbiased_md/biased_md/50ns/cluster_protein_backbone_allosteric_site_2A_cutoff0.1/cluster_frame_map.csv"

cluster_frames = []
cluster_id = 1
with open(input_pdb, "r") as f:
    for line in f:
        if line.startswith("TITLE") and "frame t=" in line:
            try:
                # 提取时间戳
                t_part = line.strip().split("frame t=")[1]
                frame_t = float(t_part)
                cluster_frames.append((cluster_id, frame_t))
                cluster_id += 1
            except Exception as e:
                print(f"Error parsing line: {line.strip()}")
                print(e)

# 写入CSV
with open(output_csv, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["cluster_id", "frame_t"])
    writer.writerows(cluster_frames)

print(f"写入完成，共提取 {len(cluster_frames)} 个 cluster，保存至 {output_csv}")

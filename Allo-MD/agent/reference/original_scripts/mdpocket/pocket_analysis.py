import pandas as pd
import matplotlib.pyplot as plt

# 读取文件（以空格或多个空格为分隔符）
df = pd.read_csv("/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/af2_rank1/mdpocket/distance/50ns_unbiased/biased_md/50ns/output/select_pocket/mdpout_descriptors.txt", delim_whitespace=True)

# 按 snapshot 排序（保险起见）
df = df.sort_values(by="snapshot")

# 提取 snapshot 和 pock_volume
x = (df["snapshot"]* 100).tolist()
y = df["pock_volume"].tolist()



plt.figure(figsize=(12, 4))  # 横向拉长图像比例

# 绘图
plt.plot(x, y)
plt.xlabel("Time (ps)")
plt.ylabel("Pocket Volume (Å³)")
plt.title("Pocket Volume Over Time")
plt.grid(True)


plt.tight_layout()
plt.savefig("/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/af2_rank1/mdpocket/distance/50ns_unbiased/biased_md/50ns/output/select_pocket/pocket_volume.png", dpi=300) 
plt.show()
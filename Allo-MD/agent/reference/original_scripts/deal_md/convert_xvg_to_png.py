import matplotlib.pyplot as plt
import numpy as np

# cluster-id-over-time.xvg 解析
data = np.loadtxt('/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/deal_md/distance/50ns_unbiased_md/biased_md/50ns/protein_all_atoms_allosteric_site_2A.xvg', comments=['#', '@'])
time = data[:, 0]
cluster_ids = data[:, 1]

plt.plot(time, cluster_ids, lw=1)
plt.xlabel("Time (ps)")
plt.ylabel("Cluster ID")
plt.title("Cluster assignment over time")
plt.savefig('/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/deal_md/distance/50ns_unbiased_md/biased_md/50ns/protein_all_atoms_allosteric_site_2A.png', dpi=300)  # 你也可以用 pdf/svg 等
plt.show()

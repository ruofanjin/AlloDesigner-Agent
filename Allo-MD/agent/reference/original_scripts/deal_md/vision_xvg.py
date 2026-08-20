import matplotlib.pyplot as plt

# 读取数据
x, y = [], []
with open('/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/deal_md/distance/50ns_unbiased_md/biased_md/50ns/protein_backbone_allosteric_site_2A.xvg') as f:
    for line in f:
        if line.startswith(('#', '@')):
            continue  # 忽略注释和元数据
        parts = line.split()
        x.append(float(parts[0]))  # 时间
        y.append(float(parts[1]))  # RMSD

# 绘图
plt.plot(x, y)
plt.xlabel('Time (ps)')
plt.ylabel('RMSD (nm)')
plt.title('RMSD over Time')
plt.grid(True)
plt.tight_layout()

# 保存图像
plt.savefig('/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/deal_md/distance/50ns_unbiased_md/biased_md/50ns/protein_backbone_allosteric_site_2A.png', dpi=300)  # 你也可以用 pdf/svg 等

# 显示图像
plt.show()
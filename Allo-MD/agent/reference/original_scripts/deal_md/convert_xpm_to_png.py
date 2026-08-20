from PIL import Image

# 打开 EPS 文件
img = Image.open("/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/deal_md/distance/50ns_unbiased_md/biased_md/50ns/clusters2.eps")

# 可选：设置白色背景（EPS 可能带透明背景）
img = img.convert("RGB")

# 保存为 PNG
img.save("/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/deal_md/distance/50ns_unbiased_md/biased_md/50ns/clusters2.png", "PNG")

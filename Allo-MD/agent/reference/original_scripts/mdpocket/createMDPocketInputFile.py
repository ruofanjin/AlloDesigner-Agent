import fnmatch
import os
import re

# ----------------------------------------------------------------------
# 在这里设置参数
# data_directory = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/mdpocket/plumed_sasa/8.0A_pocket/50ns/pdb_frame"  
# output_file = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/mdpocket/plumed_sasa/8.0A_pocket/50ns/output/snapshot_list_pdb_frame.txt"               

# data_directory = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/alpflow/mdpocket/pdb_frame"  
# output_file = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/alpflow/mdpocket/output/snapshot_list_pdb_frame.txt"               

# data_directory = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/mdpocket/md_normal/50ns/pdb_frame"  
# output_file = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/mdpocket/md_normal/50ns/output/snapshot_list_pdb_frame.txt" 

# data_directory = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/mdpocket/plumed_sasa/8.0A_pocket/10ns/pdb_frame"  
# output_file = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/mdpocket/plumed_sasa/8.0A_pocket/10ns/output/snapshot_list_pdb_frame.txt" 

# data_directory = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/mdpocket/plumed_distance/50ns_unbiased_md/biased_md/50ns/pdb_frame"  
# output_file = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/mdpocket/plumed_distance/50ns_unbiased_md/biased_md/50ns/output/snapshot_list_pdb_frame.txt" 

# data_directory = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/af2/pdb_frame"  
# output_file = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/af2/output/snapshot_list_pdb_frame.txt" 

data_directory = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/deal_md/md_normal/50ns/pdb_frame"  
output_file = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/deal_md/md_normal/50ns/output/snapshot_list_pdb_frame.txt" 

# ----------------------------------------------------------------------

# 检查目录是否存在
if not os.path.exists(data_directory):
    sys.exit(f"ERROR: The directory '{data_directory}' does not exist. Breaking up.")

# 生成文件的完整路径
def getFname(s):
    return os.path.join(data_directory, s)

# 获取所有 .pdb 文件
snapshots = fnmatch.filter(os.listdir(data_directory), "*.pdb")

# 转换为绝对路径
snapshots = [os.path.abspath(getFname(sn)) for sn in snapshots]

# 排序（按数字部分排序，例如 frame1.pdb, frame2.pdb, frame10.pdb）
RE_DIGIT = re.compile(r'(\d+)')
ALPHANUM_KEY = lambda s: [int(g) if g.isdigit() else g for g in RE_DIGIT.split(s)]
snapshots.sort(key=ALPHANUM_KEY)

# 写入输出文件
with open(output_file, "w") as fout:
    for sn in snapshots:
        fout.write(sn + "\n")

print(f"Finished writing snapshot list to '{output_file}'")

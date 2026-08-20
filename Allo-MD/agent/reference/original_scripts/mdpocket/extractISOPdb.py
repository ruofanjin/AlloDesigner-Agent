#!/usr/bin/python

import re
import numpy as npy
import sys
import os

# ----------------------------------------------------------------------------------------------------------
# 直接在此处设置你的参数（不再使用 sys.argv）

# inputfile = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/mdpocket/plumed_sasa/8.0A_pocket/50ns/output/mdpout_dens_grid.dx"       # DX 文件路径
# pathOutput = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/mdpocket/plumed_sasa/8.0A_pocket/50ns/output/mdpout_dens_iso_0.5.pdb"          # 输出 PDB 文件名

inputfile = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/af2/output/mdpout_dens_grid.dx"       # DX 文件路径
pathOutput = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/af2/output/mdpout_dens_iso_0.5.pdb"          # 输出 PDB 文件名

# inputfile = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/alpflow/mdpocket/output/mdpout_dens_grid.dx"      
# pathOutput = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/alpflow/mdpocket/output/mdpout_dens_iso_0.5.pdb"

# inputfile = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/mdpocket/md_normal/50ns/output/mdpout_dens_grid.dx"      
# pathOutput = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/mdpocket/md_normal/50ns/output/mdpout_dens_iso_0.5.pdb"

# inputfile = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/mdpocket/plumed_sasa/8.0A_pocket/10ns/output/mdpout_dens_grid.dx"      
# pathOutput = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/mdpocket/plumed_sasa/8.0A_pocket/10ns/output/mdpout_dens_iso_0.5.pdb"

# inputfile = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/mdpocket/plumed_distance/50ns_unbiased_md/biased_md/50ns/output/mdpout_dens_grid.dx"      
# pathOutput = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/mdpocket/plumed_distance/50ns_unbiased_md/biased_md/50ns/output/mdpout_dens_iso_0.5.pdb"

iso_value = 0.5                            # 设置等值面阈值，例如 0.05 或 -0.05

# ------------------------------------------------------------------------------------------------------------

# 不要改动以下部分，除非你清楚其功能

if not os.path.exists(inputfile):
    sys.exit("ERROR: the dx file provided does not exist. Breaking up.")

f = open(inputfile, "r")

# 读取 header，直到遇到 "object" 行（表示进入数据部分）
header = ""
tmp = f.readline()
while tmp[0] != "o":
    header += tmp
    tmp = f.readline()

# 读取 grid size（网格大小）
r = re.compile(r'\w+')
gsize = r.findall(tmp)
gsize = [int(gsize[-3]), int(gsize[-2]), int(gsize[-1])]

# 读取 origin（起点坐标）
line = f.readline().split()
origin = [float(line[-3]), float(line[-2]), float(line[-1])]

# 读取每个轴的步长（spacing）
line = f.readline().split()
deltax = [float(line[-3]), float(line[-2]), float(line[-1])]
line = f.readline().split()
deltay = [float(line[-3]), float(line[-2]), float(line[-1])]
line = f.readline().split()
deltaz = [float(line[-3]), float(line[-2]), float(line[-1])]

# 步长向量（这里只使用对角线元素，假设是正交坐标系）
delta = npy.array([deltax[0], deltay[1], deltaz[2]])

# 跳过一行（"object"）
f.readline()

# 获取数据点数量
r = re.compile(r'\d+')
n_entries = int(r.findall(f.readline())[2])

if n_entries != gsize[0] * gsize[1] * gsize[2]:
    sys.exit("Error reading the file. Number of expected data points does not match actual data points.")

# 读入网格数据并筛选出符合 iso-value 条件的点，输出为 PDB 格式
print("Reading the grid. Depending on the number of data points, this might take a while...")

path = open(pathOutput, "w")

z = 0
y = 0
x = 0
counter = 1

for count in range(n_entries // 3):
    c = f.readline().split()
    if len(c) != 3:
        print("Error reading grid data")
        sys.exit("Exiting the program")

    for i in range(3):
        val = float(c[i])
        if (iso_value < 0 and val < iso_value) or (iso_value > 0 and val > iso_value):
            x_pos = origin[0] + x * delta[0]
            y_pos = origin[1] + y * delta[1]
            z_pos = origin[2] + z * delta[2]
            path.write('ATOM  %5d  C   PTH     1    %8.3f%8.3f%8.3f%6.2f%6.2f\n' % (counter, x_pos, y_pos, z_pos, 0.0, 0.0))
            counter += 1

        z += 1
        if z >= gsize[2]:
            z = 0
            y += 1
            if y >= gsize[1]:
                y = 0
                x += 1

path.close()
f.close()

print(f"Finished writing {pathOutput}")

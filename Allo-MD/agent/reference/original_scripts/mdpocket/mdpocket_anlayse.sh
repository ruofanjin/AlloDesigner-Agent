step1
gmx_mpi make_ndx -f biased_sasa_allosteric_site_1ns_from_step7_3.tpr -o protein.ndx
keep 1
q

step2
#echo "Backbone" | gmx trjconv -f traj.xtc -s topol.tpr -n protein.ndx -o aligned.xtc -fit rot+trans -center -pbc mol

#gmx trjconv -f biased_sasa_allosteric_site_1ns_from_step7_3.xtc -s  biased_sasa_allosteric_site_1ns_from_step7_3.tpr -n protein.ndx -o aligned.xtc -fit rot+trans -center -pbc mol

#!/bin/bash

# 从GROMACS的tpr中提取第0帧作为reference.pdb

# 1. 修复PBC
echo "Protein" | gmx trjconv -f biased_sasa_allosteric_site_1ns_from_step7_3.xtc -s biased_sasa_allosteric_site_1ns_from_step7_3.tpr -n protein.ndx -o pbc_fixed.xtc -center -pbc mol -ur compact

# 2. 旋转对齐
echo "Backbone" | gmx trjconv -f pbc_fixed.xtc -s biased_sasa_allosteric_site_1ns_from_step7_3.tpr -n protein.ndx -o aligned.xtc -fit rot+trans

echo "Protein" | gmx trjconv -s biased_sasa_allosteric_site_1ns_from_step7_3.tpr -f aligned.xtc -o aligned_reference.pdb -dump 0
keep 1


step3
# 3. 可选：提取PDB帧供MDpocket分析
echo "Protein" | gmx trjconv -f aligned.xtc -s biased_sasa_allosteric_site_10ns_from_step7_3.tpr -n protein.ndx -o /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/mdpocket/plumed_sasa/10ns/pdb_frame/frames.pdb -dt 10 -sep

注意 aligned_reference.pdb 和 reference.pdb 坐标一致 说明同一条轨迹的各帧本身就是对齐的 

step4
#mdpocket --trajectory_file /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/mdpocket/plumed_sasa/1ns/aligned.xtc --trajectory_format xtc -f /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/mdpocket/plumed_sasa/1ns/reference.pdb
mdpocket --pdb_list snapshot_list_pdb_frame.txt

mdpocket --pdb_list snapshot_list_pdb_frame.txt --selected_pocket selected_grid_iso_0.5_1A_pocket.pdb


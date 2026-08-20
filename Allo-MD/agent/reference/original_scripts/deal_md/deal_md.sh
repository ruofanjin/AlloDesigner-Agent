
gmx_mpi make_ndx -f biased_sasa_allosteric_site_50ns_from_step7_3.tpr -o protein_backbone.ndx

计算rmsd
gmx rms -s md.tpr -f md.xtc -o rmsd.xvg
4

gmx rms -s md.tpr -f md.xtc -o rmsd_TM6-ECL3-TM7.xvg -n protein_backbone_TM6-ECL3-TM7.ndx 
gmx rms -s md.tpr -f md.xtc -o rmsd_TM6-TM7.xvg -n protein_backbone_TM6-TM7.ndx 
gmx rms -s md.tpr -f md.xtc -o protein_all_atoms_allosteric_site_2A.xvg -n protein_all_atoms_allosteric_site_2A.ndx 
gmx rms -s md.tpr -f md.xtc -o protein_backbone_allosteric_site_2A.xvg -n protein_backbone_allosteric_site_2A.ndx 


计算同一条轨迹中构象的RMSD矩阵
gmx rms -s md.tpr -f md.xtc -f2 md.xtc -o rmsd.xvg -m rmsd.xpm -n index.ndx

cluster
gmx cluster -s md.tpr -f propep_fit.xtc -dm rmsd.xpm -dist rmsd-distribution.xvg -o clusters.xpm -sz cluster-sizes.xvg -tr cluster-transitions.xpm -ntr cluster-transitions.xvg -clid cluster-id-over-time.xvg -cl clusters.pdb -cutoff 0.2 -method gromos

gmx cluster -f md_0_10_center.xtc -s md_0_10.tpr -cutoff 0.8 -b 1000 -wcl 10 -method gromos -sz



gmx trjconv -s biased_50ns_from_unbiaed_50ns.tpr -f biased_50ns_from_unbiaed_50ns.xtc -o biased_50ns_from_unbiaed_50ns_center.xtc -center -pbc mol -ur compact -fit rot+trans
拆分成两条
gmx_mpi trjconv -s biased_50ns_from_unbiaed_50ns.tpr -f biased_50ns_from_unbiaed_50ns.xtc -o step1_pbc.xtc -pbc mol -ur compact -center

gmx_mpi trjconv -s biased_50ns_from_unbiaed_50ns.tpr -f step1_pbc.xtc -o biased_50ns_from_unbiaed_50ns_center.xtc -fit rot+trans

都是protein

gmx cluster -s biased_50ns_from_unbiaed_50ns.tpr -f biased_50ns_from_unbiaed_50ns_center.xtc -o clusters.xpm -cl clusters.pdb -cutoff 0.1 -method gromos -sz cluster-sizes.xvg -clid cluster-id-over-time.xvg
gmx cluster -s biased_50ns_from_unbiaed_50ns.tpr -f biased_50ns_from_unbiaed_50ns_center.xtc -n protein_backbone_TM6-ECL3-TM7.ndx -o clusters.xpm -cl clusters.pdb -cutoff 0.1 -method gromos -sz cluster-sizes.xvg -clid cluster-id-over-time.xvg

gmx xpm2ps -f clusters.xpm -o clusters2.eps -rainbow red

提取特定帧  dump后的单位是ps
gmx trjconv -s biased_sasa_allosteric_site_1ns_from_step7_3.tpr -f aligned.xtc -o aligned_reference.pdb -dump 0

tar -czvf cluster_pdb_frame.tar.gz /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/deal_md/distance/50ns_unbiased_md/biased_md/50ns/cluster_protein_backbone_allosteric_site_2A_cutoff0.1/cluster_pdb_frame

zip -r cluster_pdb_frame.zip /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/deal_md/distance/50ns_unbiased_md/biased_md/50ns/cluster_protein_backbone_allosteric_site_2A_cutoff0.1/cluster_pdb_frame/

计算holo和cluster中心的rmsd
gmx rms -s 5vex_holo_convert_apo_id_allosteric_site_2A.pdb -f clusters.pdb -o rmsd-ref-vs-clusters.xvg  

根据.ndx文件 每帧值保留指定的原子
gmx trjconv -s biased_50ns_from_unbiaed_50ns.tpr -f biased_50ns_from_unbiaed_50ns_center.xtc -n protein_backbone_allosteric_site_2A.ndx -o filtered.xtc

gmx trjconv -s biased_50ns_from_unbiaed_50ns.tpr -f filtered.xtc -o frames0_1.pdb -dump 0


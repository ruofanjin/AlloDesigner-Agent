$ cp -r toppar /your/installation/path/of/GMX/gromacs/top/toppar

$ gmx grompp -f step6.0_minimization.mdp -c step5_input.gro -r step5_input.gro -p topol.top -o em.tpr
$ gmx mdrun -deffnm em

$ gmx grompp -f step6.1_equilibration.mdp -c em.gro -r em.gro -p topol.top -o eq1.tpr -n index.ndx
$ gmx mdrun -deffnm eq1
$ gmx grompp -f step6.2_equilibration.mdp -c eq1.gro -r eq1.gro -p topol.top -o eq2.tpr -n index.ndx
$ gmx mdrun -deffnm eq2
$ gmx grompp -f step6.3_equilibration.mdp -c eq2.gro -r eq2.gro -p topol.top -o eq3.tpr -n index.ndx
$ gmx mdrun -deffnm eq3
$ gmx grompp -f step6.4_equilibration.mdp -c eq3.gro -r eq3.gro -p topol.top -o eq4.tpr -n index.ndx
$ gmx mdrun -deffnm eq4
$ gmx grompp -f step6.5_equilibration.mdp -c eq4.gro -r eq4.gro -p topol.top -o eq5.tpr -n index.ndx
$ gmx mdrun -deffnm eq5
$ gmx grompp -f step6.6_equilibration.mdp -c eq5.gro -r eq5.gro -p topol.top -o eq6.tpr -n index.ndx
$ gmx mdrun -deffnm eq6


$ gmx grompp -f step7_production.mdp -o md.tpr -c eq6.gro -p topol.top -n index.ndx
$ gmx mdrun -deffnm md                               #不使用GPU加速或者无GPU运行
$ gmx mdrun -deffnm md -pme gpu -nb gpu -bonded gpu  #使用GPU加速运行

md_normal

gmx grompp -f step7.1_production.mdp -o step7_1.tpr -c eq6.gro -p topol.top -n index.ndx
gmx mdrun -v -deffnm step7_1

gmx grompp -f step7_production.mdp -o step7_2.tpr -c step7_1.gro -t step7_1.cpt -p topol.top -n index.ndx
gmx mdrun -v -deffnm step7_2

gmx grompp -f step7_production.mdp -o step7_3.tpr -c step7_2.gro -t step7_2.cpt -p topol.top -n index.ndx
gmx mdrun -v -deffnm step7_3

200ns
gmx_mpi grompp -f step7.4_production.mdp -o step7_4.tpr -c step7_3.gro -t step7_3.cpt -p topol.top -n index.ndx
gmx_mpi mdrun -deffnm step7_4 

gmx grompp -f step7_plumed_test.mdp -o step7_plumed_test.tpr -c eq6.gro -p topol.top -n index.ndx
gmx_mpi mdrun -deffnm step7_plumed_test -plumed plumed_chi_defined.dat


plumed_sasa

gmx grompp -f plumed_sasa_metad_biased.mdp -o biased_sasa_allosteric_site_1ns_from_step7_3.tpr -c /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/md_normal/step7_3.gro -t /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/md_normal/step7_3.cpt -p /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/topol.top -n /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/index.ndx
gmx_mpi mdrun -deffnm biased_sasa_allosteric_site_1ns_from_step7_3 -plumed plumed_sasa_metad_allosteric_site.dat

gmx grompp -f plumed_sasa_metad_biased.mdp -o biased_sasa_8.0A_pocket_1ns_from_step7_3.tpr -c /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/md_normal/step7_3.gro -t /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/md_normal/step7_3.cpt -p /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/topol.top -n /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/index.ndx
gmx_mpi mdrun -deffnm biased_sasa_8.0A_pocket_1ns_from_step7_3 -plumed plumed_sasa_metad_8.0A_pocket.dat

biased md

gmx grompp -f step7_plumed_test_production_biased_1ns.mdp -o biased_1ns_from_unbiaed_1ns.tpr -c /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/plumed/step7_plumed_test.gro -t /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/plumed/step7_plumed_test.cpt -p /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/topol.top -n /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/index.ndx
gmx_mpi mdrun -deffnm biased_1ns_from_unbiaed_1ns -plumed plumed_biased.dat


plumed_distance

gmx grompp -f plumed_sasa_metad_biased.mdp -o biased_sasa_allosteric_site_50ns_from_step7_3.tpr -c /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/md_normal/step7_3.gro -t /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/md_normal/step7_3.cpt -p /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/topol.top -n /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/index.ndx
gmx_mpi mdrun -deffnm biased_sasa_allosteric_site_50ns_from_step7_3 -plumed plumed_sasa_metad_allosteric_site.dat



 
biased md sasa distance

gmx grompp -f plumed_biased.mdp -o biased_1ns_from_unbiaed_10ns.tpr -c /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/plumed_distance/10ns_unbiased_md/biased_sasa_allosteric_site_10ns_from_step7_3.gro -t /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/plumed_distance/10ns_unbiased_md/biased_sasa_allosteric_site_10ns_from_step7_3.cpt -p /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/topol.top -n /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/index.ndx
gmx_mpi mdrun -deffnm biased_1ns_from_unbiaed_10ns -plumed /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/plumed_distance/10ns_unbiased_md/biased_md/plumed_biased.dat

50ns
gmx grompp -f plumed_biased.mdp -o biased_1ns_from_unbiaed_50ns.tpr -c /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/plumed_distance/50ns_unbiased_md/biased_sasa_allosteric_site_50ns_from_step7_3.gro -t /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/plumed_distance/50ns_unbiased_md/biased_sasa_allosteric_site_50ns_from_step7_3.cpt -p /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/topol.top -n /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/index.ndx
gmx_mpi mdrun -deffnm biased_1ns_from_unbiaed_50ns -plumed /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/plumed_distance/50ns_unbiased_md/biased_md/plumed_biased.dat
GMX_MAXCONSTRWARN=-1 gmx_mpi mdrun -deffnm biased_1ns_from_unbiaed_50ns -plumed /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/plumed_distance/50ns_unbiased_md/biased_md/plumed_biased.dat

unbiased 50ns  biased_50ns to  biased_100ns  
gmx grompp -f plumed_biased.mdp -o biased_100ns_from_biaed_50ns.tpr -c /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/plumed_distance/50ns_unbiased_md/biased_md/50ns/biased_50ns_from_unbiaed_50ns.gro -t /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/plumed_distance/50ns_unbiased_md/biased_md/50ns/biased_50ns_from_unbiaed_50ns.cpt -p /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/topol.top -n /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/index.ndx
GMX_MAXCONSTRWARN=-1 gmx_mpi mdrun -deffnm biased_100ns_from_biaed_50ns -plumed /root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/plumed_distance/50ns_unbiased_md/biased_md/plumed_biased.dat





#@title 4.1 SPIB on unbiased simulations
import numpy as np
import os
import time
# import matplotlib.pyplot as plt

light_version =  False
# light_version =  True


#@markdown Input SPIB time lag in units of number of input trajectory steps
dt=145 #@param{type:"number"}

# if os.path.isdir("/home/zhangyangyang/work/af2rave/State-Predictive-Information-Bottleneck/unbiased")==True:
#   os.system('rm -r /home/zhangyangyang/work/af2rave/State-Predictive-Information-Bottleneck/unbiased')
# if os.path.isdir("/home/zhangyangyang/work/af2rave/alphafold2rave-main/SPIB_unbiased"):
#   os.system("rm -r /home/zhangyangyang/work/af2rave/alphafold2rave-main/SPIB_unbiased")

# os.chdir('/root/data1/data/move/ZYY/zyy/works/State-Predictive-Information-Bottleneck/GPCR/')
# os.chdir('/root/data1/data/move/ZYY/zyy/works/State-Predictive-Information-Bottleneck/GPCR/plumed_distance/50ns/')
os.chdir('/root/data1/data/move/ZYY/zyy/works/State-Predictive-Information-Bottleneck/GPCR/af2rank1/plumed_distance/50ns/')

# listindices=[1, 533, 571]
cvs=[]
# os.mkdir("SPIB_unbiased")
os.chdir("SPIB_unbiased")
# num_state=len(listindices)*2
num_state=2
# for i,index in enumerate(listindices):
#     cvs.append(np.loadtxt("/home/zhangyangyang/work/af2rave/alphafold2rave-main/unbiased/unbiased_md_20ns/%i/COLVAR_unb.dat"%index)[:,1:])
#     np.save("colvar_%i_unb.npy"%i,cvs[i])
#     lentraj=len(cvs[i])
#     zeroone=np.hstack([np.zeros(int(lentraj/2),dtype=np.int8),np.ones(lentraj-int(lentraj/2),dtype=np.int8)])
#     initlabels=np.eye(num_state)[zeroone+int(i*2)]
#     np.save("labels_%i_unb.npy"%i,initlabels)

# cvs.append(np.loadtxt("/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/plumed/bck.0.COLVARS_1ns.dat")[:,1:])
# cvs.append(np.loadtxt("/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/plumed_distance/50ns_unbiased_md/colvar_distance")[:,1:])
cvs.append(np.loadtxt("/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/af2_rank1/plumed_distance/50ns_unbiased/colvar_distance")[:,1:])


np.save("colvar_0_unb.npy",cvs[0])
lentraj=len(cvs[0])
zeroone=np.hstack([np.zeros(int(lentraj/2),dtype=np.int8),np.ones(lentraj-int(lentraj/2),dtype=np.int8)])
initlabels=np.eye(num_state)[zeroone+int(0*2)]
np.save("labels_0_unb.npy",initlabels)

f_nodt=open("/root/data1/data/move/ZYY/zyy/works/State-Predictive-Information-Bottleneck/GPCR/sample_config.ini")
f=open("config.ini","w")
lines=f_nodt.readlines()
lines.insert(2,f"dt =[{dt}]\n")
f.writelines(lines)
f_nodt.close()
unbpath="unbiased"
f.write("\n traj_data = [%s]\n"%",".join(["%s/colvar_%i_unb.npy"%(unbpath,i) for i in range(len(cvs))]))
f.write("\n initial_labels = [%s]\n"%",".join(["%s/labels_%i_unb.npy"%(unbpath,i) for i in range(len(cvs))]))
f.write("\n traj_weights \n")
f.close()
os.chdir("..")
# os.system("cp /root/data1/data/move/ZYY/zyy/works/State-Predictive-Information-Bottleneck/GPCR/SPIB_unbiased/* /root/data1/data/move/ZYY/zyy/works/State-Predictive-Information-Bottleneck/unbiased/")
# os.system("cp /root/data1/data/move/ZYY/zyy/works/State-Predictive-Information-Bottleneck/GPCR/plumed_distance/50ns/SPIB_unbiased/* /root/data1/data/move/ZYY/zyy/works/State-Predictive-Information-Bottleneck/unbiased/")
os.system("cp /root/data1/data/move/ZYY/zyy/works/State-Predictive-Information-Bottleneck/GPCR/af2rank1/plumed_distance/50ns/SPIB_unbiased/* /root/data1/data/move/ZYY/zyy/works/State-Predictive-Information-Bottleneck/unbiased/")


os.chdir("/root/data1/data/move/ZYY/zyy/works/State-Predictive-Information-Bottleneck/")
os.system("python /root/data1/data/move/ZYY/zyy/works/State-Predictive-Information-Bottleneck/test_model_advanced.py -config /root/data1/data/move/ZYY/zyy/works/State-Predictive-Information-Bottleneck/unbiased/config.ini")

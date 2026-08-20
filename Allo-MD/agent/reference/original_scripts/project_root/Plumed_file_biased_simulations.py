#@title 4.3 Plumed file for biased simulations

#@markdown Here we are using an already solvated and equilibrated system from our unbiased runs

# Inputs definition

#@markdown Metadynamics parameters

import numpy as np
import os
import logging



def make_biased_plumed(plumedfile,weights,colvar,height,biasfactor,width1,width2,gridmin1,gridmin2,gridmax1,gridmax2,temperature):
    f_unb=open(plumedfile)
    f=open('plumed_biased.dat','w')
    lines=f_unb.readlines()
    p=lines.pop(-2)
    w0=",".join([str(weights[0][i]) for i in range (len(weights[0]))])
    w1=",".join([str(weights[1][i]) for i in range (len(weights[1]))])
    lines.insert(-1,"\nsigma1: COMBINE ARG=%s COEFFICIENTS=%s PERIODIC=NO"%(colvar,w0))
    lines.insert(-1,"\nsigma2: COMBINE ARG=%s COEFFICIENTS=%s PERIODIC=NO"%(colvar,w1))

    lines.insert(-1,"\nMETAD ...\n \
      LABEL=metad\n \
      ARG=sigma1,sigma2\n \
      PACE=500 HEIGHT=%f TEMP=%i\n \
      BIASFACTOR=%i\n \
      SIGMA=%f,%f\n \
      FILE=HILLS GRID_MIN=%f,%f GRID_MAX=%f,%f GRID_BIN=200,200\n \
      CALC_RCT RCT_USTRIDE=500\n \
      ... METAD\n"%(height,temperature,biasfactor,width1,width2,gridmin1,gridmin2,gridmax1,gridmax2))
  
    f.writelines(lines)
    f.write("\n PRINT ARG=%s,sigma1,sigma2,metad.rbias STRIDE=500 FILE=COLVAR_biased.dat"%colvar)

    f.close()
    


logging.basicConfig(level=logging.INFO)  


# listindices=[1, 533, 571]
# listindices=[1]
dt=145
cvs=[]
# for i,index in enumerate(listindices):
# cvs.append(np.loadtxt("/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/plumed/bck.0.COLVARS_1ns.dat")[:,1:])
# cvs.append(np.loadtxt("/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/plumed_distance/10ns_unbiased_md/colvar_distance")[:,1:])
# cvs.append(np.loadtxt("/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/plumed_distance/50ns_unbiased_md/colvar_distance")[:,1:])
cvs.append(np.loadtxt("/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/af2_rank1/plumed_distance/50ns_unbiased/colvar_distance")[:,1:])

# os.chdir("/root/data1/data/move/ZYY/zyy/works/State-Predictive-Information-Bottleneck/GPCR/SPIB_lr-2")
# os.chdir("/root/data1/data/move/ZYY/zyy/works/State-Predictive-Information-Bottleneck/GPCR/plumed_distance/50ns/SPIB")
os.chdir("/root/data1/data/move/ZYY/zyy/works/State-Predictive-Information-Bottleneck/GPCR/af2rank1/plumed_distance/50ns/SPIB")


prefix='Unweighted_d=2_t=%i_b=0.0100_learn=0.010000_'%dt
weights=np.load(prefix+"z_mean_encoder_weight0.npy")
lspace=[np.load(prefix+"traj0_mean_representation0.npy") ]
lstacked=np.vstack([np.hstack([lspace[j][:,i] for j in range(len(cvs))]) for i in range(2)])
width1=np.std(lspace[0])/1.2
width2=np.std(lspace[0])/1.2
gridmin1=lstacked[0].min()-60
gridmax1=lstacked[0].max()+60
gridmin2=lstacked[1].min()-60
gridmax2=lstacked[1].max()+60

#@markdown Gaussian deposit height in kJ/mol
height = 5 #@param{type:"number"}

#@markdown Bias factor for tempering (ratio of temperatures)
biasfactor=10 #@param{type:"number"}

#@markdown Temperature of molecular dy
temperature=310.15 #@param{type:"number"}
#@markdown Length of metadynamics simulation

# filename = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/plumed/bck.0.COLVARS_1ns.dat"
# filename = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/plumed_distance/50ns_unbiased_md/colvar_distance"
filename = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/af2_rank1/plumed_distance/50ns_unbiased/colvar_distance"


with open(filename, 'r') as f:
    for line in f:
        if line.startswith('#'):
            header = line.strip().lstrip('#').strip()
            columns = header.split()
            break  

filtered_columns = [col for col in columns if col.lower() not in ('time', 'step')][2:]

colvar =  ','.join(filtered_columns) 

#colvar="sc1_r1,cc1_r1,sc1_r2,cc1_r2,sc1_r3,cc1_r3,sc1_r5,cc1_r5,sc1_r6,cc1_r6,sc1_r7,cc1_r7,sc1_r8,cc1_r8,sc1_r9,cc1_r9,sc1_r10,cc1_r10,sc1_r11,cc1_r11,sc1_r12,cc1_r12,sc1_r13,cc1_r13,sc1_r15,cc1_r15,sc1_r17,cc1_r17,sc1_r18,cc1_r18,sc1_r19,cc1_r19,sc1_r20,cc1_r20,sc1_r21,cc1_r21,sc1_r24,cc1_r24,sc1_r25,cc1_r25,sc1_r26,cc1_r26,sc1_r27,cc1_r27,sc1_r28,cc1_r28,sc1_r29,cc1_r29,sc1_r30,cc1_r30,sc1_r31,cc1_r31,sc1_r33,cc1_r33,sc1_r34,cc1_r34,sc1_r36,cc1_r36,sc1_r38,cc1_r38,sc1_r39,cc1_r39,sc1_r40,cc1_r40,sc1_r41,cc1_r41,sc1_r42,cc1_r42,sc1_r43,cc1_r43,sc1_r45,cc1_r45,sc1_r46,cc1_r46,sc1_r47,cc1_r47,sc1_r48,cc1_r48,sc1_r49,cc1_r49,sc1_r50,cc1_r50,sc1_r51,cc1_r51,sc1_r52,cc1_r52,sc1_r53,cc1_r53,sc1_r55,cc1_r55,sc1_r56,cc1_r56,sc1_r58,cc1_r58,sc1_r59,cc1_r59,sc1_r62,cc1_r62,sc1_r63,cc1_r63,sc1_r64,cc1_r64,sc1_r65,cc1_r65,sc1_r66,cc1_r66,sc2_r1,cc2_r1,sc2_r2,cc2_r2,sc2_r3,cc2_r3,sc2_r5,cc2_r5,sc2_r7,cc2_r7,sc2_r8,cc2_r8,sc2_r9,cc2_r9,sc2_r10,cc2_r10,sc2_r11,cc2_r11,sc2_r12,cc2_r12,sc2_r13,cc2_r13,sc2_r15,cc2_r15,sc2_r17,cc2_r17,sc2_r18,cc2_r18,sc2_r19,cc2_r19,sc2_r21,cc2_r21,sc2_r25,cc2_r25,sc2_r27,cc2_r27,sc2_r29,cc2_r29,sc2_r30,cc2_r30,sc2_r33,cc2_r33,sc2_r34,cc2_r34,sc2_r36,cc2_r36,sc2_r38,cc2_r38,sc2_r39,cc2_r39,sc2_r41,cc2_r41,sc2_r42,cc2_r42,sc2_r43,cc2_r43,sc2_r45,cc2_r45,sc2_r46,cc2_r46,sc2_r49,cc2_r49,sc2_r50,cc2_r50,sc2_r51,cc2_r51,sc2_r53,cc2_r53,sc2_r55,cc2_r55,sc2_r56,cc2_r56,sc2_r58,cc2_r58,sc2_r59,cc2_r59,sc2_r62,cc2_r62,sc2_r65,cc2_r65,sc2_r66,cc2_r66,sc3_r1,cc3_r1,sc3_r2,cc3_r2,sc3_r3,cc3_r3,sc3_r5,cc3_r5,sc3_r7,cc3_r7,sc3_r12,cc3_r12,sc3_r13,cc3_r13,sc3_r19,cc3_r19,sc3_r21,cc3_r21,sc3_r34,cc3_r34,sc3_r36,cc3_r36,sc3_r39,cc3_r39,sc3_r42,cc3_r42,sc3_r43,cc3_r43,sc3_r45,cc3_r45,sc3_r46,cc3_r46,sc3_r50,cc3_r50,sc3_r53,cc3_r53,sc3_r56,cc3_r56,sc3_r59,cc3_r59,sc3_r65,cc3_r65,sc3_r66,cc3_r66,sc4_r3,cc4_r3,sc4_r5,cc4_r5,sc4_r7,cc4_r7,sc4_r13,cc4_r13,sc4_r39,cc4_r39,sc4_r56,cc4_r56,sc4_r65,cc4_r65,sc5_r3,cc5_r3,sc5_r56,cc5_r56"
# plumedfile="/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/plumed/plumed_chi_defined.dat"
# plumedfile="/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/gromacs/plumed_distance/50ns_unbiased_md/plumed_sasa_metad_allosteric_site.dat"
plumedfile="/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/af2_rank1/plumed_distance/50ns_unbiased/plumed_distance.dat"

make_biased_plumed(plumedfile,weights,colvar,height,biasfactor,width1,width2,gridmin1,gridmin2,gridmax1,gridmax2,temperature)

print("Plumed file for biasing using SPIB weights has been written as plumed_biased.dat")

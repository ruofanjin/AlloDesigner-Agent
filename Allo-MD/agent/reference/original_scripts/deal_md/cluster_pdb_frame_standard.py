import os


input_folder = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/deal_md/distance/50ns_unbiased_md/biased_md/50ns/cluster_protein_backbone_allosteric_site_2A_cutoff0.1/cluster_pdb_frame"    
output_folder = "/root/data1/data/move/ZYY/zyy/works/GPCRs_MD/GLP1/interation1_shuffle8_group37/deal_md/distance/50ns_unbiased_md/biased_md/50ns/cluster_protein_backbone_allosteric_site_2A_cutoff0.1/cluster_pdb_frame_fix"   

os.makedirs(output_folder, exist_ok=True)


prefix_map = {
    "NALA": "ALA",
    "NARG": "ARG",
    "NASN": "ASN",
    "NASP": "ASP",
    "NCYS": "CYS",
    "NGLN": "GLN",
    "NGLU": "GLU",
    "NGLY": "GLY",
    "NHIS": "HIS",
    "NILE": "ILE",
    "NLEU": "LEU",
    "NLYS": "LYS",
    "NMET": "MET",
    "NPHE": "PHE",
    "NPRO": "PRO",
    "NSER": "SER",
    "NTHR": "THR",
    "NTRP": "TRP",
    "NTYR": "TYR",
    "NVAL": "VAL",
    "CALA": "ALA",
    "CARG": "ARG",
    "CASN": "ASN",
    "CASP": "ASP",
    "CCYS": "CYS",
    "CGLN": "GLN",
    "CGLU": "GLU",
    "CGLY": "GLY",
    "CHIS": "HIS",
    "CILE": "ILE",
    "CLEU": "LEU",
    "CLYS": "LYS",
    "CMET": "MET",
    "CPHE": "PHE",
    "CPRO": "PRO",
    "CSER": "SER",
    "CTHR": "THR",
    "CTRP": "TRP",
    "CTYR": "TYR",
    "CVAL": "VAL",
    "CHID": "HID",
}

for filename in os.listdir(input_folder):
    if filename.lower().endswith(".pdb"):
        input_pdb = os.path.join(input_folder, filename)
        output_pdb = os.path.join(output_folder, filename)

        with open(input_pdb, "r") as f_in, open(output_pdb, "w") as f_out:
            for line in f_in:
                if line.startswith("ATOM") or line.startswith("HETATM"):
                    resname = line[17:21].strip()  # 原始残基名
                    new_resname = prefix_map.get(resname, resname)

                    line = line[:17] + f"{new_resname:>3} A" + line[22:]
                f_out.write(line)

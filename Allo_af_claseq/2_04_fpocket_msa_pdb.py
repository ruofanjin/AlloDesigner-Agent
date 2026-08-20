import os


def run_fpocket_on_folder(pdb_folder):
    for filename in os.listdir(pdb_folder):
        if filename.endswith(".pdb"):
            os.system(f"/root/miniconda3/envs/deepallo/bin/fpocket -f {filename }")



run_fpocket_on_folder("./AF_ClaSeq/case/PCKS9/4ne9/run/04_recompile/pocket_min_distance/control_prediction/bin_12_13_14_15_fpocket")


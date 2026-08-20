import os


def run_fpocket_on_folder(pdb_folder):
    for filename in os.listdir(pdb_folder):
        if filename.endswith("seed_042.pdb"):
            pdb_path = os.path.join(pdb_folder, filename)

            os.chdir(pdb_folder)
            os.system(f"/root/miniconda3/envs/deepallo/bin/fpocket -f {pdb_path}")



run_fpocket_on_folder("./AF-ClaSeq2/case/GLP1/raw_msa_colabfold_fpocket")

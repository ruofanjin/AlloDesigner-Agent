import os
import pandas as pd
import numpy as np
import pickle
from Bio import PDB
from sklearn.cluster import DBSCAN

# csv_file = './case/GLP1/5vex/mapped_residues_pocketminer_residue_probabilities_averge_0.7.csv'
csv_file = './case/lepu_test/p7_test1/model/4ne9/pocketminer_residue_probabilities_averge_0.7.csv'
# mapping_pkl = './case/GLP1/6x18/6x18_seqres_to_atom_mapping.pkl'
eps = 4.5
min_samples = 2

df = pd.read_csv(csv_file)
# with open(mapping_pkl, "rb") as f:
#     pocket_res_map = pickle.load(f)[0]['seq_indices']

df = df[df['probability'] == 1]
binding_residues = [res for res in df['residue']]

# base_dir = "./AF_ClaSeq/case/GPL1/6x18_chianR_R/run/01_iterative_shuffling/Iteration_1"
base_dir = "./AF_ClaSeq/case/PCKS9/4ne9/run/01_iterative_shuffling/Iteration_1"

for i in range(2, 11):
    pdb_root_dir = os.path.join(base_dir, f"shuffle_{i}_fpocket")
    output_folder = os.path.join(base_dir, f"shuffle_{i}_pocketminer_predict_residues_cluster/eps{eps}_min_samples{min_samples}")
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(pdb_root_dir):
        if not filename.endswith(".pdb"):
            continue

        pdb_path = os.path.join(pdb_root_dir, filename)
        pdb_code = os.path.splitext(filename)[0]

        structure = PDB.PDBParser(QUIET=True).get_structure("protein", pdb_path)
        residue_coords, residue_info = [], []

        for model in structure:
            for chain in model:
                for residue in chain:
                    if residue.id[1] in binding_residues and "CA" in residue:
                        residue_coords.append(residue["CA"].coord)
                        residue_info.append((chain.id, residue.resname, residue.id[1], residue))

        if len(residue_coords) == 0:
            continue

        io = PDB.PDBIO()

        if len(residue_coords) == 1:
            chain_id, resname, resnum, residue = residue_info[0]
            output_structure = PDB.Structure.Structure("single")
            model = PDB.Model.Model(0)
            new_chain = PDB.Chain.Chain(chain_id)
            new_chain.add(residue)
            model.add(new_chain)
            output_structure.add(model)

            out_path = os.path.join(output_folder, f"{pdb_code}_clustered.pdb")
            io.set_structure(output_structure)
            io.save(out_path)
            continue

        residue_coords = np.array(residue_coords)
        cluster_labels = DBSCAN(eps=eps, min_samples=min_samples).fit(residue_coords).labels_

    
        noise_structure = PDB.Structure.Structure("noise")
        model = PDB.Model.Model(0)
        noise_structure.add(model)
        chains_dict = {}

        for (chain_id, resname, resnum, residue), label in zip(residue_info, cluster_labels):
            if label == -1:
                if chain_id not in chains_dict:
                    new_chain = PDB.Chain.Chain(chain_id)
                    model.add(new_chain)
                    chains_dict[chain_id] = new_chain
                chains_dict[chain_id].add(residue)

        noise_out = os.path.join(output_folder, f"{pdb_code}_noise_residues.pdb")
        io.set_structure(noise_structure)
        io.save(noise_out)

        unique_clusters = np.unique(cluster_labels[cluster_labels != -1])
        for cluster in unique_clusters:
            cluster_structure = PDB.Structure.Structure(f"cluster_{cluster}")
            model = PDB.Model.Model(0)
            cluster_structure.add(model)
            chains_dict = {}

            for (chain_id, resname, resnum, residue), label in zip(residue_info, cluster_labels):
                if label == cluster:
                    if chain_id not in chains_dict:
                        new_chain = PDB.Chain.Chain(chain_id)
                        model.add(new_chain)
                        chains_dict[chain_id] = new_chain
                    chains_dict[chain_id].add(residue)

            cluster_out = os.path.join(output_folder, f"{pdb_code}_cluster_{cluster}.pdb")
            io.set_structure(cluster_structure)
            io.save(cluster_out)


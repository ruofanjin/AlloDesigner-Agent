import os
import glob
import re
import numpy as np
import pandas as pd
import pickle
from Bio.PDB import PDBParser
from utils.extract_sequence import extract_sequence
import torch
import torch.nn as nn
from transformers import AutoModel, BertTokenizer
from autogluon.tabular import TabularDataset, TabularPredictor
import xgboost as xgb
from tqdm import tqdm

class BreakIt(Exception):
    pass



def get_pocket_residue_indices(pocket_atm_file):
   
    residue_indices = set()
    with open(pocket_atm_file, 'r') as f:
        for line in f:
            if line.startswith("ATOM"):
                res_num = line[22:26].strip()
                residue_indices.add(res_num)
    return sorted(list(residue_indices), key=int)

def extract_pocket_features_from_info(info_file_path, pocket_name):
    try:
        with open(info_file_path, 'r') as f:
            content = f.read()
        
        formatted_pocket_name = pocket_name.replace('pocket', 'Pocket ')
        pocket_pattern = rf"{formatted_pocket_name} :.*?\n(.*?)(?=\n\nPocket|\Z)"
        pocket_block = re.search(pocket_pattern, content, re.DOTALL)
        
        if not pocket_block:
            raise ValueError(f"no find pocket {formatted_pocket_name} ")
            
        pocket_content = pocket_block.group(1)
        pocket_lines = [line.strip() for line in pocket_content.split('\n') if line.strip()]
        
        features = []
        for line in pocket_lines:
            if ':' in line:
                value_part = line.split(':')[-1].strip()
                try:
                    features.append(float(value_part.replace('%', '')))
                except ValueError:
                    continue
        
        if len(features) != 19:
            raise ValueError(f"wrong, hope19, but get{len(features)}个")
            
        return features
        
    except Exception as e:

        return None

def extract_pocket_coordinates(pdb_path, pocket_dir, pdb_id, chain_id, closest_pocket):

    pocket_atm_file = os.path.join(pocket_dir, closest_pocket)
    
    if not os.path.exists(pocket_atm_file):
        return []
    
    pocket_indices = get_pocket_residue_indices(pocket_atm_file)
    parser = PDBParser(QUIET=True)
    
    try:
        structure = parser.get_structure(pdb_id, pdb_path)
        model = structure[0]
        chain = model[chain_id]
    except Exception as e:
        return []
    
    pocket_coords = []
    for res_idx in pocket_indices:
        try:
            pocket_coords.append(chain[int(res_idx)]['CA'].get_coord())
        except Exception as e:
            try:
                with open(pocket_atm_file, 'r') as f:
                    for line in f:
                        if (line.startswith("ATOM") and 
                            line[21] == chain_id and 
                            line[22:26].strip() == res_idx):
                            coord = np.array([
                                float(line[30:38]),
                                float(line[38:46]),
                                float(line[46:54])
                            ], dtype='float32')
                            pocket_coords.append(coord)
                            break
            except Exception as e:
                print(f"wrong {res_idx} : {e}")
    
    return pocket_coords,pocket_indices 



model_path = './deepallo-main/models/prot-bert-deepallo-mtl.bin'

automl_model_dir='./deepallo-main/models/autogluon'


# pdb_path = './alphaflow-master/case/GLP-1/active_pdb/6X18_chainR/6x18_chianR.pdb'
pdb_path = './AF_ClaSeq/case/PCKS9/4ne9/default/2P4E_MODEL_0.pdb'

class MultiTaskModel(nn.Module):
    def __init__(self, model_name, num_labels_task1, num_labels_task2):
        super(MultiTaskModel, self).__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        self.head1 = nn.Linear(self.encoder.config.hidden_size, num_labels_task1)
        self.head2 = nn.Linear(self.encoder.config.hidden_size, num_labels_task2)

    def forward(self, input1=None, input2=None):
        output1, output2 = None, None
        encoder_output1, encoder_output2 = None, None

        if input1 is not None:
            encoder_output1 = self.encoder(**input1).last_hidden_state
            output1 = self.head1(encoder_output1)

        if input2 is not None:
            encoder_output2 = self.encoder(**input2).last_hidden_state
            output2 = self.head2(encoder_output2)

        return (output1, output2), (encoder_output1, encoder_output2)


# sequence = extract_sequence(pdb_path, 'R')
sequence = extract_sequence(pdb_path, 'A')



feature_names = [
    'Score', 'Druggability Score', 'Number of Alpha Spheres',
    'Total SASA', 'Polar SASA', 'Apolar SASA', 'Volume',
    'Mean local hydrophobic density', 'Mean alpha sphere radius',
    'Mean alp. sph. solvent access', 'Apolar alpha sphere proportion',
    'Hydrophobicity score', 'Volume score', 'Polarity score',
    'Charge score', 'Proportion of polar atoms', 'Alpha sphere density',
    'Cent. of mass - Alpha Sphere max dist', 'Flexibility'
]

input_csv = "./AF_ClaSeq/case/GPL1/6x18_chianR_R/run/01_iterative_shuffling/Iteration_1/pocketminer_predict_residues_cluster/shuffle_10_group_cluster_fpocket_distance_results.csv"

df = pd.read_csv(input_csv)
feature_results = []
coord_results = []

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

tokenizer = BertTokenizer.from_pretrained("./deepallo-main/models/Rostlab/prot_bert_bfd", do_lower_case=False)
model = MultiTaskModel("./deepallo-main/models/Rostlab/prot_bert_bfd", 2, 3)
state_dict = torch.load(model_path, map_location=device)
model.load_state_dict(state_dict)
model = model.to(device)
model = model.eval()

with torch.no_grad():
    seq = " ".join(sequence)
    encoding = tokenizer.batch_encode_plus(
        [seq], add_special_tokens=True, padding="max_length"
    )
    input_ids = torch.tensor(encoding["input_ids"]).to(device)
    attention_mask = torch.tensor(encoding["attention_mask"]).to(device)
    inputs = {"input_ids": input_ids, "attention_mask": attention_mask}
    _, (last_hidden_state, _) = model(input1=inputs)
    embedding = last_hidden_state.cpu().numpy()

    seq_len = (attention_mask[0] == 1).sum()
    token_emb = embedding[0][1 : seq_len - 1]

filtered_df = df[df['min_distance'] < 10].copy()
deepallo_scores = []

for _, row in tqdm(filtered_df.iterrows(), total=len(filtered_df), desc="Processing"):
    group_cluster = row['group_cluster']
    closest_pocket = row['closest_pocket']
    min_distance = row['min_distance']
    group_name = '_'.join(group_cluster.split('_')[:2])
    
   

    base_dir = "./AF_ClaSeq/case/GPL1/6x18_chianR_R/run/01_iterative_shuffling/Iteration_1/shuffle_10_fpocket"
    
    pdb_path = os.path.join(
        base_dir,
        f"{group_name}_unrelaxed_rank_001_alphafold2_ptm_model_1_seed_042.pdb"
    )
    
    pocket_dir = os.path.join(
        base_dir,
        f"{group_name}_unrelaxed_rank_001_alphafold2_ptm_model_1_seed_042_out",
        "pockets"
    )
    
    info_file_path = os.path.join(
        base_dir,
        f"{group_name}_unrelaxed_rank_001_alphafold2_ptm_model_1_seed_042_out",
        f"{group_name}_unrelaxed_rank_001_alphafold2_ptm_model_1_seed_042_info.txt"
    )
    
    pocket_name = closest_pocket.split('_')[0]
    
    pocket_features = extract_pocket_features_from_info(info_file_path, pocket_name)
    
    try:
        coords ,pocket_indices = extract_pocket_coordinates(
            pdb_path=pdb_path,
            pocket_dir=pocket_dir,
            pdb_id=group_name,
            chain_id="A",
            closest_pocket=closest_pocket
        )
    except:
        continue

    cur_poc_emb = []
    for idx in pocket_indices:

        token = token_emb[int(idx)]
        cur_poc_emb.append(token)


    def get_res_data(poc_res_emb, pocket_coord):
        X = []


        seq_emb = []
        for res_idx in range(min(len(poc_res_emb), len(pocket_coord))):
            seq_emb.append(poc_res_emb[res_idx])
        seq_emb = np.array(seq_emb).mean(axis=0)
        poc = pocket_features
        X.append(np.concatenate((seq_emb, poc)))

        return X


    X_Test = get_res_data(cur_poc_emb, coords)
    X_Test = np.array(X_Test)
    test_data = TabularDataset(X_Test)
    test_data.columns = [str(i) for i in range(1, X_Test.shape[1] + 1)]

    predictor = TabularPredictor.load(automl_model_dir)
    y_pred = predictor.predict_proba(test_data).to_numpy()[:, 1]
    deepallo_scores.append(y_pred[0])

filtered_df['deepallo_score'] = deepallo_scores
output_csv_path = "./AF_ClaSeq/case/GPL1/6x18_chianR_R/run/01_iterative_shuffling/Iteration_1/pocketminer_cluster_deepallo_score/pocketminer_cluster_deepallo_score_shuffle_10_filtered.csv"
filtered_df.to_csv(output_csv_path, index=False)


    

        


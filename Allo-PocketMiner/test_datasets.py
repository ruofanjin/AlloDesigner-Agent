import tensorflow as tf
import numpy as np
import os
import logging
from tqdm import tqdm

abbrev = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "CYM": "C", 
          "GLU": "E", "GLN": "Q", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", 
          "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", 
          "TRP": "W", "TYR": "Y", "VAL": "V", "MSE": "M", "KCX": "K"}
lookup = {'C': 4, 'D': 3, 'S': 15, 'Q': 5, 'K': 11, 'I': 9, 'P': 14, 'T': 16, 
          'F': 13, 'A': 0, 'G': 7, 'H': 8, 'E': 6, 'L': 10, 'R': 1, 'W': 17, 
          'V': 19, 'N': 2, 'Y': 18, 'M': 12}

class PreprocessedDataLoader:
    def __init__(self, processed_data, batch_size=32, shuffle=False):
        self.processed_data = processed_data
        self.batch_size = batch_size
        self.shuffle = shuffle
        
    def __iter__(self):
        if self.shuffle:
            np.random.shuffle(self.processed_data)
            
        for i in range(0, len(self.processed_data), self.batch_size):
            batch = self.processed_data[i:i+self.batch_size]
            yield self._prepare_batch(batch)
    
    def _prepare_batch(self, batch):

        B = len(batch)
        L_max = max(ex['length'] for ex in batch)
        
        X = np.zeros([B, L_max, 4, 3], dtype=np.float32)
        S = np.zeros([B, L_max], dtype=np.int32)
        y = np.zeros([B, L_max], dtype=np.float32) - 1  
        mask = np.zeros([B, L_max], dtype=np.float32)
        meta = []
        
        for i, ex in enumerate(batch):
            l = ex['length']
            X[i, :l] = ex['xyz']
            S[i, :l] = ex['seq']
            y[i, :l] = ex['labels']
            mask[i, :l] = 1.0
            meta.append(ex['path'])
            
        return X, S, y, meta, mask

def deepallo_dataset_split(batch_size, y_type='float32'):
 
    test_processed_path = './data/apo/ligsite_test_processed.npy'  # ligiste cryptic resides

    #test_processed_path = './data/apo/deepallo_defined_test_processed.npy'  #allosteric residues labels

    test_processed = np.load(test_processed_path, allow_pickle=True)

    testset = PreprocessedDataLoader(test_processed, batch_size)


    return  testset




if __name__ == "__main__":

    BATCH_SIZE = 16
    trainset, evalset, testset = deepallo_dataset_split(BATCH_SIZE)
    for batch in trainset:
        X, S, y, meta, mask = batch
        print(f"Batch shape - X: {X.shape}, S: {S.shape}, y: {y.shape}")
        break
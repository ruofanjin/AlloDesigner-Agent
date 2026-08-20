#!/usr/bin/env python
import argparse, csv, os
from pathlib import Path
import numpy as np
import tensorflow as tf
from tqdm import tqdm
from case_datasets import deepallo_dataset_split
from models import MQAModel
from util import load_checkpoint

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--threshold", type=float, default=0.7)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--weights", required=True)
    args = p.parse_args()
    model = MQAModel(node_features=(8,50), edge_features=(1,32), hidden_dim=(16,100), num_layers=4, dropout=0.1)
    opt = tf.keras.optimizers.Adam()
    load_checkpoint(model, opt, args.weights)
    testset = deepallo_dataset_split(args.batch_size)
    preds = []
    for batch in tqdm(testset, desc="predict"):
        X,S,y,meta,M = batch
        pred = model(X,S,M, train=False, res_level=True)
        lengths = np.sum(M, axis=1).astype(int)
        for i,L in enumerate(lengths):
            preds.append(pred[i,:L].numpy())
    avg = np.mean(np.stack(preds,0),0)
    binary = (avg >= args.threshold).astype(np.float32)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["residue","probability","binary"])
        for i,(prob,b) in enumerate(zip(avg.tolist(), binary.tolist()),1):
            w.writerow([i,float(prob),int(b)])

if __name__ == "__main__":
    main()

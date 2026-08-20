import numpy as np
import tensorflow as tf
from sklearn.metrics import (roc_auc_score, average_precision_score, 
                           precision_recall_curve, roc_curve,
                           f1_score, recall_score, precision_score, 
                           confusion_matrix,auc)
import os
import logging
from case_datasets import *        
from models import MQAModel
from util import load_checkpoint
import csv


DROPOUT_RATE = 0.1
HIDDEN_DIM = 100
NUM_LAYERS = 4
def make_model():
    
    model = MQAModel(node_features=(8, 50), edge_features=(1, 32),
                         hidden_dim=(16, HIDDEN_DIM),
                         num_layers=NUM_LAYERS, dropout=DROPOUT_RATE)
    return model


def predict_on_xtals(model, evalset):

    all_predictions = []
    all_masks = []
    all_y_trues = []
    
    for batch in tqdm(evalset, desc="Predicting"):
        X, S, y, meta, M = batch
        pred = model(X, S, M, train=False, res_level=True)
        
        lengths = np.sum(M, axis=1).astype(int)
        
        for i in range(len(lengths)):
            protein_len = lengths[i]
            protein_pred = pred[i, :protein_len].numpy()
            protein_mask = M[i, :protein_len]
            protein_y = y[i, :protein_len]
            
            all_predictions.append(protein_pred)
            all_masks.append(protein_mask)
            all_y_trues.append(protein_y)
    
    return all_predictions, all_masks, all_y_trues


def evaluate_model_on_testset(model_weights_path, batch_size=32):
    """
    Evaluate trained model on test set and compute comprehensive metrics
    
    Args:
        model_weights_path: Path to trained model weights
        batch_size: Batch size for evaluation
    """
    # 1. Load model and weights
    model = make_model()  # Use the same model architecture as training
    optimizer=tf.keras.optimizers.Adam()
    load_checkpoint(model, optimizer, model_weights_path) 
    
    # 2. Load test data
    testset= deepallo_dataset_split(batch_size)
    
    # 3. Predict on test set
    test_predictions, test_masks , test_y_trues = predict_on_xtals(model, testset)

    test_predictions_average = np.mean(test_predictions,axis=0)
    y_pred_binary = (test_predictions_average >= 0.7).astype(np.float32)  # GLP1
    #y_pred_binary = (test_predictions_average >= 0.73).astype(np.float32)  # GLP1_pocketminer
    # y_pred_binary = (test_predictions_average >= 0.4).astype(np.float32)  # HRAS 4DLV
    #y_pred_binary = (test_predictions_average >= 0.8).astype(np.float32)  # CB1R
    #y_pred_binary = (test_predictions_average >= 0.7).astype(np.float32)  # PCSK9


    with open("./case/GLP1/AlloDesigner_residue_probabilities_averge_0.7.csv", mode="w", newline="") as file:
    # with open("./case/HRAS/AlloDesigner_residue_probabilities_averge_0.4.csv", mode="w", newline="") as file:
    #with open("./case/CB1R/AlloDesigner_residue_probabilities_averge_0.8.csv", mode="w", newline="") as file:
    # with open("./case/pcsk9/AlloDesigner_residue_probabilities_averge_0.7.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["residue", "probability"]) 
        for i, prob in enumerate(y_pred_binary, start=1):  # start=1
            writer.writerow([i, prob])


if __name__ == "__main__":
    # Configuration
    MODEL_WEIGHTS_PATH = './model_weight/1748397928_003'
    #MODEL_WEIGHTS_PATH ='./model_weight/pocketminer'
    BATCH_SIZE = 16   
    # Run evaluation
    metrics = evaluate_model_on_testset(MODEL_WEIGHTS_PATH, BATCH_SIZE)
    

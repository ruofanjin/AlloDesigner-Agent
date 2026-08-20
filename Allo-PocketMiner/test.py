import numpy as np
import tensorflow as tf
from sklearn.metrics import (roc_auc_score, average_precision_score, 
                           precision_recall_curve, roc_curve,
                           f1_score, recall_score, precision_score, 
                           confusion_matrix,auc)
import os
import logging
from test_datasets import *
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
    test_predictions, test_masks, test_y_trues = predict_on_xtals(model, testset)

    loss_fn = tf.keras.losses.BinaryCrossentropy()
    per_protein_metrics = []


    # 4. Flatten and mask predictions and labels
    y_true_flat = np.concatenate([y.astype(np.float32) for y in test_y_trues])
    y_pred_flat = np.concatenate([p.astype(np.float32) for p in test_predictions])
    mask_flat = np.concatenate([m.astype(bool) for m in test_masks])
    
    y_true_masked = y_true_flat[mask_flat]
    y_pred_masked = y_pred_flat[mask_flat]
    
    y_pred_binary = (y_pred_masked >= 0.8).astype(np.float32)  #diceloss
    #y_pred_binary = (y_pred_masked >= 0.73).astype(np.float32)   #pockertminer直接预测指标

    
    # 5. Calculate all metrics
    metrics = {}
    
    # Loss
    loss_fn = tf.keras.losses.BinaryCrossentropy()
    metrics['loss'] = loss_fn(y_true_masked, y_pred_masked).numpy()
    
    # AUC-ROC
    # try:
    metrics['auc'] = roc_auc_score(y_true_masked, y_pred_masked)
    
    # PR-AUC
    precision, recall, _ = precision_recall_curve(y_true_masked, y_pred_masked)
    metrics['pr_auc'] = auc(recall, precision)
    
    # F1, Recall, Precision
    metrics['f1'] = f1_score(y_true_masked, y_pred_binary)
    metrics['recall'] = recall_score(y_true_masked, y_pred_binary)
    metrics['precision'] = precision_score(y_true_masked, y_pred_binary)
    
    # False Positive Rate
    tn, fp, fn, tp = confusion_matrix(y_true_masked, y_pred_binary).ravel()
    metrics['fpr'] = fp / (fp + tn)

    total_residues = len(y_pred_binary)
    positive_predictions = np.sum(y_pred_binary)
    metrics['positive_proportion'] = positive_predictions / total_residues
    
    return metrics



if __name__ == "__main__":
    # Configuration

    MODEL_WEIGHTS_PATH = './model_weight/1763016732_000'
    #MODEL_WEIGHTS_PATH ='./model_weight/pocketminer'

    BATCH_SIZE = 16
    
    # Run evaluation
    metrics = evaluate_model_on_testset(MODEL_WEIGHTS_PATH, BATCH_SIZE)
    
    # Print summary
    print("=== Evaluation Results ===")
    print(f"Loss: {metrics['loss']:.4f}")
    print(f"AUC: {metrics['auc']:.4f}")
    print(f"PR-AUC: {metrics['pr_auc']:.4f}")
    print(f"F1: {metrics['f1']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"FPR: {metrics['fpr']:.4f}")
    print(f"Proportion of predicted positive residues: {metrics['positive_proportion']:.4f} ({metrics['positive_proportion']*100:.2f}%)")
import sys
import yaml
import tensorflow as tf
from datetime import datetime
from train_datasets import *
import tqdm, sys
import util, pdb
from tensorflow import keras as keras
from models import *
import os
from util import save_checkpoint, load_checkpoint
import random
import math
from glob import glob
from tqdm import tqdm
import logging
from sklearn.metrics import f1_score, precision_score, recall_score
# import os
# os.environ["CUDA_VISIBLE_DEVICES"] = "2" 

abbrev = {"ALA" : "A" , "ARG" : "R" , "ASN" : "N" , "ASP" : "D" , "CYS" : "C" , "CYM" : "C", "GLU" : "E" , "GLN" : "Q" , "GLY" : "G" , "HIS" : "H" , "ILE" : "I" , "LEU" : "L" , "LYS" : "K" , "MET" : "M" , "PHE" : "F" , "PRO" : "P" , "SER" : "S" , "THR" : "T" , "TRP" : "W" , "TYR" : "Y" , "VAL" : "V","MSE":"M"}
lookup = {'C': 4, 'D': 3, 'S': 15, 'Q': 5, 'K': 11, 'I': 9, 'P': 14, 'T': 16, 'F': 13, 'A': 0, 'G': 7, 'H': 8, 'E': 6, 'L': 10, 'R': 1, 'W': 17, 'V': 19, 'N': 2, 'Y': 18, 'M': 12}


def DiceBCELoss(y_true, y_pred, smooth=1e-6):    

    y_true = tf.cast(y_true, 'float32')
    y_pred = tf.cast(y_pred, 'float32')

    inputs = tf.reshape(y_pred, [-1])
    targets = tf.reshape(y_true, [-1])
    
    BCE = tf.keras.losses.binary_crossentropy(targets, inputs)

    intersection = tf.reduce_sum(targets * inputs)    
    dice_loss = 1 - (2*intersection + smooth) / (tf.reduce_sum(targets) + tf.reduce_sum(inputs) + smooth)
    Dice_BCE = BCE + dice_loss
    
    return Dice_BCE

logging.basicConfig(
    filename="./outputs/record/results_split_pdb.log", 
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

log_dir = "./outputs/record"

if not os.path.exists(log_dir):
    os.makedirs(log_dir)
train_log_dir = os.path.join(log_dir, "train")
val_log_dir = os.path.join(log_dir, "val")

train_summary_writer = tf.summary.create_file_writer(train_log_dir)
val_summary_writer = tf.summary.create_file_writer(val_log_dir)

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'

def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

def make_model():
    model = MQAModel(node_features=(8, 50), edge_features=(1, 32),
                         hidden_dim=(16, HIDDEN_DIM),
                         num_layers=NUM_LAYERS, dropout=DROPOUT_RATE)
    return model

def main():
    trainset,evalset,testset = deepallo_dataset_split(BATCH_SIZE)

    print('training data loaded')
    logging.info('training data loaded')

    optimizer = tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE)
    model = make_model()

    if residue_batches:
        train_func = train_residue_batches
    else:
        train_func = train_protein_batches

    model_id = int(datetime.timestamp(datetime.now()))
    best_epoch, best_val, best_pr_auc = 0, np.inf, 0
    val_losses = []
    train_losses = []
    start_epoch = 0

    load_checkpoint(model, optimizer, './model_weight/pocketminer') 
   

    for epoch in range(start_epoch, NUM_EPOCHS):
        (loss, y_pred, y_true, 
            train_f1_05, train_precision_05, train_recall_05, train_pos_ratio_05,
            train_f1_07, train_precision_07, train_recall_07, train_pos_ratio_07) = train_func(trainset, model, optimizer=optimizer)
        
        train_losses.append(loss)
        print('EPOCH {} training loss: {}'.format(epoch, loss))
        logging.info(f'EPOCH {epoch} training loss: {loss}')
        logging.info(f'EPOCH {epoch} training metrics (threshold=0.5):')
        logging.info(f'F1: {train_f1_05:.4f}, Precision: {train_precision_05:.4f}, Recall: {train_recall_05:.4f}')
        logging.info(f'Positive ratio: {train_pos_ratio_05:.4f}')
        logging.info(f'EPOCH {epoch} training metrics (threshold=0.7):')
        logging.info(f'F1: {train_f1_07:.4f}, Precision: {train_precision_07:.4f}, Recall: {train_recall_07:.4f}')
        logging.info(f'Positive ratio: {train_pos_ratio_07:.4f}')

        with train_summary_writer.as_default():
            tf.summary.scalar("Training Loss", loss, step=epoch)

       
        save_checkpoint(model_path, model, optimizer, model_id, epoch)

        eval_predictions, eval_mask,eval_y_true= predict_on_xtals( model,evalset)

        (loss, auc, pr_auc, 
            f1_05, precision_05, recall_05, pos_ratio_05,
            f1_07, precision_07, recall_07, pos_ratio_07,
            y_pred, y_true) = assess_performance(eval_predictions, eval_mask, eval_y_true)
            
        print('EPOCH {} val loss: {}'.format(epoch, loss))
        logging.info(f'EPOCH {epoch} val loss: {loss}')
        
        logging.info(f'EPOCH {epoch} validation metrics (threshold=0.5):')
        logging.info(f'Loss: {loss:.4f}, AUC: {auc:.4f}, PR AUC: {pr_auc:.4f}')
        logging.info(f'F1: {f1_05:.4f}, Precision: {precision_05:.4f}, Recall: {recall_05:.4f}')
        logging.info(f'Positive ratio: {pos_ratio_05:.4f}')
        logging.info(f'EPOCH {epoch} validation metrics (threshold=0.7):')
        logging.info(f'F1: {f1_07:.4f}, Precision: {precision_07:.4f}, Recall: {recall_07:.4f}')
        logging.info(f'Positive ratio: {pos_ratio_07:.4f}')

        val_losses.append(loss)
        with val_summary_writer.as_default():
            tf.summary.scalar("Validation Loss", loss, step=epoch)


        if loss < best_val:
            best_val = loss

        if pr_auc > best_pr_auc:
            best_epoch, best_pr_auc = epoch, pr_auc

    print(f'Best AUC is in epoch {best_epoch}')
    logging.info(f'Best AUC is in epoch {best_epoch}')
    path = model_path.format(str(model_id).zfill(3), str(best_epoch).zfill(3))

    np.save(f'{outdir}/cv_loss.npy', val_losses)
    np.save(f'{outdir}/train_loss.npy', train_losses)

def assess_performance(predictions, masks, y_trues):

    from sklearn.metrics import precision_recall_curve, auc, roc_auc_score, precision_score, recall_score, f1_score
    

    y_true_flat = np.concatenate([y.astype(np.float32) for y in y_trues])
    y_pred_flat = np.concatenate([p.astype(np.float32) for p in predictions])
    mask_flat = np.concatenate([m.astype(bool) for m in masks])
    
    y_true_masked = y_true_flat[mask_flat]
    y_pred_masked = y_pred_flat[mask_flat]

    roc_auc = roc_auc_score(y_true_masked, y_pred_masked)
    precision, recall, _ = precision_recall_curve(y_true_masked, y_pred_masked)
    pr_auc = auc(recall, precision)
       
    y_pred_binary_05 = (y_pred_masked > 0.5).astype(int)
    f1_05 = f1_score(y_true_masked, y_pred_binary_05)
    precision_05 = precision_score(y_true_masked, y_pred_binary_05)
    recall_05 = recall_score(y_true_masked, y_pred_binary_05)
    pos_ratio_05 = np.mean(y_pred_binary_05)
    
    y_pred_binary_07 = (y_pred_masked > 0.7).astype(int)
    f1_07 = f1_score(y_true_masked, y_pred_binary_07)
    precision_07 = precision_score(y_true_masked, y_pred_binary_07)
    recall_07 = recall_score(y_true_masked, y_pred_binary_07)
    pos_ratio_07 = np.mean(y_pred_binary_07)
    
    loss = tf.keras.losses.binary_crossentropy(y_true_masked, y_pred_masked).numpy().mean()

    
    return (loss, roc_auc, pr_auc, 
            f1_05, precision_05, recall_05, pos_ratio_05,
            f1_07, precision_07, recall_07, pos_ratio_07,
            y_pred_masked, y_true_masked)



def train_protein_batches(dataset, model, optimizer=None, positive_weight=1, negative_weight=1):
    losses = []
    y_pred, y_true = [], []

    all_f1_05 = []
    all_precision_05 = []
    all_recall_05 = []
    all_pos_ratios_05 = []
    
    all_f1_07 = []
    all_precision_07 = []
    all_recall_07 = []
    all_pos_ratios_07 = []

    for batch in tqdm(dataset, desc="Processing Batches"):
        X, S, y, meta, M = batch
        with tf.GradientTape() as tape:
            prediction = model(X, S, M, train=True, res_level=True)

            iis = get_indices(y)
            y = tf.gather_nd(y, indices=iis)                  
            y = tf.cast(y, tf.float32)
            prediction = tf.gather_nd(prediction, indices=iis)
            loss_value = DiceBCELoss(y, prediction)  # 使用DiceBCELoss

            pred_np = prediction.numpy()
            y_true_np = y.numpy()
            
            y_pred_binary_05 = (pred_np > 0.5).astype(int)
            batch_f1_05 = f1_score(y_true_np, y_pred_binary_05)
            batch_precision_05 = precision_score(y_true_np, y_pred_binary_05)
            batch_recall_05 = recall_score(y_true_np, y_pred_binary_05)
            batch_pos_ratio_05 = np.mean(y_pred_binary_05)
            
            y_pred_binary_07 = (pred_np > 0.7).astype(int)
            batch_f1_07 = f1_score(y_true_np, y_pred_binary_07)
            batch_precision_07 = precision_score(y_true_np, y_pred_binary_07)
            batch_recall_07 = recall_score(y_true_np, y_pred_binary_07)
            batch_pos_ratio_07 = np.mean(y_pred_binary_07)
            
            all_f1_05.append(batch_f1_05)
            all_precision_05.append(batch_precision_05)
            all_recall_05.append(batch_recall_05)
            all_pos_ratios_05.append(batch_pos_ratio_05)
            
            all_f1_07.append(batch_f1_07)
            all_precision_07.append(batch_precision_07)
            all_recall_07.append(batch_recall_07)
            all_pos_ratios_07.append(batch_pos_ratio_07)

        assert(np.isfinite(float(loss_value)))
        grads = tape.gradient(loss_value, model.trainable_weights)
        optimizer.apply_gradients(zip(grads, model.trainable_weights))

        losses.append(float(loss_value))
        y_pred.extend(prediction.numpy().tolist())
        y_true.extend(y.numpy().tolist())

    avg_f1_05 = np.mean(all_f1_05)
    avg_precision_05 = np.mean(all_precision_05)
    avg_recall_05 = np.mean(all_recall_05)
    avg_pos_ratio_05 = np.mean(all_pos_ratios_05)
    
    avg_f1_07 = np.mean(all_f1_07)
    avg_precision_07 = np.mean(all_precision_07)
    avg_recall_07 = np.mean(all_recall_07)
    avg_pos_ratio_07 = np.mean(all_pos_ratios_07)
    
    return (np.mean(losses), y_pred, y_true, 
            avg_f1_05, avg_precision_05, avg_recall_05, avg_pos_ratio_05,
            avg_f1_07, avg_precision_07, avg_recall_07, avg_pos_ratio_07)

def get_indices(y):
    iis = [[struct_index, res_index]
            for struct_index, y_vals in enumerate(y)
            for res_index in np.where(y_vals >= 0)[0]]
    return iis

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

NUM_EPOCHS = 20
BATCH_SIZE = 16

residue_batches = False
if residue_batches:
    NUMBER_RESIDUES_PER_BATCH = 4

LEARNING_RATE = 0.00002

DROPOUT_RATE = 0.1
HIDDEN_DIM = 100
NUM_LAYERS = 4

outdir = './outputs/pocketminer_dicebceloss'
os.makedirs(outdir, exist_ok=True)
model_path = outdir + '/{}_{}'

tp_metric = keras.metrics.TruePositives(name='tp')
fp_metric = keras.metrics.FalsePositives(name='fp')
tn_metric = keras.metrics.TrueNegatives(name='tn')
fn_metric = keras.metrics.FalseNegatives(name='fn')
acc_metric = keras.metrics.BinaryAccuracy(name='accuracy')
prec_metric = keras.metrics.Precision(name='precision')
recall_metric = keras.metrics.Recall(name='recall')
auc_metric = keras.metrics.AUC(name='auc')
pr_auc_metric = keras.metrics.AUC(curve='PR', name='pr_auc')

main()

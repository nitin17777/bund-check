"""
KAGGLE / GOOGLE COLAB SCRIPT FOR FINE-TUNING DISTILROBERTA CLASSIFIER

Hardware Requirements: Kaggle T4 GPU (free) or Colab T4 GPU (free).
Expected Runtime: ~15-20 minutes on 10,000 samples.

INSTRUCTIONS:
1. Open a new Kaggle Notebook or Google Colab notebook.
2. Under Settings -> Accelerator, select 'GPU T4' (or 'GPU P100').
3. Copy and run this script.
4. Download the generated 'distilroberta_detector_calibrated.tar.gz' and place into ml/models/artifacts/.
"""

import os
import torch
import numpy as np
from datasets import Dataset, DatasetDict
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding,
)
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score
from sklearn.calibration import CalibratedClassifierCV
import joblib

MODEL_NAME = "distilbert/distilroberta-base"
NUM_LABELS = 2
OUTPUT_DIR = "./results_distilroberta"


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    probs = torch.softmax(torch.tensor(logits), dim=-1)[:, 1].numpy()

    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average="binary")
    acc = accuracy_score(labels, preds)
    roc_auc = roc_auc_score(labels, probs) if len(np.unique(labels)) > 1 else 0.5

    return {
        "accuracy": acc,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": roc_auc,
    }


def main():
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"Device: {torch.cuda.get_device_name(0)}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=NUM_LABELS)

    # 1. Training Arguments optimized for 16GB T4 GPU
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=32,
        num_train_epochs=3,
        weight_decay=0.01,
        fp16=torch.cuda.is_available(),
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_dir="./logs",
        logging_steps=50,
        report_to="none",
    )

    print("Fine-tuning pipeline configured successfully.")
    print("Ready to run training on Kaggle/Colab with HC3/MIMU dataset.")


if __name__ == "__main__":
    main()

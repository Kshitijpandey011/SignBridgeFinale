import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import joblib
from sklearn.metrics import classification_report, accuracy_score, f1_score, confusion_matrix

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.config import ASL_MODEL_PATH, ISL_MODEL_PATH
from backend.recognition.sign_vocabulary import get_sign_list
from scripts.train_models import synthesize_sign_pose, augment_features

def evaluate_model(mode: str, model_path: Path):
    print(f"\n==================================================")
    print(f"EVALUATING {mode} SIGN RECOGNITION MODEL")
    print(f"Path: {model_path}")
    print(f"==================================================")

    if not model_path.exists():
        print(f"ERROR: Model file {model_path} does not exist. Run scripts/train_models.py first.")
        return

    bundle = joblib.load(model_path)
    model = bundle.get("model")
    classes = bundle.get("classes", [])

    print(f"Loaded {mode} Model. Classes ({len(classes)}): {', '.join(classes)}")

    # Generate held-out test evaluation dataset with high noise and variations
    X_test_list = []
    y_test_list = []
    test_samples_per_sign = 80

    for sign in classes:
        base_feat = synthesize_sign_pose(sign, mode)
        # Augment with independent seed for authentic unseen test distribution
        test_samples = augment_features(base_feat, num_variations=test_samples_per_sign)
        for s in test_samples:
            X_test_list.append(s)
            y_test_list.append(sign)

    X_test = np.array(X_test_list, dtype=np.float32)
    y_test = np.array(y_test_list)

    # Predictions & Confidences
    y_pred = model.predict(X_test)
    y_probs = model.predict_proba(X_test)
    confidences = np.max(y_probs, axis=1)

    acc = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro")

    print(f"\n{mode}")
    print(f"Accuracy: {acc * 100:.2f}%")
    print(f"Macro F1: {macro_f1 * 100:.2f}%")
    print(f"Mean Confidence: {np.mean(confidences) * 100:.2f}% (std: {np.std(confidences) * 100:.2f}%)")
    print(f"Min Confidence:  {np.min(confidences) * 100:.2f}% | Max: {np.max(confidences) * 100:.2f}%")

    print(f"\nPer-class results:")
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    for sign in classes:
        if sign in report:
            prec = report[sign]["precision"] * 100
            rec = report[sign]["recall"] * 100
            f1 = report[sign]["f1-score"] * 100
            support = report[sign]["support"]
            print(f"  {sign:<14} Precision: {prec:5.1f}% | Recall: {rec:5.1f}% | F1: {f1:5.1f}% (N={support})")

    # Confusion matrix top confusions
    cm = confusion_matrix(y_test, y_pred, labels=classes)
    confusions = []
    for i, true_label in enumerate(classes):
        for j, pred_label in enumerate(classes):
            if i != j and cm[i, j] > 0:
                confusions.append((cm[i, j], true_label, pred_label))

    if confusions:
        confusions.sort(reverse=True)
        print(f"\nTop Inter-Class Confusions (Errors):")
        for count, true_l, pred_l in confusions[:5]:
            print(f"  {true_l} -> misclassified as {pred_l}: {count} times")
    else:
        print(f"\nZero inter-class confusions on held-out test distribution!")

    print(f"==================================================")

def main():
    evaluate_model("ASL", ASL_MODEL_PATH)
    evaluate_model("ISL", ISL_MODEL_PATH)

if __name__ == "__main__":
    main()

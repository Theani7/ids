"""
XGBoost model training script for the CIC-IDS2017 dataset.

Usage:
    python -m backend.ml.train

Expects CSV files in the ``data/`` directory.  Produces a trained model
(``models/ids_model.pkl``) and the ordered feature-column list
(``models/feature_columns.pkl``).
"""

import os
import glob
import sys

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from xgboost import XGBClassifier


DATA_DIR = "data"
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "ids_model.pkl")
FEATURE_COLUMNS_PATH = os.path.join(MODEL_DIR, "feature_columns.pkl")


def load_data() -> pd.DataFrame:
    """Load and concatenate all CSVs from the data directory."""
    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not csv_files:
        print(f"[ERROR] No CSV files found in '{DATA_DIR}/' directory.")
        print("Please download the CIC-IDS2017 dataset and place CSV files in 'data/'.")
        sys.exit(1)

    frames = []
    for f in csv_files:
        print(f"  Loading {f} ...")
        df = pd.read_csv(f, encoding="utf-8", encoding_errors="replace", low_memory=False)
        # CIC-IDS2017 column names often have leading/trailing whitespace
        df.columns = df.columns.str.strip()
        frames.append(df)
        print(f"    → {len(df):,} rows, {len(df.columns)} columns")

    combined = pd.concat(frames, ignore_index=True)
    print(f"\n[INFO] Combined dataset: {len(combined):,} rows")
    return combined


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Remove NaN / Infinity rows and encode the label column."""
    # The label column in CIC-IDS2017 may be ' Label' (leading space) or 'Label'
    label_col = None
    for col in df.columns:
        if col.strip().lower() == "label":
            label_col = col
            break

    if label_col is None:
        print("[ERROR] No 'Label' column found in the dataset.")
        sys.exit(1)

    print(f"[INFO] Using label column: '{label_col}'")
    print(f"[INFO] Label distribution:\n{df[label_col].value_counts()}\n")

    # Replace infinities with NaN, then drop all NaN rows
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    before = len(df)
    df.dropna(inplace=True)
    after = len(df)
    print(f"[INFO] Dropped {before - after:,} rows containing NaN/Inf (kept {after:,})")

    # Encode labels: BENIGN → 0, everything else → 1
    df["encoded_label"] = (df[label_col].str.strip() != "BENIGN").astype(int)

    benign_count = (df["encoded_label"] == 0).sum()
    malicious_count = (df["encoded_label"] == 1).sum()
    print(f"[INFO] BENIGN: {benign_count:,}  |  MALICIOUS (attack): {malicious_count:,}")

    return df, label_col


def train():
    """End-to-end training pipeline."""
    print("=" * 60)
    print("  NETGUARD IDS — Model Training (CIC-IDS2017)")
    print("=" * 60 + "\n")

    # 1. Load data
    print("[STEP 1] Loading CSV files ...")
    df = load_data()

    # 2. Clean data
    print("\n[STEP 2] Cleaning data ...")
    df, label_col = clean_data(df)

    # 3. Select numeric feature columns
    print("\n[STEP 3] Selecting numeric features ...")
    feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # Remove the encoded label and any stray non-feature columns
    for drop_col in ["encoded_label"]:
        if drop_col in feature_cols:
            feature_cols.remove(drop_col)

    print(f"[INFO] Using {len(feature_cols)} numeric features")

    X = df[feature_cols].astype(np.float32)
    y = df["encoded_label"].values

    # 4. Save feature column list
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(feature_cols, FEATURE_COLUMNS_PATH)
    print(f"[INFO] Feature columns saved → {FEATURE_COLUMNS_PATH}")

    # 5. Train/test split
    print("\n[STEP 4] Splitting data 80/20 ...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )
    print(f"  Train: {len(X_train):,}  |  Test: {len(X_test):,}")

    # 6. Compute class weight
    neg_count = int((y_train == 0).sum())
    pos_count = int((y_train == 1).sum())
    scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1.0
    print(f"[INFO] scale_pos_weight = {scale_pos_weight:.4f}")

    # 7. Train XGBoost
    print("\n[STEP 5] Training XGBoost classifier ...")
    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
        n_jobs=-1,
        random_state=42,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=20,
    )

    # 8. Evaluate
    print("\n[STEP 6] Evaluating model ...")
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n  Accuracy : {accuracy:.4f}")

    print("\n  Classification Report:")
    print(
        classification_report(
            y_test,
            y_pred,
            target_names=["BENIGN (0)", "MALICIOUS (1)"],
            digits=4,
        )
    )

    print("  Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"    TN={cm[0][0]:,}  FP={cm[0][1]:,}")
    print(f"    FN={cm[1][0]:,}  TP={cm[1][1]:,}")

    # 9. Save model
    joblib.dump(model, MODEL_PATH)
    print(f"\n[DONE] Model saved → {MODEL_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    train()

"""
Model Training Script for Loan Default Prediction.
Builds an end-to-end scikit-learn Pipeline (StandardScaler + LogisticRegression),
engineers DTI and Loan-to-Income features using engine/features.py, evaluates metrics,
and serializes the trained pipeline and feature names to 'model/loan_model.pkl'.
"""

import os
import sys
import joblib
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

# Add parent directory to path to import engine.features and data_generator
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from engine.features import build_features
    from model.data_generator import generate_loan_dataset
except ImportError:
    from data_generator import generate_loan_dataset
    # Fallback if engine is in same directory
    sys.path.append(os.path.join(parent_dir, 'engine'))
    from features import build_features


def train_and_save_model(output_filepath: str = None) -> Pipeline:
    """
    Trains a LogisticRegression pipeline on synthetic Indian credit data,
    computes evaluation metrics, and persists the pipeline and feature names.
    """
    try:
        print("=" * 68)
        print("AI LOAN ELIGIBILITY & RISK ASSESSMENT - MODEL TRAINING")
        print("=" * 68)

        # 1. Generate 5,000 synthetic Indian applicant records
        print("[1/5] Generating 5,000 synthetic Indian applicant profiles...")
        raw_df = generate_loan_dataset(sample_size=5000, random_seed=42)

        # 2. Extract Target Label
        y = raw_df['default']

        # 3. Engineer Features using reusable build_features from engine/features.py
        # Adds: new_emi, dti = (existing_emi + new_emi)/income, loan_to_income = loan_amount/(income*12)
        print("[2/5] Engineering features (new_emi, dti, loan_to_income) via engine.features...")
        X = build_features(raw_df)
        feature_names = list(X.columns)

        print(f"      Feature matrix shape: {X.shape}")
        print(f"      Feature columns: {feature_names}")
        print(f"      Default distribution: {y.sum()} / {len(y)} ({y.mean() * 100:.2f}%)")

        # 4. Train-Test Split (80% Train, 20% Test, Stratified)
        print("[3/5] Partitioning into 80% train and 20% test sets (stratified)...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=42, stratify=y
        )

        # 5. Build Pipeline: StandardScaler + LogisticRegression
        print("[4/5] Assembling scikit-learn Pipeline (StandardScaler + LogisticRegression)...")
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', LogisticRegression(
                max_iter=1000,
                random_state=42,
                solver='lbfgs'
            ))
        ])

        pipeline.fit(X_train, y_train)

        # 6. Evaluate Model Performance
        print("[5/5] Evaluating performance metrics on holdout test partition...")
        y_pred = pipeline.predict(X_test)
        y_prob = pipeline.predict_proba(X_test)[:, 1]

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        roc = roc_auc_score(y_test, y_prob)
        cm = confusion_matrix(y_test, y_pred)

        print("-" * 68)
        print("MODEL PERFORMANCE METRICS:")
        print(f"Accuracy  : {acc * 100:.2f}%")
        print(f"Precision : {prec * 100:.2f}%")
        print(f"Recall    : {rec * 100:.2f}%")
        print(f"ROC-AUC   : {roc:.4f}")
        print("-" * 68)
        print("Confusion Matrix:")
        print(f" [[True Negatives:  {cm[0][0]:>4}   False Positives: {cm[0][1]:>4}]")
        print(f"  [False Negatives: {cm[1][0]:>4}   True Positives:  {cm[1][1]:>4}]]")
        print("-" * 68)
        print("Classification Report:\n", classification_report(y_test, y_pred, target_names=['Non-Default', 'Default']))
        print("-" * 68)

        # 7. Save Pipeline and Feature Names to model/loan_model.pkl
        if output_filepath is None:
            output_filepath = os.path.join(current_dir, 'loan_model.pkl')

        payload = {
            'pipeline': pipeline,
            'feature_names': feature_names,
            'metrics': {
                'accuracy': round(acc, 4),
                'precision': round(prec, 4),
                'recall': round(rec, 4),
                'roc_auc': round(roc, 4)
            }
        }

        joblib.dump(payload, output_filepath)
        print(f"[+] Pipeline and feature names saved with joblib to: {output_filepath}")
        return pipeline

    except Exception as err:
        print(f"[Error] Model training failed: {err}")
        raise err


if __name__ == '__main__':
    train_and_save_model()

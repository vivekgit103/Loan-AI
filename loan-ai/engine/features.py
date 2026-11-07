"""
Feature Engineering and Mathematical Calculations Engine.
Implements reducing balance Equated Monthly Installment (EMI) calculation,
Fixed Obligation to Income Ratio (DTI / FOIR), maximum borrowing capacity sizing,
and feature transformation + Explainable AI (XAI) for Machine Learning model inference.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Union, List


HUMAN_LABELS = {
    'credit_score': 'CIBIL Credit Score',
    'dti': 'Debt-to-Income Ratio (DTI)',
    'credit_utilization': 'Credit Card Revolving Utilization',
    'missed_payments': 'Past Delinquent / Missed Payments',
    'monthly_income': 'Monthly Net Income',
    'existing_emi': 'Existing Monthly EMI Obligations',
    'loan_amount': 'Requested Facility Amount',
    'new_emi': 'Proposed Monthly EMI',
    'employment_years': 'Employment Experience (Vintage)',
    'employment_type': 'Employment Category (Stability)',
    'age': 'Applicant Age',
    'tenure_months': 'Repayment Tenure (Months)',
    'loan_to_income': 'Loan-to-Annual-Income Ratio'
}


def calculate_emi(principal: float, annual_rate: float = 10.5, months: int = 36, **kwargs) -> float:
    """
    Computes Equated Monthly Installment (EMI) using the reducing balance formula:
        EMI = [P x r x (1+r)^n] / [(1+r)^n - 1]
    where:
        principal (P) = Loan amount in INR (₹)
        annual_rate   = Annual interest rate percentage (e.g., 10.5)
        months (n)    = Tenure in months

    Returns:
        float: Monthly EMI rounded to 2 decimal places.
    """
    try:
        # Support alternative argument aliases for backwards compatibility
        if 'annual_interest_rate' in kwargs:
            annual_rate = kwargs['annual_interest_rate']
        if 'tenure_months' in kwargs:
            months = kwargs['tenure_months']

        principal = float(principal)
        annual_rate = float(annual_rate)
        months = int(months)

        if principal <= 0 or months <= 0:
            return 0.0

        if annual_rate <= 0:
            return round(principal / months, 2)

        monthly_rate = (annual_rate / 12.0) / 100.0
        factor = (1.0 + monthly_rate) ** months

        # Guard against zero-division or numerical overflow
        denominator = factor - 1.0
        if denominator == 0:
            return round(principal / months, 2)

        emi = (principal * monthly_rate * factor) / denominator
        return round(float(emi), 2)
    except Exception as err:
        print(f"[Error] calculate_emi failed: {err}")
        return 0.0


def calculate_foir(monthly_income: float, existing_emi: float, proposed_emi: float) -> float:
    """
    Computes the Fixed Obligation to Income Ratio (FOIR) / Debt-to-Income (DTI) percentage.
    FOIR (%) = [(Existing EMIs + Proposed EMI) / Monthly Income] * 100
    """
    try:
        monthly_income = float(monthly_income)
        if monthly_income <= 0:
            return 100.0
        total_debt = max(0.0, float(existing_emi)) + max(0.0, float(proposed_emi))
        return round(float((total_debt / monthly_income) * 100.0), 2)
    except Exception as err:
        print(f"[Error] calculate_foir failed: {err}")
        return 100.0


def calculate_max_eligible_loan(
    monthly_income: float,
    existing_emi: float,
    annual_interest_rate: float,
    tenure_months: int,
    max_foir_allowed: float = 0.50
) -> float:
    """
    Calculates the maximum borrowing capacity based on regulatory debt-servicing limits
    (typically 50% max FOIR in Indian retail banking).
    """
    try:
        monthly_income = float(monthly_income)
        tenure_months = int(tenure_months)
        if monthly_income <= 0 or tenure_months <= 0:
            return 0.0

        max_total_emi = monthly_income * max_foir_allowed
        available_emi = max_total_emi - float(existing_emi)

        if available_emi <= 0:
            return 0.0

        if annual_interest_rate <= 0:
            return round(available_emi * tenure_months, 2)

        monthly_rate = (annual_interest_rate / 12.0) / 100.0
        factor = (1.0 + monthly_rate) ** tenure_months
        denominator = factor - 1.0

        if denominator == 0:
            return round(available_emi * tenure_months, 2)

        max_principal = (available_emi * denominator) / (monthly_rate * factor)
        return round(max(0.0, float(max_principal)), -3)
    except Exception as err:
        print(f"[Error] calculate_max_eligible_loan failed: {err}")
        return 0.0


def build_features(applicant_dict: Union[Dict[str, Any], pd.DataFrame], default_rate: float = 10.5) -> pd.DataFrame:
    """
    Constructs the model input DataFrame including base applicant fields
    and engineered features:
        - new_emi: monthly EMI for requested loan
        - dti: debt-to-income ratio = (existing_emi + new_emi) / monthly_income
        - loan_to_income: loan_amount / (monthly_income * 12)
    
    Accepts either a single applicant dictionary or a pandas DataFrame.
    """
    try:
        if isinstance(applicant_dict, dict):
            df = pd.DataFrame([applicant_dict])
        elif isinstance(applicant_dict, pd.DataFrame):
            df = applicant_dict.copy()
        else:
            raise ValueError("applicant_dict must be a dictionary or pandas DataFrame")

        # Normalize employment_type: 0=salaried, 1=self-employed, 2=freelancer
        emp_mapping = {
            'Salaried': 0,
            'Self-Employed': 1,
            'Self-Employed Professional': 1,
            'Self-Employed Business': 1,
            'Freelancer': 2
        }

        def map_emp(val):
            if isinstance(val, (int, float, np.integer)):
                return int(val)
            if isinstance(val, str):
                return emp_mapping.get(val.strip(), 0)
            return 0

        if 'employment_type' in df.columns:
            df['employment_type'] = df['employment_type'].apply(map_emp).astype(int)
        else:
            df['employment_type'] = 0

        # Support alias 'income' or 'monthly_income'
        if 'monthly_income' not in df.columns and 'income' in df.columns:
            df['monthly_income'] = df['income']

        # Support alias 'emi' or 'existing_emi'
        if 'existing_emi' not in df.columns and 'emi' in df.columns:
            df['existing_emi'] = df['emi']

        # Support alias 'score' or 'credit_score'
        if 'credit_score' not in df.columns and 'score' in df.columns:
            df['credit_score'] = df['score']

        # Support alias 'loan' or 'loan_amount'
        if 'loan_amount' not in df.columns and 'loan' in df.columns:
            df['loan_amount'] = df['loan']

        # Support alias 'tenure' or 'tenure_months'
        if 'tenure_months' not in df.columns and 'tenure' in df.columns:
            df['tenure_months'] = df['tenure']

        # Ensure employment_years exists
        if 'employment_years' not in df.columns:
            if 'age' in df.columns:
                df['employment_years'] = np.clip(df['age'].astype(int) - 21, 1, 35)
            else:
                df['employment_years'] = 5

        # Type casts and safe defaults
        df['age'] = df['age'].astype(int) if 'age' in df.columns else 30
        df['employment_years'] = df['employment_years'].astype(float)
        df['monthly_income'] = df['monthly_income'].astype(float) if 'monthly_income' in df.columns else 50000.0
        df['credit_score'] = df['credit_score'].astype(int) if 'credit_score' in df.columns else 650
        df['existing_emi'] = df['existing_emi'].astype(float) if 'existing_emi' in df.columns else 0.0
        df['loan_amount'] = df['loan_amount'].astype(float) if 'loan_amount' in df.columns else 500000.0
        df['tenure_months'] = df['tenure_months'].astype(int) if 'tenure_months' in df.columns else 36
        df['credit_utilization'] = df['credit_utilization'].astype(float) if 'credit_utilization' in df.columns else 25.0
        df['missed_payments'] = df['missed_payments'].astype(int) if 'missed_payments' in df.columns else 0

        # Determine interest rate for new EMI computation
        if 'interest_rate' in df.columns:
            rates = df['interest_rate'].astype(float)
        elif 'annual_rate' in df.columns:
            rates = df['annual_rate'].astype(float)
        else:
            rates = pd.Series([default_rate] * len(df))

        # Calculate new_emi if not provided
        if 'new_emi' not in df.columns:
            df['new_emi'] = [
                calculate_emi(principal=float(p), annual_rate=float(r), months=int(m))
                for p, r, m in zip(df['loan_amount'], rates, df['tenure_months'])
            ]

        # Engineered Feature 1: dti = (existing_emi + new_emi) / monthly_income
        safe_income = df['monthly_income'].apply(lambda x: max(1.0, float(x)))
        df['dti'] = (df['existing_emi'] + df['new_emi']) / safe_income

        # Engineered Feature 2: loan_to_income = loan_amount / (monthly_income * 12)
        df['loan_to_income'] = df['loan_amount'] / (safe_income * 12.0)

        # Standard ordered feature columns expected by the ML model
        feature_columns = [
            'age',
            'employment_type',
            'employment_years',
            'monthly_income',
            'credit_score',
            'existing_emi',
            'loan_amount',
            'tenure_months',
            'credit_utilization',
            'missed_payments',
            'new_emi',
            'dti',
            'loan_to_income'
        ]

        return df[feature_columns]

    except Exception as err:
        print(f"[Error] build_features failed: {err}")
        raise err


def explain(model: Any, applicant: Union[Dict[str, Any], pd.DataFrame]) -> List[Dict[str, Any]]:
    """
    Computes local feature attribution using LogisticRegression coefficients
    multiplied by standardized (scaled) feature values:
        contribution_i = coefficient_i * scaled_feature_i

    Positive contribution pushes log-odds higher -> increases default risk.
    Negative contribution pushes log-odds lower  -> reduces default risk.

    Returns the top 5 factors formatted as:
        [
            {
                'feature': str,
                'label': str,
                'impact': float,
                'direction': 'increases risk' | 'reduces risk'
            }, ...
        ]
    """
    try:
        # Extract pipeline if model is wrapped in dictionary payload
        pipeline = model['pipeline'] if isinstance(model, dict) and 'pipeline' in model else model
        scaler = pipeline.named_steps['scaler']
        classifier = pipeline.named_steps['classifier']

        # Ensure features are engineered and ordered properly
        df_features = build_features(applicant)
        feature_cols = list(df_features.columns)

        # Standardize features using the pipeline's fitted StandardScaler
        X_scaled = scaler.transform(df_features[feature_cols])[0]

        # LogisticRegression coefficients for class 1 (default)
        coefs = classifier.coef_[0]

        # Individual feature contributions to the logit
        contributions = coefs * X_scaled

        factors = []
        for col_name, contrib in zip(feature_cols, contributions):
            direction = 'increases risk' if contrib > 0 else 'reduces risk'
            factors.append({
                'feature': col_name,
                'label': HUMAN_LABELS.get(col_name, col_name),
                'impact': round(float(abs(contrib)), 3),
                'direction': direction
            })

        # Sort by absolute impact descending and select top 5
        factors.sort(key=lambda item: item['impact'], reverse=True)
        return factors[:5]

    except Exception as err:
        print(f"[Error] explain failed: {err}")
        return []


def extract_feature_vector(raw_input: Dict[str, Any]) -> pd.DataFrame:
    """
    Convenience alias for build_features used across Flask controllers.
    """
    return build_features(raw_input)


def evaluate(applicant_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unified evaluation pipeline wrapper invoking engine.rules.evaluate.
    Returns: pd, risk_band, decision, emi, max_eligible, interest_rate,
             factors, hard_reasons, foir, dti.
    """
    from engine.rules import evaluate as _eval_pipeline
    return _eval_pipeline(applicant_dict)

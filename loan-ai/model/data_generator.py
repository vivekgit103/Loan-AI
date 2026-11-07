"""
Synthetic Indian Loan Applicant Dataset Generator.
Generates 5,000 realistic applicant profiles with demographic, employment,
bureau history (CIBIL 300-900), existing leverage, and requested facility parameters.
Synthesizes a realistic default label (~18% default rate) using a calibrated logistic formula.
"""

import os
import sys
import numpy as np
import pandas as pd

# Add parent directory to path to enable reusable imports from engine.features
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from engine.features import calculate_emi
except ImportError:
    def calculate_emi(principal: float, annual_rate: float, months: int) -> float:
        if principal <= 0 or months <= 0:
            return 0.0
        if annual_rate <= 0:
            return round(principal / months, 2)
        r = (annual_rate / 12.0) / 100.0
        factor = (1.0 + r) ** months
        if factor == 1.0:
            return round(principal / months, 2)
        emi = (principal * r * factor) / (factor - 1.0)
        return round(float(emi), 2)


def generate_loan_dataset(sample_size: int = 5000, random_seed: int = 42) -> pd.DataFrame:
    """
    Generates synthetic Indian loan applicants dataset.
    
    Columns:
        - age (21 - 60)
        - employment_type (0=salaried, 1=self-employed, 2=freelancer)
        - employment_years (realistic work experience based on age)
        - monthly_income (₹15,000 to ₹2,50,000)
        - credit_score (CIBIL 300 - 900)
        - existing_emi (₹0 to ~40% of income)
        - loan_amount (₹50,000 to ₹15,00,000)
        - tenure_months (12, 24, 36, 48, 60)
        - credit_utilization (0 - 100%)
        - missed_payments (0 - 8)
        - default (0 or 1, calibrated to ~18% default rate)
    """
    np.random.seed(random_seed)

    # 1. Demographics & Employment
    age = np.random.randint(21, 61, size=sample_size)
    employment_type = np.random.choice([0, 1, 2], size=sample_size, p=[0.65, 0.25, 0.10])
    
    # Employment years: correlated with age (career begins ~21 yrs)
    exp_gap = np.random.randint(0, 5, size=sample_size)
    employment_years = np.clip(age - 21 - exp_gap, 0, 35)

    # 2. Monthly Income in INR (₹15,000 to ₹2,50,000)
    raw_income = np.random.lognormal(mean=10.8, sigma=0.6, size=sample_size)
    monthly_income = np.clip(np.round(raw_income, -2), 15000, 250000)

    # 3. Credit Score (CIBIL 300 to 900)
    raw_cibil = np.random.normal(loc=700, scale=95, size=sample_size)
    credit_score = np.clip(np.round(raw_cibil).astype(int), 300, 900)

    # 4. Credit Card Revolving Utilization (%)
    # Inversely correlated with CIBIL score plus random variance
    util_base = 100.0 - ((credit_score - 300) / 600.0) * 85.0
    credit_utilization = np.clip(util_base + np.random.normal(0, 12, size=sample_size), 0.0, 100.0)
    credit_utilization = np.round(credit_utilization, 1)

    # 5. Missed / Delinquent Payments in Last 12 Months (0 to 8)
    missed_payments = np.zeros(sample_size, dtype=int)
    for i in range(sample_size):
        score = credit_score[i]
        if score < 550:
            missed_payments[i] = np.random.choice([2, 3, 4, 5, 6, 7, 8], p=[0.10, 0.20, 0.25, 0.20, 0.15, 0.05, 0.05])
        elif score < 650:
            missed_payments[i] = np.random.choice([0, 1, 2, 3, 4], p=[0.20, 0.35, 0.25, 0.15, 0.05])
        elif score < 750:
            missed_payments[i] = np.random.choice([0, 1, 2], p=[0.70, 0.25, 0.05])
        else:
            missed_payments[i] = np.random.choice([0, 1], p=[0.95, 0.05])

    # 6. Existing Monthly EMIs / Liabilities
    emi_ratio = np.random.beta(a=1.5, b=5.0, size=sample_size)
    existing_emi = np.round(monthly_income * emi_ratio, -2)

    # 7. Requested Facility: Amount and Tenure
    loan_amount = np.round(np.random.uniform(50000, 1500000, size=sample_size), -3)
    tenure_months = np.random.choice([12, 24, 36, 48, 60], size=sample_size)

    # 8. Compute New EMI and Debt-to-Income (DTI)
    annual_rate = 10.5
    new_emi = np.array([
        calculate_emi(p, annual_rate, int(t))
        for p, t in zip(loan_amount, tenure_months)
    ])
    dti = (existing_emi + new_emi) / monthly_income
    loan_to_income = loan_amount / (monthly_income * 12.0)

    # 9. Realistic Logistic Formula for Default Label (~18% Target Rate)
    # Risk factors: low credit score, high DTI, high utilization, missed payments
    # Protective factors: high income, long employment experience
    z = (
        -5.25
        - 0.010 * (credit_score - 650)
        + 3.80 * (dti - 0.40)
        + 0.035 * (credit_utilization - 30.0)
        + 0.65 * missed_payments
        - 0.000010 * (monthly_income - 50000.0)
        - 0.05 * (employment_years - 5.0)
        + 0.30 * employment_type
        + np.random.normal(0, 0.35, size=sample_size)
    )

    prob = 1.0 / (1.0 + np.exp(-z))
    default = (prob > 0.50).astype(int)

    df = pd.DataFrame({
        'age': age,
        'employment_type': employment_type,
        'employment_years': employment_years,
        'monthly_income': monthly_income,
        'credit_score': credit_score,
        'existing_emi': existing_emi,
        'loan_amount': loan_amount,
        'tenure_months': tenure_months,
        'credit_utilization': credit_utilization,
        'missed_payments': missed_payments,
        'default': default
    })

    return df


if __name__ == '__main__':
    try:
        print("[*] Generating 5,000 synthetic Indian loan applicant records...")
        dataset = generate_loan_dataset(sample_size=5000, random_seed=42)

        output_dir = os.path.dirname(os.path.abspath(__file__))
        csv_file = os.path.join(output_dir, 'loan_data.csv')
        dataset.to_csv(csv_file, index=False)

        default_count = dataset['default'].sum()
        default_rate = dataset['default'].mean() * 100.0

        print(f"[+] Dataset successfully created at: {csv_file}")
        print(f"[+] Total Records : {len(dataset)}")
        print(f"[+] Default Cases : {default_count} / {len(dataset)} ({default_rate:.2f}% default rate)")
        print("\nDataset Summary Preview:")
        print(dataset.describe().T[['mean', 'std', 'min', '50%', 'max']])
    except Exception as e:
        print(f"[Error] Failed to generate dataset: {e}")

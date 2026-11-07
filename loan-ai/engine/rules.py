"""
Credit Policy and Rule-Based Decision Engine.
Implements Indian retail banking risk guidelines (RBI prudential norms),
determines risk bands, risk-adjusted interest rates, max borrowing eligibility,
and evaluates full loan application diagnostics.
"""

import os
import sys
import joblib
from typing import Dict, Any, List, Tuple

# Add parent directory to path to import engine.features
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from engine.features import calculate_emi, build_features, explain

# Cached model instance
_CACHED_MODEL = None


def _get_model():
    """
    Loads and caches the serialized model pipeline from model/loan_model.pkl.
    """
    global _CACHED_MODEL
    if _CACHED_MODEL is None:
        model_path = os.path.join(parent_dir, 'model', 'loan_model.pkl')
        if os.path.exists(model_path):
            payload = joblib.load(model_path)
            _CACHED_MODEL = payload['pipeline'] if isinstance(payload, dict) and 'pipeline' in payload else payload
        else:
            raise FileNotFoundError(f"Model file not found at {model_path}. Run model/train_model.py first.")
    return _CACHED_MODEL


def hard_rules(applicant: Dict[str, Any]) -> List[str]:
    """
    Evaluates mandatory statutory credit policy rules.
    Returns a list of specific reject reasons:
        - credit_score < 550
        - FOIR > 65%
        - age < 21 or age > 60
        - income < 15,000
    """
    reasons = []

    # 1. CIBIL Score threshold (< 550)
    score = int(applicant.get('credit_score', applicant.get('score', 650)))
    if score < 550:
        reasons.append(f"CIBIL credit score ({score}) is below institutional minimum cutoff of 550.")

    # 2. Monthly Income threshold (< ₹15,000)
    income = float(applicant.get('monthly_income', applicant.get('income', 50000.0)))
    if income < 15000.0:
        reasons.append(f"Monthly income (₹{income:,.0f}) is below statutory minimum threshold of ₹15,000.")

    # 3. Age bounds (21 to 60 years)
    age = int(applicant.get('age', 30))
    if age < 21 or age > 60:
        reasons.append(f"Applicant age ({age} yrs) is outside eligible range (21 to 60 years).")

    # 4. Debt-to-Income / FOIR ceiling (> 65%)
    foir = applicant.get('foir')
    if foir is None:
        if 'dti' in applicant:
            foir = float(applicant['dti']) * 100.0
        else:
            existing_emi = float(applicant.get('existing_emi', applicant.get('emi', 0.0)))
            loan_amount = float(applicant.get('loan_amount', applicant.get('loan', 0.0)))
            tenure = int(applicant.get('tenure_months', applicant.get('tenure', 36)))
            rate = float(applicant.get('interest_rate', 11.5))
            proposed_emi = calculate_emi(loan_amount, rate, tenure)
            foir = ((existing_emi + proposed_emi) / max(1.0, income)) * 100.0
    else:
        foir = float(foir)

    if foir > 65.0:
        reasons.append(f"Total debt obligations (FOIR: {foir:.1f}%) exceed statutory prudential ceiling of 65%.")

    return reasons


def risk_band(pd: float) -> str:
    """
    Maps Probability of Default (PD) to risk categories:
        - Low:    pd < 0.15
        - Medium: 0.15 <= pd <= 0.35
        - High:   pd > 0.35
    """
    pd_val = float(pd)
    if pd_val < 0.15:
        return 'Low'
    elif pd_val <= 0.35:
        return 'Medium'
    else:
        return 'High'


def decide(pd: float, hard_reasons: List[str]) -> str:
    """
    Arrives at final credit decision:
        - Rejected: if hard reasons exist or risk band is High (pd > 0.35)
        - Manual Review: if risk band is Medium (0.15 <= pd <= 0.35)
        - Approved: if risk band is Low (pd < 0.15) and no hard reasons
    """
    band = risk_band(pd)
    if hard_reasons or band == 'High':
        return 'Rejected'
    elif band == 'Medium':
        return 'Manual Review'
    else:
        return 'Approved'


def interest_rate(band: str, loan_type: str = 'personal') -> float:
    """
    Computes annualized interest rate incorporating loan-type base rates
    plus risk spreads based on risk band:
        Base Rates:
            - home: 8.5%
            - auto: 9.5%
            - education: 9.0%
            - personal: 11.5%
        Risk Spreads:
            - Low: +0%
            - Medium: +2%
            - High: +4%
    """
    base_rates = {
        'home': 8.5,
        'auto': 9.5,
        'education': 9.0,
        'personal': 11.5,
        'business': 13.5
    }

    lt = str(loan_type).strip().lower()
    base = base_rates.get(lt, 11.5)

    band_clean = str(band).strip().capitalize()
    spreads = {
        'Low': 0.0,
        'Medium': 2.0,
        'High': 4.0
    }
    spread = spreads.get(band_clean, 0.0)

    return round(base + spread, 2)


def max_eligible_amount(income: float, existing_emi: float, rate: float, tenure: int) -> float:
    """
    Calculates the maximum permissible loan amount where total debt obligations (FOIR) stay capped at 50%:
        Max Total Permissible Monthly EMI = income * 0.50
        Available EMI for New Loan = Max Total Permissible - existing_emi
        P = Available EMI * [(1+r)^n - 1] / [r * (1+r)^n]
    """
    try:
        income = float(income)
        existing_emi = float(existing_emi)
        rate = float(rate)
        tenure = int(tenure)

        if income <= 0 or tenure <= 0:
            return 0.0

        max_total_emi = income * 0.50
        available_emi = max(0.0, max_total_emi - existing_emi)

        if available_emi <= 0 or rate <= 0:
            return 0.0

        monthly_rate = (rate / 12.0) / 100.0
        factor = (1.0 + monthly_rate) ** tenure
        denominator = factor - 1.0

        if denominator == 0:
            return round(available_emi * tenure, -3)

        max_principal = (available_emi * denominator) / (monthly_rate * factor)
        return round(max(0.0, float(max_principal)), -3)
    except Exception as err:
        print(f"[Error] max_eligible_amount failed: {err}")
        return 0.0


def evaluate(applicant_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs the full end-to-end loan evaluation pipeline on an applicant dictionary.
    Returns:
        {
            'pd': float,
            'risk_band': 'Low' | 'Medium' | 'High',
            'decision': 'Approved' | 'Manual Review' | 'Rejected',
            'emi': float,
            'max_eligible': float,
            'interest_rate': float,
            'factors': list of top 5 feature attributions,
            'hard_reasons': list of hard policy rejections,
            'foir': float,
            'dti': float
        }
    """
    try:
        model = _get_model()

        # Extract and normalize fields with flexible key aliases
        income = float(applicant_dict.get('monthly_income', applicant_dict.get('income', 50000.0)))
        existing_emi = float(applicant_dict.get('existing_emi', applicant_dict.get('emi', 0.0)))
        loan_amount = float(applicant_dict.get('loan_amount', applicant_dict.get('loan', 500000.0)))
        credit_score = int(applicant_dict.get('credit_score', applicant_dict.get('score', 650)))
        tenure = int(applicant_dict.get('tenure_months', applicant_dict.get('tenure', 36)))
        loan_type = str(applicant_dict.get('loan_type', 'personal')).lower()
        age = int(applicant_dict.get('age', 32))
        employment_type = applicant_dict.get('employment_type', 0)
        employment_years = applicant_dict.get('employment_years', max(1, age - 21))
        credit_util = float(applicant_dict.get('credit_utilization', 25.0))
        missed = int(applicant_dict.get('missed_payments', 0))

        standardized_applicant = {
            'name': applicant_dict.get('name', 'Applicant'),
            'age': age,
            'employment_type': employment_type,
            'employment_years': employment_years,
            'monthly_income': income,
            'credit_score': credit_score,
            'existing_emi': existing_emi,
            'loan_amount': loan_amount,
            'tenure_months': tenure,
            'credit_utilization': credit_util,
            'missed_payments': missed,
            'loan_type': loan_type
        }

        # 1. Feature Engineering & Probability of Default (PD) ML Prediction
        df_features = build_features(standardized_applicant)
        pd_val = float(model.predict_proba(df_features)[0][1])

        # 2. Risk Band & Applicable Interest Rate
        band = risk_band(pd_val)
        rate = interest_rate(band, loan_type)

        # 3. Monthly EMI & FOIR / DTI
        emi = calculate_emi(loan_amount, rate, tenure)
        dti = round((existing_emi + emi) / max(1.0, income), 4)
        foir = round(dti * 100.0, 2)

        standardized_applicant['foir'] = foir
        standardized_applicant['dti'] = dti
        standardized_applicant['interest_rate'] = rate

        # 4. Mandatory Hard Rule Policy Checks
        hard_reasons = hard_rules(standardized_applicant)

        # 5. Final Decision Synthesis
        decision = decide(pd_val, hard_reasons)

        # 6. Maximum Borrowing Capacity (50% FOIR Ceiling)
        max_eligible = max_eligible_amount(income, existing_emi, rate, tenure)

        # 7. Local Explainability (Top 5 Risk Factors)
        factors = explain(model, standardized_applicant)

        return {
            'pd': round(pd_val, 4),
            'risk_band': band,
            'decision': decision,
            'emi': emi,
            'max_eligible': max_eligible,
            'interest_rate': rate,
            'factors': factors,
            'hard_reasons': hard_reasons,
            'foir': foir,
            'dti': dti
        }

    except Exception as err:
        print(f"[Error] evaluate failed: {err}")
        raise err


# ------------------------------------------------------------------------------
# Backward Compatibility Wrappers for Flask app & Database
# ------------------------------------------------------------------------------
def get_benchmark_interest_rate(loan_type: str, credit_score: int) -> float:
    band = 'Low' if credit_score >= 750 else 'Medium' if credit_score >= 650 else 'High'
    return interest_rate(band, loan_type)

def evaluate_policy_rules(applicant_data: Dict[str, Any], foir: float) -> Tuple[str, List[str], List[str]]:
    applicant_copy = dict(applicant_data)
    applicant_copy['foir'] = foir
    hard_reasons = hard_rules(applicant_copy)
    cautions = []
    if 550 <= applicant_copy.get('credit_score', 650) < 660:
        cautions.append("CIBIL score is in fair zone (550-659).")
    if 50.0 < foir <= 65.0:
        cautions.append(f"FOIR ratio ({foir:.1f}%) exceeds recommended 50% guideline.")
    flag = "REJECT" if hard_reasons else "REVIEW" if cautions else "PASS"
    return flag, hard_reasons, cautions

def determine_final_decision(pd_value: float, policy_flag: str, hard_reasons: List[str], cautions: List[str]) -> Tuple[str, str]:
    band = risk_band(pd_value)
    dec = decide(pd_value, hard_reasons)
    risk_band_label = f"{band} Risk"
    return dec, risk_band_label


# ------------------------------------------------------------------------------
# Test Block: Evaluate the 4 Sample Applicants
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    sample_applicants = [
        {
            'name': 'Rahul',
            'income': 90000,
            'score': 780,
            'emi': 8000,
            'loan': 800000,
            'tenure': 36,
            'loan_type': 'personal'
        },
        {
            'name': 'Priya',
            'income': 45000,
            'score': 680,
            'emi': 12000,
            'loan': 600000,
            'tenure': 36,
            'loan_type': 'personal'
        },
        {
            'name': 'Arun',
            'income': 30000,
            'score': 540,
            'emi': 15000,
            'loan': 1000000,
            'tenure': 36,
            'credit_utilization': 85.0,
            'missed_payments': 4,
            'loan_type': 'personal'
        },
        {
            'name': 'Sneha',
            'income': 35000,
            'score': 720,
            'emi': 0,
            'loan': 300000,
            'tenure': 36,
            'loan_type': 'personal'
        }
    ]

    print("=" * 80)
    print("LOAN RISK ASSESSMENT & POLICY ENGINE - 4 APPLICANT TEST RESULTS")
    print("=" * 80)

    for applicant in sample_applicants:
        res = evaluate(applicant)
        print(f"\nApplicant: {applicant['name']}")
        print(f"  Monthly Income  : ₹{applicant['income']:,.0f}")
        print(f"  CIBIL Score     : {applicant['score']}")
        print(f"  Existing EMIs   : ₹{applicant['emi']:,.0f}")
        print(f"  Loan Requested  : ₹{applicant['loan']:,.0f}")
        print("-" * 50)
        print(f"  Default Risk (PD): {res['pd']:.4f} ({res['pd']*100:.2f}%)")
        print(f"  Risk Band        : {res['risk_band']}")
        print(f"  Interest Rate    : {res['interest_rate']}% p.a.")
        print(f"  Monthly EMI      : ₹{res['emi']:,.2f}")
        print(f"  FOIR / DTI       : {res['foir']}% (DTI: {res['dti']})")
        print(f"  Max Eligible Loan: ₹{res['max_eligible']:,.0f}")
        print(f"  Final Decision   : {res['decision']}")
        if res['hard_reasons']:
            print(f"  Hard Rejections  : {res['hard_reasons']}")
        print("  Top Contributing Factors:")
        for idx, f in enumerate(res['factors'], 1):
            print(f"    {idx}. {f['label']} ({f['feature']}): impact={f['impact']:.3f} [{f['direction']}]")
        print("-" * 50)

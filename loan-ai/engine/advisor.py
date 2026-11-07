"""
AI Advisor and Financial Recommendation Engine.
Produces friendly, professional credit decision explanations and actionable improvement tips.
Supports Anthropic Claude API (model "claude-sonnet-4-6") with an intelligent rule-based template fallback.
"""

import os
import json
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()


def generate_advice(applicant: Dict[str, Any], result: Dict[str, Any]) -> str:
    """
    Generates tailored, plain-text financial advice for a loan applicant.

    1) If ANTHROPIC_API_KEY exists in .env, calls the Anthropic Messages API
       using model 'claude-sonnet-4-6' with max_tokens 400 and bank advisor system prompt.
    2) On any exception or missing key, falls back to a rule-based template
       synthesized from the applicant's top factors and hard_reasons.

    Returns:
        str: Plain text explanation in 4-5 sentences followed by 3 bullet improvement tips.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if api_key and api_key.strip():
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key.strip())

            # Prepare structured JSON payloads for the prompt
            applicant_json = json.dumps(applicant, indent=2, default=str)
            result_json = json.dumps(result, indent=2, default=str)

            user_prompt = (
                f"Applicant Financial Details:\n{applicant_json}\n\n"
                f"Underwriting Assessment Result:\n{result_json}\n\n"
                "Please explain this loan decision to the applicant based on the data above."
            )

            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=400,
                system=(
                    "You are a friendly bank loan advisor. Explain the decision in simple English "
                    "in 4-5 sentences, then give 3 bullet improvement tips. Never promise approval."
                ),
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            )

            if response and response.content:
                advice_text = response.content[0].text.strip()
                if advice_text:
                    return advice_text

        except Exception as err:
            print(f"[Warning] Anthropic API call failed ({err}). Falling back to rule-based template.")

    # Rule-Based Fallback Engine
    return _rule_based_fallback(applicant, result)


def _rule_based_fallback(applicant: Dict[str, Any], result: Dict[str, Any]) -> str:
    """
    Constructs a clear, polite, and practical rule-based plain text explanation
    in 4-5 sentences followed by 3 bullet improvement tips, utilizing top factors
    and hard_reasons from the underwriting result.
    """
    name = applicant.get("name", "Applicant")
    income = float(applicant.get("monthly_income", applicant.get("income", 50000.0)))
    score = int(applicant.get("credit_score", applicant.get("score", 650)))
    loan_amount = float(applicant.get("loan_amount", applicant.get("loan", 500000.0)))
    existing_emi = float(applicant.get("existing_emi", applicant.get("emi", 0.0)))

    decision = result.get("decision", "Manual Review")
    risk_band = result.get("risk_band", "Medium")
    pd_val = float(result.get("pd", 0.20))
    emi = float(result.get("emi", 0.0))
    foir = float(result.get("foir", 0.0))
    max_eligible = float(result.get("max_eligible", 0.0))
    hard_reasons = result.get("hard_reasons", [])
    factors = result.get("factors", [])

    # Identify primary risk-increasing and risk-reducing factors
    risk_drivers = [f["label"] for f in factors if f.get("direction") == "increases risk"]
    protective_drivers = [f["label"] for f in factors if f.get("direction") == "reduces risk"]

    # --------------------------------------------------------------------------
    # 1. 4-5 Sentence Narrative Explanation
    # --------------------------------------------------------------------------
    if decision == "Approved":
        sentences = [
            f"Hello {name}, thank you for applying for a retail loan facility of ₹{loan_amount:,.0f} with our institution.",
            f"We are pleased to inform you that your application has been evaluated as {risk_band} risk with an estimated default probability of {pd_val * 100:.1f}%, and is officially Approved.",
            f"Your proposed monthly installment of ₹{emi:,.2f} results in a healthy debt-to-income ratio (FOIR) of {foir:.1f}%, leaving adequate disposable surplus from your monthly earnings of ₹{income:,.0f}.",
            f"Your strong CIBIL credit score of {score} and disciplined repayment history were significant positive drivers in securing standard prime terms.",
            "Please review the sanction terms carefully before proceeding with final disbursement documentation."
        ]
        tips = [
            "Maintain your credit card revolving utilization consistently under 30% to protect your prime credit profile.",
            "Establish an automated mandate (e-NACH) for your monthly EMI to avoid any inadvertent payment delays.",
            "Avoid making multiple concurrent hard loan inquiries across lenders to preserve your favorable bureau score."
        ]

    elif decision == "Manual Review":
        factor_mention = (
            f"primarily influenced by your {risk_drivers[0].lower()}"
            if risk_drivers else "due to leverage and debt servicing parameters"
        )
        sentences = [
            f"Hello {name}, thank you for your recent loan application for ₹{loan_amount:,.0f}.",
            f"Following our preliminary risk assessment, your application has been placed in the {risk_band} risk category and referred for Manual Review by our credit committee.",
            f"While your monthly earnings of ₹{income:,.0f} show steady repayment capacity, your overall debt obligations (FOIR: {foir:.1f}%) are {factor_mention}.",
            f"Your maximum safe borrowing capacity under institutional guidelines is estimated at ₹{max_eligible:,.0f}.",
            "A loan officer will evaluate whether restructured tenure terms or additional collateral could qualify your request for final approval."
        ]
        tips = [
            "Consider extending your loan tenure to reduce monthly EMI commitments and lower your debt-to-income ratio (FOIR).",
            "Pay down smaller existing short-term loans or credit card balances to free up additional monthly repayment headroom.",
            "Explore adding a salaried co-applicant (such as a spouse or parent) to strengthen household income eligibility."
        ]

    else:  # Rejected
        reasons_text = "; ".join(hard_reasons) if hard_reasons else (
            f"high default probability ({pd_val * 100:.1f}%) driven by {risk_drivers[0].lower() if risk_drivers else 'overall credit leverage'}"
        )
        sentences = [
            f"Hello {name}, thank you for considering our bank for your credit needs.",
            f"After carefully evaluating your loan application of ₹{loan_amount:,.0f}, we regret to inform you that we cannot approve your request at this time as it falls into our {risk_band} risk band.",
            f"This decision was guided by institutional risk standards: {reasons_text}.",
            f"With existing EMIs of ₹{existing_emi:,.0f} against monthly income of ₹{income:,.0f}, adding the proposed EMI would stretch your debt-to-income ratio to an unsustainable {foir:.1f}%.",
            "We encourage you to take corrective steps to rehabilitate your credit profile before submitting a future application."
        ]
        tips = [
            "Clear all past-due amounts and delinquent marks on your credit bureau report to begin rebuilding your CIBIL score.",
            "Reduce revolving credit card balances below 30% of total limits to demonstrate prudent liquidity management.",
            "Maintain an uninterrupted 6-month clean repayment track record before reapplying, or consider a secured loan against fixed deposits or gold."
        ]

    # Combine narrative paragraphs and bullet points
    narrative_text = " ".join(sentences)
    bullet_text = "\n".join([f"• {tip}" for tip in tips])

    return f"{narrative_text}\n\nKey Improvement Tips:\n{bullet_text}"


# ------------------------------------------------------------------------------
# Backward Compatibility Wrappers for Flask app & Database
# ------------------------------------------------------------------------------

def generate_structured_explanation(
    applicant_data: Dict[str, Any],
    foir: float,
    pd_value: float,
    decision: str,
    hard_reasons: List[str],
    cautions: List[str]
) -> Dict[str, Any]:
    """
    Constructs a structured JSON-compatible explanation dictionary detailing
    strengths, risk factors, credit metrics, and model underwriting notes.
    """
    cibil = int(applicant_data.get("credit_score", applicant_data.get("score", 650)))
    credit_util = float(applicant_data.get("credit_utilization", 25.0))
    monthly_income = float(applicant_data.get("monthly_income", applicant_data.get("income", 50000.0)))
    missed_payments = int(applicant_data.get("missed_payments", 0))

    strengths = []
    risk_factors = list(hard_reasons) + list(cautions)

    if cibil >= 750:
        strengths.append(f"Strong CIBIL credit score of {cibil} reflects exemplary repayment discipline.")
    elif cibil >= 680:
        strengths.append(f"CIBIL score ({cibil}) meets retail credit underwriting benchmarks.")

    if foir <= 40.0:
        strengths.append(f"Conservative debt-to-income ratio (FOIR: {foir:.1f}%) provides ample financial cushion.")
    elif foir <= 50.0:
        strengths.append(f"FOIR of {foir:.1f}% remains within regulatory guidelines.")

    if credit_util < 30.0:
        strengths.append(f"Low credit card utilization ({credit_util:.1f}%) shows controlled revolving debt.")

    if missed_payments == 0:
        strengths.append("Zero missed or delinquent payments across credit bureau records.")

    if monthly_income >= 80000.0:
        strengths.append(f"Verified monthly net earnings (₹{monthly_income:,.0f}) support strong cashflow.")

    if not strengths and decision != "Rejected":
        strengths.append("Applicant satisfies baseline KYC and institutional policy guidelines.")

    return {
        "decision": decision,
        "default_probability_percent": round(pd_value * 100.0, 1),
        "cibil_score": cibil,
        "foir_percent": round(foir, 1),
        "credit_utilization_percent": round(credit_util, 1),
        "strengths": strengths,
        "risk_factors": risk_factors if risk_factors else ["No adverse risk triggers identified."],
        "recommended_action": (
            "Approve application under standard prime retail lending terms."
            if decision == "Approved"
            else "Refer to credit committee for conditional terms or co-applicant review."
            if decision in ["Manual Review", "Review"]
            else "Decline loan application due to excessive risk of default."
        )
    }


def generate_financial_advice(
    applicant_data: Dict[str, Any],
    foir: float,
    pd_value: float,
    decision: str,
    max_eligible: float,
    hard_reasons: List[str],
    cautions: List[str]
) -> str:
    """
    Backward-compatible wrapper mapping to generate_advice().
    """
    result_dict = {
        "pd": pd_value,
        "risk_band": "Low" if pd_value < 0.15 else "Medium" if pd_value <= 0.35 else "High",
        "decision": decision,
        "foir": foir,
        "max_eligible": max_eligible,
        "hard_reasons": hard_reasons,
        "factors": []
    }
    return generate_advice(applicant_data, result_dict)

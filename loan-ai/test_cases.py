"""
Comprehensive Test Script: test_cases.py
Evaluates 8 applicant profiles across standard benchmarks and regulatory edge cases:
  1. Rahul Sharma (Prime salaried, high income, excellent CIBIL)
  2. Priya Patel (Self-employed, moderate income, fair credit)
  3. Arun Kumar (Freelancer, low income, subprime score, high DTI)
  4. Sneha Reddy (Salaried, zero existing debt, good score)
  5. Edge Case 1: Underage applicant (Age 19 - Statutory Age Violation < 21)
  6. Edge Case 2: Sub-cutoff income (₹10,000 - Income Shortfall < ₹15,000)
  7. Edge Case 3: Perfect Bureau (CIBIL 900) requesting large loan (₹85 Lakhs)
  8. Edge Case 4: Delinquent borrower (7 Missed Payments / Excessive Defaults)
"""

import os
import sys

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.features import evaluate


TEST_APPLICANTS = [
    {
        "id": "CASE-1",
        "name": "Rahul Sharma",
        "case_type": "Prime Salaried",
        "profile": {
            "name": "Rahul Sharma",
            "age": 32,
            "employment_type": 0,  # Salaried
            "employment_years": 7.0,
            "monthly_income": 90000.0,
            "credit_score": 780,
            "existing_emi": 8000.0,
            "loan_amount": 800000.0,
            "tenure_months": 36,
            "loan_type": "personal",
            "credit_utilization": 15.0,
            "missed_payments": 0
        }
    },
    {
        "id": "CASE-2",
        "name": "Priya Patel",
        "case_type": "Self-Employed Moderate",
        "profile": {
            "name": "Priya Patel",
            "age": 29,
            "employment_type": 1,  # Self-employed
            "employment_years": 4.0,
            "monthly_income": 45000.0,
            "credit_score": 680,
            "existing_emi": 12000.0,
            "loan_amount": 600000.0,
            "tenure_months": 48,
            "loan_type": "personal",
            "credit_utilization": 42.0,
            "missed_payments": 1
        }
    },
    {
        "id": "CASE-3",
        "name": "Arun Kumar",
        "case_type": "Subprime / High DTI",
        "profile": {
            "name": "Arun Kumar",
            "age": 38,
            "employment_type": 2,  # Freelancer
            "employment_years": 2.0,
            "monthly_income": 30000.0,
            "credit_score": 540,
            "existing_emi": 15000.0,
            "loan_amount": 1000000.0,
            "tenure_months": 60,
            "loan_type": "personal",
            "credit_utilization": 82.0,
            "missed_payments": 4
        }
    },
    {
        "id": "CASE-4",
        "name": "Sneha Reddy",
        "case_type": "Clean Credit / Low Debt",
        "profile": {
            "name": "Sneha Reddy",
            "age": 26,
            "employment_type": 0,  # Salaried
            "employment_years": 3.0,
            "monthly_income": 35000.0,
            "credit_score": 720,
            "existing_emi": 0.0,
            "loan_amount": 300000.0,
            "tenure_months": 24,
            "loan_type": "personal",
            "credit_utilization": 10.0,
            "missed_payments": 0
        }
    },
    {
        "id": "EDGE-1",
        "name": "Karan Malhotra",
        "case_type": "Edge: Underage (Age 19)",
        "profile": {
            "name": "Karan Malhotra",
            "age": 19,  # Statutory Hard Rule Violation: age < 21
            "employment_type": 0,
            "employment_years": 1.0,
            "monthly_income": 40000.0,
            "credit_score": 710,
            "existing_emi": 2000.0,
            "loan_amount": 250000.0,
            "tenure_months": 24,
            "loan_type": "personal",
            "credit_utilization": 20.0,
            "missed_payments": 0
        }
    },
    {
        "id": "EDGE-2",
        "name": "Sunil Bansal",
        "case_type": "Edge: Low Income (₹10,000)",
        "profile": {
            "name": "Sunil Bansal",
            "age": 34,
            "employment_type": 0,
            "employment_years": 5.0,
            "monthly_income": 10000.0,  # Statutory Hard Rule Violation: income < 15,000
            "credit_score": 670,
            "existing_emi": 1000.0,
            "loan_amount": 100000.0,
            "tenure_months": 18,
            "loan_type": "personal",
            "credit_utilization": 25.0,
            "missed_payments": 0
        }
    },
    {
        "id": "EDGE-3",
        "name": "Vikram Singhania",
        "case_type": "Edge: CIBIL 900 + Large Loan",
        "profile": {
            "name": "Vikram Singhania",
            "age": 45,
            "employment_type": 1,
            "employment_years": 18.0,
            "monthly_income": 350000.0,
            "credit_score": 900,  # Perfect bureau score
            "existing_emi": 40000.0,
            "loan_amount": 8500000.0,  # ₹85 Lakhs large facility
            "tenure_months": 120,
            "loan_type": "home",
            "credit_utilization": 8.0,
            "missed_payments": 0
        }
    },
    {
        "id": "EDGE-4",
        "name": "Manoj Tiwari",
        "case_type": "Edge: 7 Delinquencies",
        "profile": {
            "name": "Manoj Tiwari",
            "age": 41,
            "employment_type": 1,
            "employment_years": 8.0,
            "monthly_income": 65000.0,
            "credit_score": 510,
            "existing_emi": 18000.0,
            "loan_amount": 500000.0,
            "tenure_months": 36,
            "loan_type": "personal",
            "credit_utilization": 88.0,
            "missed_payments": 7  # High missed payments
        }
    }
]


def run_all_test_cases():
    print("\n" + "=" * 115)
    print(" " * 32 + "LOANIQ: AUTOMATED TEST SUITE EXECUTION TABLE")
    print("=" * 115)
    print(f"{'Case ID':<8} | {'Applicant Name':<17} | {'Income':<9} | {'CIBIL':<6} | {'Loan (₹)':<10} | {'FOIR':<7} | {'PD (%)':<8} | {'Risk Band':<10} | {'Decision':<14} | {'Policy Hard Reasons'}")
    print("-" * 115)

    results = []
    for test in TEST_APPLICANTS:
        cid = test["id"]
        name = test["name"]
        p = test["profile"]

        # Run unified engine evaluation
        res = evaluate(p)
        results.append((test, res))

        pd_pct = f"{res['pd'] * 100:.1f}%"
        foir_str = f"{res['foir']:.1f}%"
        income_str = f"₹{int(p['monthly_income']):,}"
        loan_str = f"₹{int(p['loan_amount']):,}"
        reasons = "; ".join(res["hard_reasons"]) if res["hard_reasons"] else "None (Passed Gates)"

        print(f"{cid:<8} | {name:<17} | {income_str:<9} | {p['credit_score']:<6} | {loan_str:<10} | {foir_str:<7} | {pd_pct:<8} | {res['risk_band']:<10} | {res['decision']:<14} | {reasons}")

    print("=" * 115)
    print("\nDetailed Diagnostic Breakdown:\n")

    for test, res in results:
        print(f"[{test['id']}] {test['name']} ({test['case_type']}):")
        print(f"  • Monthly EMI: ₹{res['emi']:,.2f} | Interest Rate: {res['interest_rate']:.2f}% p.a.")
        print(f"  • Max Sanction Capacity: ₹{res['max_eligible']:,.0f} | FOIR: {res['foir']:.1f}%")
        print(f"  • Probability of Default (PD): {res['pd']:.4f} ({res['risk_band']} Tier)")
        print(f"  • Underwriting Outcome: {res['decision']}")
        if res["hard_reasons"]:
            print(f"  • Policy Rule Violations: {', '.join(res['hard_reasons'])}")
        print(f"  • Top XAI Feature Drivers: {', '.join([f['label'] + ' (' + f['direction'] + ')' for f in res['factors'][:3]])}")
        print("-" * 80)

    print("\n[✔] All 8 test cases executed successfully without runtime exceptions.\n")


if __name__ == "__main__":
    run_all_test_cases()


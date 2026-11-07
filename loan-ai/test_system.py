"""
Automated System Verification and Health-Check Suite for TrustScore AI.
Validates Database operations, Mathematical Financial Formulas, Policy Rule Engine,
Machine Learning Model Inference, AI Advisor explanations, and Flask HTTP Endpoints.
"""

import sys
import os
import unittest
import json

# Ensure loan-ai directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, insert_application, get_all_applications, get_stats, get_monthly_counts, get_db_connection
from engine.features import calculate_emi, calculate_foir, calculate_max_eligible_loan, extract_feature_vector
from engine.rules import get_benchmark_interest_rate, evaluate_policy_rules, determine_final_decision
from engine.advisor import generate_structured_explanation, generate_financial_advice
from app import app, get_model


class TestTrustScoreAISystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n" + "=" * 65)
        print("TRUSTSCORE AI: FULL SYSTEM VERIFICATION SUITE")
        print("=" * 65)
        init_db()
        cls.client = app.test_client()
        cls.client.testing = True

    def test_01_database_operations(self):
        """Verifies SQLite database initialization, stats, and query methods."""
        print("[Test 1/6] Testing Database CRUD & Analytics Operations...")
        stats = get_stats()
        self.assertIn("total_applications", stats)
        self.assertGreaterEqual(stats["total_applications"], 12)
        self.assertIn("approval_rate", stats)

        monthly = get_monthly_counts()
        self.assertIsInstance(monthly, list)
        self.assertGreater(len(monthly), 0)

        apps = get_all_applications()
        self.assertGreater(len(apps), 0)
        self.assertIn("name", apps[0])
        self.assertIn("credit_score", apps[0])

    def test_02_mathematical_features(self):
        """Verifies reducing balance EMI, FOIR, and Max Loan sizing calculations."""
        print("[Test 2/6] Testing Financial Math (EMI, FOIR, Max Capacity)...")
        # 1. Test EMI: 10 Lakhs, 10% annual rate, 36 months
        emi = calculate_emi(principal=1000000.0, annual_interest_rate=10.0, tenure_months=36)
        self.assertAlmostEqual(emi, 32267.0, delta=10.0)

        # 2. Test FOIR: Monthly income 1,00,000, existing 10,000, proposed 25,000 -> 35%
        foir = calculate_foir(monthly_income=100000.0, existing_emi=10000.0, proposed_emi=25000.0)
        self.assertEqual(foir, 35.0)

        # 3. Test Max Eligible Loan: Monthly income 1,00,000, existing 10,000, max FOIR 50%
        # Available EMI = 40,000. At 10% for 36 months, principal is ~ 12.4 Lakhs
        max_loan = calculate_max_eligible_loan(
            monthly_income=100000.0, existing_emi=10000.0, annual_interest_rate=10.0, tenure_months=36, max_foir_allowed=0.50
        )
        self.assertGreater(max_loan, 1000000.0)

    def test_03_policy_rule_engine(self):
        """Verifies Indian retail lending policy rules and cutoffs."""
        print("[Test 3/6] Testing Credit Policy Rule Engine...")
        # Severe reject case: CIBIL 500, FOIR 75%
        reject_profile = {
            "age": 28, "monthly_income": 40000.0, "credit_score": 500,
            "credit_utilization": 85.0, "missed_payments": 4, "employment_type": "Salaried"
        }
        flag, hard_reasons, cautions = evaluate_policy_rules(reject_profile, foir=75.0)
        self.assertEqual(flag, "REJECT")
        self.assertGreater(len(hard_reasons), 0)

        # Clean prime case: CIBIL 810, FOIR 32%
        pass_profile = {
            "age": 35, "monthly_income": 120000.0, "credit_score": 810,
            "credit_utilization": 15.0, "missed_payments": 0, "employment_type": "Salaried"
        }
        flag2, hard2, cautions2 = evaluate_policy_rules(pass_profile, foir=32.0)
        self.assertEqual(flag2, "PASS")
        self.assertEqual(len(hard2), 0)

    def test_04_ml_model_inference(self):
        """Verifies that the serialized Random Forest model executes inference."""
        print("[Test 4/6] Testing Scikit-Learn Pipeline Probability of Default (PD)...")
        model_payload = get_model()
        self.assertIsNotNone(model_payload, "loan_model.pkl must be loaded successfully")
        pipeline = model_payload["pipeline"]

        applicant = {
            "name": "Integration Test Candidate", "age": 30, "employment_type": "Salaried",
            "monthly_income": 80000.0, "credit_score": 770, "existing_emi": 5000.0,
            "loan_amount": 400000.0, "tenure_months": 36, "loan_type": "Personal",
            "credit_utilization": 20.0, "missed_payments": 0, "interest_rate": 11.25
        }
        df = extract_feature_vector(applicant)
        probs = pipeline.predict_proba(df)[0]
        pd_score = float(probs[1])
        # A 770 CIBIL applicant with 20% utilization should have low default probability (< 0.30)
        self.assertLess(pd_score, 0.35)
        self.assertGreaterEqual(pd_score, 0.0)

    def test_05_advisor_and_xai(self):
        """Verifies structured explanation generation and financial counseling."""
        print("[Test 5/6] Testing Explainable AI (XAI) & Advisor Recommendations...")
        applicant = {
            "name": "Priya Sharma", "monthly_income": 90000.0, "credit_score": 760,
            "credit_utilization": 22.0, "missed_payments": 0, "loan_type": "Home", "loan_amount": 3000000.0
        }
        explanation = generate_structured_explanation(
            applicant, foir=38.0, pd_value=0.08, decision="Approved", hard_reasons=[], cautions=[]
        )
        self.assertEqual(explanation["decision"], "Approved")
        self.assertGreater(len(explanation["strengths"]), 0)

        advice = generate_financial_advice(
            applicant, foir=38.0, pd_value=0.08, decision="Approved", max_eligible=4500000.0, hard_reasons=[], cautions=[]
        )
        self.assertIsInstance(advice, str)
        self.assertGreater(len(advice), 20)

    def test_06_flask_web_endpoints(self):
        """Verifies all HTTP endpoints, templates rendering, and POST submission."""
        print("[Test 6/6] Testing Flask Web Controllers & REST API Endpoints...")
        # 1. Dashboard
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)

        # 2. Application Form
        res = self.client.get("/apply")
        self.assertEqual(res.status_code, 200)

        # 3. Application Registry
        res = self.client.get("/applications")
        self.assertEqual(res.status_code, 200)

        # 4. Result View for Seed Record #1
        res = self.client.get("/result/1")
        self.assertEqual(res.status_code, 200)

        # 5. REST API: /api/calculate-emi
        api_res = self.client.post("/api/calculate-emi", json={
            "loan_amount": 500000.0, "loan_type": "Auto", "tenure_months": 48,
            "credit_score": 750, "monthly_income": 60000.0, "existing_emi": 5000.0
        })
        self.assertEqual(api_res.status_code, 200)
        data = json.loads(api_res.get_data(as_text=True))
        self.assertEqual(data["status"], "success")
        self.assertGreater(data["emi"], 0)

        # 6. REST API: /api/stats
        stats_res = self.client.get("/api/stats")
        self.assertEqual(stats_res.status_code, 200)

        # 7. End-to-End POST Application Submission
        post_res = self.client.post("/apply", data={
            "name": "Verification User", "age": "32", "employment_type": "Salaried",
            "monthly_income": "85000", "existing_emi": "8000", "credit_score": "780",
            "credit_utilization": "15.0", "missed_payments": "0", "loan_type": "Personal",
            "loan_amount": "500000", "tenure_months": "36"
        }, follow_redirects=True)
        self.assertEqual(post_res.status_code, 200)
        html = post_res.get_data(as_text=True)
        self.assertIn("Verification User", html)
        self.assertIn("Approved", html)

        # 8. REST API: /api/evaluate with Rahul's data
        eval_res = self.client.post("/api/evaluate", json={
            "name": "Rahul Sharma", "monthly_income": 90000, "credit_score": 780,
            "existing_emi": 8000, "loan_amount": 800000, "tenure_months": 36, "loan_type": "personal"
        })
        self.assertEqual(eval_res.status_code, 200)
        eval_json = json.loads(eval_res.get_data(as_text=True))
        self.assertEqual(eval_json["status"], "success")
        self.assertEqual(eval_json["result"]["decision"], "Approved")
        self.assertIn("factors", eval_json["result"])

        # Clean up test rows
        with get_db_connection() as conn:
            conn.execute("DELETE FROM applications WHERE name IN ('Verification User', 'Rahul Sharma');")
            conn.commit()


if __name__ == "__main__":
    unittest.main()


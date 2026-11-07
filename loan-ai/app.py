"""
Flask Web Application for AI-Based Loan Eligibility & Risk Assessment System.
Serves web routes, validates JSON underwriting payloads, executes feature engineering
and ML pipeline scoring, coordinates AI advisor recommendations, and persists applications to SQLite.
"""

import os
import json
import joblib
from datetime import datetime
from typing import Dict, Any, List
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv

# Database, Feature, Rule, and Advisor Imports
from database import init_db, insert_application, get_all_applications, get_stats, get_monthly_counts, get_db_connection
import engine.features
import engine.advisor

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "trustscore-ai-secret-key-2024-indian-retail-credit")

# Global cached model payload
MODEL_PAYLOAD = None


def get_model():
    """
    Loads and caches the trained ML pipeline from disk once at startup.
    """
    global MODEL_PAYLOAD
    if MODEL_PAYLOAD is None:
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model", "loan_model.pkl")
        try:
            if os.path.exists(model_path):
                MODEL_PAYLOAD = joblib.load(model_path)
                print(f"[+] Loaded ML model pipeline from {model_path}")
            else:
                print(f"[!] Warning: Model file not found at {model_path}. Train using model/train_model.py")
        except Exception as e:
            print(f"[Error] Failed to load model pipeline: {e}")
            MODEL_PAYLOAD = None
    return MODEL_PAYLOAD


# ------------------------------------------------------------------------------
# CORS-Free Simple Setup
# ------------------------------------------------------------------------------
@app.after_request
def add_cors_headers(response):
    """
    Attaches permissive CORS headers to allow cross-origin API integration without extra dependencies.
    """
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


# ------------------------------------------------------------------------------
# Predefined Loan Products List
# ------------------------------------------------------------------------------
LOAN_PRODUCTS = [
    {
        "name": "Home Loan",
        "type": "Home",
        "base_rate": 8.50,
        "min_amount": 500000,
        "max_amount": 10000000,
        "max_tenure": 240,
        "tag": "Priority Banking"
    },
    {
        "name": "Personal Loan",
        "type": "Personal",
        "base_rate": 11.50,
        "min_amount": 50000,
        "max_amount": 1500000,
        "max_tenure": 60,
        "tag": "Instant Sanction"
    },
    {
        "name": "Auto Loan",
        "type": "Auto",
        "base_rate": 9.50,
        "min_amount": 200000,
        "max_amount": 2500000,
        "max_tenure": 84,
        "tag": "Vehicle Hypothecation"
    },
    {
        "name": "Education Loan",
        "type": "Education",
        "base_rate": 9.00,
        "min_amount": 100000,
        "max_amount": 4000000,
        "max_tenure": 120,
        "tag": "Section 80E Rebate"
    },
    {
        "name": "Business Loan",
        "type": "Business",
        "base_rate": 13.50,
        "min_amount": 200000,
        "max_amount": 5000000,
        "max_tenure": 60,
        "tag": "Working Capital"
    },
    {
        "name": "Gold Loan",
        "type": "Gold",
        "base_rate": 8.90,
        "min_amount": 25000,
        "max_amount": 2500000,
        "max_tenure": 36,
        "tag": "Instant Valuation"
    }
]


# ------------------------------------------------------------------------------
# Web Interface Routes
# ------------------------------------------------------------------------------

@app.route("/")
def dashboard():
    """
    Executive dashboard with KPI metric cards, portfolio breakdown,
    last 6 months trend bars, recent 8 applications, and loan products.
    """
    try:
        stats = get_stats()
        monthly_counts = get_monthly_counts()
        all_apps = get_all_applications()
        recent_apps = all_apps[:8]  # Pass recent 8 applications as requested

        return render_template(
            "dashboard.html",
            stats=stats,
            monthly_counts=monthly_counts,
            recent_applications=recent_apps,
            loan_products=LOAN_PRODUCTS
        )
    except Exception as e:
        flash(f"Error loading dashboard metrics: {e}", "danger")
        return render_template(
            "dashboard.html",
            stats={},
            monthly_counts=[],
            recent_applications=[],
            loan_products=LOAN_PRODUCTS
        )


@app.route("/apply", methods=["GET", "POST"])
def apply_loan():
    """
    Loan application intake:
    - GET: Displays interactive application form with live EMI & FOIR calculator.
    - POST: Handles HTML form submission, executes evaluation pipeline, and redirects to /result/<id>.
    """
    if request.method == "POST":
        try:
            raw_form = request.form.to_dict()

            # Normalize applicant parameters
            name = raw_form.get("name", "").strip() or "Anonymous Applicant"
            age = int(raw_form.get("age", 30))
            employment_type = raw_form.get("employment_type", "Salaried")
            employment_years = float(raw_form.get("employment_years", max(1, age - 21)))
            monthly_income = float(raw_form.get("monthly_income", 0.0))
            existing_emi = float(raw_form.get("existing_emi", 0.0))
            credit_score = int(raw_form.get("credit_score", 650))
            credit_utilization = float(raw_form.get("credit_utilization", 25.0))
            missed_payments = int(raw_form.get("missed_payments", 0))
            loan_type = raw_form.get("loan_type", "Personal")
            loan_amount = float(raw_form.get("loan_amount", 0.0))
            tenure_months = int(raw_form.get("tenure_months", 36))

            applicant_payload = {
                "name": name,
                "age": age,
                "employment_type": employment_type,
                "employment_years": employment_years,
                "monthly_income": monthly_income,
                "credit_score": credit_score,
                "existing_emi": existing_emi,
                "loan_amount": loan_amount,
                "tenure_months": tenure_months,
                "loan_type": loan_type,
                "credit_utilization": credit_utilization,
                "missed_payments": missed_payments
            }

            # 1. Run Unified Evaluation via engine.features.evaluate
            eval_result = engine.features.evaluate(applicant_payload)

            # 2. Generate Actionable Advisory Feedback via advisor.generate_advice
            advice_text = engine.advisor.generate_advice(applicant_payload, eval_result)

            # 3. Persist to SQLite Database
            db_record = {
                "name": name,
                "age": age,
                "employment_type": str(employment_type),
                "monthly_income": monthly_income,
                "credit_score": credit_score,
                "existing_emi": existing_emi,
                "loan_amount": loan_amount,
                "tenure_months": tenure_months,
                "loan_type": loan_type,
                "credit_utilization": credit_utilization,
                "missed_payments": missed_payments,
                "pd": eval_result["pd"],
                "risk_band": eval_result["risk_band"],
                "decision": eval_result["decision"],
                "emi": eval_result["emi"],
                "max_eligible": eval_result["max_eligible"],
                "interest_rate": eval_result["interest_rate"],
                "explanation_json": eval_result,
                "advice": advice_text,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            application_id = insert_application(db_record)
            flash(f"Application #{application_id} for {name} evaluated successfully!", "success")
            return redirect(url_for("view_result", application_id=application_id))

        except Exception as err:
            flash(f"Error processing application: {err}", "danger")
            return redirect(url_for("apply_loan"))

    return render_template("apply.html")


@app.route("/result/<int:application_id>")
def view_result(application_id: int):
    """
    Renders comprehensive underwriting decision report for a specific application.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM applications WHERE id = ?;", (application_id,))
            row = cursor.fetchone()

            if not row:
                flash(f"Application #{application_id} not found.", "danger")
                return redirect(url_for("dashboard"))

            app_dict = dict(row)

            # Parse explanation JSON string
            explanation = {}
            if app_dict.get("explanation_json"):
                try:
                    explanation = json.loads(app_dict["explanation_json"])
                except Exception:
                    explanation = {}

            return render_template("result.html", app=app_dict, explanation=explanation)

    except Exception as e:
        flash(f"Failed to retrieve application details: {e}", "danger")
        return redirect(url_for("dashboard"))


@app.route("/applications")
def list_applications():
    """
    Displays full searchable and filterable table of all applications.
    """
    try:
        apps = get_all_applications()
        return render_template("applications.html", applications=apps)
    except Exception as e:
        flash(f"Error fetching application registry: {e}", "danger")
        return render_template("applications.html", applications=[])


@app.route("/delete/<int:application_id>", methods=["POST"])
def delete_application_route(application_id: int):
    """
    Deletes an application record from the registry.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM applications WHERE id = ?;", (application_id,))
            conn.commit()
            flash(f"Application #{application_id} deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting application #{application_id}: {e}", "danger")

    return redirect(url_for("list_applications"))


# ------------------------------------------------------------------------------
# JSON REST API Endpoints
# ------------------------------------------------------------------------------

def validate_evaluation_payload(data: Dict[str, Any]) -> List[str]:
    """
    Validates applicant input payload ranges and types.
    Returns a list of specific error messages (empty if valid).
    """
    errors = []

    # Monthly Income
    income = data.get("monthly_income", data.get("income"))
    if income is None:
        errors.append("monthly_income (or income) is required.")
    else:
        try:
            inc_val = float(income)
            if inc_val <= 0:
                errors.append("monthly_income must be a positive number greater than 0.")
        except (ValueError, TypeError):
            errors.append("monthly_income must be a valid number.")

    # Credit Score (300 to 900)
    score = data.get("credit_score", data.get("score"))
    if score is None:
        errors.append("credit_score (or score) is required.")
    else:
        try:
            score_val = int(score)
            if score_val < 300 or score_val > 900:
                errors.append("credit_score must be an integer between 300 and 900.")
        except (ValueError, TypeError):
            errors.append("credit_score must be a valid integer between 300 and 900.")

    # Loan Amount
    amount = data.get("loan_amount", data.get("loan"))
    if amount is None:
        errors.append("loan_amount (or loan) is required.")
    else:
        try:
            amt_val = float(amount)
            if amt_val <= 0:
                errors.append("loan_amount must be a positive number greater than 0.")
        except (ValueError, TypeError):
            errors.append("loan_amount must be a valid number.")

    # Existing EMI
    existing_emi = data.get("existing_emi", data.get("emi", 0.0))
    try:
        emi_val = float(existing_emi)
        if emi_val < 0:
            errors.append("existing_emi cannot be negative.")
    except (ValueError, TypeError):
        errors.append("existing_emi must be a valid non-negative number.")

    # Tenure Months
    tenure = data.get("tenure_months", data.get("tenure", 36))
    try:
        tenure_val = int(tenure)
        if tenure_val < 6 or tenure_val > 360:
            errors.append("tenure_months must be an integer between 6 and 360 months.")
    except (ValueError, TypeError):
        errors.append("tenure_months must be a valid integer between 6 and 360.")

    # Age (if supplied)
    if "age" in data and data["age"] is not None:
        try:
            age_val = int(data["age"])
            if age_val < 18 or age_val > 80:
                errors.append("age must be an integer between 18 and 80.")
        except (ValueError, TypeError):
            errors.append("age must be a valid integer.")

    # Credit Utilization (if supplied)
    if "credit_utilization" in data and data["credit_utilization"] is not None:
        try:
            util_val = float(data["credit_utilization"])
            if util_val < 0.0 or util_val > 100.0:
                errors.append("credit_utilization must be a percentage between 0 and 100.")
        except (ValueError, TypeError):
            errors.append("credit_utilization must be a valid number.")

    # Missed Payments (if supplied)
    if "missed_payments" in data and data["missed_payments"] is not None:
        try:
            missed_val = int(data["missed_payments"])
            if missed_val < 0 or missed_val > 24:
                errors.append("missed_payments must be an integer between 0 and 24.")
        except (ValueError, TypeError):
            errors.append("missed_payments must be a non-negative integer.")

    # Loan Type (if supplied)
    if "loan_type" in data and data["loan_type"]:
        allowed_types = ["personal", "home", "auto", "education", "business"]
        if str(data["loan_type"]).strip().lower() not in allowed_types:
            errors.append(f"loan_type must be one of: {', '.join(allowed_types)}.")

    return errors


@app.route("/api/evaluate", methods=["POST"])
def api_evaluate():
    """
    POST /api/evaluate:
    - Accepts JSON applicant payload.
    - Validates inputs and returns 400 with clear error messages for invalid ranges.
    - Calls engine.features.evaluate, then advisor.generate_advice.
    - Saves evaluation record to SQLite database.
    - Returns JSON with new application_id, result, and advice.
    """
    try:
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            return jsonify({
                "status": "error",
                "message": "Request body must be a valid JSON object."
            }), 400

        # Validate input ranges
        validation_errors = validate_evaluation_payload(data)
        if validation_errors:
            return jsonify({
                "status": "error",
                "message": "Validation failed: " + "; ".join(validation_errors),
                "errors": validation_errors
            }), 400

        # Standardize applicant attributes
        name = str(data.get("name", "Applicant")).strip()
        income = float(data.get("monthly_income", data.get("income")))
        score = int(data.get("credit_score", data.get("score")))
        existing_emi = float(data.get("existing_emi", data.get("emi", 0.0)))
        loan_amount = float(data.get("loan_amount", data.get("loan")))
        tenure_months = int(data.get("tenure_months", data.get("tenure", 36)))
        loan_type = str(data.get("loan_type", "personal")).strip().lower()
        age = int(data.get("age", 30))
        employment_type = data.get("employment_type", 0)
        employment_years = float(data.get("employment_years", max(1, age - 21)))
        credit_util = float(data.get("credit_utilization", 25.0))
        missed = int(data.get("missed_payments", 0))

        applicant_payload = {
            "name": name,
            "age": age,
            "employment_type": employment_type,
            "employment_years": employment_years,
            "monthly_income": income,
            "credit_score": score,
            "existing_emi": existing_emi,
            "loan_amount": loan_amount,
            "tenure_months": tenure_months,
            "loan_type": loan_type,
            "credit_utilization": credit_util,
            "missed_payments": missed
        }

        # 1. Evaluate via engine.features.evaluate
        eval_result = engine.features.evaluate(applicant_payload)

        # 2. Generate Advice via advisor.generate_advice
        advice_text = engine.advisor.generate_advice(applicant_payload, eval_result)

        # 3. Save to Database
        db_record = {
            "name": name,
            "age": age,
            "employment_type": str(employment_type),
            "monthly_income": income,
            "credit_score": score,
            "existing_emi": existing_emi,
            "loan_amount": loan_amount,
            "tenure_months": tenure_months,
            "loan_type": loan_type.capitalize(),
            "credit_utilization": credit_util,
            "missed_payments": missed,
            "pd": eval_result["pd"],
            "risk_band": eval_result["risk_band"],
            "decision": eval_result["decision"],
            "emi": eval_result["emi"],
            "max_eligible": eval_result["max_eligible"],
            "interest_rate": eval_result["interest_rate"],
            "explanation_json": eval_result,
            "advice": advice_text,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        app_id = insert_application(db_record)

        return jsonify({
            "status": "success",
            "application_id": app_id,
            "result": eval_result,
            "advice": advice_text,
            "redirect_url": f"/result/{app_id}"
        }), 200

    except Exception as err:
        return jsonify({
            "status": "error",
            "message": f"Server evaluation failure: {str(err)}"
        }), 500


@app.route("/api/calculate-emi", methods=["POST"])
def api_calculate_emi():
    """
    POST /api/calculate-emi:
    Lightweight endpoint for interactive loan calculators:
    computes estimated EMI, FOIR, and max eligible loan without running the full ML pipeline.
    """
    try:
        data = request.get_json(silent=True) or {}
        principal = float(data.get("loan_amount", 0.0))
        tenure = int(data.get("tenure_months", 36))
        loan_type = str(data.get("loan_type", "personal")).lower()
        income = float(data.get("monthly_income", 0.0))
        existing_emi = float(data.get("existing_emi", 0.0))
        score = int(data.get("credit_score", 700))

        # Benchmark rate based on score tier
        from engine.rules import interest_rate, max_eligible_amount
        band = "Low" if score >= 750 else ("Medium" if score >= 650 else "High")
        rate = interest_rate(band, loan_type)
        emi = engine.features.calculate_emi(principal, rate, tenure)
        max_amount = max_eligible_amount(income, existing_emi, rate, tenure)
        foir = round(((existing_emi + emi) / income * 100), 2) if income > 0 else 0.0

        return jsonify({
            "status": "success",
            "emi": emi,
            "interest_rate": rate,
            "max_eligible": max_amount,
            "foir": foir
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/stats", methods=["GET"])
def api_stats():
    """
    GET /api/stats:
    Returns JSON portfolio statistics and volume metrics including monthly trend breakdown.
    """
    try:
        stats = get_stats()
        monthly = get_monthly_counts()
        # Include monthly counts under data.monthly_counts and stats.monthly_counts
        stats["monthly_counts"] = monthly
        return jsonify({
            "status": "success",
            "data": stats,
            "monthly_counts": monthly
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ------------------------------------------------------------------------------
# Startup Initialization & Server Run
# ------------------------------------------------------------------------------

# 1. Initialize SQLite Database Schema & Seed Data
init_db()

# 2. Preload Machine Learning Pipeline into Memory
get_model()

if __name__ == "__main__":
    print("[+] TrustScore AI online. Starting server on http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=True)

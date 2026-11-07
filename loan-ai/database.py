"""
SQLite Database Management Module for Loan Eligibility and Risk Assessment System.
Handles schema initialization, CRUD operations, risk aggregation statistics,
monthly loan trend reporting, and populates realistic Indian sample profiles.
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Resolve database path relative to this file to prevent multiple stray DB files
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "loan_ai.db")


def get_db_connection(db_path: str = DB_FILE) -> sqlite3.Connection:
    """
    Establishes and returns an active connection to the SQLite database.
    Configures Row factory to allow both dictionary-like and index-based access.
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"[Error] Failed to connect to SQLite database at {db_path}: {e}")
        raise e


def init_db(db_path: str = DB_FILE) -> None:
    """
    Initializes the SQLite database schema.
    Creates the 'applications' table if it does not exist, and seeds
    12 realistic Indian credit applicant sample profiles if the table is empty.
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        employment_type TEXT NOT NULL,
        monthly_income REAL NOT NULL,
        credit_score INTEGER NOT NULL,
        existing_emi REAL NOT NULL,
        loan_amount REAL NOT NULL,
        tenure_months INTEGER NOT NULL,
        loan_type TEXT NOT NULL,
        credit_utilization REAL NOT NULL,
        missed_payments INTEGER NOT NULL,
        pd REAL NOT NULL,
        risk_band TEXT NOT NULL,
        decision TEXT NOT NULL,
        emi REAL NOT NULL,
        max_eligible REAL NOT NULL,
        interest_rate REAL NOT NULL,
        explanation_json TEXT,
        advice TEXT,
        created_at TEXT NOT NULL
    );
    """
    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(create_table_sql)

        # Check if table already contains data
        cursor.execute("SELECT COUNT(*) AS total_records FROM applications;")
        count = cursor.fetchone()["total_records"]

        if count == 0:
            print("[*] 'applications' table is empty. Populating 12 realistic Indian applicant profiles...")
            _insert_sample_applications(cursor)
            conn.commit()
            print("[+] 12 sample application records populated successfully.")
        else:
            print(f"[i] 'applications' table already contains {count} records. Skipping seed.")

    except sqlite3.Error as e:
        print(f"[Error] Failed to initialize database: {e}")
        raise e
    finally:
        if conn:
            conn.close()


def insert_application(data: Dict[str, Any], db_path: str = DB_FILE) -> int:
    """
    Inserts a newly evaluated loan application record into SQLite.
    
    Args:
        data (dict): Dictionary with keys matching the schema:
                     name, age, employment_type, monthly_income, credit_score,
                     existing_emi, loan_amount, tenure_months, loan_type,
                     credit_utilization, missed_payments, pd, risk_band,
                     decision, emi, max_eligible, interest_rate,
                     explanation_json, advice, [created_at optional]
        db_path (str): Path to SQLite database file.
        
    Returns:
        int: The newly generated application ID (primary key).
    """
    insert_sql = """
    INSERT INTO applications (
        name, age, employment_type, monthly_income, credit_score,
        existing_emi, loan_amount, tenure_months, loan_type,
        credit_utilization, missed_payments, pd, risk_band,
        decision, emi, max_eligible, interest_rate,
        explanation_json, advice, created_at
    ) VALUES (
        :name, :age, :employment_type, :monthly_income, :credit_score,
        :existing_emi, :loan_amount, :tenure_months, :loan_type,
        :credit_utilization, :missed_payments, :pd, :risk_band,
        :decision, :emi, :max_eligible, :interest_rate,
        :explanation_json, :advice, :created_at
    );
    """
    conn = None
    try:
        record = {
            "name": str(data.get("name", "Anonymous Applicant")).strip(),
            "age": int(data.get("age", 30)),
            "employment_type": str(data.get("employment_type", "Salaried")),
            "monthly_income": float(data.get("monthly_income", 0.0)),
            "credit_score": int(data.get("credit_score", 650)),
            "existing_emi": float(data.get("existing_emi", 0.0)),
            "loan_amount": float(data.get("loan_amount", 0.0)),
            "tenure_months": int(data.get("tenure_months", 12)),
            "loan_type": str(data.get("loan_type", "Personal")),
            "credit_utilization": float(data.get("credit_utilization", 25.0)),
            "missed_payments": int(data.get("missed_payments", 0)),
            "pd": float(data.get("pd", 0.15)),
            "risk_band": str(data.get("risk_band", "Moderate Risk")),
            "decision": str(data.get("decision", "Review")),
            "emi": float(data.get("emi", 0.0)),
            "max_eligible": float(data.get("max_eligible", 0.0)),
            "interest_rate": float(data.get("interest_rate", 10.5)),
            "explanation_json": (
                json.dumps(data.get("explanation_json"))
                if isinstance(data.get("explanation_json"), (dict, list))
                else str(data.get("explanation_json", "{}"))
            ),
            "advice": str(data.get("advice", "")),
            "created_at": str(
                data.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            ),
        }

        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(insert_sql, record)
        conn.commit()
        return cursor.lastrowid

    except (sqlite3.Error, ValueError, TypeError) as err:
        print(f"[Error] Failed to insert application into database: {err}")
        raise err
    finally:
        if conn:
            conn.close()


def get_all_applications(db_path: str = DB_FILE) -> List[Dict[str, Any]]:
    """
    Fetches all application records from the database, sorted from newest to oldest.
    
    Returns:
        List[Dict[str, Any]]: List of dictionary representations of all applications.
    """
    select_sql = """
    SELECT * FROM applications
    ORDER BY id DESC;
    """
    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(select_sql)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"[Error] Failed to fetch applications: {e}")
        return []
    finally:
        if conn:
            conn.close()


def get_stats(db_path: str = DB_FILE) -> Dict[str, Any]:
    """
    Computes portfolio KPIs, approval/rejection rates, and volume analytics.
    
    Returns:
        Dict[str, Any]: Aggregated metrics (total count, approval rate, total portfolio,
                        average CIBIL, average PD, risk breakdown).
    """
    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                COUNT(*) AS total_applications,
                SUM(CASE WHEN decision = 'Approved' THEN 1 ELSE 0 END) AS approved_count,
                SUM(CASE WHEN decision = 'Review' THEN 1 ELSE 0 END) AS review_count,
                SUM(CASE WHEN decision = 'Rejected' THEN 1 ELSE 0 END) AS rejected_count,
                COALESCE(AVG(credit_score), 0) AS avg_credit_score,
                COALESCE(AVG(pd), 0) AS avg_pd,
                COALESCE(SUM(loan_amount), 0) AS total_requested_amount,
                COALESCE(SUM(CASE WHEN decision = 'Approved' THEN loan_amount ELSE 0 END), 0) AS total_approved_amount,
                COALESCE(AVG(monthly_income), 0) AS avg_monthly_income
            FROM applications;
        """)
        overall = dict(cursor.fetchone())

        total = overall["total_applications"]
        approved = overall["approved_count"] or 0
        review = overall["review_count"] or 0
        rejected = overall["rejected_count"] or 0

        approval_rate = round((approved / total * 100.0), 1) if total > 0 else 0.0
        rejection_rate = round((rejected / total * 100.0), 1) if total > 0 else 0.0
        review_rate = round((review / total * 100.0), 1) if total > 0 else 0.0

        cursor.execute("""
            SELECT 
                risk_band,
                COUNT(*) as count
            FROM applications
            GROUP BY risk_band;
        """)
        risk_band_counts = {row["risk_band"]: row["count"] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT 
                loan_type,
                COUNT(*) as count,
                COALESCE(SUM(loan_amount), 0) as total_volume
            FROM applications
            GROUP BY loan_type;
        """)
        loan_type_breakdown = [dict(row) for row in cursor.fetchall()]

        return {
            "total_applications": total,
            "approved_count": approved,
            "review_count": review,
            "rejected_count": rejected,
            "approval_rate": approval_rate,
            "rejection_rate": rejection_rate,
            "review_rate": review_rate,
            "avg_credit_score": round(float(overall["avg_credit_score"]), 1),
            "avg_pd": round(float(overall["avg_pd"]), 4),
            "avg_pd_percent": round(float(overall["avg_pd"]) * 100.0, 1),
            "total_requested_amount": float(overall["total_requested_amount"]),
            "total_approved_amount": float(overall["total_approved_amount"]),
            "avg_monthly_income": round(float(overall["avg_monthly_income"]), 2),
            "risk_band_counts": risk_band_counts,
            "loan_type_breakdown": loan_type_breakdown,
        }

    except sqlite3.Error as e:
        print(f"[Error] Failed to compute loan stats: {e}")
        return {
            "total_applications": 0,
            "approved_count": 0,
            "review_count": 0,
            "rejected_count": 0,
            "approval_rate": 0.0,
            "rejection_rate": 0.0,
            "review_rate": 0.0,
            "avg_credit_score": 0.0,
            "avg_pd": 0.0,
            "avg_pd_percent": 0.0,
            "total_requested_amount": 0.0,
            "total_approved_amount": 0.0,
            "avg_monthly_income": 0.0,
            "risk_band_counts": {},
            "loan_type_breakdown": [],
        }
    finally:
        if conn:
            conn.close()


def get_monthly_counts(db_path: str = DB_FILE) -> List[Dict[str, Any]]:
    """
    Returns monthly application volume and decisions for the last 6 months.
    
    Returns:
        List[Dict[str, Any]]: Formatted list of monthly trend dictionaries:
        [{
            "month": "2024-06",
            "display_month": "Jun 2024",
            "total": 2,
            "approved": 2,
            "review": 0,
            "rejected": 0,
            "volume_amount": 4500000.0
        }, ...]
    """
    query_sql = """
    SELECT 
        SUBSTR(created_at, 1, 7) AS month_key,
        COUNT(*) AS total,
        SUM(CASE WHEN decision = 'Approved' THEN 1 ELSE 0 END) AS approved,
        SUM(CASE WHEN decision = 'Review' THEN 1 ELSE 0 END) AS review,
        SUM(CASE WHEN decision = 'Rejected' THEN 1 ELSE 0 END) AS rejected,
        COALESCE(SUM(loan_amount), 0) AS total_volume
    FROM applications
    GROUP BY month_key
    ORDER BY month_key ASC;
    """
    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(query_sql)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            month_key = row["month_key"]  # Format: "YYYY-MM"
            try:
                dt = datetime.strptime(month_key, "%Y-%m")
                display_month = dt.strftime("%b %Y")
            except ValueError:
                display_month = month_key

            result.append({
                "month": month_key,
                "display_month": display_month,
                "total": int(row["total"]),
                "approved": int(row["approved"] or 0),
                "review": int(row["review"] or 0),
                "rejected": int(row["rejected"] or 0),
                "volume_amount": float(row["total_volume"] or 0.0),
            })
        return result
    except sqlite3.Error as e:
        print(f"[Error] Failed to calculate monthly counts: {e}")
        return []
    finally:
        if conn:
            conn.close()


def _insert_sample_applications(cursor: sqlite3.Cursor) -> None:
    """
    Internal helper to seed 12 realistic Indian applicant profiles across the past 6 months.
    Distribution: 6 Approved, 3 Review, 3 Rejected.
    Includes rich Indian names, ₹ salary scales, CIBIL scores (300-900), and structured JSON explanations.
    """
    now = datetime.now()

    sample_records = [
        # --- Month 1 (approx 5 months ago) ---
        {
            "name": "Aarav Sharma",
            "age": 34,
            "employment_type": "Salaried",
            "monthly_income": 125000.0,
            "credit_score": 810,
            "existing_emi": 15000.0,
            "loan_amount": 3500000.0,
            "tenure_months": 180,
            "loan_type": "Home",
            "credit_utilization": 14.5,
            "missed_payments": 0,
            "pd": 0.042,
            "risk_band": "Low Risk",
            "decision": "Approved",
            "emi": 34560.0,
            "max_eligible": 5200000.0,
            "interest_rate": 8.50,
            "explanation_json": json.dumps({
                "strengths": ["CIBIL score is in top tier (810)", "FOIR is comfortably under 40%", "Zero delayed payments"],
                "risk_factors": ["Long tenure requested (15 years)"],
                "credit_utilization_status": "Optimal (14.5%)",
                "recommended_action": "Instant approval at prime interest rate of 8.50%."
            }),
            "advice": "Excellent credit discipline. Maintain low credit card utilization and continue prompt EMI payments to retain sovereign prime rates.",
            "created_at": (now - timedelta(days=162)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "name": "Priya Patel",
            "age": 28,
            "employment_type": "Salaried",
            "monthly_income": 65000.0,
            "credit_score": 765,
            "existing_emi": 5000.0,
            "loan_amount": 350000.0,
            "tenure_months": 36,
            "loan_type": "Personal",
            "credit_utilization": 22.0,
            "missed_payments": 0,
            "pd": 0.088,
            "risk_band": "Low Risk",
            "decision": "Approved",
            "emi": 11625.0,
            "max_eligible": 620000.0,
            "interest_rate": 11.50,
            "explanation_json": json.dumps({
                "strengths": ["Healthy CIBIL of 765", "Low existing financial leverage", "Clean bureau track record"],
                "risk_factors": ["Personal loan is unsecured"],
                "credit_utilization_status": "Healthy (< 30%)",
                "recommended_action": "Sanction loan with zero collateral requirement."
            }),
            "advice": "Consider setting up auto-debit (e-NACH) for monthly EMIs to ensure you never miss a due date as your income expands.",
            "created_at": (now - timedelta(days=148)).strftime("%Y-%m-%d %H:%M:%S")
        },

        # --- Month 2 (approx 4 months ago) ---
        {
            "name": "Rajesh Kumar",
            "age": 42,
            "employment_type": "Self-Employed Business",
            "monthly_income": 45000.0,
            "credit_score": 540,
            "existing_emi": 22000.0,
            "loan_amount": 800000.0,
            "tenure_months": 48,
            "loan_type": "Business",
            "credit_utilization": 82.4,
            "missed_payments": 4,
            "pd": 0.765,
            "risk_band": "High Risk",
            "decision": "Rejected",
            "emi": 22250.0,
            "max_eligible": 150000.0,
            "interest_rate": 15.00,
            "explanation_json": json.dumps({
                "strengths": ["Business operational experience > 5 yrs"],
                "risk_factors": [
                    "CIBIL score is critically poor (540 < 650 threshold)",
                    "Severe delinquency: 4 missed payments in last 12 months",
                    "Excessive credit card revolving balance (82.4%)",
                    "FOIR exceeds 98% with proposed loan"
                ],
                "credit_utilization_status": "Severe (> 80%)",
                "recommended_action": "Reject application due to default risk."
            }),
            "advice": "Clear all overdue loan payments and settle revolving credit card debt below 30% utilization. Rebuild CIBIL history for at least 6 months before reapplying.",
            "created_at": (now - timedelta(days=122)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "name": "Sunita Rao",
            "age": 31,
            "employment_type": "Salaried",
            "monthly_income": 85000.0,
            "credit_score": 780,
            "existing_emi": 8000.0,
            "loan_amount": 650000.0,
            "tenure_months": 60,
            "loan_type": "Auto",
            "credit_utilization": 18.2,
            "missed_payments": 0,
            "pd": 0.065,
            "risk_band": "Low Risk",
            "decision": "Approved",
            "emi": 13650.0,
            "max_eligible": 1200000.0,
            "interest_rate": 9.25,
            "explanation_json": json.dumps({
                "strengths": ["CIBIL score of 780 reflects superior repayment behavior", "FOIR stands at an optimal 25.5%", "Collateral vehicle backing"],
                "risk_factors": ["None observed"],
                "credit_utilization_status": "Superior (18.2%)",
                "recommended_action": "Immediate sanction at concessional auto rate."
            }),
            "advice": "Your strong credit score qualifies you for pre-approved vehicle loans at premier interest rates.",
            "created_at": (now - timedelta(days=105)).strftime("%Y-%m-%d %H:%M:%S")
        },

        # --- Month 3 (approx 3 months ago) ---
        {
            "name": "Vikram Malhotra",
            "age": 38,
            "employment_type": "Self-Employed Professional",
            "monthly_income": 95000.0,
            "credit_score": 672,
            "existing_emi": 32000.0,
            "loan_amount": 600000.0,
            "tenure_months": 36,
            "loan_type": "Personal",
            "credit_utilization": 54.0,
            "missed_payments": 1,
            "pd": 0.385,
            "risk_band": "Moderate Risk",
            "decision": "Review",
            "emi": 20450.0,
            "max_eligible": 420000.0,
            "interest_rate": 13.50,
            "explanation_json": json.dumps({
                "strengths": ["Consistent professional income", "Stable self-employed tax filings"],
                "risk_factors": [
                    "CIBIL score is borderline (672)",
                    "Credit utilization is elevated at 54%",
                    "1 minor 30-day late payment recorded 7 months ago",
                    "Combined FOIR is slightly high at 55.2%"
                ],
                "credit_utilization_status": "Elevated (54.0%)",
                "recommended_action": "Manual review required. Request co-applicant or offer reduced loan amount of ₹4.2 Lakh."
            }),
            "advice": "Pay off one existing short-term EMI or reduce the requested loan to ₹4,00,000 to bring your debt-to-income ratio within auto-approval boundaries.",
            "created_at": (now - timedelta(days=88)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "name": "Amit Verma",
            "age": 25,
            "employment_type": "Salaried",
            "monthly_income": 50000.0,
            "credit_score": 745,
            "existing_emi": 0.0,
            "loan_amount": 800000.0,
            "tenure_months": 84,
            "loan_type": "Education",
            "credit_utilization": 12.0,
            "missed_payments": 0,
            "pd": 0.095,
            "risk_band": "Low Risk",
            "decision": "Approved",
            "emi": 12900.0,
            "max_eligible": 950000.0,
            "interest_rate": 8.85,
            "explanation_json": json.dumps({
                "strengths": ["Zero existing liabilities", "Pristine credit history", "Accredited master's program"],
                "risk_factors": ["Young applicant with limited credit depth"],
                "credit_utilization_status": "Excellent (12%)",
                "recommended_action": "Approved under Student Higher Education Priority Scheme."
            }),
            "advice": "Avail tax deductions under Section 80E of the Indian Income Tax Act on full interest paid for education loans.",
            "created_at": (now - timedelta(days=74)).strftime("%Y-%m-%d %H:%M:%S")
        },

        # --- Month 4 (approx 2 months ago) ---
        {
            "name": "Neha Joshi",
            "age": 29,
            "employment_type": "Salaried",
            "monthly_income": 38000.0,
            "credit_score": 585,
            "existing_emi": 16000.0,
            "loan_amount": 300000.0,
            "tenure_months": 24,
            "loan_type": "Personal",
            "credit_utilization": 89.5,
            "missed_payments": 3,
            "pd": 0.720,
            "risk_band": "High Risk",
            "decision": "Rejected",
            "emi": 14500.0,
            "max_eligible": 80000.0,
            "interest_rate": 15.50,
            "explanation_json": json.dumps({
                "strengths": ["Salaried regular income"],
                "risk_factors": [
                    "CIBIL score 585 falls well below minimum 650 cutoff",
                    "3 delinquent payments logged in last 6 months",
                    "Extreme credit card max-out at 89.5%",
                    "Total FOIR would breach 80%"
                ],
                "credit_utilization_status": "Critical (89.5%)",
                "recommended_action": "Strict rejection as per prudential risk guidelines."
            }),
            "advice": "Prioritize paying down the highest-interest credit card balance first. Do not apply for multiple credit products consecutively to avoid hard inquiry score deductions.",
            "created_at": (now - timedelta(days=58)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "name": "Rohit Deshmukh",
            "age": 45,
            "employment_type": "Salaried",
            "monthly_income": 180000.0,
            "credit_score": 830,
            "existing_emi": 25000.0,
            "loan_amount": 6000000.0,
            "tenure_months": 240,
            "loan_type": "Home",
            "credit_utilization": 9.5,
            "missed_payments": 0,
            "pd": 0.035,
            "risk_band": "Low Risk",
            "decision": "Approved",
            "emi": 52100.0,
            "max_eligible": 8500000.0,
            "interest_rate": 8.35,
            "explanation_json": json.dumps({
                "strengths": ["High net-worth profile", "Exceptional CIBIL score of 830", "Substantial disposable liquidity", "FOIR well contained at 42.8%"],
                "risk_factors": ["None"],
                "credit_utilization_status": "Exceptional (< 10%)",
                "recommended_action": "Sanctioned at our lowest benchmark prime lending rate."
            }),
            "advice": "You are eligible for pre-sanctioned top-up loans and accelerated processing through priority banking.",
            "created_at": (now - timedelta(days=46)).strftime("%Y-%m-%d %H:%M:%S")
        },

        # --- Month 5 (approx 1 month ago) ---
        {
            "name": "Ananya Iyer",
            "age": 36,
            "employment_type": "Self-Employed Professional",
            "monthly_income": 110000.0,
            "credit_score": 685,
            "existing_emi": 38000.0,
            "loan_amount": 1200000.0,
            "tenure_months": 48,
            "loan_type": "Business",
            "credit_utilization": 58.0,
            "missed_payments": 0,
            "pd": 0.315,
            "risk_band": "Moderate Risk",
            "decision": "Review",
            "emi": 32800.0,
            "max_eligible": 850000.0,
            "interest_rate": 13.00,
            "explanation_json": json.dumps({
                "strengths": ["Strong professional turnover as Medical Consultant", "Zero historical defaults"],
                "risk_factors": [
                    "High combined EMI burden pushing FOIR to 64.3%",
                    "Credit utilization at 58% indicates working capital tightness"
                ],
                "credit_utilization_status": "High (58.0%)",
                "recommended_action": "Conditional approval subject to extending tenure to 60 months or reducing amount to ₹8.5 Lakh."
            }),
            "advice": "Extending the loan tenure from 48 to 60 months lowers the monthly installment to ₹27,300, safely reducing your FOIR to acceptable 59%.",
            "created_at": (now - timedelta(days=28)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "name": "Deepak Choudhary",
            "age": 50,
            "employment_type": "Self-Employed Business",
            "monthly_income": 32000.0,
            "credit_score": 510,
            "existing_emi": 19000.0,
            "loan_amount": 500000.0,
            "tenure_months": 36,
            "loan_type": "Personal",
            "credit_utilization": 94.0,
            "missed_payments": 5,
            "pd": 0.885,
            "risk_band": "High Risk",
            "decision": "Rejected",
            "emi": 17500.0,
            "max_eligible": 50000.0,
            "interest_rate": 16.00,
            "explanation_json": json.dumps({
                "strengths": ["None identified for unsecured credit"],
                "risk_factors": [
                    "Extremely low CIBIL (510)",
                    "Chronic default status (5 missed payments)",
                    "Existing EMIs consume 59.4% of total income prior to new loan",
                    "New loan would result in debt servicing exceeding total earnings"
                ],
                "credit_utilization_status": "Severe Max-Out (94.0%)",
                "recommended_action": "Decline. Significant risk of immediate default."
            }),
            "advice": "Consider approaching an Indian public sector bank or NBFC for a gold loan or secured asset-backed facility while clearing outstanding dues.",
            "created_at": (now - timedelta(days=19)).strftime("%Y-%m-%d %H:%M:%S")
        },

        # --- Month 6 (recent / current month) ---
        {
            "name": "Pooja Nair",
            "age": 27,
            "employment_type": "Salaried",
            "monthly_income": 58000.0,
            "credit_score": 678,
            "existing_emi": 12000.0,
            "loan_amount": 450000.0,
            "tenure_months": 48,
            "loan_type": "Auto",
            "credit_utilization": 46.5,
            "missed_payments": 1,
            "pd": 0.295,
            "risk_band": "Moderate Risk",
            "decision": "Review",
            "emi": 11500.0,
            "max_eligible": 380000.0,
            "interest_rate": 10.25,
            "explanation_json": json.dumps({
                "strengths": ["Stable MNC employment tenure", "Vehicle hypothecation reduces unsecured risk"],
                "risk_factors": [
                    "CIBIL score is in fair zone (678)",
                    "Single missed payment 10 months ago",
                    "Credit utilization is slightly above 40%"
                ],
                "credit_utilization_status": "Moderate (46.5%)",
                "recommended_action": "Conditional approval with 15% upfront vehicle down-payment."
            }),
            "advice": "A marginally higher initial down payment of 15% to 20% will secure auto-approval at our preferential 9.75% interest slab.",
            "created_at": (now - timedelta(days=9)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "name": "Siddharth Sen",
            "age": 33,
            "employment_type": "Salaried",
            "monthly_income": 140000.0,
            "credit_score": 795,
            "existing_emi": 18000.0,
            "loan_amount": 750000.0,
            "tenure_months": 36,
            "loan_type": "Personal",
            "credit_utilization": 16.0,
            "missed_payments": 0,
            "pd": 0.055,
            "risk_band": "Low Risk",
            "decision": "Approved",
            "emi": 24500.0,
            "max_eligible": 1500000.0,
            "interest_rate": 11.00,
            "explanation_json": json.dumps({
                "strengths": [
                    "Impressive CIBIL score of 795",
                    "High monthly surplus post-EMI",
                    "Very conservative credit card utilization"
                ],
                "risk_factors": ["None"],
                "credit_utilization_status": "Optimal (16%)",
                "recommended_action": "Pre-approved with waiver on loan processing charges."
            }),
            "advice": "You maintain an exemplary credit footprint. Consider opting for flexible tenure prepayment without foreclosure penalties.",
            "created_at": (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
        }
    ]

    insert_sql = """
    INSERT INTO applications (
        name, age, employment_type, monthly_income, credit_score,
        existing_emi, loan_amount, tenure_months, loan_type,
        credit_utilization, missed_payments, pd, risk_band,
        decision, emi, max_eligible, interest_rate,
        explanation_json, advice, created_at
    ) VALUES (
        :name, :age, :employment_type, :monthly_income, :credit_score,
        :existing_emi, :loan_amount, :tenure_months, :loan_type,
        :credit_utilization, :missed_payments, :pd, :risk_band,
        :decision, :emi, :max_eligible, :interest_rate,
        :explanation_json, :advice, :created_at
    );
    """
    for record in sample_records:
        cursor.execute(insert_sql, record)

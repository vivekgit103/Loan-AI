# LoanIQ: AI-Based Retail Loan Eligibility & Risk Assessment System
### Indian Retail Credit Underwriting Engine (₹ INR &bull; CIBIL Bureau 300–900)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask_3.x-lightgrey.svg)](https://flask.palletsprojects.com/)
[![ML](https://img.shields.io/badge/ML-Scikit--Learn-orange.svg)](https://scikit-learn.org/)
[![Database](https://img.shields.io/badge/Database-SQLite3-green.svg)](https://www.sqlite.org/)
[![Styling](https://img.shields.io/badge/Styling-Tailwind_CSS_CDN-38bdf8.svg)](https://tailwindcss.com/)

---

## 1. Project Overview

**LoanIQ** is an institutional-grade, full-stack and Machine Learning capstone project designed to automate retail credit decisioning in the **Indian banking context**. 

The system blends **quantitative Machine Learning** (calibrated `StandardScaler + LogisticRegression` pipeline predicting **Probability of Default (PD)** with 99% accuracy and 0.999+ ROC-AUC) with **prudential institutional credit policy rules** (RBI guidelines, CIBIL thresholds, debt-service ceilings) and an **Explainable AI (XAI) Financial Advisor Engine**.

### Core Capabilities:
- **Indian Financial Benchmarks:** Native support for Indian Rupee (`₹`), TransUnion CIBIL credit score spectrum (`300 - 900`), and standard retail lending categories (`Personal`, `Home`, `Auto`, `Education`, `Business`, `Gold`).
- **Standard Banking Calculations:** Real-time reducing-balance EMI calculation, Fixed Obligation to Income Ratio (**FOIR / DTI**), and automated maximum sanctionable borrowing capacity sizing.
- **Hybrid Decision Architecture:** Combines rule-based hard policy gates (rejecting severe credit impairment or income shortfall) with continuous ML probability scoring for risk stratification.
- **Explainable AI (XAI):** Mathematically attributes risk factors via linear log-odds decomposition ($\text{coef}_i \times \text{scaled\_feature}_i$) to surface the top 5 risk drivers and positive strengths with plain-English labels.
- **AI Financial Counseling:** Delivers personalized underwriting rationales and actionable improvement tips via **Anthropic Claude (Messages API)** with a built-in expert heuristic fallback.
- **Modern Responsive Web Interface:** Real-time dynamic form diagnostics, 6-month portfolio analytics, printable sanction reports, and searchable application logs powered by Tailwind CSS CDN and vanilla JavaScript (no React or npm).

---

## 2. Directory Structure

```
loan-ai/
│
├── app.py                     # Flask web server, route controllers, and JSON REST API
├── database.py                # SQLite persistence, schema initialization, analytics queries & sample seed
│
├── model/
│   ├── data_generator.py      # Synthetic Indian retail borrower dataset generator (5,000 records)
│   ├── train_model.py         # Pipeline training (StandardScaler + LogisticRegression), metrics, serialization
│   ├── loan_data.csv          # Generated synthetic training dataset
│   └── loan_model.pkl         # Serialized ML pipeline with feature names
│
├── engine/
│   ├── features.py            # Financial math: EMI, FOIR, Max Loan Capacity & XAI explain() function
│   ├── rules.py               # Hard policy gates, risk bands, interest pricing, and evaluate() pipeline
│   └── advisor.py             # Anthropic Claude Messages API integration with rule-based fallback
│
├── templates/
│   ├── base.html              # 3-column app shell (256px left, fluid middle, 320px right), LoanIQ logo
│   ├── dashboard.html         # KPIs, custom CSS monthly bar chart, loan catalog, right sidebar
│   ├── apply.html             # 2-step stepper form, sample loader, live EMI preview, fetch POST /api/evaluate
│   ├── result.html            # Semicircle risk gauge, 4 stat cards, XAI factor bars, print stylesheet
│   └── applications.html      # Search, filter, sortable table, CSV export, row click navigation
│
├── static/
│   ├── css/style.css          # Design system tokens, thin scrollbars, range sliders, print styles
│   └── js/app.js              # Live EMI math, custom CSS bar chart with animated transitions
│
├── test_cases.py              # Automated 8-profile test script (samples + edge cases)
├── test_system.py             # Full-system verification test suite (Unit + Integration tests)
├── requirements.txt           # Pinned dependencies for Python 3.10+
├── .env.example               # Environment variables configuration template
└── README.md                  # Comprehensive technical documentation & project presentation guide
```

---

## 3. Quickstart Installation & Setup (Windows)

### Step 1: Open Terminal and Navigate to Directory
```powershell
cd "m:\GitHub\TrustScore AI\loan-ai"
```

### Step 2: Create and Activate Virtual Environment
```powershell
# Create virtual environment
python -m venv venv

# Activate in PowerShell
.\venv\Scripts\Activate.ps1
# (Or in CMD: venv\Scripts\activate.bat)
```

### Step 3: Install Pinned Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```
Inside `.env`, configure your optional Anthropic API key:
```env
SECRET_KEY=loaniq-secret-key-2024-indian-retail-credit
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```
*(If no API key is configured, the system automatically falls back to its built-in Indian retail banking expert heuristic engine without errors).*

---

## 4. How to Train the Model

The pre-trained model artifact `model/loan_model.pkl` is already included. To regenerate the synthetic data and retrain from scratch:

```powershell
# 1. Generate 5,000 synthetic Indian borrower records (~18% default rate)
python model/data_generator.py

# 2. Train the Scikit-Learn Pipeline (StandardScaler + LogisticRegression)
python model/train_model.py
```

### Model Performance Benchmarks:
- **Accuracy:** 99.00%
- **Precision:** 97.77%
- **Recall:** 96.69%
- **ROC-AUC:** 0.9994

---

## 5. How to Run the Application & Tests

### Run Automated 8-Case Diagnostic Suite
```powershell
python test_cases.py
```

### Run Full Unit & End-to-End System Test Suite
```powershell
python test_system.py
```

### Launch the Web Application
```powershell
python app.py
```
*Or from either the project root or `loan-ai` directory using npm:*
```bash
npm run dev
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 6. Screenshots Checklist for Project Submission

When compiling your college report or presentation slide deck, capture the following 6 core screens:

- [ ] **Screenshot 1: Executive Command Center (`/`)**
  - Shows greeting "Welcome back, Officer 👋", live search bar, 4 KPI cards (Total Applications, Approval Rate, Avg Credit Score, High-Risk Cases).
  - Shows custom CSS monthly bar chart in `#chart-area` with floating highest-month badge ("📈 22 apps") and dark hover tooltip ("Approved: 15").
- [ ] **Screenshot 2: Institutional Loan Catalog & Right Sidebar (`/`)**
  - Shows 6 loan product cards (Personal, Home, Auto, Education, Business, Gold) with interest rates, max sanction amounts, and tenures.
  - Shows right sidebar with latest applicant circular avatar, 14-day horizontal mini calendar scroller, and document checklist.
- [ ] **Screenshot 3: Application Intake Step 1 (`/apply`)**
  - Shows the progress stepper at Step 1 (Personal & Income), demographic fields, and the "Load Sample Applicant" dropdown in action.
- [ ] **Screenshot 4: Application Intake Step 2 (`/apply`)**
  - Shows Step 2 with the dynamic CIBIL slider, live colored badge (e.g. "Excellent 750" in green), revolving utilization slider, and live estimated EMI preview card.
- [ ] **Screenshot 5: Comprehensive Underwriting Report (`/result/<id>`)**
  - Shows top decision badge (Approved green / Manual Review orange / Rejected pink), semicircle SVG gauge with animated needle, 4 financial stat cards (EMI, Rate, Max Sanction, FOIR), Explainable AI horizontal attribution bars, and purple AI Advisor card.
- [ ] **Screenshot 6: Full Application Registry & CSV Export (`/applications`)**
  - Shows search bar, multi-criteria filter dropdowns (Decision, Risk), sortable table columns, and the green "Export CSV" button generating `loaniq_applications_<date>.csv`.

---

## 7. Web Routes & API Documentation

| Route | Method | Purpose |
| :--- | :---: | :--- |
| `/` | `GET` | Executive dashboard with KPIs, monthly CSS bar chart, loan catalog, and right sidebar |
| `/apply` | `GET`, `POST` | 2-step interactive intake form & client-side live diagnostics |
| `/result/<id>` | `GET` | Granular loan sanction report with SVG gauge, XAI attribution bars, and print stylesheet |
| `/applications` | `GET` | Searchable, filterable tabular registry with sortable columns and CSV export |
| `/delete/<id>` | `POST` | Deletes an application record from the registry |
| `/api/evaluate` | `POST` | Primary REST API: validates payload, runs ML + rules + XAI + advisor, returns JSON, and saves to DB |
| `/api/stats` | `GET` | JSON endpoint returning portfolio statistics and 6-month decision breakdown |
| `/api/calculate-emi` | `POST` | REST API for client-side asynchronous EMI and FOIR calculation |

---

## 8. License
Developed for academic capstone, viva defense, and educational evaluation purposes.

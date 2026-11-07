# Loan-AI: AI-Based Retail Loan Eligibility & Risk Assessment System

Institutional-grade Indian retail credit underwriting engine powered by Python, Flask, Scikit-Learn, and Explainable AI (XAI).

## Quick Start

### Option 1: Via npm (Node.js wrapper)
If you prefer running with `npm`:
```bash
npm install
npm run dev
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

Other npm commands:
- `npm run test`  - Run the 8-applicant verification test suite
- `npm run train` - Retrain the Scikit-Learn risk model

---

### Option 2: Native Python / Flask
```powershell
cd loan-ai
.\venv\Scripts\activate
python app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

For comprehensive architecture, mathematical formulas, policy rules, and technical viva documentation, see [loan-ai/README.md](loan-ai/README.md).

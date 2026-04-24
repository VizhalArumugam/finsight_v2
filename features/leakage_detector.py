"""
FinSight v2 — features/leakage_detector.py
=========================================
Blueprint: /api/audit
Module 5B — Financial Leakage Detector

Validates daily sales against bank/cash deposits to identify
potential fraud or unaccounted cash (leakage) > 2%.
Uses free AI (Groq → Gemini) to generate an audit report.
"""

from flask import Blueprint, request, jsonify
from config.ai_client import ask_ai_json
import json

audit_bp = Blueprint("audit", __name__, url_prefix="/api/audit")

def ai_audit_report(total_sales, total_deposits, mismatch, mismatch_pct):
    prompt = f"""You are a financial auditor for Indian small businesses.
There is a discrepancy in today's books:
- Total Sales Recorded: ₹{total_sales}
- Total Bank/Cash Deposits: ₹{total_deposits}
- Unaccounted mismatch: ₹{mismatch} ({mismatch_pct}%)
    
Analyze what might have happened (e.g. forgotten petty cash, employee theft, unrecorded vendor payments) and give actionable advice.

Return strictly JSON format:
{{
  "anomalies": ["reason 1", "reason 2"],
  "ai_report": "A 2-sentence summary of the risk.",
  "action_steps": ["step 1", "step 2", "step 3"]
}}
"""
    try:
        result = ask_ai_json(prompt)
        return {
            "anomalies": result.get("anomalies", []),
            "ai_report": result.get("ai_report", "Unable to generate specific report."),
            "action_steps": result.get("action_steps", [])
        }
    except Exception as e:
        return {
            "anomalies": ["AI analysis failed."],
            "ai_report": f"System error during analysis: {str(e)}",
            "action_steps": ["Manually review all cash drawer transactions today."]
        }

@audit_bp.route("/run", methods=["POST"])
def run_audit():
    body = request.get_json(force=True)
    sales = body.get("sales", [])
    deposits = body.get("deposits", [])

    if not sales and not deposits:
        return jsonify({"error": "Sales or deposits arrays are required."}), 400

    try:
        total_sales = sum([float(s.get("qty", 0)) * float(s.get("price", 0)) for s in sales])
        total_deposits = sum([float(d.get("amount", 0)) for d in deposits])
        
        mismatch = round(total_sales - total_deposits, 2)
        mismatch_pct = round((mismatch / total_sales) * 100, 2) if total_sales > 0 else 0

        if mismatch_pct > 5:
            status = "critical"
        elif mismatch_pct > 2:
            status = "warning"
        else:
            status = "clean"

        if status == "clean":
            return jsonify({
                "total_sales": total_sales,
                "total_deposits": total_deposits,
                "mismatch": mismatch,
                "mismatch_pct": mismatch_pct,
                "status": status,
                "anomalies": [],
                "ai_report": "Books are balanced. Excellent day!",
                "action_steps": []
            }), 200

        report = ai_audit_report(total_sales, total_deposits, mismatch, mismatch_pct)
        
        return jsonify({
            "total_sales": total_sales,
            "total_deposits": total_deposits,
            "mismatch": mismatch,
            "mismatch_pct": mismatch_pct,
            "status": status,
            "anomalies": report["anomalies"],
            "ai_report": report["ai_report"],
            "action_steps": report["action_steps"]
        }), 200

    except ValueError as e:
        return jsonify({"error": "Invalid numerical data in request.", "detail": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error.", "detail": str(e)}), 500

@audit_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"module": "leakage_detector", "status": "ok"}), 200

"""
FinSight v2 — features/abc_classifier.py
=======================================
Blueprint: /api/abc
Module 3 — ABC Inventory Classifier
"""
from flask import Blueprint, request, jsonify

abc_bp = Blueprint("abc", __name__, url_prefix="/api/abc")

@abc_bp.route("/classify", methods=["POST"])
def classify():
    body = request.get_json(force=True)
    products = body.get("products", [])
    
    if not products:
        return jsonify({"error": "products array required"}), 400

    # Calculate revenue
    enriched = []
    total_rev = 0
    for p in products:
        rev = float(p.get("monthly_sales_qty", 0)) * float(p.get("unit_price", 0))
        total_rev += rev
        enriched.append({**p, "revenue": rev})

    # Sort descending by revenue
    enriched.sort(key=lambda x: x["revenue"], reverse=True)

    # Classify cumulative
    cum_rev = 0
    results = []
    summary = {"A": 0, "B": 0, "C": 0}

    for p in enriched:
        cum_rev += p["revenue"]
        pct = (cum_rev / total_rev) * 100 if total_rev > 0 else 0
        
        if pct <= 70:
            cls = "A"
        elif pct <= 90:
            cls = "B"
        else:
            cls = "C"
            
        summary[cls] += 1
        results.append({
            "name": p.get("name"),
            "revenue": round(p["revenue"], 2),
            "class": cls
        })

    return jsonify({
        "status": "success",
        "data": {
            "total_revenue": round(total_rev, 2),
            "summary_counts": summary,
            "products": results
        }
    }), 200

@abc_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"module": "abc", "status": "ok"}), 200

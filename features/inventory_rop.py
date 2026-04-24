"""
FinSight v2 — features/inventory_rop.py
======================================
Blueprint: /api/inventory
Module 2 — Inventory Reorder Point (ROP) Calculator
"""
from flask import Blueprint, request, jsonify

inventory_bp = Blueprint("inventory", __name__, url_prefix="/api/inventory")

@inventory_bp.route("/rop", methods=["POST"])
def calculate_rop():
    body = request.get_json(force=True)
    products = body.get("products")
    
    if products and isinstance(products, list):
        results = []
        for p in products:
            product = p.get("product", "Unknown")
            daily_sales = float(p.get("avg_daily_sales", 0))
            lead_time = float(p.get("lead_time_days", 0))
            safety_stock = float(p.get("safety_stock", 0))
            current_stock = float(p.get("current_stock", 0))
            
            rop = (daily_sales * lead_time) + safety_stock
            status = "order_now" if current_stock <= rop else "sufficient"
            days_until_stockout = current_stock / daily_sales if daily_sales > 0 else 999
            order_qty = max(0, rop - current_stock + safety_stock)
            
            results.append({
                "product": product,
                "rop": round(rop, 2),
                "status": status,
                "days_until_stockout": round(days_until_stockout, 1),
                "order_quantity_suggested": round(order_qty, 2),
                "current_stock": current_stock
            })
        return jsonify({"status": "success", "data": {"batch": True, "results": results}}), 200
        
    else:
        product = body.get("product")
        daily_sales = float(body.get("avg_daily_sales", 0))
        lead_time = float(body.get("lead_time_days", 0))
        safety_stock = float(body.get("safety_stock", 0))
        current_stock = float(body.get("current_stock", 0))
        
        if not product:
            return jsonify({"error": "product name required"}), 400

        rop = (daily_sales * lead_time) + safety_stock
        status = "order_now" if current_stock <= rop else "sufficient"
        days_until_stockout = current_stock / daily_sales if daily_sales > 0 else 999
        order_qty = max(0, rop - current_stock + safety_stock)

        return jsonify({
            "status": "success",
            "data": {
                "batch": False,
                "product": product,
                "rop": round(rop, 2),
                "status": status,
                "days_until_stockout": round(days_until_stockout, 1),
                "order_quantity_suggested": round(order_qty, 2),
                "current_stock": current_stock
            }
        }), 200

@inventory_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"module": "inventory", "status": "ok"}), 200

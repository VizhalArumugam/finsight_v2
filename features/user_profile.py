"""
FinSight v2 — features/user_profile.py
=======================================
Blueprint: /api/profile
Module 1 — User Profile & Onboarding

Saves user business data to a SQLite database.
"""

from flask import Blueprint, request, jsonify
from config.database import db

profile_bp = Blueprint("profile", __name__, url_prefix="/api/profile")

class BusinessProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_name = db.Column(db.String(100), nullable=False)
    shop_name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(100))
    business_type = db.Column(db.String(50), nullable=False)
    inventory_type = db.Column(db.String(50))
    lead_time_days = db.Column(db.Integer, default=7)

@profile_bp.route("/save", methods=["POST"])
def save_profile():
    body = request.get_json(force=True)
    if not body.get("owner_name") or not body.get("business_type"):
        return jsonify({"error": "owner_name and business_type are required"}), 400

    profile = BusinessProfile.query.get(1)
    if not profile:
        profile = BusinessProfile(id=1)
        db.session.add(profile)

    profile.owner_name = body.get("owner_name")
    profile.shop_name = body.get("shop_name", "My Store")
    profile.location = body.get("location", "")
    profile.business_type = body.get("business_type")
    profile.inventory_type = body.get("inventory_type", "durable")
    profile.lead_time_days = body.get("lead_time_days", 7)

    db.session.commit()
    return jsonify({"status": "success", "message": "Profile saved"}), 200

@profile_bp.route("/get", methods=["GET"])
def get_profile():
    profile = BusinessProfile.query.get(1)
    if not profile:
        return jsonify({"status": "not_found"}), 404
        
    return jsonify({
        "status": "success",
        "data": {
            "owner_name": profile.owner_name,
            "shop_name": profile.shop_name,
            "location": profile.location,
            "business_type": profile.business_type,
            "inventory_type": profile.inventory_type,
            "lead_time_days": profile.lead_time_days
        }
    }), 200

@profile_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"module": "user_profile", "status": "ok"}), 200

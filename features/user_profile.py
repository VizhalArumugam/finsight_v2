"""
FinSight v2 — features/user_profile.py
========================================
Blueprint: /api/profile
Module 1 — User Profile & Onboarding

Profile is now stored inside the User model.
All routes require a valid JWT token.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from config.database import db

profile_bp = Blueprint("profile", __name__, url_prefix="/api/profile")


def _get_user():
    """Helper: return the User object from JWT or None."""
    try:
        from features.auth import User
        user_id = int(get_jwt_identity())
        return User.query.get(user_id)
    except Exception:
        return None


@profile_bp.route("/save", methods=["POST"])
@jwt_required()
def save_profile():
    user = _get_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    body = request.get_json(force=True)
    user.owner_name     = body.get("owner_name",     user.owner_name)
    user.shop_name      = body.get("shop_name",      user.shop_name)
    user.business_type  = body.get("business_type",  user.business_type)
    user.location       = body.get("location",       user.location)
    user.inventory_type = body.get("inventory_type", user.inventory_type)
    user.lead_time_days = body.get("lead_time_days", user.lead_time_days)
    
    db.session.commit()
    return jsonify({"status": "success", "message": "Profile saved"}), 200


@profile_bp.route("/get", methods=["GET"])
@jwt_required()
def get_profile():
    user = _get_user()
    if not user:
        return jsonify({"status": "not_found"}), 404

    return jsonify({
        "status": "success",
        "data": {
            "owner_name":     user.owner_name,
            "shop_name":      user.shop_name,
            "business_type":  user.business_type,
            "location":       user.location,
            "inventory_type": user.inventory_type,
            "lead_time_days": user.lead_time_days,
        }
    }), 200


@profile_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"module": "user_profile", "status": "ok"}), 200

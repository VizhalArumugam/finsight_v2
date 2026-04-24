"""
FinSight v2 — features/auth.py
================================
Blueprint: /api/auth
Multi-user authentication using JWT tokens.

Endpoints:
    POST /api/auth/register  — create a new account
    POST /api/auth/login     — get a JWT access token
    GET  /api/auth/me        — verify token & return user info
"""

import bcrypt
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from config.database import db

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


class User(db.Model):
    __tablename__ = "users"
    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    owner_name    = db.Column(db.String(100), nullable=False)
    shop_name     = db.Column(db.String(150), nullable=False, default="My Store")
    business_type = db.Column(db.String(50),  nullable=False, default="Grocery")

    def set_password(self, plain_password: str):
        self.password_hash = bcrypt.hashpw(
            plain_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, plain_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            self.password_hash.encode("utf-8"),
        )

    def to_dict(self):
        return {
            "id":            self.id,
            "email":         self.email,
            "owner_name":    self.owner_name,
            "shop_name":     self.shop_name,
            "business_type": self.business_type,
        }


# ── Register ──────────────────────────────────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    body = request.get_json(force=True)
    email         = (body.get("email") or "").strip().lower()
    password      = body.get("password", "")
    owner_name    = (body.get("owner_name") or "").strip()
    shop_name     = (body.get("shop_name") or "My Store").strip()
    business_type = (body.get("business_type") or "Grocery").strip()

    if not email or not password or not owner_name:
        return jsonify({"error": "email, password and owner_name are required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists"}), 409

    user = User(
        email=email,
        owner_name=owner_name,
        shop_name=shop_name,
        business_type=business_type,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"status": "success", "token": token, "user": user.to_dict()}), 201


# ── Login ─────────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    body     = request.get_json(force=True)
    email    = (body.get("email") or "").strip().lower()
    password = body.get("password", "")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"status": "success", "token": token, "user": user.to_dict()}), 200


# ── Me (verify token) ─────────────────────────────────────────────────────────
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user    = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"status": "success", "user": user.to_dict()}), 200

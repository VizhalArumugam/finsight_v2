"""
FinSight v2 — app.py
==================
Main Flask server. Registers all blueprints.

Run:
    cd finsight_v2
    python app.py          ← development
    gunicorn app:app       ← production
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from config.database import db
from features.gst_calculator import gst_bp
from features.price_validator import price_bp
from features.leakage_detector import audit_bp
from features.user_profile import profile_bp
from features.inventory_rop import inventory_bp
from features.abc_classifier import abc_bp
from config.ai_client import ai_status


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///finsight.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    db.init_app(app)
    with app.app_context():
        db.create_all()

    app.register_blueprint(gst_bp)
    app.register_blueprint(price_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(abc_bp)

    @app.route("/", methods=["GET"])
    def root():
        return jsonify({
            "app": "FinSight", "version": "2.0.0", "status": "running",
            "ai_providers": ai_status(),
            "endpoints": {
                "POST /api/gst/calculate":       "NLP GST assessment",
                "GET  /api/gst/hsn-lookup?q=":   "HSN code search",
                "GET  /api/gst/slabs":            "All GST slabs",
                "POST /api/price/validate":       "Single product price check",
                "POST /api/price/validate-batch": "Batch price check (max 20)",
                "GET  /api/price/benchmarks":     "Static price database",
                "POST /api/audit/run":            "Financial leakage detector",
                "POST /api/profile/save":         "Save business profile",
                "GET  /api/profile/get":          "Get business profile",
                "POST /api/inventory/rop":        "Inventory ROP Calculator",
                "POST /api/abc/classify":         "ABC Inventory Classifier",
            }
        }), 200

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Route not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"

    status   = ai_status()
    groq_ok  = "✓ Ready" if status["groq"]["configured"] else "✗ Missing"
    gemini_ok= "✓ Ready" if status["gemini"]["configured"] else "✗ Missing"

    print(f"""
╔══════════════════════════════════════════╗
║         FinSight Backend v2.0            ║
╠══════════════════════════════════════════╣
║  http://localhost:{port:<25}║
║                                          ║
║  AI Router: {status['router']:<27}║
║    Groq   : {groq_ok:<27}║
║    Gemini : {gemini_ok:<27}║
║                                          ║
║  Modules:                                ║
║    ✓ User Profile    /api/profile        ║
║    ✓ GST Calculator  /api/gst            ║
║    ✓ Price Validator /api/price          ║
║    ✓ Audit Leakage   /api/audit          ║
║    ✓ Inventory ROP   /api/inventory      ║
║    ✓ ABC Classifier  /api/abc            ║
╚══════════════════════════════════════════╝
""")

    app.run(host="0.0.0.0", port=port, debug=debug)

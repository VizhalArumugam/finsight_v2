"""
FinSight — features/gst_calculator.py
=======================================
Blueprint: /api/gst
Module 5A — GST Tax Advisor

Uses free AI (Groq → Gemini fallback) for NLP business parsing.
All GST rate data is from hardcoded CBIC knowledge — no paid API.
"""

from flask import Blueprint, request, jsonify
from config.ai_client import ask_ai_json
import json

gst_bp = Blueprint("gst", __name__, url_prefix="/api/gst")


# ─────────────────────────────────────────────────────────────
# GST KNOWLEDGE BASE  (CBIC notifications, 2024-25)
# ─────────────────────────────────────────────────────────────

HSN_DB = {
    # Dairy
    "fresh_milk":          {"hsn": "0401", "rate": 0,  "desc": "Fresh / pasteurised milk"},
    "curd_lassi":          {"hsn": "0403", "rate": 0,  "desc": "Curd, lassi, buttermilk"},
    "butter_ghee":         {"hsn": "0405", "rate": 12, "desc": "Butter and ghee"},
    "cheese_paneer":       {"hsn": "0406", "rate": 12, "desc": "Cheese and paneer"},
    "ice_cream":           {"hsn": "2105", "rate": 18, "desc": "Ice cream"},
    # Grocery
    "rice_wheat":          {"hsn": "1006", "rate": 0,  "desc": "Rice / wheat flour (unbranded)"},
    "edible_oil":          {"hsn": "1511", "rate": 5,  "desc": "Edible oil"},
    "sugar":               {"hsn": "1701", "rate": 5,  "desc": "Sugar"},
    "tea_coffee":          {"hsn": "0902", "rate": 5,  "desc": "Tea and coffee"},
    "packaged_food":       {"hsn": "2106", "rate": 12, "desc": "Packaged / branded food"},
    "biscuits":            {"hsn": "1905", "rate": 18, "desc": "Biscuits and wafers"},
    "aerated_drinks":      {"hsn": "2202", "rate": 28, "desc": "Aerated drinks"},
    # Hardware
    "iron_steel_hardware": {"hsn": "7318", "rate": 18, "desc": "Iron/steel screws, bolts, nuts"},
    "hand_tools":          {"hsn": "8205", "rate": 18, "desc": "Hand tools"},
    "paints":              {"hsn": "3210", "rate": 18, "desc": "Paints and varnishes"},
    "cement":              {"hsn": "2523", "rate": 28, "desc": "Cement"},
    "electrical_wires":    {"hsn": "8544", "rate": 18, "desc": "Electrical wires"},
    # Electronics
    "mobile_phones":       {"hsn": "8517", "rate": 12, "desc": "Mobile phones"},
    "laptops":             {"hsn": "8471", "rate": 18, "desc": "Laptops / computers"},
    "televisions":         {"hsn": "8528", "rate": 18, "desc": "Televisions"},
    "appliances":          {"hsn": "8418", "rate": 18, "desc": "Home appliances"},
    # Clothing
    "clothing_u1000":      {"hsn": "6109", "rate": 5,  "desc": "Garments ≤ ₹1000/piece"},
    "clothing_a1000":      {"hsn": "6109", "rate": 12, "desc": "Garments > ₹1000/piece"},
    # Pharmacy
    "branded_medicine":    {"hsn": "3004", "rate": 12, "desc": "Branded medicines"},
    "generic_medicine":    {"hsn": "3003", "rate": 0,  "desc": "Generic / unbranded medicines"},
    "medical_devices":     {"hsn": "9018", "rate": 12, "desc": "Medical devices"},
    # Restaurant
    "restaurant_dine":     {"hsn": "9963", "rate": 5,  "desc": "Restaurant dine-in (no liquor)"},
    "outdoor_catering":    {"hsn": "9963", "rate": 18, "desc": "Outdoor catering"},
    # Services
    "it_consulting":       {"hsn": "9983", "rate": 18, "desc": "IT / consulting services"},
    "repair_services":     {"hsn": "9987", "rate": 18, "desc": "Repair and maintenance"},
    "transport_goods":     {"hsn": "9965", "rate": 5,  "desc": "Goods transport (GTA)"},
    "education":           {"hsn": "9992", "rate": 0,  "desc": "Education services"},
    "healthcare":          {"hsn": "9993", "rate": 0,  "desc": "Healthcare services"},
}

THRESHOLDS = {
    "goods":    4000000,   # ₹40L
    "services": 2000000,   # ₹20L
    "special":  1000000,   # ₹10L NE states
}

NE_STATES = [
    "manipur", "mizoram", "nagaland", "tripura", "meghalaya",
    "sikkim", "arunachal pradesh", "himachal pradesh", "uttarakhand",
    "puducherry", "jammu and kashmir", "ladakh"
]

COMPOSITION = {
    "goods":      {"limit": 15000000, "rate": 1},
    "restaurant": {"limit": 15000000, "rate": 5},
    "services":   {"limit": 5000000,  "rate": 6},
}

FILING = {
    "monthly":     {"returns": "GSTR-1 + GSTR-3B", "due": "11th and 20th of next month"},
    "quarterly":   {"returns": "GSTR-1 (IFF) + GSTR-3B", "due": "13th and 22nd after quarter end"},
    "composition": {"returns": "CMP-08 quarterly + GSTR-4 annual", "due": "18th after quarter, 30 April annual"},
}

WHY_MAP = {
    "0401": "Fresh milk is nil-rated — Schedule I, Notification 2/2017-CT(Rate), essential food.",
    "0403": "Curd/lassi nil-rated — Schedule I, Notification 2/2017-CT(Rate).",
    "0405": "Butter and ghee at 12% — Schedule III, Notification 1/2017-CT(Rate), processed dairy.",
    "0406": "Cheese at 12% — Schedule III, Notification 1/2017-CT(Rate).",
    "7318": "Iron/steel hardware at 18% — Chapter 73, GST Tariff Schedule IV.",
    "8205": "Hand tools at 18% — Chapter 82, GST Tariff.",
    "3210": "Paints at 18% — Chapter 32, GST Tariff.",
    "2523": "Cement at 28% — Schedule V, Notification 1/2017-CT(Rate).",
    "8517": "Mobile phones at 12% — reduced from 18% via Notification 01/2020-CT(Rate).",
    "8471": "Laptops at 18% — Chapter 84, GST Tariff.",
    "6109": "Garments: ≤₹1000 → 5%, >₹1000 → 12% — Notification 1/2017-CT(Rate), Schedule I & II.",
    "3004": "Branded medicines at 12% — Chapter 30, Notification 1/2017-CT(Rate).",
    "3003": "Unbranded medicines nil-rated — Schedule I, Notification 2/2017-CT(Rate).",
    "9963": "Restaurant at 5% (no ITC) — Notification 11/2017-CT(Rate), amended by 46/2017.",
    "9983": "IT/consulting services at 18% — SAC 9983, Schedule III.",
    "1511": "Edible oil at 5% — Schedule I, Notification 1/2017-CT(Rate).",
    "1701": "Sugar at 5% — Schedule I, Notification 1/2017-CT(Rate).",
    "1006": "Rice nil-rated (unbranded) — Schedule I, Notification 2/2017-CT(Rate).",
    "9018": "Medical devices at 12% — Chapter 90, Notification 1/2017-CT(Rate).",
}


# ─────────────────────────────────────────────────────────────
# STEP 1 — NLP PARSING via free AI
# ─────────────────────────────────────────────────────────────

def parse_business(description: str) -> dict:
    system = (
        "You are a GST data extractor for Indian businesses. "
        "Return ONLY valid JSON, no explanation, no markdown."
    )
    prompt = f"""Extract business info from this description and return JSON:

Description: "{description}"

Return exactly this JSON structure:
{{
  "business_type": "dairy|grocery|hardware|electronics|clothing|pharmacy|restaurant|services|other",
  "goods_services": ["item1", "item2"],
  "sale_mode": "local|interstate|online|wholesale|mixed",
  "turnover_monthly": <number or null>,
  "state": "<state name lowercase or null>",
  "is_manufacturer": <true or false>,
  "has_ac": <true or false>,
  "serves_liquor": <true or false>,
  "medicine_type": "branded|unbranded|both|null",
  "clothing_price_range": "under_1000|above_1000|mixed|null",
  "is_export": <true or false>
}}

Rules:
- Convert turnover like "2 lakh" → 200000, "50k" → 50000, "3L" → 300000
- If not mentioned, use null or false
- sale_mode: local = sells only in same city/state, interstate = across states, online = ecommerce"""

    return ask_ai_json(prompt, system)


# ─────────────────────────────────────────────────────────────
# STEP 2 — MAP to HSN items
# ─────────────────────────────────────────────────────────────

def get_hsn_items(parsed: dict) -> list:
    btype  = parsed.get("business_type", "")
    goods  = " ".join(parsed.get("goods_services", [])).lower()
    items  = []

    def add(key, label=None):
        if key in HSN_DB:
            e = HSN_DB[key].copy()
            e["label"] = label or e["desc"]
            items.append(e)

    if btype == "dairy":
        add("fresh_milk")
        if any(w in goods for w in ["ghee", "butter"]): add("butter_ghee")
        if any(w in goods for w in ["cheese", "paneer"]): add("cheese_paneer")
        if any(w in goods for w in ["curd", "lassi", "yogurt"]): add("curd_lassi")

    elif btype == "grocery":
        add("rice_wheat"); add("edible_oil"); add("sugar"); add("tea_coffee")
        if any(w in goods for w in ["packaged", "biscuit", "branded", "snack"]):
            add("packaged_food")

    elif btype == "hardware":
        add("iron_steel_hardware"); add("hand_tools"); add("paints")
        if "cement" in goods: add("cement")
        if any(w in goods for w in ["wire", "electrical", "switch"]): add("electrical_wires")

    elif btype == "electronics":
        if any(w in goods for w in ["mobile", "phone"]): add("mobile_phones")
        add("laptops"); add("televisions"); add("appliances")

    elif btype == "clothing":
        pr = parsed.get("clothing_price_range", "mixed")
        if pr == "under_1000":   add("clothing_u1000")
        elif pr == "above_1000": add("clothing_a1000")
        else:                    add("clothing_u1000"); add("clothing_a1000")

    elif btype == "pharmacy":
        mt = parsed.get("medicine_type", "both")
        if mt in ("branded", "both"):   add("branded_medicine")
        if mt in ("unbranded", "both"): add("generic_medicine")
        add("medical_devices")

    elif btype == "restaurant":
        if parsed.get("serves_liquor"):
            items.append({"hsn": "9963", "rate": 18, "label": "Restaurant with liquor", "desc": "18% GST"})
        else:
            add("restaurant_dine")
        if any(w in goods for w in ["catering", "outdoor", "event"]): add("outdoor_catering")

    elif btype == "services":
        add("it_consulting")
        if any(w in goods for w in ["repair", "maintenance"]): add("repair_services")
        if any(w in goods for w in ["transport", "freight", "logistics"]): add("transport_goods")
        if any(w in goods for w in ["education", "school", "tuition"]): add("education")
        if any(w in goods for w in ["hospital", "clinic", "doctor"]): add("healthcare")

    else:
        items.append({"hsn": "9983", "rate": 18, "label": "General services", "desc": "Default 18% GST"})

    # Deduplicate by hsn+rate
    seen, unique = set(), []
    for it in items:
        k = it["hsn"] + str(it["rate"])
        if k not in seen:
            seen.add(k); unique.append(it)

    return unique


# ─────────────────────────────────────────────────────────────
# STEP 3 — COMPUTE LIABILITY
# ─────────────────────────────────────────────────────────────

def compute_liability(parsed: dict, hsn_items: list) -> dict:
    btype       = parsed.get("business_type", "other")
    sale_mode   = parsed.get("sale_mode", "local")
    state       = (parsed.get("state") or "").lower()
    is_export   = parsed.get("is_export", False)
    turnover_m  = parsed.get("turnover_monthly")
    is_service  = btype in ("services",)
    is_special  = state in NE_STATES
    is_interstate = sale_mode in ("interstate", "online", "mixed") or is_export

    threshold  = THRESHOLDS["special"] if is_special else THRESHOLDS["services"] if is_service else THRESHOLDS["goods"]
    turnover_a = turnover_m * 12 if turnover_m else None
    primary    = hsn_items[0]["rate"] if hsn_items else 18

    # Registration
    if is_interstate:
        reg_req, reg_status, reg_reason = True, "interstate_mandatory", \
            "Interstate/online supply → mandatory registration under Section 24(i) CGST Act 2017."
    elif turnover_a and turnover_a > threshold:
        reg_req, reg_status, reg_reason = True, "exceeded", \
            f"Annual turnover ₹{turnover_a:,.0f} exceeds ₹{threshold:,.0f} threshold. Section 22 CGST Act."
    elif turnover_a and turnover_a > threshold * 0.75:
        reg_req, reg_status, reg_reason = False, "approaching", \
            f"Approaching ₹{threshold//100000}L threshold. Register proactively."
    else:
        reg_req, reg_status, reg_reason = False, "optional", \
            f"Below ₹{threshold//100000}L threshold. Voluntary registration allows Input Tax Credit."

    # Composition
    comp_type  = "restaurant" if btype == "restaurant" else "services" if is_service else "goods"
    comp_info  = COMPOSITION[comp_type]
    comp_elig  = (
        turnover_a is not None and
        turnover_a <= comp_info["limit"] and
        not is_interstate and
        btype != "services"
    )

    # GST items with CGST/SGST/IGST
    gst_items = []
    for item in hsn_items:
        r = item["rate"]
        if r == 0:
            cgst = sgst = igst = 0
        elif is_interstate:
            cgst = sgst = 0; igst = r
        else:
            cgst = sgst = r / 2; igst = 0
        gst_items.append({
            "name":     item.get("label", item["desc"]),
            "hsn_sac":  item["hsn"],
            "gst_rate": r,
            "cgst":     cgst,
            "sgst":     sgst,
            "igst":     igst,
            "why":      WHY_MAP.get(item["hsn"], f"{item['desc']} at {r}% under applicable GST schedule."),
        })

    # Monetary liability
    liability = None
    if turnover_m:
        taxable  = round(turnover_m / (1 + primary / 100), 2)
        gst_amt  = round(turnover_m - taxable, 2)
        cgst_m   = sgst_m = round(gst_amt / 2, 2) if not is_interstate else 0
        igst_m   = gst_amt if is_interstate else 0
        liability = {
            "turnover_monthly":  round(turnover_m, 2),
            "taxable_value":     taxable,
            "cgst_monthly":      cgst_m,
            "sgst_monthly":      sgst_m,
            "igst_monthly":      igst_m,
            "total_gst_monthly": gst_amt,
            "total_gst_annual":  round(gst_amt * 12, 2),
        }

    # Filing
    if comp_elig:
        filing = FILING["composition"]
    elif turnover_a and turnover_a <= 50000000:
        filing = FILING["quarterly"]
    else:
        filing = FILING["monthly"]

    return {
        "gst_items":          gst_items,
        "primary_rate":       primary,
        "is_interstate":      is_interstate,
        "registration": {
            "required": reg_req,
            "status":   reg_status,
            "reason":   reg_reason,
            "threshold": threshold,
        },
        "composition": {
            "eligible": comp_elig,
            "rate":     comp_info["rate"] if comp_elig else None,
        },
        "liability": liability,
        "filing":    filing,
    }


# ─────────────────────────────────────────────────────────────
# STEP 4 — AI ADVICE (free AI)
# ─────────────────────────────────────────────────────────────

def get_ai_advice(parsed: dict, result: dict) -> list:
    btype    = parsed.get("business_type", "")
    turnover = parsed.get("turnover_monthly")
    rate     = result["primary_rate"]
    reg      = result["registration"]

    prompt = f"""You are a GST advisor for Indian small businesses. Give 3 short, practical tips.

Business: {btype}
GST Rate: {rate}%
Monthly Turnover: ₹{turnover if turnover else 'unknown'}
Registration: {'Required' if reg['required'] else 'Optional'} ({reg['status']})
Sale Mode: {parsed.get('sale_mode', 'local')}

Return ONLY a JSON array of 3 strings, each a practical tip. No markdown, no explanation.
Example: ["tip 1", "tip 2", "tip 3"]"""

    try:
        raw = ask_ai_json(prompt)
        if isinstance(raw, list):
            return raw[:3]
        if isinstance(raw, dict) and "tips" in raw:
            return raw["tips"][:3]
    except Exception:
        pass

    # Fallback static advice
    advice = []
    if result["composition"]["eligible"]:
        advice.append(f"You are eligible for Composition Scheme at {result['composition']['rate']}% flat rate — much simpler quarterly filing.")
    if reg["required"]:
        advice.append("Register on gstin.gov.in immediately. Late registration attracts 18% interest + penalty on unpaid tax.")
    if result["liability"] and result["liability"]["total_gst_monthly"] > 0:
        m = result["liability"]["total_gst_monthly"]
        advice.append(f"Set aside ₹{m:,.0f}/month in a separate account for GST — don't mix it with working capital.")
    return advice[:3]


# ─────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────

@gst_bp.route("/calculate", methods=["POST"])
def calculate_gst():
    """
    POST /api/gst/calculate
    Body: { "description": "I run a hardware store in Chennai, ₹3L/month turnover" }
    Returns: Full GST assessment.
    """
    body        = request.get_json(force=True)
    description = (body.get("description") or "").strip()

    if not description:
        return jsonify({"error": "description is required"}), 400

    try:
        parsed    = parse_business(description)
        hsn_items = get_hsn_items(parsed)
        result    = compute_liability(parsed, hsn_items)
        advice    = get_ai_advice(parsed, result)

        return jsonify({
            "status":       "success",
            "understood":   parsed,
            "gst_items":    result["gst_items"],
            "liability":    result["liability"],
            "registration": result["registration"],
            "composition":  result["composition"],
            "filing":       result["filing"],
            "primary_rate": result["primary_rate"],
            "is_interstate":result["is_interstate"],
            "advice":       advice,
        }), 200

    except RuntimeError as e:
        return jsonify({"error": str(e), "hint": "Get free API key at console.groq.com"}), 503
    except json.JSONDecodeError as e:
        return jsonify({"error": "AI response parse failed", "detail": str(e)}), 422
    except Exception as e:
        return jsonify({"error": "Server error", "detail": str(e)}), 500


@gst_bp.route("/hsn-lookup", methods=["GET"])
def hsn_lookup():
    """GET /api/gst/hsn-lookup?q=milk"""
    q = request.args.get("q", "").lower()
    results = [{"key": k, **v} for k, v in HSN_DB.items()
               if not q or q in k or q in v["desc"].lower()]
    return jsonify({"count": len(results), "results": results}), 200


@gst_bp.route("/slabs", methods=["GET"])
def get_slabs():
    """GET /api/gst/slabs"""
    return jsonify({
        "slabs": [0, 5, 12, 18, 28],
        "thresholds": THRESHOLDS,
        "ne_states": NE_STATES,
        "composition_limits": COMPOSITION,
        "filing": FILING,
    }), 200


@gst_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"module": "gst_calculator", "status": "ok", "ai": "groq+gemini (free)"}), 200

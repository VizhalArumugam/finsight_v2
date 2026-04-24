"""
FinSight — features/price_validator.py
========================================
Blueprint: /api/price  |  Module 4 — Market Price Validator

Data sources (all FREE, live, no dummy data):
  1. DuckDuckGo Lite — live search scraping
  2. Groq / Gemini AI — dynamic AI estimate based on context
  Live store links are provided directly for user verification.
"""

from flask import Blueprint, request, jsonify
from config.ai_client import ask_ai_json
import json, re, time, requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

price_bp = Blueprint("price", __name__, url_prefix="/api/price")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
}

# ─── Price extraction helpers ────────────────────────────────
def _prices_from_text(text: str) -> list:
    text = text.replace(",", "")
    prices = []
    for pat in [r"₹\s*(\d+(?:\.\d+)?)", r"Rs\.?\s*(\d+(?:\.\d+)?)"]:
        for m in re.finditer(pat, text, re.I):
            try:
                v = float(m.group(1))
                if 1 < v < 100000: prices.append(v)
            except ValueError: pass
    return prices

def _summarize(prices: list, source: str, additional_data: dict = None):
    prices = sorted(set(p for p in prices if 1 < p < 100000))
    if not prices: return additional_data or {}
    
    # Basic outlier trimming (drop top & bottom 15% if enough points)
    if len(prices) >= 4:
        idx_low = int(len(prices) * 0.15)
        idx_high = int(len(prices) * 0.85)
        filtered = prices[idx_low:idx_high] if idx_high > idx_low else prices
    else:
        filtered = prices

    res = {"low": round(filtered[0], 2), "avg": round(sum(filtered)/len(filtered), 2),
           "high": round(filtered[-1], 2), "source": source, "count": len(filtered),
           "raw_prices": prices[:20]}
    if additional_data: res.update(additional_data)
    return res

# ─── Live Data: DuckDuckGo Lite Search ────────────────────────
def search_ddg_lite(q: str):
    search_query = f"{q} price in india jiomart bigbasket"
    try:
        url = "https://lite.duckduckgo.com/lite/"
        headers = {
            "User-Agent": HEADERS["User-Agent"],
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"q": search_query, "kl": "in-en"}
        r = requests.post(url, headers=headers, data=data, timeout=8)
        if r.status_code != 200: return {}
        soup = BeautifulSoup(r.text, "html.parser")
        prices = []
        for tr in soup.find_all("tr"):
            td = tr.find("td", class_="result-snippet")
            if td:
                prices.extend(_prices_from_text(td.get_text()))
        if len(prices) >= 2:
            return _summarize(prices, "Live Web Search (DuckDuckGo)")
        return {}
    except Exception: return {}

# ─── Orchestrator ────────────────────────────────────────────
def get_market_price(product: str, category: str):
    from urllib.parse import quote
    # Construct real, live links for direct verification
    live_links = [
        {"store": "JioMart", "url": f"https://www.jiomart.com/search?q={quote(product)}"},
        {"store": "BigBasket", "url": f"https://www.bigbasket.com/ps/?q={quote_plus(product)}"},
        {"store": "Amazon IN", "url": f"https://www.amazon.in/s?k={quote_plus(product)}"}
    ]
    
    r = search_ddg_lite(product)

    # Always return what we have (even if empty, the AI handles fallback) + live URLs
    r["live_links"] = live_links
    if r.get("count", 0) >= 2:
        r["data_source"] = "Live Web Search"
    else:
        r["data_source"] = "AI Market Estimate"
    return r


# ─── AI market data (prices + qualitative only) ──────────────
def ai_verdict(product: str, category: str, your_price: float, market: dict):
    """
    Ask AI for MARKET PRICE DATA and qualitative analysis ONLY.
    Do NOT ask AI to calculate verdict/diff — we do that in Python
    to avoid arithmetic hallucinations.
    """
    mctx = ""
    if market.get("avg"):
        mctx = f"Scraped Data — Raw Extracted Prices: {market.get('raw_prices', [])}\nNaive Scraped Avg: ₹{market.get('avg')}"

    prompt = f"""You are an Indian retail market price expert (2024-25).
Product: {product} | Category: {category}
{mctx}

Carefully evaluate the Scraped Data. Web scraping often pulls wild outliers (e.g., bulk 5kg packs, unrelated items).
CRITICAL REALITY CHECK: If the scraped prices contradict basic Indian retail common sense, COMPLETELY IGNORE the scraped data.
Your job is ONLY to determine the TRUE market price for exactly ONE unit (or 1kg/1L) of this product in India right now.

DO NOT calculate verdicts or percentage differences — just provide the market price and analysis.

CRITICAL INSTRUCTION: Return ONLY valid JSON, no markdown, no extra text.
{{"market_low":0.0,"market_avg":0.0,"market_high":0.0,"market_unit":"per unit",
"suggestion":"one actionable strategic tip for a small shop owner",
"competitive_context":"market retail reality in India for this item in 1-2 sentences",
"selling_less_where":"list specific Indian grocery retailers that may sell this cheaper",
"data_confidence":"high|medium|low"}}"""
    result = ask_ai_json(prompt)
    if isinstance(result, list) and len(result) > 0:
        result = result[0]
    elif not isinstance(result, dict):
        result = {}
    return result

# ─── Full pipeline ───────────────────────────────────────────
def validate_single(product: str, category: str, your_price: float) -> dict:
    market   = get_market_price(product, category)
    analysis = ai_verdict(product, category, your_price, market)

    market_avg = analysis.get("market_avg") or 0.0
    market_low = analysis.get("market_low") or 0.0
    market_high = analysis.get("market_high") or 0.0

    # ── Python-calculated math (never trust AI for arithmetic) ──
    FAIR_THRESHOLD_PCT = 8.0  # ±8% is "fair"

    if market_avg and market_avg > 0:
        diff_absolute = round(your_price - market_avg, 2)          # positive = owner charges MORE
        diff_percent  = round((diff_absolute / market_avg) * 100, 2)

        if diff_percent > FAIR_THRESHOLD_PCT:
            verdict = "overpriced"
        elif diff_percent < -FAIR_THRESHOLD_PCT:
            verdict = "underpriced"
        else:
            verdict = "fair"

        # Build a factually accurate price position sentence in Python
        direction = "higher" if diff_absolute >= 0 else "lower"
        abs_diff  = abs(diff_absolute)
        price_position = (
            f"Your price of ₹{your_price} is ₹{abs_diff} {direction} than the "
            f"market average of ₹{market_avg} ({abs(diff_percent):.1f}% {direction})."
        )
    else:
        diff_absolute  = None
        diff_percent   = None
        verdict        = "unknown"
        price_position = f"Market average could not be determined for {product}."

    return {
        "product": product, "category": category, "your_price": your_price,
        "market": {
            "low":    market_low,
            "avg":    market_avg,
            "high":   market_high,
            "unit":   analysis.get("market_unit", "per unit"),
            "source": market.get("data_source", "AI Estimate"),
        },
        "live_links":          market.get("live_links", []),
        "diff_percent":        diff_percent,
        "diff_absolute":       diff_absolute,
        "verdict":             verdict,
        "price_position":      price_position,
        "suggestion":          analysis.get("suggestion"),
        "competitive_context": analysis.get("competitive_context"),
        "selling_less_where":  analysis.get("selling_less_where", "No competitor data available"),
        "data_confidence":     analysis.get("data_confidence"),
    }

# ─── Routes ──────────────────────────────────────────────────
@price_bp.route("/validate", methods=["POST"])
def validate_price():
    body     = request.get_json(force=True)
    product  = (body.get("product") or "").strip()
    category = (body.get("category") or "General").strip()
    price    = body.get("your_price")

    if not product: return jsonify({"error": "product is required"}), 400
    if price is None: return jsonify({"error": "your_price is required"}), 400
    try: price = float(price)
    except: return jsonify({"error": "your_price must be a number"}), 400
    if price <= 0: return jsonify({"error": "your_price must be > 0"}), 400

    try:
        data = validate_single(product, category, price)
        return jsonify({"status": "success", "data": data}), 200
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": "Server error", "detail": str(e)}), 500

@price_bp.route("/validate-batch", methods=["POST"])
def validate_batch():
    products = (request.get_json(force=True) or {}).get("products", [])
    if not products: return jsonify({"error": "products array required"}), 400
    if len(products) > 20: return jsonify({"error": "max 20 products"}), 400

    results = []; errors = []; over = under = fair = 0
    for i, item in enumerate(products):
        p = (item.get("product") or "").strip()
        c = (item.get("category") or "General").strip()
        pr = item.get("your_price")
        if not p or pr is None:
            errors.append({"index": i, "error": "product and your_price required"}); continue
        try:
            r = validate_single(p, c, float(pr)); results.append(r)
            v = r.get("verdict","")
            if v=="overpriced": over+=1
            elif v=="underpriced": under+=1
            elif v=="fair": fair+=1
            time.sleep(1.0)
        except Exception as e:
            errors.append({"index": i, "product": p, "error": str(e)})

    return jsonify({"status":"success",
        "summary":{"total":len(products),"processed":len(results),
                   "fair":fair,"overpriced":over,"underpriced":under,"errors":len(errors)},
        "results":results,"errors":errors}), 200

@price_bp.route("/benchmarks", methods=["GET"])
def get_benchmarks():
    # Deprecated: No more static dummy benchmarks. Return empty logic or a warning.
    return jsonify({"count": 0, "benchmarks": {}, "message": "Static benchmarks deprecated. Using live API."}), 200

@price_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"module":"price_validator","status":"ok","paid_apis":"none","mode":"live"}), 200

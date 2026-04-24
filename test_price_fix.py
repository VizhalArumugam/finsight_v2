import requests, json

cases = [
    {"product": "Sugar 1kg",  "category": "Grocery",  "your_price": 55,  "expected": "overpriced"},
    {"product": "Tomato 1kg", "category": "Grocery",  "your_price": 20,  "expected": "underpriced"},
    {"product": "Basmati Rice 1kg", "category": "Grocery", "your_price": 80, "expected": "fair"},
]

print("=" * 60)
print("PRICE VALIDATOR FIX — VERIFICATION")
print("=" * 60)

for c in cases:
    r = requests.post(
        "http://localhost:5000/api/price/validate",
        json={"product": c["product"], "category": c["category"], "your_price": c["your_price"]},
        timeout=30
    )
    d = r.json().get("data", {})
    verdict    = d.get("verdict", "ERROR")
    diff_pct   = d.get("diff_percent")
    diff_abs   = d.get("diff_absolute")
    mkt_avg    = d.get("market", {}).get("avg")
    position   = d.get("price_position", "")
    ok         = "[PASS]" if diff_abs is not None and (
                    (c["your_price"] > mkt_avg and diff_abs > 0) or
                    (c["your_price"] < mkt_avg and diff_abs < 0) or
                    c["your_price"] == mkt_avg
                  ) else "[FAIL]"

    print(f"\nProduct  : {c['product']}")
    print(f"Your Price: Rs.{c['your_price']}  |  Market Avg: Rs.{mkt_avg}")
    print(f"Diff Abs  : Rs.{diff_abs}  |  Diff %: {diff_pct}%")
    print(f"Verdict   : {verdict}")
    print(f"Position  : {position}")
    print(f"Math Check: {ok}  (owner > market should be positive diff)")

print("\n" + "=" * 60)

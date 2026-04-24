import requests

print("Testing ABC...")
try:
    res = requests.post("http://localhost:5000/api/abc/classify", json={
        "products": [
            {"name": "Milk", "monthly_sales_qty": 100, "unit_price": 50},
            {"name": "Curd", "monthly_sales_qty": 50, "unit_price": 40}
        ]
    })
    print("ABC:", res.status_code, res.json())
except Exception as e:
    print("ABC FAILED:", e)

print("Testing ROP...")
try:
    res = requests.post("http://localhost:5000/api/inventory/rop", json={
        "products": [
            {"product": "Milk", "avg_daily_sales": 10, "lead_time_days": 2, "safety_stock": 5, "current_stock": 20}
        ]
    })
    print("ROP:", res.status_code, res.json())
except Exception as e:
    print("ROP FAILED:", e)

print("Testing Profile Get...")
try:
    res = requests.get("http://localhost:5000/api/profile/get")
    print("Profile:", res.status_code, res.json())
except Exception as e:
    print("Profile FAILED:", e)

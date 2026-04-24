import requests
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

def test_bb_api(q):
    try:
        url = f"https://www.bigbasket.com/custompage/getsearchdata/?nc=1&q={q}"
        print(f"Fetching {url}")
        r = requests.get(url, headers=HEADERS, timeout=10)
        print("Status:", r.status_code)
        if r.status_code == 200:
            data = r.json()
            items = data.get("json_data", {}).get("tab_info", [{}])[0].get("product_info", {}).get("products", [])
            print(f"Found {len(items)} items")
            for item in items[:2]:
                print(item.get("p_desc"), item.get("sp"), item.get("mrp"))
    except Exception as e:
        print("BB Error:", e)

def test_jiomart_search(q):
    try:
        url = f"https://www.jiomart.com/api/v2/catalog/search/v1?q={q}"
        print(f"Fetching {url}")
        r = requests.get(url, headers={"User-Agent": HEADERS["User-Agent"], "Accept": "application/json, text/plain, */*"}, timeout=10)
        print("Status:", r.status_code)
        # If it's HTML or 403, we know it's blocked.
        print(r.text[:200])
    except Exception as e:
        print("Jio Error:", e)

test_bb_api("milk")
test_jiomart_search("milk")

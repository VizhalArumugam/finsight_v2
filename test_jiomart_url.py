import requests
from urllib.parse import quote, quote_plus

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"}

def check(url):
    try:
        r = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=5)
        print(f"[{r.status_code}] {url}")
        if "Something went wrong" in r.text or "page you are looking for" in r.text:
            print("  -> Page Not Found text detected.")
    except Exception as e:
        print(f"[ERR] {url}: {e}")

product = "Tomato 1kg"
check(f"https://www.jiomart.com/search/{quote_plus(product)}")
check(f"https://www.jiomart.com/search/{quote(product)}")
check(f"https://www.jiomart.com/catalogsearch/result?q={quote_plus(product)}")

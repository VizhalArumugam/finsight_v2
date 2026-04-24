import requests
from bs4 import BeautifulSoup

def test_ddg_lite(q):
    try:
        url = "https://lite.duckduckgo.com/lite/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"q": q + " price in india jiomart bigbasket", "kl": "in-en"}
        r = requests.post(url, headers=headers, data=data, timeout=10)
        print("Status:", r.status_code)
        soup = BeautifulSoup(r.text, "html.parser")
        for tr in soup.find_all("tr"):
            td = tr.find("td", class_="result-snippet")
            if td:
                print(td.get_text().strip()[:100])
    except Exception as e:
        print("Error:", e)

test_ddg_lite("toned milk 500ml")
test_ddg_lite("atta 5kg")

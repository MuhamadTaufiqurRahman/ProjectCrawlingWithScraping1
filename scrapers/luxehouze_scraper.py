import requests
import json
import re
import time

class LuxehouzeScraper:
    BASE_LIST_URL = "https://luxehouze.com/api/v1/collections/all-watches"
    BASE_DETAIL_URL = "https://luxehouze.com/api/v1/products/{}"

    def __init__(self):
        self.session = requests.Session()
        self.products = []

        # Header standar browser
        self.session.headers.update({
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json;charset=UTF-8",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
            "referer": "https://luxehouze.com/id/en/watch/category/all-watches",
        })

    def fetch_listing(self, page=1):
        payload = {
            "store": "id",
            "lang": "en",
            "page": page,
            "pageSize": 18,
            "filter": [],
            "sort": []
        }
        resp = self.session.post(self.BASE_LIST_URL, json=payload)
        if resp.status_code != 200:
            print(f"Page {page} error:", resp.status_code)
            return []
        data = resp.json()
        slugs = [p["handle"] for p in data.get("contents", {}).get("list", [])]
        print(f"Page {page} - Found {len(slugs)} products")
        return slugs
    

    # Exktact Title for Refference Number
    def extract_reference(self, title):
        if not title:
            return None

        patterns = [
            r"\b\d{3}\.\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{3}\b",     # Omega
            r"\b[A-Z0-9]{5,7}-[A-Z0-9]{3,4}\b",                 # Rolex
            r"\bRM\d{2,3}-\d{2}\b",                              # Richard Mille
            r"\b\d{4}[A-Z]?/?\d?[A-Z]?-\d{3}\b",                 # Patek
            r"\b\d{5}[A-Z]{2}\.[A-Z]{2}\.\d{4}[A-Z]{2}\.\d{2}\b",# AP
            r"\b\d{4}/\d[A-Z]-\d{3}\b",                          # Slash format
            r"\b[A-Z0-9]{4,8}[-\.][A-Z0-9]{3,6}\b",              # General
            r"\b\d{5,8}\b"                                       # Numbers only
        ]

        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                return match.group(0)

        return None
    

    def fetch_product_detail(self, handle):
        url = self.BASE_DETAIL_URL.format(handle)
        resp = self.session.get(url, params={"store":"id","lang":"en"})
        if resp.status_code != 200:
            print(f"Error detail: {handle} | Status: {resp.status_code}")
            print(resp.text[:200])
            return None
        data = resp.json().get("data", {}).get("contents", {})

        sale_price = data.get("salePrice")
        normal_price = data.get("normalPrice")

        title = data.get("title")
        number_reference = self.extract_reference(title)
        if sale_price is not None and sale_price > 0:
            final_price = sale_price
        else:
            final_price = normal_price

        # Struktur mirip JSON Selenium lama
        product = {
            "url_Product": "https://luxehouze.com" + data.get("url", ""),
            "title": data.get("title"),
            "number_reference": number_reference,
            "price_IDR": final_price,
            "price_USD": None,
            "description": data.get("description"),
            "sku": data.get("sku"),
            "brand": next((s["value"] for s in data.get("specifications", []) if s["key"]=="brand"), None),
            "year": next((s["value"] for s in data.get("specifications", []) if s["key"]=="year"), None),
            "condition": data.get("condition"),
            "gender": next((s["value"] for s in data.get("specifications", []) if s["key"]=="gender"), None),
            "movement": next((s["value"] for s in data.get("specifications", []) if s["key"]=="movement"), None),
            "case_material": next((s["value"] for s in data.get("specifications", []) if s["key"]=="case_material"), None),
            "case_size": next((s["value"] for s in data.get("specifications", []) if s["key"]=="case_size"), None),
            "bezel_material": next((s["value"] for s in data.get("specifications", []) if s["key"]=="bezel_material"), None),
            "dial": next((s["value"] for s in data.get("specifications", []) if s["key"]=="dial"), None),
            "water_resistance": next((s["value"] for s in data.get("specifications", []) if s["key"]=="water_resistance"), None),
            "dial_numeral": next((s["value"] for s in data.get("specifications", []) if s["key"]=="dial_numeral"), None),
            "bracelet_material": next((s["value"] for s in data.get("specifications", []) if s["key"]=="bracelet_material"), None),
            "bracelet_color": next((s["value"] for s in data.get("specifications", []) if s["key"]=="bracelet_color"), None),
            "clasp": next((s["value"] for s in data.get("specifications", []) if s["key"]=="clasp"), None),
            "completeness": next((s["value"] for s in data.get("specifications", []) if s["key"]=="completeness"), None),
            "limitedEdition": data.get("limitedEdition"),
            "totalInventory": data.get("totalInventory"),
            "image": data.get("image", {}).get("url")
        }
        return product

    def run(self):
        page = 1
        while True:
            slugs = self.fetch_listing(page)
            if not slugs:
                break
            for slug in slugs:
                product = self.fetch_product_detail(slug)
                if product:
                    self.products.append(product)
                time.sleep(0.1)  # jangan spam server
            page += 1

        # Simpan ke file JSON
        with open("dataScraping_luxehouze.json", "w", encoding="utf-8") as f:
            json.dump(self.products, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(self.products)} products")
import time
import re
import random
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from concurrent.futures import ThreadPoolExecutor, as_completed

from scrapers.base_scraper import BaseScraper


class WatchesTraderScraper(BaseScraper):

    def __init__(self):
        super().__init__(
            base_url="https://watchestrader.id/product/all",
            json_file="dataScraping_watchestrader.json"
        )

        self.max_workers = 3
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0"
        })

    # ===============================
    # GET PRODUCT URLS (WITH RETRY)
    # ===============================
    def get_product_urls_from_page(self, page_url):

        print(f"Mengambil URL dari: {page_url}")

        for attempt in range(3):

            try:
                response = self.session.get(
                    page_url,
                    timeout=10
                )

                if response.status_code != 200:
                    print("Status bukan 200:", response.status_code)
                    time.sleep(3)
                    continue

                soup = BeautifulSoup(response.text, "html.parser")

                links = soup.find_all(
                    "a",
                    class_="border-[#eee] border p-3"
                )

                urls = []

                for link in links:
                    url = link.get("href")

                    if url:
                        if not url.startswith("http"):
                            url = "https://watchestrader.id" + url
                        urls.append(url)

                print(f"Ditemukan {len(urls)} produk")

                return urls

            except Exception as e:
                print(f"Retry {attempt+1} karena error:", e)
                time.sleep(3)

        return None  # error total setelah retry


    # ===============================
    # SCRAPE PRODUCT DETAIL
    # ===============================
    def scrape_product(self, url, driver):

        print(f"\nScraping: {url}")

        try:
            driver.get(url)
            time.sleep(2)

            driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(0.5)

            # Klik tab SPECIFICATION & HISTORY
            for tab_name in ["SPECIFICATION", "HISTORY"]:
                try:
                    driver.execute_script(f"""
                        var buttons = document.querySelectorAll('button');
                        for(var i=0;i<buttons.length;i++) {{
                            if(buttons[i].textContent.includes('{tab_name}')) {{
                                var parent = buttons[i].parentElement;
                                if(parent && parent.getAttribute('data-state') === 'closed') {{
                                    buttons[i].click();
                                    break;
                                }}
                            }}
                        }}
                    """)
                    time.sleep(1)
                except:
                    pass

            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            time.sleep(1)

            soup = BeautifulSoup(
                driver.page_source,
                "html.parser"
            )

            data = {
                "url": url,
                "title": None,
                "price_IDR": None,
                "price_USD": None,
                "sku": None,
                "brand": None,
                "number_reference": None,
                "condition": None,
                "year": None,
                "location": None,
                "type": None,
                "diameter_size": None,
                "case_material": None,
                "dial_color": None,
                "bezel": None,
                "movement": None,
                "watch_strap": None,
                "water_resistant": None,
                "wt_meter": None,
                "description": None,
            }

            # Title
            title = soup.find("h1")
            if title:
                data["title"] = title.text.strip()

            # Price
            price = soup.find(
                "h4",
                class_="text-xl font-semibold"
            )

            if price:
                price_int = re.sub(r"[^\d]", "", price.text)
                if price_int:
                    data["price_IDR"] = int(price_int)

            # Detail rows
            rows = soup.find_all(
                "div",
                class_=re.compile(r"py-2 flex gap-3")
            )

            main_mapping = {
                "SKU": "sku",
                "Brands": "brand",
                "Reference": "number_reference",
                "Condition": "condition",
                "Year": "year",
                "Availability": "location",
            }

            spec_mapping = {
                "Type": "type",
                "Diameter Size": "diameter_size",
                "Case Material": "case_material",
                "Dial Color": "dial_color",
                "Bezel": "bezel",
                "Movement": "movement",
                "Watch Strap": "watch_strap",
                "Water Resistant": "water_resistant",
                "WT Meter": "wt_meter",
            }

            for row in rows:

                label_p = (
                    row.find("p", class_="w-24 font-medium")
                    or
                    row.find("p", class_="w-36 font-medium")
                )

                if not label_p:
                    continue

                label = label_p.text.strip()
                all_p = row.find_all("p")

                if len(all_p) >= 2:

                    value = all_p[1].text.strip()
                    label_clean = label.replace(":", "").strip()

                    if label_clean in main_mapping:
                        data[main_mapping[label_clean]] = value

                    elif label_clean in spec_mapping:
                        data[spec_mapping[label_clean]] = value

            desc = soup.find(
                "div",
                class_="text-[#6A6A6A]"
            )

            if desc:
                data["description"] = desc.text.strip()

            return data
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None

    # ===============================
    # MAIN RUN
    # ===============================
    def run(self):
        print("\n=== WatchesTrader Scraper ===")

        # 1. Buat 1 driver
        driver = self.setup_driver()

        try:
            page = 1
            while True:
                page_url = f"{self.base_url}?page={page}"
                urls = self.get_product_urls_from_page(page_url)
                if urls is None or not urls:
                    break
                self.all_product_urls.extend(urls)
                page += 1
                time.sleep(random.uniform(1.5, 4))

            self.all_product_urls = list(set(self.all_product_urls))
            print(f"Total URL: {len(self.all_product_urls)}")

            # 2. Scrape semua URL dengan 1 driver saja
            for url in self.all_product_urls:
                try:
                    result = self.scrape_product(url, driver)
                    if result:
                        self.all_products.append(result)
                        if len(self.all_products) % 5 == 0:
                            self.save_progress()
                except Exception as e:
                    print("Error scrape product:", e)

            # Final save
            self.save_progress()
            print("WatchesTrader selesai")

        finally:
            driver.quit()
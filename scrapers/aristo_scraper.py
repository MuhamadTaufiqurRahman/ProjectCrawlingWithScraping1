import time
import re
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from concurrent.futures import ThreadPoolExecutor, as_completed

from scrapers.base_scraper import BaseScraper


class AristoScraper(BaseScraper):

    def __init__(self):
        super().__init__(
            base_url="https://aristohk.com/new-watch",
            json_file="dataScraping_aristohk.json"
        )
        self.start_page = 1
        self.max_pages = 5
        self.max_workers = 2

    # ==============================
    # GET PRODUCT URLS
    # ==============================
    def get_product_urls_from_page(self, page_url):
        try:
            print(f"Mengambil URL dari: {page_url}")
            response = requests.get(page_url)
            soup = BeautifulSoup(response.text, "html.parser")
            products = soup.select("div.my-12.grid > div.flex.flex-col")
            urls = []

            for product in products:
                link = product.find("a", href=True)
                if not link:
                    continue

                url = link["href"]
                if not url.startswith("http"):
                    url = "https://aristohk.com" + url

                urls.append(url)
                print(" ditemukan:", url)

            print(f"Total ditemukan: {len(urls)}")
            return urls

        except Exception as e:
            print("Error:", e)
            return []

    # ==============================
    # NUMBER REFERENCE EXTRACTOR (PERBAIKAN)
    # ==============================
    def extract_number_reference(self, title=None, model=None, series=None):
        """
        Extract watch reference number from various fields
        """
        texts = [title, model, series]
        # Filter None dan convert ke string
        texts = [str(t).upper() for t in texts if t]
        combined = " ".join(texts)
        
        print(f"🔍 Mencari reference di: {combined}")
        
        # Pattern khusus untuk berbagai format
        patterns = [
            # 1. Format Omega dengan titik (310.60.42.50.10.001)
            (r"\b\d{3}\.\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{3}\b", "Omega"),
            
            # 2. Format Rolex dengan strip (128235-0039, 126518LN-0010)
            (r"\b[A-Z0-9]{5,7}-[A-Z0-9]{3,4}\b", "Rolex"),
            
            # 3. Format Richard Mille (RM30-01, RM67-02, RM07-02)
            (r"\bRM\d{2,3}-\d{2}\b", "Richard Mille"),
            
            # 4. Format Patek Philippe (6104R-001, 4947R-001, 7118/1R-001)
            (r"\b\d{4}[A-Z]?/?\d?[A-Z]?-\d{3}\b", "Patek"),
            
            # 5. Format Audemars Piguet (26240CE.OO.1225CE.02)
            (r"\b\d{5}[A-Z]{2}\.[A-Z]{2}\.\d{4}[A-Z]{2}\.\d{2}\b", "AP"),
            
            # 6. Format dengan slash (5712/1R-001)
            (r"\b\d{4}/\d[A-Z]-\d{3}\b", "Slash format"),
            
            # 7. Format umum dengan titik dan strip
            (r"\b[A-Z0-9]{4,8}[-\.][A-Z0-9]{3,6}\b", "General"),
            
            # 8. Format angka saja minimal 5 digit (126610, 228238)
            (r"\b\d{5,8}\b", "Numbers only"),
        ]
        
        for pattern, desc in patterns:
            matches = re.findall(pattern, combined)
            if matches:
                # Ambil match terpanjang (paling spesifik)
                result = max(matches, key=len)
                print(f"✅ Found ({desc}): {result}")
                return result
        
        # Fallback: coba extract dari model langsung
        if model and isinstance(model, str):
            # Ambil bagian setelah spasi atau sebelum spasi
            parts = model.split()
            for part in parts:
                if re.match(r"\d{4,}", part):
                    print(f"✅ Fallback from model: {part}")
                    return part
        
        print("❌ No reference found")
        return None

    # ==============================
    # SCRAPE DETAIL PRODUK
    # ==============================
    def scrape_product(self, url):
        print(f"\nScraping: {url}")
        driver = self.setup_driver()

        try:
            driver.get(url)
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(1)

            # Klik tab Description jika ada
            try:
                desc_button = driver.find_element(
                    By.XPATH,
                    "//button[normalize-space()='Description']"
                )
                driver.execute_script("arguments[0].click();", desc_button)
                time.sleep(1)
                print("Tab Description diklik")
            except:
                print("Tab Description tidak ditemukan")

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            soup = BeautifulSoup(driver.page_source, "html.parser")

            data = {
                "url_Product": url,
                "title": None,
                "price_HKD": None,
                "price_USD": None,
                "price_IDR": None,
                "description": None,
                "number_reference": None,
                "release_year_start": None,
                "release_year_end": None,
                "model": None,
                "series": None,
                "brand": None  # Tambah field brand
            }

            # ==============================
            # TITLE
            # ==============================
            title = soup.find("h1")
            if title:
                data["title"] = title.get_text(strip=True)
                # Extract brand dari title (kata pertama)
                if data["title"]:
                    data["brand"] = data["title"].split()[0]
                print("Title:", data["title"])

            # ==============================
            # PRICE + BASIC INFO
            # ==============================
            rows = soup.select("div.flex.items-center")
            for row in rows:
                text = row.get_text(strip=True)
                if ":" not in text:
                    continue

                key, value = text.split(":", 1)
                key = key.lower().strip().replace(" ", "_")
                value = value.strip()

                if key == "retail_price":
                    price_int = re.sub(r"[^\d]", "", value)
                    if price_int:
                        data["price_HKD"] = int(price_int)
                        print("Price_HKD:", data["price_HKD"])
                else:
                    data[key] = value

            # ==============================
            # DETAILED SPECS
            # ==============================
            sections = soup.select("div.grid.grid-cols-6")
            for section in sections:
                cells = section.select("div.col-span-3")
                for i in range(0, len(cells), 2):
                    try:
                        label = cells[i].get_text(strip=True)
                        value = cells[i + 1].get_text(strip=True)
                        key = label.lower().replace(" ", "_")

                        if key == "release_year":
                            match = re.search(r"(\d{4})(?:\s*-\s*(\d{4}))?", value)
                            if match:
                                data["release_year_start"] = int(match.group(1))
                                data["release_year_end"] = int(match.group(2)) if match.group(2) else None
                        else:
                            data[key] = value
                    except Exception as e:
                        pass

            # ==============================
            # DESCRIPTION
            # ==============================
            desc = soup.select_one("div[role='tabpanel'] div.py-4")
            if desc:
                data["description"] = desc.get_text(strip=True)

            # ==============================
            # NUMBER REFERENCE (PAKAI METHOD YANG SUDAH DIPERBAIKI)
            # ==============================
            # Simpan URL untuk fallback
            self.current_url = url
            
            data["number_reference"] = self.extract_number_reference(
                title=data.get("title"),
                model=data.get("model"),
                series=data.get("series")
            )
            
            # Jika masih null, coba extract dari URL
            if not data["number_reference"]:
                # Ambil bagian terakhir dari URL
                url_parts = url.split('/')
                last_part = url_parts[-1] if url_parts else ""
                if last_part.isdigit() and len(last_part) >= 5:
                    data["number_reference"] = last_part
                    print(f"✅ From URL: {data['number_reference']}")

            print("Number Reference:", data["number_reference"])

            return data

        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
        finally:
            driver.quit()

    # ==============================
    # RUN SCRAPER
    # ==============================
    def run(self):
        print("Memulai Aristo Scraper")
        print("="*50)

        for page in range(self.start_page, self.start_page + self.max_pages):
            print(f"\n📄 HALAMAN {page}")
            page_url = f"{self.base_url}?page={page}"
            urls = self.get_product_urls_from_page(page_url)
            if not urls:
                print(f"❌ Tidak ada URL di halaman {page}, berhenti")
                break
            self.all_product_urls.extend(urls)
            time.sleep(2)

        print(f"\n📊 Total URL: {len(self.all_product_urls)}")

        if not self.all_product_urls:
            print("❌ Tidak ada URL untuk discrape")
            return

        successful = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.scrape_product, url): url for url in self.all_product_urls}

            for future in as_completed(futures):
                result = future.result()
                if result:
                    self.all_products.append(result)
                    successful += 1
                    print(f"✅ Success ({successful}): {result.get('title')}")
                    
                    if len(self.all_products) % 5 == 0:
                        self.save_progress()
                        print(f"💾 Progress saved: {len(self.all_products)} items")

        self.save_progress()
        print("\n" + "="*50)
        print(f"✅ Scraping selesai! Total: {len(self.all_products)} produk")
        print(f"📁 File: {self.json_file}")
        
        # Tampilkan statistik number reference
        with_ref = sum(1 for p in self.all_products if p.get('number_reference'))
        print(f"🔢 Number reference found: {with_ref}/{len(self.all_products)}")
        print("="*50)
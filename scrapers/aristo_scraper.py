import time
import re
import random
import gc
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.common.exceptions import InvalidSessionIdException, WebDriverException, TimeoutException

from scrapers.base_scraper import BaseScraper


class AristoScraper(BaseScraper):

    def __init__(self):
        super().__init__(
            base_url="https://aristohk.com",
            json_file="dataScraping_aristohk.json"
        )

        self.brands = [
            "rolex",
            "audemars-piguet",
            "patek-philippe",
            "richard-mille",
            "alange-soehne",
            "bulgari",
            "f-p-journe",
            "hublot",
            "jaeger-lecoultre",
            "omega",
            "roger-dubuis",
            "van-cleef-arpels",
            "baume-mercier",
            "cartier",
            "girard-perregaux",
            "hyt",
            "longines",
            "panerai",
            "tag-heuer",
            "zenith",
            "blancpain",
            "chanel",
            "glashutte",
            "iwc",
            "mb-f",
            "parmigiani-fleurier",
            "tudor",
            "breguet",
            "chopard",
            "h-moser-cie",
            "jacob-and-co",
            "montblanc",
            "piaget",
            "vacheron-constantin"
        ]

        self.start_page = 1
        self.max_pages = 1
        self.driver = None
        self.batch_size = 15  # Restart setiap 15 produk
        self.max_retries = 2   # Maksimal retry per produk

    # ==============================
    # HELPER: CEK DRIVER
    # ==============================
    def is_driver_alive(self):
        """Cek apakah driver masih hidup"""
        try:
            self.driver.current_url
            return True
        except:
            return False

    # ==============================
    # HELPER: RESTART DRIVER
    # ==============================
    def restart_driver(self):
        """Restart driver dengan aman"""
        print("🔄 Merestart driver untuk hemat memory...")
        try:
            self.driver.quit()
        except:
            pass
        
        time.sleep(3)
        self.driver = self.setup_driver()
        print("✅ Driver berhasil direstart")

    # ==============================
    # GET PRODUCT URLS
    # ==============================
    def get_product_urls_from_page(self, page_url, brand):
        try:
            print(f"Mengambil URL dari: {page_url}")
            response = requests.get(page_url)
            soup = BeautifulSoup(response.text, "html.parser")
            products = soup.select("div.my-12.grid > div.flex.flex-col")

            items = []

            for product in products:
                link = product.find("a", href=True)
                if not link:
                    continue

                url = link["href"]
                if not url.startswith("http"):
                    url = self.base_url + url

                ref_text = link.get("aria-label", "").strip().upper()

                items.append({
                    "url": url,
                    "brand": brand,
                    "number_reference": ref_text
                })

                print(" ditemukan:", url, "| REF:", ref_text)

            print(f"Total ditemukan: {len(items)}")
            return items

        except Exception as e:
            print("Error:", e)
            return []

    # ==============================
    # NUMBER REFERENCE EXTRACTOR
    # ==============================
    def extract_number_reference(self, title=None, model=None, series=None):
        texts = [title, model, series]
        texts = [str(t).upper() for t in texts if t]
        combined = " ".join(texts)

        print(f"🔍 Mencari reference di: {combined}")

        patterns = [
            (r"\b\d{3}\.\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{3}\b", "Omega"),
            (r"\b[A-Z0-9]{5,7}-[A-Z0-9]{3,4}\b", "Rolex"),
            (r"\bRM\d{2,3}-\d{2}\b", "Richard Mille"),
            (r"\bRM\d{2,3}[- ]?[A-Z0-9]{2}\b", "Richard Mille"),
            (r"\b\d{4}[A-Z]?/?\d?[A-Z]?-\d{3}\b", "Patek"),
            (r"\b\d{5}[A-Z]{2}\.[A-Z]{2}\.\d{4}[A-Z]{2}\.\d{2}\b", "AP"),
            (r"\b\d{4}/\d[A-Z]-\d{3}\b", "Slash format"),
            (r"\b[A-Z0-9]{4,8}[-\.][A-Z0-9]{3,6}\b", "General"),
            (r"\b\d{5,8}\b", "Numbers only"),
        ]

        for pattern, desc in patterns:
            matches = re.findall(pattern, combined)
            if matches:
                matches = [m for m in matches if re.search(r"\d", m)]
                if matches:
                    result = max(matches, key=len)
                    print(f"✅ Found ({desc}): {result}")
                    return result

        if model and isinstance(model, str):
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
    def scrape_product(self, item):
        url = item["url"]
        brand = item["brand"]
        listing_ref = item.get("number_reference")

        # Cek driver sebelum mulai
        if not self.is_driver_alive():
            print("⚠️ Driver mati, merestart...")
            self.restart_driver()

        print(f"\nScraping: {url}")

        for attempt in range(self.max_retries):
            try:
                driver = self.driver

                # Buka tab baru
                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[-1])
                
                # Set timeout
                driver.set_page_load_timeout(30)
                
                # Load URL dengan error handling
                try:
                    driver.get(url)
                except TimeoutException:
                    print("⚠️ Timeout load page, retry...")
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    if attempt < self.max_retries - 1:
                        time.sleep(3)
                        continue
                    else:
                        return None
                except Exception as e:
                    print(f"⚠️ Error load page: {e}")
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    if attempt < self.max_retries - 1:
                        time.sleep(3)
                        continue
                    else:
                        return None

                time.sleep(2)
                
                # Scroll
                try:
                    driver.execute_script("window.scrollTo(0, 500);")
                    time.sleep(1)
                except:
                    pass

                # Klik tab Description
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

                # Scroll ke bawah
                try:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                except:
                    pass

                # Parse dengan BeautifulSoup
                soup = BeautifulSoup(driver.page_source, "html.parser")

                # Inisialisasi data
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
                    "brand": brand.upper().replace("-", " ")
                }

                # TITLE
                title = soup.find("h1")
                if title:
                    data["title"] = title.get_text(strip=True)
                    print("Title:", data["title"])

                # PRICE + BASIC INFO
                rows = soup.select("div.flex.items-center")
                for row in rows:
                    text = row.get_text(strip=True)
                    if ":" not in text:
                        continue
                    try:
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
                    except:
                        continue

                # DETAILED SPECS
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
                        except:
                            pass

                # DESCRIPTION
                desc = soup.select_one("div[role='tabpanel'] div.py-4")
                if desc:
                    data["description"] = desc.get_text(strip=True)

                # NUMBER REFERENCE
                if listing_ref and len(listing_ref) >= 4:
                    data["number_reference"] = listing_ref.strip().upper()
                else:
                    data["number_reference"] = self.extract_number_reference(
                        title=data.get("title"),
                        model=data.get("model"),
                        series=data.get("series")
                    )

                # Fallback dari URL slug
                if not data["number_reference"]:
                    url_parts = url.strip("/").split("/")
                    if len(url_parts) >= 2:
                        slug = url_parts[-2].replace("-", " ").upper()
                        match = re.search(r"(RM\d{2,3}[- ]?\d{2})", slug)
                        if match:
                            data["number_reference"] = match.group(1).replace(" ", "-")
                            print(f"✅ From URL slug: {data['number_reference']}")

                print("Number Reference:", data["number_reference"])
                
                # Force garbage collection
                gc.collect()
                
                return data

            except (InvalidSessionIdException, WebDriverException) as e:
                print(f"⚠️ Session error pada attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    self.restart_driver()
                    time.sleep(3)
                else:
                    print(f"❌ Gagal setelah {self.max_retries} percobaan")
                    return None
            except Exception as e:
                print(f"⚠️ Error umum: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                else:
                    return None
            finally:
                # Tutup tab dengan aman
                try:
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                except:
                    try:
                        driver.switch_to.window(driver.window_handles[0])
                    except:
                        pass

        return None

    # ==============================
    # RUN SCRAPER (MULTI BRAND)
    # ==============================
    def run(self):
        print("Memulai Aristo Scraper Multi-Brand")
        print(f"🔄 Batch size: {self.batch_size} produk (untuk hemat memory)")
        
        self.driver = self.setup_driver()

        try:
            # STEP 1: Kumpulkan Semua URL
            for brand in self.brands:
                print(f"\n========== BRAND: {brand.upper()} ==========")
                page = 1
                max_empty_pages = 2  # Berhenti jika 2 halaman berturut-turut kosong
                empty_count = 0
                
                while empty_count < max_empty_pages:
                    page_url = f"{self.base_url}/{brand}?page={page}"
                    print(f"\n📄 HALAMAN {page} | {brand}")
                    
                    items = self.get_product_urls_from_page(page_url, brand)
                    
                    if not items:
                        empty_count += 1
                        print(f"❌ Halaman {page} kosong (empty count: {empty_count})")
                        if empty_count >= max_empty_pages:
                            print(f"🛑 Stop brand {brand} setelah {max_empty_pages} halaman kosong")
                            break
                    else:
                        empty_count = 0  # Reset jika ada produk
                        for item in items:
                            self.all_product_urls.append(item)
                    
                    page += 1
                    time.sleep(1)

            print(f"\n📊 Total URL terkumpul: {len(self.all_product_urls)}")
            if not self.all_product_urls:
                print("❌ Tidak ada URL untuk discrape")
                return

            # STEP 2: Scrape Detail Produk dengan BATCH PROCESSING
            for idx, item in enumerate(self.all_product_urls, start=1):
                result = self.scrape_product(item)
                
                if result:
                    self.all_products.append(result)
                    print(f"✅ Success ({idx}): {result.get('title', 'No Title')}")
                    
                    # Save progress setiap 5 produk
                    if idx % 5 == 0:
                        self.save_progress()
                        print(f"💾 Progress saved at produk ke-{idx}")
                    
                    # Restart driver setiap batch_size produk
                    if idx % self.batch_size == 0:
                        print(f"🔄 Mencapai {idx} produk, restart driver untuk hemat memory...")
                        self.restart_driver()
                    
                    # Delay random antar produk (1-3 detik)
                    time.sleep(random.uniform(1, 3))
                else:
                    print(f"❌ Gagal ({idx}): {url}")

            # Final save
            self.save_progress()
            print("💾 Final save completed")

            # Statistik
            with_ref = sum(1 for p in self.all_products if p.get("number_reference"))
            print(f"\n📊 STATISTIK:")
            print(f"🔢 Number reference found: {with_ref}/{len(self.all_products)}")
            print(f"✅ Scraping selesai!")

        except KeyboardInterrupt:
            print("\n⚠️ Scraping dihentikan oleh user")
            self.save_progress()
            
        except Exception as e:
            print(f"❌ Error fatal di run(): {e}")
            import traceback
            traceback.print_exc()
            self.save_progress()  # Tetap save progress
            
        finally:
            try:
                self.driver.quit()
                print("🛑 Driver ditutup")
            except:
                pass
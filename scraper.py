import time
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from driver import setup_driver


def scrape_product(url):

    print(f"\nScraping: {url}")

    driver = setup_driver()

    try:

        driver.get(url)

        time.sleep(2)

        driver.execute_script("window.scrollTo(0, 500);")

        time.sleep(1)

        try:

            desc_button = driver.find_element(By.XPATH, "//button[normalize-space()='Description']")

            driver.execute_script("arguments[0].click();", desc_button)

            time.sleep(1)

            print("  - Tab Description diklik")

        except:

            print("  - Tab Description tidak ditemukan")

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        time.sleep(1)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        data = {
            "url": url,
            "title": None,
            "price": None,
            "description": None
        }

        title = soup.find("h1")

        if title:

            data["title"] = title.get_text(strip=True)

            print("  Title:", data["title"])

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

                    data["price"] = int(price_int)

                    print("  Price:", data["price"])

            else:

                data[key] = value

        sections = soup.select("div.grid.grid-cols-6")

        for section in sections:

            cells = section.select("div.col-span-3")

            for i in range(0, len(cells), 2):

                try:

                    label = cells[i].get_text(strip=True)

                    value = cells[i+1].get_text(strip=True)

                    key = label.lower().replace(" ", "_")

                    if key == "release_year":

                        year = re.sub(r"[^\d]", "", value)

                        if year:

                            data[key] = int(year)

                    else:

                        data[key] = value

                except:

                    pass

        desc = soup.select_one("div[role='tabpanel'] div.py-4")

        if desc:

            data["description"] = desc.get_text(strip=True)

        return data

    finally:

        driver.quit()


def scrape_product_wrapper(url):

    try:

        return scrape_product(url)

    except Exception as e:

        print(f"Error scraping {url}: {e}")

        return None
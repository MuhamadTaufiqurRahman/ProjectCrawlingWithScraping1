# Web Scraper – Watch Product Scraper

## Overview

This project is an automated web scraper built using *Python* to extract watch product data from the Aristohk website:

https://aristohk.com/new-watch
https://watchestrader.id/
https://luxehouze.com/id/en/watch/category/all-watches

The scraper collects product information including title, price, specifications, release year, and description, then saves the data into a structured JSON file.

This scraper supports:

* Pagination handling
* Dynamic content scraping using Selenium
* Parallel scraping using multi-threading
* Automatic progress saving
* Class-based modular and maintainable architecture

---

## Features

* Scrapes product listing pages with pagination

* Extracts detailed product information:

  * URL
  * Title
  * Retail price
  * Specifications
  * Release year
  * Description

* Uses headless browser for automation

* Multi-threaded scraping for improved performance

* Saves results in JSON format

* Class-based architecture for scalability

* Easily extendable to support multiple websites

---

## Technology Stack

**Language**

* Python 3

**Libraries**

* selenium – browser automation
* beautifulsoup4 – HTML parsing
* requests – HTTP requests
* concurrent.futures – parallel execution

**Tools**

* Google Chrome

---

## Architecture

This project uses a class-based scraper architecture for better scalability and maintainability.

### BaseScraper

Provides reusable core functionality:

* Selenium WebDriver setup
* Progress saving
* Base scraper structure
* Shared configuration handling

### AristoScraper

Implements Aristohk-specific scraping logic:

* Product URL collection
* Product detail extraction
* Pagination handling
* Multi-threaded scraping

This architecture allows easy expansion to support additional websites by creating new scraper classes.

Example:

```
scrapers/
├── base_scraper.py
├── aristo_scraper.py
├── watchtrader_scraper.py
└── amazon_scraper.py
```

---

## Installation

### 1. Install Python

Minimum version:

```
Python 3.10+
```

Check version:

```
python --version
```

---

### 2. Install Google Chrome

Download and install:

https://www.google.com/chrome/

---

### 4. Install Dependencies

Install using pip:

```
pip install -r requirements.txt
```

Or manually:

```
pip install selenium beautifulsoup4 requests
```

---

## Usage

Run the scraper:

```
python main.py
```

---

## Output

Output file:

```
hasil.json
```

Example:

```
[
  {
    "url": "https://aristohk.com/...",
    "title": "Rolex Submariner",
    "price": 125000,
    "release_year": 2023,
    "description": "Product description..."
  }
]
```

---

## Configuration

You can modify scraper settings inside:

```
scrapers/aristo_scraper.py
```

Example:

```
self.start_page = 1
self.max_pages = 5
self.max_workers = 3
self.json_file = "hasil.json"
```

---

## How It Works

1. Collect product URLs from paginated listing pages using Requests
2. Open each product page using Selenium
3. Render JavaScript content
4. Extract data using BeautifulSoup
5. Save data into JSON file
6. Run scraping concurrently using ThreadPoolExecutor

---

## Requirements

* Python 3.10+
* Google Chrome
* ChromeDriver
* Internet connection

---

## Performance

Supports parallel scraping using ThreadPoolExecutor.

Default configuration:

```
3 concurrent browser instances
```

Performance depends on:

* CPU cores
* RAM availability
* Internet speed

---

## Scalability

This scraper is designed with scalability in mind.

You can easily add support for new websites by creating new scraper classes:

Example:

```
class WatchTraderScraper(BaseScraper):
    def get_product_urls_from_page(self, page_url):
        pass

    def scrape_product(self, url):
        pass
```

---

## Notes

* Uses headless Chrome for automation
* Automatically saves progress every 5 products
* Uses class-based architecture for maintainability
* Designed for scalability and production use
* Easy to extend for scraping multiple websites

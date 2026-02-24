# Web Scraper – Aristohk Watch Product Scraper

## Overview

This project is an automated web scraper built using *Python* to extract watch product data from the Aristohk website:

https://aristohk.com/new-watch

The scraper collects product information including title, price, specifications, release year, and description, then saves the data into a structured JSON file.

This scraper supports:

* Pagination handling
* Dynamic content scraping using Selenium
* Parallel scraping using multi-threading
* Automatic progress saving
* Modular and maintainable architecture

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
* Modular structure for easy maintenance

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
* ChromeDriver

---

## Project Structure

```
scraper_project/
│
├── main.py              # Entry point
├── config.py            # Configuration
├── driver.py            # Selenium driver setup
├── scraper.py           # Product scraper logic
├── url_collector.py     # Collect product URLs
├── hasil.json           # Output file
└── requirements.txt     # Dependencies
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

### 3. Install ChromeDriver

Download version matching your Chrome browser:

https://chromedriver.chromium.org/downloads

Add ChromeDriver to:

```
C:\Windows\
```

or project folder.

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

You can modify settings in:

```
config.py
```

Example:

```
BASE_URL = 'https://aristohk.com/new-watch'
START_PAGE = 1
MAX_PAGES = 5
MAX_WORKERS = 3
JSON_FILE = 'hasil.json'
```

---

## How It Works

1. Collect product URLs from paginated listing pages using Requests
2. Open each product page using Selenium
3. Render JavaScript content
4. Extract data using BeautifulSoup
5. Save data into JSON file
6. Run scraping concurrently for better performance

---

## Requirements

* Python 3.10+
* Google Chrome
* ChromeDriver
* Internet connection

---

## Performance

Supports parallel scraping using ThreadPoolExecutor.

Default:

```
3 concurrent browser instances
```

Can be configured in config.py.

---

## Notes

* Uses headless Chrome for automation
* Automatically saves progress every 5 products
* Designed for maintainability and scalability

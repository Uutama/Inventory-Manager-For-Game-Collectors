# Inventory Management for Game Collectors

A Python app to scrape video game pricing and sales data, manage on-hand inventory, and store game details locally.

## Features

- Scrape pricing and sales metadata from configured sources like PriceCharting
- Add, edit, and manage on-hand inventory items
- Store scraped game details in a local JSON database
- Store and display suggested price values from scraped online data
- Command-line interface for inventory operations

## Setup

1. Create a virtual environment:

```bash
python -m venv .venv
```

2. Activate the environment:

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

4. Ensure Google Chrome is installed on your system. The PriceCharting scraper uses Selenium and webdriver-manager to drive Chrome.

## Run

```bash
python main.py
```

Or launch the Tkinter GUI:

```bash
python run_gui.py
```

If `main.py` detects missing packages, it will attempt to install them automatically using the current Python interpreter.

## Notes

This scaffold includes a starter scraper module with placeholder logic. Update `inventory_scraper/scraper.py` with the actual website scraping logic and data sources.

## Special Thanks
https://github.com/markfoster314/Pricecharting-Scraper - My parsing data was inspired by this repo.

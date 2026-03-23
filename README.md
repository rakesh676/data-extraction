# Google Maps Leads Scraper

A complete, production-ready Python project that extracts local businesses from Google Maps and ONLY saves the ones WITHOUT websites. Perfect for finding potential clients for web development and SEO services.

## Features
- Scrapes Google Maps dynamically utilizing Playwright steering clear of expensive APIs.
- Built-in stealth measures (headers, human-like delays, scrolling) to evade bot detection.
- Extracts: Name, Category, Address, Phone Number, and Website.
- Automatically filters out businesses that ALREADY have a website.
- Saves validated leads into a `leads.xlsx` file.

## Setup Instructions

1. Ensure **Python 3.8+** is installed on your Windows machine.
2. Open your Command Prompt or PowerShell in the `d:\maps` directory.
3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Install the Playwright browser binaries:
   ```bash
   playwright install chromium
   ```

## Running the Scraper

To run the script with its default configurations, execute:
```bash
python main.py
```
*(By default, this will search for "real estate", "tuition centers", and "event planners" in "Visakhapatnam, India", attempting to grab up to 20 results per category).*

### Running with Command Line Arguments

If you want to search for different categories or locations, use command line arguments:
```bash
python main.py --categories "plumbers" "electricians" --location "London, UK" --max_results 50
```

- `--categories`: A space-separated list of search keywords.
- `--location`: The target city, region, or neighborhood.
- `--max_results`: The maximum number of items to load and scan per category.
- `--headless`: Run the browser invisibly in the background. Note: Google might block headless browsers slightly faster than visible ones. 

## Example Console Output
```text
2026-03-22 12:38:05 - INFO - Initializing Google Maps Scraper...
2026-03-22 12:38:05 - INFO - Target Location: Visakhapatnam, India
2026-03-22 12:38:05 - INFO - Categories: ['real estate', 'tuition centers', 'event planners']
...
2026-03-22 12:38:20 - INFO - LEAD FOUND: Elite Estate Agency (No Website)
2026-03-22 12:38:25 - INFO - Skipped: Sunrise Real Estate (Has Website)
...
2026-03-22 12:39:15 - INFO - --- Scraping Complete ---
2026-03-22 12:39:15 - INFO - Total Leads found (NO WEBSITE): 15
2026-03-22 12:39:15 - INFO - Successfully saved 15 records to leads.xlsx
```

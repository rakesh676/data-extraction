from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import stealth_sync
from utils import logger, random_delay, has_website

import subprocess

subprocess.run(["playwright", "install", "chromium"])


class GoogleMapsScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.base_url = "https://www.google.com/maps"
        self.results = []
        self.seen_names = set()

    def scrape(self, categories, location, max_results_per_category=20, yield_callback=None):
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"]
            )
            # Create a context with human-like realistic viewport
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            # Apply anti-bot stealth measures
            stealth_sync(page)

            for category in categories:
                logger.info(f"--- Starting scrape for '{category}' in '{location}' ---")
                self._scrape_category(page, category, location, max_results_per_category, yield_callback)

            browser.close()
            return self.results

    def _scrape_category(self, page, category, location, max_results, yield_callback=None):
        import urllib.parse
        search_query = f"{category} in {location}"
        encoded_query = urllib.parse.quote(search_query)
        search_url = f"{self.base_url}/search/{encoded_query}"
        
        try:
            page.goto(search_url, timeout=60000)
            random_delay(2.0, 4.0)
        except Exception as e:
            logger.error(f"Failed to load search URL: {e}")
            return
        
        # Accept cookies if the popup appears (common in European regions)
        try:
            page.locator('button:has-text("Accept all")').click(timeout=3000)
            logger.info("Accepted cookies.")
        except PlaywrightTimeoutError:
            pass

        # Wait for results feed to load
        try:
            page.wait_for_selector('div[role="feed"]', timeout=15000)
        except PlaywrightTimeoutError:
            logger.error("Results feed did not load. Note: No results found or page changed. Skipping.")
            return
            
        logger.info("Results feed loaded. Scrolling to fetch items...")
        
        # Scroll the feed to load results lazily
        self._scroll_feed(page, max_results)
        
        # Get all business listing links in the container
        # Updated selector to be more robust
        links_locator = page.locator('div[role="feed"] a[href*="/maps/place/"]')
        count = links_locator.count()
        logger.info(f"Found {count} business listings on page. Starting data extraction...")

        processed = 0
        for i in range(count):
            if max_results > 0 and processed >= max_results:
                break
                
            try:
                # Click the listing to open details panel
                link = links_locator.nth(i)
                link.scroll_into_view_if_needed()
                
                # Human-like click mechanism
                box = link.bounding_box()
                if box:
                    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                else:
                    link.click()
                    
                random_delay(1.5, 3.0)
                
                # Wait for the h1 in details panel to update indicating it fully loaded
                page.wait_for_selector('h1.DUwDvf', timeout=10000)
                
                # Extract data
                business_data = self._extract_business_details(page)
                
                name = business_data.get("Name", "").strip()
                if not name or name in self.seen_names:
                    continue
                self.seen_names.add(name)
                
                # Add it to leads (we want ALL businesses now)
                has_web = has_website(business_data.get("Website", ""))
                business_data["Has Website"] = "Yes" if has_web else "No"
                self.results.append(business_data)
                
                logger.info(f"Extracted: {business_data['Name']} (Has Website: {business_data['Has Website']})")
                
                if yield_callback:
                    yield_callback(business_data)
                
                processed += 1
                if processed % 10 == 0:
                    logger.info(f"Processed {processed} listings for {category}...")
                    
            except Exception as e:
                logger.warning(f"Error processing listing index {i}: {e}")
                continue

    def _scroll_feed(self, page, target_count):
        """Scrolls the left-hand results feed slowly to load more items."""
        feed_selector = 'div[role="feed"]'
        feed_locator = page.locator(feed_selector)
        last_count = 0
        retries = 0
        
        # If target_count is 0 or very high, we scrape "all"
        is_scrape_all = target_count <= 0 or target_count >= 1000
        
        while True:
            # Use a more generic link selector for counting
            links = feed_locator.locator('a[href*="/maps/place/"]')
            count = links.count()
            
            if not is_scrape_all and count >= target_count:
                break
                
            # Check for "You've reached the end of the list" or similar
            end_of_list = page.locator('span:has-text("You\'ve reached the end of the list"), span:has-text("No more results")').count() > 0
            if end_of_list:
                logger.info("Reached the end of the Google Maps results list.")
                break

            if count == last_count:
                retries += 1
                if retries > 10:  # Increased retries for slow loading or very long lists
                    logger.info("No new results found after several scrolls. Ending scroll.")
                    break
            else:
                retries = 0
                
            last_count = count
            
            # Perform scroll
            try:
                # Scroll element dynamically
                feed_locator.evaluate("element => element.scrollBy(0, 1000)")
                # Slightly longer delay for "All" searches to ensure loading
                random_delay(2.0, 3.5)
            except Exception:
                break

    def _extract_business_details(self, page):
        """Extracts text from the details panel on right-hand side using common attributes."""
        data = {
            "Name": "",
            "Category": "",
            "Rating": "",
            "Reviews": "",
            "Phone": "",
            "Address": "",
            "Website": ""
        }
        
        # 1. Extract Name
        try:
            data["Name"] = page.locator('h1.DUwDvf').inner_text(timeout=2000)
        except PlaywrightTimeoutError:
            pass
            
        # 2. Extract Category (Usually the first button with class DkEaL)
        try:
            data["Category"] = page.locator('button.DkEaL').first.inner_text(timeout=1000)
        except PlaywrightTimeoutError:
            pass
            
        # 3. Extract Address
        try:
            address_btn = page.locator('button[data-item-id="address"]')
            aria_label = address_btn.get_attribute('aria-label', timeout=1000)
            if aria_label:
                # E.g. "Address: 123 Main St"
                data["Address"] = aria_label.replace("Address: ", "").strip()
            else:
                data["Address"] = address_btn.inner_text()
        except PlaywrightTimeoutError:
            pass
            
        # 4. Extract Phone
        try:
            phone_btn = page.locator('button[data-item-id^="phone:tel:"]')
            aria_label = phone_btn.get_attribute('aria-label', timeout=1000)
            if aria_label:
                # E.g. "Phone: +1 234..."
                data["Phone"] = aria_label.replace("Phone: ", "").strip()
            else:
                data["Phone"] = phone_btn.inner_text()
        except PlaywrightTimeoutError:
            pass
            
        # 5. Extract Website
        try:
            website_link = page.locator('a[data-item-id="authority"]')
            # Website uses href instead of inner text as it cleanly gives the domain
            href = website_link.get_attribute('href', timeout=1000)
            data["Website"] = href if href else ""
        except PlaywrightTimeoutError:
            data["Website"] = ""
            
        # 6. Extract Rating and Reviews
        try:
            rating_container = page.locator('div.F7nice')
            if rating_container.count() > 0:
                rating_text = rating_container.first.inner_text(timeout=1000)
                # Usually text is like "4.5(120)" or "4.5 \n (120)"
                rating_text = rating_text.replace('\n', '')
                if '(' in rating_text and ')' in rating_text:
                    data["Rating"] = rating_text.split('(')[0].strip()
                    data["Reviews"] = rating_text.split('(')[1].split(')')[0].strip()
                else:
                    data["Rating"] = rating_text.strip()
        except PlaywrightTimeoutError:
            pass
            
        return data

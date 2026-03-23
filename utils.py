import time
import random
import logging
import pandas as pd

def setup_logger(name="scraper"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
    return logger

logger = setup_logger()

def random_delay(min_seconds=1.0, max_seconds=3.0):
    """Adds a human-like random delay to avoid bot detection."""
    time.sleep(random.uniform(min_seconds, max_seconds))

def save_to_excel(data, filename="leads.xlsx"):
    """Saves a list of business dictionaries to an Excel file."""
    if not data:
        logger.warning("No data to save.")
        return
        
    df = pd.DataFrame(data)
    
    # Ensure columns exist and order them
    columns_order = ['Name', 'Category', 'Rating', 'Reviews', 'Phone', 'Address', 'Website', 'Has Website']
    for col in columns_order:
        if col not in df.columns:
            df[col] = ''
            
    df = df[columns_order]
    
    # Save to Excel using pandas and openpyxl
    df.to_excel(filename, index=False, engine='openpyxl')
    logger.info(f"Successfully saved {len(df)} records to {filename}")

def has_website(url_or_domain: str) -> bool:
    """Check if the website string is valid and present.
    Returns True if a website string exists, otherwise False.
    """
    if not url_or_domain:
        return False
    # Check if the string actually contains any non-whitespace characters
    return bool(str(url_or_domain).strip())

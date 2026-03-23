import argparse
import sys
from scraper import GoogleMapsScraper
from utils import logger, save_to_excel

def main():
    # Example Default Parameters
    DEFAULT_CATEGORIES = ["real estate", "tuition centers", "event planners"]
    DEFAULT_LOCATION = "Visakhapatnam, India"
    DEFAULT_MAX_RESULTS = 20

    # Command line argument parsing
    parser = argparse.ArgumentParser(description="Google Maps Leads Scraper - Extract local businesses WITHOUT websites.")
    parser.add_argument("--categories", nargs='+', default=DEFAULT_CATEGORIES, help="Categories to search (space-separated)")
    parser.add_argument("--location", type=str, default=DEFAULT_LOCATION, help="Target location")
    parser.add_argument("--max_results", type=int, default=DEFAULT_MAX_RESULTS, help="Max results to fetch per category")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode (invisible)")

    args = parser.parse_args()

    logger.info("Initializing Google Maps Scraper...")
    logger.info(f"Target Location: {args.location}")
    logger.info(f"Categories: {args.categories}")
    logger.info(f"Max Results per Category: {args.max_results}")
    
    # Initialize the scraper. 
    # By default, running visibly (headless=False) is recommended for Google Maps to avoid early bot detection
    scraper = GoogleMapsScraper(headless=args.headless)
    
    try:
        # Run the scraper
        leads = scraper.scrape(
            categories=args.categories, 
            location=args.location, 
            max_results_per_category=args.max_results
        )
        
        logger.info(f"\n--- Scraping Complete ---")
        logger.info(f"Total Leads found (NO WEBSITE): {len(leads)}")
        
        if leads:
            save_to_excel(leads, filename="leads.xlsx")
        else:
            logger.info("No leads without websites were found.")
            
    except KeyboardInterrupt:
        logger.info("\nScraping interrupted by user. Saving whatever we found so far...")
        if scraper.results:
            save_to_excel(scraper.results, filename="leads.xlsx")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

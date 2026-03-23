import streamlit as st
import pandas as pd
import os
import asyncio
from scraper import GoogleMapsScraper
from utils import logger, save_to_excel

if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

st.set_page_config(page_title="Google Maps Scraper", page_icon="📍", layout="wide")

st.title("📍 Google Maps Lead Scraper")
st.markdown("""
Extract business leads from Google Maps in real-time. 
Enter categories and a location to get started.
""")

# Sidebar for configuration
with st.sidebar:
    st.header("Search Configuration")
    categories_input = st.text_area("Categories (comma-separated)", "Real Estate", help="Enter business types separated by commas.")
    location_input = st.text_input("Location", "Vishakapatanam, Andhra Pradesh", help="Enter a city, state, or specific area.")
    
    scrape_all = st.checkbox("Scrape All Available Results", value=True, help="If checked, the scraper will attempt to find all listings for the category. This may take longer.")
    
    if not scrape_all:
        max_results = st.number_input("Max Results per Category", min_value=1, max_value=2000, value=100)
    else:
        max_results = 0 # 0 will be interpreted as "All" by our updated scraper
    
    st.divider()
    st.info("💡 **Tip:** To get all results, ensure 'Scrape All' is checked. The scraper will scroll until Google Maps says there's no more data.")

# Initialize session state for results
if 'leads' not in st.session_state:
    st.session_state.leads = []

# Main UI layout
col1, col2 = st.columns([2, 1])

with col1:
    start_button = st.button("🚀 Start Scraping", use_container_width=True)
    stop_button = st.button("🛑 Stop (Experimental)", use_container_width=True)

    status_placeholder = st.empty()
    table_placeholder = st.empty()

with col2:
    st.header("Stats & Export")
    stats_placeholder = st.empty()
    download_placeholder = st.empty()

def update_ui(data):
    st.session_state.leads.append(data)
    # Update table
    df = pd.DataFrame(st.session_state.leads)
    table_placeholder.dataframe(df, use_container_width=True)
    # Update stats
    stats_placeholder.metric("Total Leads Found", len(st.session_state.leads))

if start_button:
    categories = [c.strip() for c in categories_input.split(',') if c.strip()]
    
    if not categories or not location_input:
        st.error("Please provide both categories and a location.")
    else:
        st.session_state.leads = [] # Reset leads
        status_placeholder.info(f"Searching for {', '.join(categories)} in {location_input}...")
        
        try:
            scraper = GoogleMapsScraper(headless=True)
            results = scraper.scrape(
                categories=categories,
                location=location_input,
                max_results_per_category=max_results,
                yield_callback=update_ui
            )
            
            if st.session_state.leads:
                filename = "leads.xlsx"
                save_to_excel(st.session_state.leads, filename=filename)
                status_placeholder.success(f"Scraping complete! Found {len(st.session_state.leads)} leads.")
                
                # Provide download button
                with open(filename, "rb") as f:
                    download_placeholder.download_button(
                        label="📄 Download Excel File",
                        data=f,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                status_placeholder.warning("No leads found. Google Maps might be blocking the request or categories/location are invalid.")
                
        except Exception as e:
            st.error(f"An error occurred during scraping.")
            st.exception(e)
            logger.error(f"Streamlit App Error: {e}", exc_info=True)

# Display existing leads if any (e.g. on page refresh/rerun)
if st.session_state.leads:
    df = pd.DataFrame(st.session_state.leads)
    table_placeholder.dataframe(df, use_container_width=True)
    stats_placeholder.metric("Total Leads Found", len(st.session_state.leads))

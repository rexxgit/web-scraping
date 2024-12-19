from playwright.sync_api import sync_playwright
import pandas as pd
import os

# Base URL for scraping
base_url = 'https://www.ubuy.et/en/category/electronics-10171?page={}'

# Output CSV file path
output_path = 'web-scraping/ecommerce/ubuy_electron.csv'

# Headers to simulate a real browser request (to avoid anti-scraping measures)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Function to scrape the data
def scrape_data():
    page_number = 1
    all_scraped_data = []

    with sync_playwright() as p:
        # Launch Chromium in headless mode
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Set the custom headers to the browser context to simulate a real browser request
        page.set_extra_http_headers(headers)
        
        while True:
            # Construct the URL for the current page
            url = base_url.format(page_number)
            page.goto(url)

            # Wait for the products to be loaded
            page.wait_for_selector("div.col-lg-3.col-md-4.col-sm-6.col-12.p-0.listing-product")

            # Extract product details
            products = page.query_selector_all("div.col-lg-3.col-md-4.col-sm-6.col-12.p-0.listing-product")
            
            if not products:
                # If no products are found, break out of the loop (end of pagination)
                print(f"No products found on page {page_number}. Stopping scrape.")
                break

            # Extract the product data from each product on the current page
            for product in products:
                # Extract title
                title_element = product.query_selector("h3.product-title.m-0.mt-2")
                title = title_element.inner_text() if title_element else 'No title'

                # Extract price
                price_element = product.query_selector("h3.product-price.m-0.mt-2")
                price = price_element.inner_text() if price_element else 'No price'

                # Extract link
                link_element = product.query_selector("a[href]")
                link = link_element.get_attribute('href') if link_element else 'No link'
                
                # Load existing data to compare and highlight new vs. existing products
                try:
                    existing_df = pd.read_csv(output_path)
                    existing_titles = set(existing_df['title'])
                except FileNotFoundError:
                    existing_titles = set()

                # Check if the product is new or existing
                highlight = 'new' if title not in existing_titles else 'existing'

                # Append the data to the list
                all_scraped_data.append({
                    'title': title,
                    'price': price,
                    'link': link,
                    'highlight': highlight
                })
            
            # Check if there is a next page link; if so, continue to the next page
            next_page_button = page.query_selector("a[rel='next']")
            if next_page_button:
                page_number += 1
                print(f"Page {page_number} fetched successfully!")
            else:
                # If there is no next page button, stop the scraping
                print(f"End of pagination reached. Scraping completed.")
                break
        
        # Close the browser
        browser.close()

        # Save the scraped data to a CSV file
        save_to_csv(all_scraped_data)

# Function to save the scraped data to CSV using pandas
def save_to_csv(data):
    # Convert the list of dictionaries to a pandas DataFrame
    df = pd.DataFrame(data)

    # Check if the file exists, if so, append new data, else create a new file
    try:
        # Try to load the existing data
        existing_df = pd.read_csv(output_path)
        # Append new data to the existing dataframe
        df = pd.concat([existing_df, df], ignore_index=True).drop_duplicates(subset=['title'], keep='last')
    except FileNotFoundError:
        # If the file doesn't exist, no action is taken and a new one will be created
        pass
    
    # Ensure the target directory exists
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save the DataFrame to CSV
    df.to_csv(output_path, index=False)
    
    print(f"Data saved to '{output_path}'")

# Directly call the function to start the scraping process
scrape_data()

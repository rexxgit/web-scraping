from playwright.sync_api import sync_playwright
import time
import pandas as pd
import os

def scrape_page(url):
    # Define the output directory and file path
    output_dir = 'web-scraping/ecommerce/car.csv'
    output_file = os.path.join(output_dir, 'car_listings.csv')

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Launch browser
        page = browser.new_page()

        # Set custom user agent to avoid detection
        page.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

        # Navigate to the URL
        page.goto(url)

        # Wait for the page content to load (adjust selector as needed)
        page.wait_for_selector('a.cur', timeout=10000)  # Wait for the car listings

        # Scroll to load all content (adjust number of scrolls as necessary)
        for _ in range(5):  # Adjust the number of scrolls
            page.evaluate('window.scrollBy(0, window.innerHeight);')
            time.sleep(2)  # Wait for content to load

        # Extract all car listings
        listings = page.query_selector_all('a.cur')  # Select all anchor tags containing car info

        print(f"Found {len(listings)} listings.")  # Debugging output

        # List to store the extracted data
        product_data = []

        # Loop through each listing and extract the details
        for listing in listings:
            # Extract car title
            title = listing.query_selector('div.text-sm')  # Adjust selector for car title
            title_text = title.text_content().strip() if title else 'No title found'

            # Extract car year (if present)
            year = listing.query_selector('div.text-disabled')  # Adjust selector for car year
            year_text = year.text_content().strip() if year else 'No year found'

            # Extract car price
            price = listing.query_selector('div.flex.flex-col.justify-between.bg-primary-main')  # Adjust selector for price
            price_text = price.text_content().strip() if price else 'No price found'

            # Add extracted data to the list
            product_data.append({
                'title': title_text,
                'year': year_text,
                'price': price_text
            })

        # Convert the data to a pandas DataFrame
        new_df = pd.DataFrame(product_data)

        # Check if the CSV file already exists
        if os.path.exists(output_file):
            existing_df = pd.read_csv(output_file)
            # Compare the new data with the existing data
            combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['title', 'year', 'price'], keep='last')

            # Highlight new and existing data
            combined_df['status'] = combined_df.apply(
                lambda row: 'New' if row.name >= len(existing_df) else 'Existing', axis=1
            )
        else:
            combined_df = new_df
            combined_df['status'] = 'New'

        # Save the combined data to the CSV
        combined_df.to_csv(output_file, index=False)

        # Close the browser
        browser.close()

        print(f"Scraping completed. Data saved to '{output_file}'.")

# Call the function with the URL of the page
url = 'https://www.mekina.net/cars/search?bodyType=suv'  # Replace with the actual URL
scrape_page(url)

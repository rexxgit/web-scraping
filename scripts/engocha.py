import os
import pandas as pd
import asyncio
from playwright.async_api import async_playwright

# Helper function to create the directory if it doesn't exist
def create_output_directory(output_path):
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

# Function to scrape data from a single page
async def scrape_page(page, url):
    # Navigate to the URL
    await page.goto(url)
    
    # Wait for the products to load (adjust selector based on actual site)
    await page.wait_for_selector('div.product-layout')  # Update this selector as needed
    
    # Get product data from the page
    products = await page.query_selector_all('div.product-layout')
    
    scraped_data = []
    
    for product in products:
        # Scraping the details (title, price, description, location, and link)
        title = await product.query_selector('span.listingtitle')
        price = await product.query_selector('span.price')
        description = await product.query_selector('div.smalldesc')
        location = await product.query_selector('span.location')
        link = await product.query_selector('a')

        # Extract the text or href
        title = await title.inner_text() if title else 'No title'
        price = await price.inner_text() if price else 'No price'
        description = await description.inner_text() if description else 'No description'
        location = await location.inner_text() if location else 'No location'
        link = await link.get_attribute('href') if link else 'No link'

        # Append to the data list
        scraped_data.append({
            'title': title,
            'price': price,
            'description': description,
            'location': location,
            'link': link
        })
    
    return scraped_data

# Function to scrape multiple pages and handle pagination
async def scrape_website(base_url, output_path, pages=5):
    # Create the output directory if it doesn't exist
    create_output_directory(output_path)

    # Initialize Playwright and the browser
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Set to False for debugging
        page = await browser.new_page()
        
        # Track previously scraped titles to identify new data
        if os.path.exists(output_path):
            existing_data = pd.read_csv(output_path)
            existing_titles = set(existing_data['title'])
        else:
            existing_titles = set()

        new_data = []

        # Loop through the pages
        for page_number in range(1, pages + 1):  # Adjust for more pages
            print(f"Scraping page {page_number}...")
            url = base_url.format(page=page_number)
            page_data = await scrape_page(page, url)

            # Identify new and existing data
            for product in page_data:
                if product['title'] not in existing_titles:
                    product['highlight'] = 'New'  # Mark new data
                    new_data.append(product)
                else:
                    product['highlight'] = 'Existing'  # Mark existing data

        # Combine new data with existing data if available
        all_data = pd.DataFrame(new_data)

        # If there's existing data, combine it with the new data
        if os.path.exists(output_path):
            existing_data = pd.read_csv(output_path)
            all_data = pd.concat([existing_data, all_data]).drop_duplicates(subset=['title'])

        # Save the updated data
        all_data.to_csv(output_path, index=False)
        print(f"Scraping completed. Data saved to '{output_path}'")

        # Close the browser
        await browser.close()

# Example usage for scraping with given base URL and output path
base_url = 'https://engocha.com/mobile-phones?page={page}'  # Replace with actual URL
output_path = 'web-scraping/ecommerce/engochascraped_data.csv'

# Run the scraper asynchronously (ensure to use an async event loop)
asyncio.run(scrape_website(base_url, output_path, pages=5))  # Scrape 5 pages

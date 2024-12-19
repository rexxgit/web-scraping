import os
import pandas as pd
import asyncio
from playwright.async_api import async_playwright

# Helper function to create the directory if it doesn't exist
def create_output_directory(output_path):
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

# Function to scrape data
async def scrape_page(page, url):
    # Navigate to the URL
    await page.goto(url)
    
    # Wait for the products to load
    await page.wait_for_selector('div.product-layout')  # Update this selector as needed
    
    # Get product data from the page
    products = await page.query_selector_all('div.product-layout')
    
    scraped_data = []
    
    for product in products:
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

# Main function to scrape multiple pages
async def main():
    # Base URL for the website
    base_url = 'https://engocha.com/mobile-phones?page={page}'  # Adjust to your actual URL
    output_path = 'web-scraping/ecommerce/engochascraped_data.csv'
    
    # Create the output directory if it doesn't exist
    create_output_directory(output_path)

    # Initialize Playwright
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
        
        # Loop through pages
        for page_number in range(1, 15):  # Scrape 5 pages, adjust as necessary
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

        # Combine new data with the old data if available
        all_data = pd.DataFrame(new_data)

        # If there’s existing data, combine it with the new data
        if os.path.exists(output_path):
            existing_data = pd.read_csv(output_path)
            all_data = pd.concat([existing_data, all_data]).drop_duplicates(subset=['title'])

        # Save the updated data
        all_data.to_csv(output_path, index=False)
        print(f"Scraping completed. Data saved to '{output_path}'")

        # Close the browser
        await browser.close()

# Ensure the script is run directly
if __name__ == "__main__":
    asyncio.run(main())

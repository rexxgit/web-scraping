import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

def scrape_static_site(base_url, output_file, start_page=1, max_pages=10):
    """
    Scrapes a static website for product data, handles pagination,
    and identifies new data compared to existing data.

    :param base_url: Base URL for the website with pagination parameter.
    :param output_file: Path to save the scraped data.
    :param start_page: Starting page number for scraping.
    :param max_pages: Maximum number of pages to scrape.
    """
    # Load existing data if the file exists
    existing_data = pd.read_csv(output_file) if os.path.exists(output_file) else pd.DataFrame()
    existing_links = set(existing_data['link']) if not existing_data.empty else set()

    data = []

    for page in range(start_page, max_pages + 1):
        print(f"Scraping page {page}...")
        url = f"{base_url}&page={page}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to retrieve page {page}. Skipping...")
            continue

        soup = BeautifulSoup(response.content, 'html.parser')
        products = soup.select('div.class="product-layout product-grid col-lg-4 col-md-4 col-sm-6 col-xs-12"')  # Adjust this selector to match the website structure

        if not products:
            print(f"No products found on page {page}. Stopping...")
            break

        for product in products:
            try:
                # Extract product details (adjust selectors based on website structure)
                title = product.select_one('p.desc').text.strip() if product.select_one('h4 a') else "No title"
                price = product.select_one('p.price').text.strip() if product.select_one('p.price') else "No price"
                link = product.select_one('h4 a')['href'] if product.select_one('h4 a') else "No link"

                # Skip if the link already exists in the dataset
                if link in existing_links:
                    continue

                data.append({'title': title, 'price': price, 'link': link})
            except Exception as e:
                print(f"Error processing a product: {e}")
                continue

    # Convert new data to DataFrame
    new_data = pd.DataFrame(data)

    # Combine new data with existing data, avoiding duplicates
    if not new_data.empty:
        if not existing_data.empty:
            combined_data = pd.concat([existing_data, new_data]).drop_duplicates(subset=['link'], keep='last')
        else:
            combined_data = new_data

        # Save combined data to the output file
        combined_data.to_csv(output_file, index=False)

        # Highlight new entries
        new_entries = new_data[~new_data['link'].isin(existing_links)]
        print(f"Scraping completed. {len(new_entries)} new items found and added to {output_file}.")
    else:
        print("No new data found. Existing file remains unchanged.")

# Run the scraper
scrape_static_site(
    base_url="https://helloomarket.com/index.php?route=product/category&path=99_86",
    output_file="web-scraping/ecommerce/helloomarket_products.csv",
    start_page=1,
    max_pages=10
)

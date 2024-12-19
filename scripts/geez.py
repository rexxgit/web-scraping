import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

# Headers to simulate a real browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Base URL for pagination (the page number will be replaced)
base_url = 'https://geezshop.com/page/{page}/?product_cat=electronics&s&post_type=product&et_search=true'

# List to store scraped data
data = []

# Path for the output CSV file
output_path = 'web-scraping/ecommerce/geez_product.csv'

# Load existing data if the file exists
existing_data = pd.read_csv(output_path) if os.path.exists(output_path) else pd.DataFrame()
existing_titles = set(existing_data['title']) if not existing_data.empty else set()

# Start scraping from page 1, and continue until a 404 error is encountered
page = 1
while True:
    url = base_url.format(page=page)

    # Send the HTTP request with headers
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx, 5xx)
        print(f"Page {page} fetched successfully!")
    except requests.exceptions.RequestException as e:
        # Stop if a 404 error is encountered (page doesn't exist)
        if response.status_code == 404:
            print(f"Page {page} does not exist. Stopping scrape.")
            break
        else:
            print(f"Failed to retrieve page {page}. Status code: {response.status_code} - {e}")
            page += 1
            continue

    # Parse the content of the page
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all product containers
    items = soup.find_all('div', class_='product-item')  # Update this if the class name changes

    # If no items are found on the page, stop scraping
    if not items:
        print(f"No products found on page {page}. Stopping scrape.")
        break

    # Loop through each product and extract details
    for item in items:
        # Extract title
        title_tag = item.find('h2', class_='product-title')
        title = title_tag.get_text(strip=True) if title_tag else 'No title found'

        # Extract price
        price_tag = item.find('span', class_='price')
        price = price_tag.get_text(strip=True) if price_tag else 'No price found'

        # Extract product link
        link_tag = item.find('a', href=True)
        link = link_tag['href'] if link_tag else 'No link found'

        # Check if this product is already in the existing data
        highlight = 'new' if title not in existing_titles else 'existing'

        # Append data to the list
        data.append({
            'title': title,
            'price': price,
            'link': link,
            'highlight': highlight
        })

    # Move to the next page
    page += 1

# Check if data was extracted before proceeding
if len(data) == 0:
    print("No products found.")
    exit()  # Exit the script if no products are found

# Convert the list of data into a DataFrame
df = pd.DataFrame(data)

# Ensure the target directory exists
output_dir = os.path.dirname(output_path)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Save the data to a CSV file, keeping existing data and adding new
if not existing_data.empty:
    # Merge new data with existing data, ensuring no duplicate titles
    df = pd.concat([existing_data, df]).drop_duplicates(subset=['title'], keep='last')

# Save to CSV
df.to_csv(output_path, index=False)

print(f"Scraping completed and data saved to '{output_path}'")

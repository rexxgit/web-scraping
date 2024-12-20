import os
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Base URL for pagination (adjust for your site)
base_url = 'https://engocha.com/classifieds/38-mens-shoes/condition_all/brand_NIKE/city_all/minprice_zr/maxprice_in/currency_df?page={}'

# Headers to simulate a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# List to store the product data
product_data = []

# Starting page for scraping
page = 1

# Function to get text from a tag
def get_text(tag):
    return tag.get_text(strip=True) if tag else 'No data found'

# Start scraping with pagination
while True:
    print(f"\nFetching page {page}...")
    url = base_url.format(page)
    response = requests.get(url, headers=headers)

    # Check if the page is successfully fetched
    if response.status_code != 200:
        print(f"Failed to retrieve page {page}. Status code: {response.status_code}")
        break

    # Parse the content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Use CSS selector to target the main container
    main_container = soup.find('div', id='listingslist')

    if not main_container:
        print("Main container not found. Stopping pagination.")
        break

    # Find all individual product containers inside the main container
    products = main_container.find_all('div', class_='listingcolumn')

    if not products:
        print("No products found on this page. Stopping pagination.")
        break

    # Loop through each product and extract details
    for product in products:
        # Extract product details
        title = get_text(product.find('span', class_='listingtitle'))
        price = get_text(product.find('span', class_='price'))
        location = get_text(product.find('span', class_='location'))
        link_tag = product.find('a', href=True)
        link = link_tag['href'] if link_tag else 'No link found'

        # Append extracted data
        product_data.append({
            'title': title,
            'price': price,
            'location': location,
            'link': link
        })

    # Move to the next page
    page += 1

# Convert collected data into a DataFrame
df = pd.DataFrame(product_data)

# Specify the output file path
output_file = 'web-scraping/ecommerce/please.csv'

# Check if the file already exists
if os.path.exists(output_file):
    existing_df = pd.read_csv(output_file)

    # Merge new data with existing data
    merged_df = pd.concat([existing_df, df]).drop_duplicates(subset=['link'], keep='last')

    # Add a column to highlight new and existing data
    merged_df['status'] = ['New' if link not in existing_df['link'].values else 'Existing' 
                           for link in merged_df['link']]

    # Save the updated data back to the file
    merged_df.to_csv(output_file, index=False)
    print(f"Data updated in '{output_file}' with highlights for new and existing entries.")
else:
    # Save new data and mark all as 'New'
    df['status'] = 'New'
    df.to_csv(output_file, index=False)
    print(f"Data saved to '{output_file}' for the first time, all entries marked as 'New'.")

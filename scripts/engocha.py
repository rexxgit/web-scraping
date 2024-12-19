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

# Output path for the CSV file
output_path = 'web-scraping/ecommerce/engocha.csv'

# Check if the file exists already
if os.path.exists(output_path):
    existing_df = pd.read_csv(output_path)
else:
    existing_df = pd.DataFrame()

# List to store the product data
product_data = []

# Starting page for scraping
page = 1

# Function to get text from a tag
def get_text(tag):
    if tag:
        return tag.get_text(strip=True)
    return 'No data found'

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
    main_container = soup.find('div', id='listingslist')  # Replace with your specific container ID if needed

    # Print the entire main container to check its structure
    if main_container:
        print("\nMain container HTML:\n", main_container)  # No prettify(), raw HTML will be printed
    else:
        print("Main container not found. Exiting...")
        break

    # Find all individual product containers inside the main container
    products = main_container.find_all('div', class_='listingcolumn')

    # If no products are found, exit pagination
    if not products:
        print("No products found on this page. Stopping pagination.")
        break

    # Loop through each product and extract details
    for index, product in enumerate(products, start=1):
        print(f"\nHTML for product {index} on page {page}:\n")
        print(product)  # Raw HTML for each product

        # Extract the product title, price, location, and link
        title_tag = product.find('span', class_='listingtitle')
        title = get_text(title_tag)

        price_tag = product.find('span', class_='price')
        price = get_text(price_tag)

        location_tag = product.find('span', class_='location')
        location = get_text(location_tag)

        # Extract the product link
        link_tag = product.find('a', href=True)
        link = link_tag['href'] if link_tag else 'No link found'

        # Append the extracted data to the list
        product_data.append({
            'title': title,
            'price': price,
            'location': location,
            'link': link
        })

    # Move to the next page
    page += 1

# Convert the collected data into a DataFrame
new_df = pd.DataFrame(product_data)

# Check for new and existing data
if not existing_df.empty:
    # Combine the existing data with the new data and remove duplicates
    combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['title', 'price', 'location', 'link'], keep='last')
    
    # Highlight new and existing data
    new_entries = new_df[~new_df['title'].isin(existing_df['title'])]
    if not new_entries.empty:
        print("\nNew data entries found:")
        print(new_entries)

    # Append new data entries to the CSV
    combined_df.to_csv(output_path, index=False)
    print(f"\nNew data saved to {output_path}")
else:
    # Save the new data directly to the CSV file if no existing data
    new_df.to_csv(output_path, index=False)
    print(f"\nData saved to {output_path}")

# Print a confirmation message
print("\nScraping completed and data saved.")

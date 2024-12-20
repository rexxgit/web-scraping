import os
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Base URL for pagination
base_url = 'https://engocha.com/classifieds/34-laptops/condition_all/brand_HP/city_all/minprice_zr/maxprice_in/currency_df?page={}'

# Headers to simulate a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Output path for the CSV file
output_path = 'web-scraping/ecommerce/engocha.csv'

# Ensure the output directory exists
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# Check if the CSV file exists and is not empty
if not os.path.exists(output_path) or os.stat(output_path).st_size == 0:
    existing_df = pd.DataFrame(columns=['title', 'price', 'location', 'link'])
    existing_df.to_csv(output_path, index=False)
    print(f"Created new CSV file with headers: {output_path}")
else:
    existing_df = pd.read_csv(output_path)

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

    # Print the HTML structure of the page
    print("\nHTML Structure of the page:")
    print(response.text[:1000])  # Print the first 1000 characters of the HTML for brevity

    # Parse the content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Use CSS selector to target the main container
    main_container = soup.find('div', id='listingslist')

    # Check if the main container is found
    if not main_container:
        print("Main container not found. Exiting...")
        break

    # Find all individual product containers inside the main container
    products = main_container.find_all('div', class_='listingcolumn')

    # If no products are found, exit pagination
    if not products:
        print("No products found on this page. Stopping pagination.")
        break

    # Loop through each product and extract details
    for product in products:
        # Extract the product title, price, location, and link
        title = get_text(product.find('span', class_='listingtitle'))
        price = get_text(product.find('span', class_='price'))
        location = get_text(product.find('span', class_='location'))
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

# Combine with existing data and remove duplicates
combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['title', 'price', 'location', 'link'], keep='last')

# Highlight new entries
new_entries = combined_df[~combined_df['title'].isin(existing_df['title'])]
if not new_entries.empty:
    print("\nNew entries found:")
    print(new_entries)

# Save the combined data to the CSV file
combined_df.to_csv(output_path, index=False)
print(f"\nData saved to {output_path}")

# Print a confirmation message
print("\nScraping completed.")

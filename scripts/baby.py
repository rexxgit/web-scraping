import os
import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL of the eCommerce product category page
url = 'https://babyshopet.com/shoes/'

# Define headers to simulate a real browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Send HTTP request to fetch the page content with headers
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    print("Page fetched successfully!")
else:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")
    exit()

# Parse the content of the page using BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

# Find all product containers
products = soup.find_all('li', class_='product')

# Initialize an empty list to store product data
product_data = []

# Loop through each product and extract details
for product in products:
    title_tag = product.find('h2', class_='woocommerce-loop-product__title')
    title = title_tag.text.strip() if title_tag else 'No title found'

    price_tag = product.find('span', class_='price')
    price = price_tag.text.strip() if price_tag else 'No price found'

    link_tag = product.find('a', href=True)
    link = link_tag['href'] if link_tag else 'No link found'

    product_data.append({
        'title': title,
        'price': price,
        'link': link
    })

# Convert the list of product data into a pandas DataFrame
df = pd.DataFrame(product_data)

# Specify the output file path
output_file = 'web-scraping/ecommerce/baby.csv'
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

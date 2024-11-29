import os
import pandas as pd
from requests import get
from bs4 import BeautifulSoup

# URL of the page to scrape
url = 'https://addisber.com/product-category/food-items/instant-foods/'

# Define headers to simulate a real browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Send the HTTP request with the headers
response = get(url, headers=headers)

# Check if the request was successful
if response.status_code != 200:
    print(f"Failed to retrieve the page: {response.status_code}")
    exit()

# Parse the content of the page using BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

# Find all product containers (you may need to adjust this based on your page structure)
products = soup.find_all('li', class_='product')

# List to store product details
new_data = []

# Loop through each product and extract details
for product in products:
    # Extract product title (updated to <h3> tag)
    title_tag = product.find('h3', class_='woocommerce-loop-product__title')
    title = title_tag.text.strip() if title_tag else 'No title found'
    
    # Extract price
    price_tag = product.find('span', class_='price')
    price = price_tag.text.strip() if price_tag else 'No price found'
    
    # Extract product link (URL)
    link_tag = product.find('a', href=True)
    link = link_tag['href'] if link_tag else 'No link found'
    
    # Append extracted data to the list
    new_data.append({
        'title': title,
        'price': price,
        'link': link
    })

# Check if the data was successfully scraped
if not new_data:
    print("No products found.")
    exit()

# Convert the list of new data into a DataFrame
new_df = pd.DataFrame(new_data)

# Create the filename based on the URL
category_name = 'food-items'
sub_category_name = 'instant-foods'
filename = f'addisber.com({category_name},{sub_category_name}).csv'

# Check if the output file already exists in the 'web-scraping/ecommerce/' directory
output_path = f'web-scraping/ecommerce/{filename}'

# If the file exists, compare it with the new data
if os.path.exists(output_path):
    old_df = pd.read_csv(output_path)
    # Compare the new data with the existing data
    if not new_df.equals(old_df):
        print("Website has updated, updating the output file.")
        new_df.to_csv(output_path, index=False)
    else:
        print("No updates detected. The file remains the same.")
else:
    # If the file doesn't exist, create it
    print("Creating new output file with scraped data.")
    new_df.to_csv(output_path, index=False)

print(f"Scraping completed. Data saved to {output_path}")

import requests
from bs4 import BeautifulSoup
import pandas as pd
import os  # To handle directory creation

# URL of the page to scrape
url = 'https://addisber.com/product-category/food-items/instant-foods/'

# Define headers to simulate a real browser request (to avoid anti-scraping measures)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Send the HTTP request with the headers
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # This will raise an exception for HTTP errors (4xx, 5xx)
    print("Request successful!")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
    exit()  # Exit the script if the request fails

# Parse the content of the page using BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

# Find all product containers (update the class based on the page structure)
products = soup.find_all('li', class_='product')

# List to store product details
product_data = []

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
    product_data.append({
        'title': title,
        'price': price,
        'link': link
    })

# Check if data was extracted before proceeding
if len(product_data) == 0:
    print("No products found on the page.")
    exit()  # Exit the script if no products are found

# Convert the list of product data into a DataFrame
df = pd.DataFrame(product_data)

# Define the path for the output CSV file
output_path = 'web-scraping/ecommerce/addisber.com_food-items_instant-foods.csv'

# Ensure the target directory exists, create it if it doesn't
output_dir = os.path.dirname(output_path)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Save the data to a CSV file
df.to_csv(output_path, index=False)

print(f"Scraping completed and data saved to '{output_path}'")

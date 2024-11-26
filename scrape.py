import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

# URL of the eCommerce product category page
url = 'https://addisber.com/product-category/party-items/birthday-beauty-accessories/'

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

# Find all product containers (typically <li> or <div> tags with class 'product')
products = soup.find_all('li', class_='product')

# Initialize an empty list to store product data
product_data = []

# Loop through each product and extract details
for product in products:
    # Extract the product name
    title_tag = product.find('h3', class_='woocommerce-loop-product__title')
    title = title_tag.text.strip() if title_tag else 'No title found'

    # Extract the product price
    price_tag = product.find('span', class_='price')
    price = price_tag.text.strip() if price_tag else 'No price found'

    # Extract the product URL
    link_tag = product.find('a', href=True)
    link = link_tag['href'] if link_tag else 'No link found'

    # Append the extracted data to the product_data list
    product_data.append({
        'title': title,
        'price': price,
        'link': link
    })

# Create the 'ecommerce' folder if it doesn't exist
os.makedirs('./ecommerce', exist_ok=True)

# Convert the list of product data into a pandas DataFrame
df = pd.DataFrame(product_data)

# Define the output CSV path inside the 'ecommerce' folder
output_csv_path = './ecommerce/output.csv'

# Save the data to a CSV file
df.to_csv(output_csv_path, index=False)

# Print a confirmation message
print(f"CSV saved to {output_csv_path}")

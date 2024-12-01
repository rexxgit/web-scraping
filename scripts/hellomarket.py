import requests
from bs4 import BeautifulSoup
import pandas as pd
import os  # To handle directory creation

# Define the URL of the page to scrape
url = 'https://helloomarket.com/index.php?route=product/category&path=82'

# Define headers to simulate a real browser request (to avoid anti-scraping measures)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Send the HTTP request with the headers
response = requests.get(url, headers=headers)

# Check if the page was fetched successfully
if response.status_code == 200:
    print("Page fetched successfully")
else:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")
    exit()  # Exit the script if the request fails

# Parse the content of the page using BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

# Find all product containers on the page (adjust the class as necessary)
products = soup.find_all('div', class_='product-layout product-list col-xs-12')

# Initialize a list to store product data
product_data = []

# Loop through each product and extract details
for product in products:
    # Extract product link
    link_tag = product.find('a', href=True)
    link = link_tag['href'] if link_tag else 'no link'
    
    # Extract product price
    price_tag = product.find('p', class_='price')
    price = price_tag.text.strip() if price_tag else 'no price'
    
    # Extract product description
    description_tag = product.find('p', class_='desc')
    description = description_tag.text.strip() if description_tag else 'no description'
    
    # Append the extracted data to the list
    product_data.append({
        'link': link,
        'price': price,
        'description': description,
    })

# Check if data was successfully extracted
if not product_data:
    print("No products found on the page.")
    exit()  # Exit the script if no products were found

# Convert the list of product data into a DataFrame
df = pd.DataFrame(product_data)

# Define the path for the output CSV file
output_path = 'web-scraping/ecommerce/hellomarket.csv'

# Ensure the target directory exists, create it if necessary
output_dir = os.path.dirname(output_path)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Save the data to a CSV file
df.to_csv(output_path, index=False)

print(f"Scraping completed and data saved to '{output_path}'")

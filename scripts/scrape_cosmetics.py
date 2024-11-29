import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL of the page to scrape
url = 'https://addisber.com/product-category/cosmetics/hair-care/'

# Define headers to simulate a real browser request (to avoid anti-scraping measures)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Send the HTTP request with the headers
response = requests.get(url, headers=headers)
if response.status_code == 200:
    print("Page fetched successfully")
else:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")

# Parse the content of the page using BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

# List to store product details
data = []

# Find all product containers
products = soup.find_all('div', class_='product-inner')

# Loop through each product and extract details
for product in products:
    # Extract product title
    title_tag = product.find('h3', class_='woocommerce-loop-product__title')
    title = title_tag.text.strip() if title_tag else 'No title found'
    
    # Extract price
    price_tag = product.find('span', class_='price')
    price = price_tag.text.strip() if price_tag else 'No price found'
    
    # Extract product link (URL)
    link_tag = product.find('a', href=True)
    link = link_tag['href'] if link_tag else 'No link found'
    
    # Append extracted data to the list
    data.append({
        'title': title,
        'price': price,
        'link': link
    })

# Convert the list of product data into a DataFrame
df = pd.DataFrame(data)

# Save the data to a CSV file in the ecommerce folder
output_path = 'web-scraping/ecommerce/addisber_cosmetics_hair_care.csv'
df.to_csv(output_path, index=False)

print(f"Scraping completed and data saved to {output_path}")

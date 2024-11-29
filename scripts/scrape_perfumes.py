import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

# URL of the page to scrape
url = 'https://addisber.com/product-category/cosmetics/perfumes/'

# Define headers to simulate a real browser request (to avoid anti-scraping measures)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Send the HTTP request
response = requests.get(url, headers=headers)
if response.status_code == 200:
    print("Page fetched successfully")
else:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")
    exit()

# Parse the content of the page
soup = BeautifulSoup(response.text, 'html.parser')
data = []

# Find all products
products = soup.find_all('div', class_='product-inner')
for product in products:
    title_tag = product.find('h3', class_='woocommerce-loop-product__title')
    title = title_tag.text.strip() if title_tag else 'No title found'
    
    price_tag = product.find('span', class_='price')
    price = price_tag.text.strip() if price_tag else 'No price found'
    
    link_tag = product.find('a', href=True)
    link = link_tag['href'] if link_tag else 'No link found'
    
    data.append({
        'title': title,
        'price': price,
        'link': link
    })

# Create DataFrame
df = pd.DataFrame(data)

# Define the output path in the ecommerce directory
output_dir = 'web-scraping/ecommerce/'
output_file = 'addisber_com_cosmetics_perfumes.csv'

# Ensure the directory exists
os.makedirs(output_dir, exist_ok=True)

# Save the data to a CSV file in the correct directory
df.to_csv(os.path.join(output_dir, output_file), index=False)

print("Scraping completed and data saved.")

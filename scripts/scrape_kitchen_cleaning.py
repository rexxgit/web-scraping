import requests
from bs4 import BeautifulSoup
import pandas as pd

# Headers to simulate a real browser request (to avoid anti-scraping measures)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Base URL of the page to scrape
base_url = 'https://addisber.com/product-category/cleaning-sanitary/kitchen-cleaning-products/page/{page}/'

# List to store product data
data = []

# Loop through pages (update range if you need more pages)
for page in range(1, 2):
    url = base_url.format(page=page)
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('div', class_='product-inner')

        for item in items:
            # Extract product details
            title_tag = item.find('h3', class_='woocommerce-loop-product__title')
            title = title_tag.text.strip() if title_tag else 'Title not found'

            price_tag = item.find('span', class_='price')
            price = price_tag.text.strip() if price_tag else 'No price found'

            link_tag = item.find('a', href=True)
            link = link_tag['href'] if link_tag else 'No link found'

            # Append to the data list
            data.append({
                'title': title,
                'price': price,
                'link': link
            })

        print(f"Page {page} fetched successfully")
    else:
        print(f"Failed to retrieve page {page}. Status code: {response.status_code}")

# Convert data to a DataFrame and save as CSV in the desired directory
df = pd.DataFrame(data)
output_path = 'web-scraping/ecommerce/kitchen_cleaning_products.csv'  # Update path to where you want to save it
df.to_csv(output_path, index=False)

print(f"Scraping completed and data saved to {output_path}")

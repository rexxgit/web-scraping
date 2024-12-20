import requests
from bs4 import BeautifulSoup
import pandas as pd
from fake_useragent import UserAgent

# Install fake_useragent if not already installed
# pip install fake-useragent

# URL of the target page
url = 'https://engocha.com/classifieds/38-mens-shoes/condition_all/brand_NIKE/city_all/minprice_zr/maxprice_in/currency_df'

# Initialize a UserAgent instance
ua = UserAgent()

# Generate a random User-Agent
headers = {
    'User-Agent': ua.random
}

# List to store product data
product_data = []

# Function to get text from a tag
def get_text(tag):
    return tag.get_text(strip=True) if tag else 'No data found'

# Fetch the webpage
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    print("Page fetched successfully!")
    # Parse the content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the main container
    main_container = soup.find('div', id='listingslist')
    if not main_container:
        print("Main container not found.")
    else:
        # Find all product containers inside the main container
        products = main_container.find_all('div', class_='listingcolumn')
        if not products:
            print("No products found.")
        else:
            # Extract details for each product
            for product in products:
                title_tag = product.find('span', class_='listingtitle')
                price_tag = product.find('span', class_='price')
                location_tag = product.find('span', class_='location')
                link_tag = product.find('a', href=True)

                product_data.append({
                    'title': get_text(title_tag),
                    'price': get_text(price_tag),
                    'location': get_text(location_tag),
                    'link': link_tag['href'] if link_tag else 'No link found'
                })

            # Save the data to a CSV file
            output_path = 'web-scraping/ecommerce/please.csv'
            df = pd.DataFrame(product_data)
            df.to_csv(output_path, index=False)
            print(f"Scraping completed and data saved to '{output_path}'")
else:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")

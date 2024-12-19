import requests
import pandas as pd
from bs4 import BeautifulSoup
import os

# Function to scrape a page and extract product details
def scrape_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    products = []
    # Extract product title, price, and link
    for product in soup.find_all('li', class_='product'):
        title = product.find('h2', class_='product-title')
        price = product.find('span', class_='price')
        link = product.find('a', href=True)

        if title and price and link:
            products.append({
                'title': title.get_text(strip=True),
                'price': price.get_text(strip=True),
                'link': link['href']
            })
    
    return products

# Function to check for new data
def check_for_new_data(products, output_path):
    # Load existing data if CSV file exists
    if os.path.exists(output_path):
        existing_data = pd.read_csv(output_path)
        existing_titles = set(existing_data['title'])
    else:
        existing_data = pd.DataFrame(columns=['title', 'price', 'link', 'status'])
        existing_titles = set()

    # Compare new products with existing ones
    new_data = []
    for product in products:
        if product['title'] not in existing_titles:
            new_data.append({**product, 'status': 'new'})
        else:
            new_data.append({**product, 'status': 'existing'})
    
    # Convert new data to a DataFrame
    new_df = pd.DataFrame(new_data)
    
    return new_df

# Function to save data to CSV
def save_data(products, output_path):
    # If file exists, append new data; otherwise, create the file
    if os.path.exists(output_path):
        products.to_csv(output_path, mode='a', header=False, index=False)
    else:
        products.to_csv(output_path, mode='w', header=True, index=False)

# Main function to scrape multiple pages and save data
def scrape_and_save(start_page, end_page, output_path):
    for page_num in range(start_page, end_page + 1):
        url = f'https://geezshop.com/page/{page_num}/?product_cat=electronics&s&post_type=product&et_search=true'
        print(f'Scraping page {page_num}...')
        
        # Scrape the page and get the product data
        products = scrape_page(url)
        new_data_df = check_for_new_data(products, output_path)
        
        # Save the new data to the CSV
        save_data(new_data_df, output_path)
        print(f'Saved data from page {page_num}.')

# Example usage: scrape pages 2 to 5 and save to 'geez_elco.csv' in the specified path
output_path = 'web-scraping/ecommerce/geez_elco.csv'
scrape_and_save(2, 5, output_path)

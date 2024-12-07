import requests
from bs4 import BeautifulSoup
import pandas as pd
import os  # To ensure the output directory exists

# Set headers to mimic a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Base URL with pagination (this will be filled in with page numbers later)
base_url = 'https://dagicomputers.com/product-category/hp/page/{page}/'

# List to store the product data
data = []

# Loop through pages 1 to 19
for page in range(1, 20):  # Assuming there are 19 pages. Adjust if needed.
    url = base_url.format(page=page)
    
    # Fetch the page content
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print(f"Page {page} fetched successfully")
        
        # Parse the page content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all product items on the page
        laptops = soup.find_all('li', class_='product')
        
        # Loop through each laptop product and extract details
        for laptop in laptops:
            title = laptop.find('h2', class_='woo-loop-product__title').get_text(strip=True)
            price = laptop.find('span', class_='woocommerce-Price-amount').get_text(strip=True)
            link = laptop.find('a', href=True)['href']
            
            # Append the product data to the list
            data.append({
                'title': title,
                'price': price,
                'link': link,
            })
    else:
        print(f"Failed to retrieve page {page}. Status code: {response.status_code}")

# Convert the data to a DataFrame
df_new = pd.DataFrame(data)

# Ensure the output directory exists
output_dir = 'web-scraping/ecommerce/'
os.makedirs(output_dir, exist_ok=True)

# Path to the existing CSV file (if it exists)
output_path = os.path.join(output_dir, 'dagi_laptops_multiple_pages.csv')

# Check if the file already exists
if os.path.exists(output_path):
    # Read the existing data
    df_existing = pd.read_csv(output_path)
    
    # Mark new rows with an additional 'highlight' column
    # Compare the new data with the existing one, marking new rows as "New"
    df_new['highlight'] = df_new.apply(lambda row: 'New' if not any(
        df_existing['link'] == row['link']) else 'Existing', axis=1)

    # Concatenate the new data with the existing data
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    
    # Remove duplicate entries based on the product link (if any)
    df_combined = df_combined.drop_duplicates(subset='link', keep='last')
else:
    # If no file exists, just use the new data
    df_new['highlight'] = 'New'  # Mark all rows as new
    df_combined = df_new

# Save the combined data to the CSV file
df_combined.to_csv(output_path, index=False)

print(f"Scraping completed and data saved to '{output_path}'")

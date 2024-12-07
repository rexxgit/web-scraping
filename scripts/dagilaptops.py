import requests
from bs4 import BeautifulSoup
import pandas as pd
import os  # To ensure the output directory exists

# Set headers to mimic a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# URL of the page to scrape
url = 'https://dagicomputers.com/product-category/hp/'

# Send a GET request to fetch the HTML page
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    print("Page fetched successfully")
else:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")
    exit()

# Parse the HTML content with BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

# Find all product items using a more general class (col-xs-6, product, etc.)
laptops = soup.find_all('li', class_='product')

# If no products are found, print a message
if len(laptops) == 0:
    print("No products found!")
    exit()

# List to store the scraped data
laptop_data = []

# Loop through each laptop item and extract relevant data
for laptop in laptops:
    # Extract product title (use 'h2' with class 'woo-loop-product__title' or another relevant tag)
    title_tag = laptop.find('h2', class_='woo-loop-product__title')
    title = title_tag.text.strip() if title_tag else 'No title found'
    
    # Extract product price (use 'span' with class 'woocommerce-Price-amount')
    price_tag = laptop.find('span', class_='woocommerce-Price-amount')
    price = price_tag.text.strip() if price_tag else 'No price found'
    
    # Extract product link (use the 'a' tag)
    link_tag = laptop.find('a', href=True)
    link = link_tag['href'] if link_tag else 'No link found'
    
    # Append the extracted data to the list
    laptop_data.append({
        'title': title,
        'price': price,
        'link': link
    })

# Convert the list of dictionaries to a DataFrame
df = pd.DataFrame(laptop_data)

# Define the output directory and file path
output_dir = 'web-scraping/ecommerce/'
os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists

# Define the full path to save the CSV
output_file_path = os.path.join(output_dir, 'dagi_laptops.csv')

# Check if the file already exists (i.e., this is not the first time running the scraper)
if os.path.exists(output_file_path):
    # Load the previous CSV data
    previous_df = pd.read_csv(output_file_path)
    
    # Merge the previous and current DataFrames on the 'link' column to detect changes
    merged_df = pd.merge(previous_df, df, on='link', how='right', suffixes=('_old', '_new'), indicator=True)

    # Initialize the 'highlight' column
    merged_df['highlight'] = 'New'  # By default, all rows are considered new

    # Mark rows as 'Updated' if there's a difference in the price or title
    merged_df['highlight'] = merged_df.apply(
        lambda row: 'Updated' if row['_merge'] == 'both' and (row['price_old'] != row['price_new'] or row['title_old'] != row['title_new']) else row['highlight'],
        axis=1
    )

    # Remove the merged columns that are not needed
    final_df = merged_df.drop(columns=['_merge', 'price_old', 'title_old', 'price_new', 'title_new'])

else:
    # If the CSV doesn't exist, it's the first time running the scraper, so all rows are new
    final_df = df
    final_df['highlight'] = 'New'

# Save the updated data with the 'highlight' column
final_df.to_csv(output_file_path, index=False)

print(f"Scraping completed and data saved to '{output_file_path}'")

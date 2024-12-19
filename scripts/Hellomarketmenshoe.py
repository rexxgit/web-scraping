import requests
from bs4 import BeautifulSoup
import pandas as pd
import os  # To handle directory creation

# Headers to simulate a real browser request (to avoid anti-scraping measures)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Base URL for pagination (adjust page parameter as necessary)
base_url = 'https://helloomarket.com/index.php?route=product/category&path=99_86&page={page}'

# List to store scraped data
data = []

# Path for the output CSV file
output_path = 'web-scraping/ecommerce/hellomarketyes.csv'

# Load existing data if the file exists
existing_data = pd.read_csv(output_path) if os.path.exists(output_path) else pd.DataFrame()
existing_titles = set(existing_data['title']) if not existing_data.empty else set()

# Loop through the pages
for page in range(1, 10):  # Change the range for more pages if necessary
    url = base_url.format(page=page)
    
    # Send the HTTP request with headers
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx, 5xx)
        print(f"Page {page} fetched successfully!")
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve page {page}. Status code: {response.status_code} - {e}")
        continue  # Skip this page and continue to the next one

    # Parse the content of the page
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all product containers
    items = soup.find_all('div', class_='product-layout product-list col-xs-12')
    
    # Loop through each product and extract details
    for item in items:
        # Extract title
        title = item.find('a', href=True)['href'] if item.find('a', href=True) else 'No title found'
        
        # Extract price
        price = item.find('p', class_='price').get_text(strip=True) if item.find('p', class_='price') else 'No price found'
        
        # Extract description
        description = item.find('p', class_='desc').get_text(strip=True) if item.find('p', class_='desc') else 'No description found'
        
        # Check if this product is already in the existing data
        highlight = 'new' if title not in existing_titles else 'existing'
        
        # Append data to the list
        data.append({
            'title': title,
            'price': price,
            'description': description,
            'highlight': highlight
        })

# Check if data was extracted before proceeding
if len(data) == 0:
    print("No products found on the page.")
    exit()  # Exit the script if no products are found

# Convert the list of data into a DataFrame
df = pd.DataFrame(data)

# Ensure the target directory exists
output_dir = os.path.dirname(output_path)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Save the data to a CSV file, keeping existing data and adding new
if not existing_data.empty:
    # Merge new data with existing data
    df = pd.concat([existing_data, df]).drop_duplicates(subset=['title'], keep='last')

# Save to CSV
df.to_csv(output_path, index=False)

print(f"Scraping completed and data saved to '{output_path}'")

import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from github import Github

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
    # Extract the product name (assuming it's inside an <h3> tag with class 'woocommerce-loop-product__title')
    title_tag = product.find('h3', class_='woocommerce-loop-product__title')
    title = title_tag.text.strip() if title_tag else 'No title found'

    # Extract the product price (assuming it's inside a <span> tag with class 'price')
    price_tag = product.find('span', class_='price')
    price = price_tag.text.strip() if price_tag else 'No price found'

    # Extract the product URL (assuming the product link is inside an <a> tag)
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

# Optionally: Push the result to GitHub (if you want to upload the CSV to your private repository)
# Use the PAT from environment variable to authenticate with GitHub API
pat = os.getenv('MY_PAT')

if pat:
    try:
        # Authenticate with GitHub using the PAT
        g = Github(pat)
        repo = g.get_repo('rexxgit/web-scraping')  # Your username and repository
        file_path = 'ecommerce/output.csv'
        
        # Try to upload the file to the repository (you can modify this part based on your requirements)
        with open(output_csv_path, 'r') as file:
            content = file.read()
        
        try:
            # Try to update the file if it exists
            existing_file = repo.get_contents(file_path)
            repo.update_file(existing_file.path, 'Update product data', content, existing_file.sha)
            print(f"File updated in the repository: {file_path}")
        except:
            # If the file does not exist, create it
            repo.create_file(file_path, 'Add product data', content)
            print(f"File created in the repository: {file_path}")
    
    except Exception as e:
        print(f"Error uploading to GitHub: {e}")

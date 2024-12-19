import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

def scrape_static_website():
    base_url = "https://addisber.com/product-category/food-items/beverage/page/1/"  # Replace with your target URL
    page_number = 1

    # Initialize an empty DataFrame to hold the scraped data
    data = []

    while True:
        print(f"Scraping page {page_number}...")
        url = f"{base_url}{page_number}"
        response = requests.get(url)
        
        # Check if the page is accessible
        if response.status_code != 200:
            print(f"Failed to load page {page_number}. Status code: {response.status_code}")
            break

        soup = BeautifulSoup(response.content, "html.parser")

        # Extract items (adjust selectors as needed)
        items = soup.select("div.product-inner")  # Replace with the appropriate selector for your target website

        if not items:
            print("No more items found. Ending scraping.")
            break

        for item in items:
            try:
                # Extract data
                title_elem = item.select_one("h3.woocommerce-loop-product__title")
                price_elem = item.select_one("small.woocommerce-price-suffix")
                link_elem = item.select_one("a")

                title = title_elem.get_text(strip=True) if title_elem else "No title"
                price = price_elem.get_text(strip=True) if price_elem else "No price"
                link = link_elem["href"] if link_elem and link_elem.has_attr("href") else "No link"

                data.append({
                    "title": title,
                    "price": price,
                    "link": link
                })
            except Exception as e:
                print(f"Error extracting item: {e}")
                continue

        # Check for the next page
        next_button = soup.select_one("a.next.page-numbers")  # Adjust selector for your site
        if next_button and next_button.has_attr("href"):
            page_number += 1
        else:
            print("No more pages found. Scraping complete.")
            break

    # Convert new data to DataFrame
    new_data = pd.DataFrame(data)

    # If the CSV file exists, load it and append new data
    ecommerce_folder = "web-scraping/ecommerce"  # Path to the ecommerce folder
    file_path = os.path.join(ecommerce_folder, "Addis_ber.csv")
    
    # Create the ecommerce folder if it doesn't exist
    if not os.path.exists(ecommerce_folder):
        os.makedirs(ecommerce_folder)

    if os.path.exists(file_path):
        existing_data = pd.read_csv(file_path)
        merged_data = pd.concat([existing_data, new_data]).drop_duplicates(subset=["link"], keep="last")
    else:
        merged_data = new_data

    # Save the merged data to CSV
    merged_data.to_csv(file_path, index=False)
    print(f"Scraping completed successfully. {len(new_data)} new items added. Data saved to '{file_path}'.")

scrape_static_website()

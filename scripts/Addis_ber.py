import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

def scrape_static_website(base_url, output_folder="web-scraping/ecommerce", output_file="Addisber_educational-entertainment-items.csv"):
    page_number = 1
    data = []

    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Define the file path where the data will be saved
    file_path = os.path.join(output_folder, output_file)

    # Define the headers with a user-agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    while True:
        print(f"Scraping page {page_number}...")
        url = f"{base_url}{page_number}/?s&post_type=product&product_cat=educational-entertainment-items"  # Construct the URL for pagination
        response = requests.get(url, headers=headers)  # Include the headers in the request
        
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
                price_elem = item.select_one("span.price")
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

        # Check for the next page by looking for the next "a.page-numbers" that doesn't have the "current" class
        next_button = soup.select_one("a.page-numbers:not(.current)")
        if next_button and next_button.has_attr("href"):
            page_number += 1
        else:
            print("No more pages found. Scraping complete.")
            break

    # Convert new data to DataFrame
    new_data = pd.DataFrame(data)

    # If the CSV file exists, load it and append new data
    if os.path.exists(file_path):
        existing_data = pd.read_csv(file_path)
        
        # Merge new data with existing data
        merged_data = pd.concat([existing_data, new_data]).drop_duplicates(subset=["link"], keep="last")

        # Identify new entries
        new_entries = merged_data[~merged_data["link"].isin(existing_data["link"])]
        
        # Classify new or existing items
        merged_data['status'] = merged_data['link'].apply(lambda x: 'new' if x in new_entries['link'].values else 'existing')

        if not new_entries.empty:
            print(f"New data added: {len(new_entries)} items.")
        else:
            print("No new items found.")
        
    else:
        merged_data = new_data
        merged_data['status'] = 'new'  # Mark all as new since it's the first scrape
        print(f"First-time scraping. {len(new_data)} items saved.")

    # Save the merged data to CSV
    merged_data.to_csv(file_path, index=False)
    print(f"Scraping completed successfully. Data saved to '{file_path}'.")

# Example Usage:
base_url = "https://addisber.com/page/1/?s&post_type=product&product_cat=educational-entertainment-items"
scrape_static_website(base_url)

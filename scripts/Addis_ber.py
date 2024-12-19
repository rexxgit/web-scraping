import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

def scrape_static_website():
    base_url = "https://addisber.com/product-category/food-items/beverage/page/1/"  # Replace with your target URL
    page_number = 1

    # Load existing data if available
    existing_data = pd.read_csv("Addis_ber.csv") if os.path.exists("Addis_ber.csv") else pd.DataFrame()
    existing_links = set(existing_data['link']) if not existing_data.empty else set()

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

                # Skip duplicates
                if link in existing_links:
                    continue

                data.append({
                    "title": title,
                    "price": price,
                    
                    "link": link
                })
            except Exception as e:
                print(f"Error extracting item: {e}")
                continue

        # Check for the next page
        next_button = soup.select_one("a.next-page")  # Adjust selector for your site
        if next_button and next_button.has_attr("href"):
            page_number += 1
        else:
            print("No more pages found. Scraping complete.")
            break

    # Convert new data to DataFrame
    new_data = pd.DataFrame(data)

    # Merge new and existing data
    if not new_data.empty:
        if not existing_data.empty:
            merged_data = pd.concat([existing_data, new_data]).drop_duplicates(subset=["link"], keep="last")
            updates = merged_data[~merged_data["link"].isin(existing_links)]
            print(f"Updates found: {len(updates)}")
        else:
            merged_data = new_data
            updates = new_data

        # Save merged data
        merged_data.to_csv("Addis_ber.csv", index=False)
        print(f"Scraping completed successfully. {len(updates)} new items added. Data saved to 'static_data.csv'.")
    else:
        print("No new data found. Existing file remains unchanged.")

scrape_static_website()

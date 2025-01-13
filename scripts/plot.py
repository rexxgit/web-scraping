from playwright.sync_api import sync_playwright
import pandas as pd
import time
import os
import matplotlib.pyplot as plt
import re

def scrape():
    output_folder = 'web-scraping/ecommerce
    output_file = "brand22.csv"
    os.makedirs(output_folder, exist_ok=True)  # Ensure output folder exists
    output_path = os.path.join(output_folder, output_file)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
        context = browser.new_context(user_agent=user_agent)
        page = context.new_page()
        page.goto('https://jiji.com.et/sellerpage-jYM8FFmFIUMVwKBqpAr8SPa6 ')

        data = []
        previous_height = 0

        existing_data = pd.read_csv(output_path) if os.path.exists(output_path) else pd.DataFrame()
        existing_links = set(existing_data['link']) if not existing_data.empty else set()

        try:
            page.wait_for_selector('div.masonry-item', timeout=10000)
        except Exception as e:
            print(f"Error: Could not load page elements. {e}")
            browser.close()
            return

        while True:
            page.mouse.wheel(0, 2000)
            time.sleep(3)

            current_height = page.evaluate("document.body.scrollHeight")
            if current_height == previous_height:
                break
            previous_height = current_height

            items = page.query_selector_all('div.masonry-item')
            print(f"Items found so far: {len(items)}")

            for item in items[len(data):]:
                try:
                    title_elem = item.query_selector('div.b-advert-title-inner')
                    price_elem = item.query_selector('div.qa-advert-price')
                    description_elem = item.query_selector('div.b-list-advert-base__description-text')
                    location_elem = item.query_selector('span.b-list-advert__region__text')
                    link_elem = item.query_selector('a')

                    title = title_elem.inner_text().strip() if title_elem else "No title"
                    price = price_elem.inner_text().strip() if price_elem else "No price"
                    description = description_elem.inner_text().strip() if description_elem else "No description"
                    location = location_elem.inner_text().strip() if location_elem else "No location"
                    link = link_elem.get_attribute('href') if link_elem else "No link"
                    full_link = f"https://jiji.com.et{link}"

                    # Extract price by removing non-numeric characters
                    price = re.sub(r'[^\d]', '', price)  # Remove non-numeric characters
                    price = int(price) if price else 0

                    if full_link in existing_links:
                        continue

                    data.append({
                        'title': title,
                        'price': price,
                        'description': description,
                        'location': location,
                        'link': full_link,
                        'brand': extract_brand_from_title(title)
                    })
                except Exception as e:
                    print(f"Error extracting item: {e}")
                    continue

        new_data = pd.DataFrame(data)
        if not new_data.empty:
            if not existing_data.empty:
                merged_data = pd.concat([existing_data, new_data]).drop_duplicates(subset=['link'], keep='last')
                updates = merged_data[~merged_data['link'].isin(existing_links)]
                print(f"Updates found: {len(updates)}")
            else:
                merged_data = new_data
                updates = new_data

            merged_data.to_csv(output_path, index=False)
            print(f"Scraping completed. {len(updates)} new items added. Data saved to '{output_path}'.")

            # Data Visualization (Price Distribution)
            plot_price_distribution(output_path)
        else:
            print("No new data found. Existing file remains unchanged.")

        browser.close()

def extract_brand_from_title(title):
    """Extracts the first word from the title as the brand."""
    return title.split()[0] if title else "Unknown"

def plot_price_distribution(csv_file_path):
    # Load the CSV file to ensure the latest scraped data is used
    try:
        data = pd.read_csv(csv_file_path)

        # Ensure 'price' is numeric
        data['price'] = pd.to_numeric(data['price'], errors='coerce')
        data = data.dropna(subset=['price'])  # Drop rows where 'price' could not be converted

        if data.empty:
            print("No valid price data available for visualization.")
            return

        # Create price ranges (bins)
        min_price = data['price'].min()
        max_price = data['price'].max()
        bin_size = (max_price - min_price) // 10 if (max_price - min_price) >= 10 else 1  # Adjust bin size dynamically
        price_bins = list(range(min_price, max_price + bin_size, bin_size))

        # Plotting the histogram
        plt.figure(figsize=(12, 8))
        plt.hist(data['price'], bins=price_bins, color='blue', alpha=0.7, edgecolor='black')

        # Adding titles and labels
        plt.title('Price Distribution of Scraped Items', fontsize=16)
        plt.xlabel('Price Range (ETB)', fontsize=14)
        plt.ylabel('Frequency', fontsize=14)

        # Show price range as x-axis ticks
        plt.xticks(price_bins, rotation=45)
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        # Save the plot as a JPEG file
        plot_path = os.path.join(os.path.dirname(csv_file_path), 'plot.jpeg')
        plt.tight_layout()
        plt.savefig(plot_path, format='jpeg')
        plt.close()

        print(f"Price distribution visualization created and saved to '{plot_path}'.")
    except Exception as e:
        print(f"Error while generating price distribution visualization: {e}")

scrape()

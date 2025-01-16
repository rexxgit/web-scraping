from playwright.sync_api import sync_playwright
import pandas as pd
import time
import os
import matplotlib.pyplot as plt
import re
from collections import Counter

def scrape():
    output_folder = "web-scraping/ecommerce"
    output_file = "brand22.csv"
    os.makedirs(output_folder, exist_ok=True)  # Ensure output folder exists
    output_path = os.path.join(output_folder, output_file)

    trend_analysis_file = os.path.join(output_folder, "trend_analysis.txt")
    popular_products_file = os.path.join(output_folder, "popular_products.csv")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
        context = browser.new_context(user_agent=user_agent)
        page = context.new_page()
        page.goto('https://jiji.com.et/sellerpage-jYM8FFmFIUMVwKBqpAr8SPa6')

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
                        'link': full_link
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

            # Data Visualization
            plot_price_distribution(merged_data)

            # Popular products and trend analysis
            popular_products = get_popular_products(merged_data)
            popular_products.to_csv(popular_products_file, index=False)
            print(f"Popular products saved to '{popular_products_file}'.")

            trend_analysis = analyze_trends(merged_data)
            with open(trend_analysis_file, "w") as f:
                f.write(trend_analysis)
            print(f"Trend analysis saved to '{trend_analysis_file}'.")

        else:
            print("No new data found. Existing file remains unchanged.")

        browser.close()

def plot_price_distribution(data):
    # Ensure 'price' is numeric
    data['price'] = pd.to_numeric(data['price'], errors='coerce')
    data = data.dropna(subset=['price'])  # Drop rows where 'price' could not be converted

    # Create price ranges (bins)
    min_price = data['price'].min()
    max_price = data['price'].max()
    bin_size = (max_price - min_price) // 10  # Adjust the bin size based on the range
    price_bins = list(range(min_price, max_price + bin_size, bin_size))
    
    # Plot the histogram with titles only (no brands)
    plt.figure(figsize=(14, 8))
    plt.bar(data.index, data['price'], color='skyblue', edgecolor='black')
    plt.title('Price Distribution and Range of Items', fontsize=16)
    plt.xlabel('Items (Scraped Titles)', fontsize=12)
    plt.ylabel('Price (ETB)', fontsize=12)

    # Set horizontal titles on X-axis with proper spacing and rotation
    plt.xticks(data.index, data['title'], rotation=45, ha='right', fontsize=10)

    # Save the plot as a JPEG file
    plot_path = os.path.join('web-scraping/ecommerce', "arki2.jpeg")
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()

    print(f"Price distribution plot with titles saved to '{plot_path}'.")

def get_popular_products(data):
    # Count the frequency of product titles
    title_counts = Counter(data['title'])
    
    # Get the top 10 most frequent products
    popular_products = pd.DataFrame(title_counts.most_common(10), columns=['Title', 'Frequency'])
    return popular_products

def analyze_trends(data):
    # Dynamically calculate price bins
    min_price = data['price'].min()
    max_price = data['price'].max()
    
    # Set the number of bins you want
    num_bins = 4  # You can adjust this number based on your needs
    
    # Create dynamic price bins
    price_bins = [min_price + i * (max_price - min_price) // num_bins for i in range(num_bins + 1)]
    
    price_ranges = {
        'Low': data[data['price'] <= price_bins[1]],
        'Mid': data[(data['price'] > price_bins[1]) & (data['price'] <= price_bins[2])],
        'High': data[data['price'] > price_bins[2]]
    }

    # Trend analysis text
    trend_analysis = ""

    # Low-priced products
    low_price_products = len(price_ranges['Low'])
    trend_analysis += f"Products in the low price range that are likely to remain popular: {low_price_products} items in the low price range.\n"

    # Mid-priced products
    mid_price_products = len(price_ranges['Mid'])
    trend_analysis += f"Mid-priced products with potential for future popularity: {mid_price_products} items in the mid price range.\n"

    # High-priced products
    high_price_products = len(price_ranges['High'])
    trend_analysis += f"High-priced products with potential future demand: {high_price_products} items in the high price range.\n"

    # Price distribution analysis
    trend_analysis += analyze_price_distribution(data)

    return trend_analysis

def analyze_price_distribution(data):
    # Dynamically calculate price bins
    min_price = data['price'].min()
    max_price = data['price'].max()
    
    # Set the number of bins you want
    num_bins = 4  # You can adjust this number based on your needs
    
    # Create dynamic price bins
    price_bins = [min_price + i * (max_price - min_price) // num_bins for i in range(num_bins + 1)]
    
    # Count the number of items in each price range
    low_count = len(data[data['price'] <= price_bins[1]])
    mid_count = len(data[(data['price'] > price_bins[1]) & (data['price'] <= price_bins[2])])
    high_count = len(data[data['price'] > price_bins[2]])

    # Informed decisions
    decisions = ""
    if high_count > mid_count and high_count > low_count:
        decisions = "High-priced items are more frequent, indicating a potential demand surge in premium products."
    elif mid_count > low_count:
        decisions = "Mid-range items dominate, indicating growing popularity in this price range."
    else:
        decisions = "Low-priced items dominate, suggesting that affordability is a key factor in popularity."

    return f"Price distribution decisions: {decisions}\n"

scrape()

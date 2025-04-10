import csv
import os
import re
import time
from collections import Counter
from playwright.sync_api import sync_playwright
import matplotlib.pyplot as plt
from textblob import Word
import random

# Constants for price thresholds
MIN_PRICE = 1800
MAX_PRICE = 3500

# Define the main output path
output_path = "eco/eph"  # Base output folder

# Function to ensure the output directory exists
def ensure_output_directory():
    if not os.path.exists(output_path):
        os.makedirs(output_path)

# Function to replace print statements with file writing, ensuring the output directory exists
def write_to_file(filename, content):
    ensure_output_directory()  # Ensure the output directory exists
    with open(os.path.join(output_path, filename), 'a', encoding='utf-8') as f:
        f.write(content + "\n")

# Function to load popular product titles from a CSV (without pandas)
def load_popular_titles(csv_file):
    ensure_output_directory()  # Ensure the output directory exists
    try:
        with open(csv_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            return [row['title'] for row in reader]
    except Exception as e:
        write_to_file("errors.log", f"Error loading popular titles: {e}")
        return []

# Function to save data to CSV
def save_to_csv(item_details, filename="eph.csv"):
    ensure_output_directory()  # Ensure the output directory exists
    try:
        fieldnames = ['title', 'price', 'location', 'link']
        file_exists = os.path.isfile(os.path.join(output_path, filename))

        with open(os.path.join(output_path, filename), mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()

            for item in item_details:
                writer.writerow(item)

        write_to_file("status.log", f"Data saved successfully to {filename}")
    except Exception as e:
        write_to_file("errors.log", f"Error saving data to CSV: {e}")

# Function to save tailored titles to a text file
def save_tailored_titles_to_txt(titles, filename="tailored_keywords.txt"):
    ensure_output_directory()  # Ensure the output directory exists
    try:
        with open(os.path.join(output_path, filename), "a", encoding='utf-8') as file:
            for title in titles:
                file.write(f"{title}\n")
        write_to_file("status.log", f"Tailored titles saved successfully to {filename}")
    except Exception as e:
        write_to_file("errors.log", f"Error saving tailored titles: {e}")

# Function to save popular products to CSV
def save_popular_products_to_csv(popular_products, filename="popular_products.csv"):
    ensure_output_directory()  # Ensure the output directory exists
    try:
        fieldnames = ['title', 'frequency', 'link', 'price']
        file_exists = os.path.isfile(os.path.join(output_path, filename))

        with open(os.path.join(output_path, filename), mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()

            for title, frequency, link, price in popular_products:
                writer.writerow({'title': title, 'frequency': frequency, 'link': link, 'price': price})

        write_to_file("status.log", f"Popular products saved successfully to {filename}")
    except Exception as e:
        write_to_file("errors.log", f"Error saving popular products to CSV: {e}")

# Function to scrape Facebook Marketplace
def scrape_facebook_marketplace(min_items=50, keywords=None):
    if keywords is None:
        keywords = ["leather shoes", "boots", "shoes for men", "shoes for women"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://web.facebook.com/marketplace/profile/100076346097013/")
        page.wait_for_selector('a.x1i10hfl', timeout=10000)

        item_details = []
        prices = []
        titles = []

        # Scraping loop
        while len(item_details) < min_items:
            items = page.query_selector_all('a.x1i10hfl')

            for item in items:
                title_element = item.query_selector('span.x1lliihq.x6ikm8r.x10wlt62.x1n2onr6')
                title = title_element.inner_text() if title_element else None

                price_element = item.query_selector('span.x193iq5w')
                price = price_element.inner_text() if price_element else None

                location_element = item.query_selector('span.x1lliihq.x6ikm8r.x10wlt62.xlyipyv')
                location = location_element.inner_text() if location_element else None

                link = item.get_attribute('href')
                if link and 'item' in link:
                    if not link.startswith('https://'):
                        link = f"https://www.facebook.com{link}"
                    if '/item/' not in link:
                        continue

                if title and any(keyword.lower() in title.lower() for keyword in keywords):
                    if price and price.startswith("ETB"):
                        try:
                            price_value = int(price.split('ETB')[1].strip().replace(',', ''))
                            if MIN_PRICE <= price_value <= MAX_PRICE:
                                if title not in ["View profile", "Create new listing", "See More", "Sell"] and location and link:
                                    if not any(keyword in title for keyword in ["California", "Sausalito", "Daly City", "Brisbane"]):
                                        item_details.append({
                                            'title': title,
                                            'price': price,
                                            'location': location,
                                            'link': link
                                        })
                                        prices.append(price_value)
                                        titles.append(title)

                                        # Generate tailored titles during scraping
                                        tailored_titles = generate_tailored_titles(item_details[-1])
                                        save_tailored_titles_to_txt(tailored_titles)

                        except ValueError:
                            write_to_file("errors.log", f"Skipping item with invalid price: {price}")
                            continue

            if len(item_details) >= min_items:
                break

            page.evaluate("window.scrollBy(0, window.innerHeight);")
            time.sleep(2)
            if not page.query_selector('a.x1i10hfl'):
                break

        browser.close()

    return item_details, prices, titles

# Function to get synonyms using TextBlob
def get_synonyms(word):
    synonyms = Word(word).synsets
    if synonyms:
        return [str(lemma.name()) for syn in synonyms for lemma in syn.lemmas() if str(lemma.name()).lower() != word.lower()]
    return [word]

# Function to generate tailored titles based on item details
def generate_tailored_titles(item):
    titles = []
    title = item['title']
    price_value = int(item['price'].split('ETB')[1].strip().replace(',', ''))  
    link = item['link']

    synonyms = get_synonyms(title)
    random_synonym1 = random.choice(synonyms)
    random_synonym2 = random.choice(synonyms)

    while random_synonym2 == random_synonym1:
        random_synonym2 = random.choice(synonyms)

    if 2800 <= price_value <= 3500:
        titles.append(f"Premium {random_synonym1} | {title} for just ETB {price_value} — perfect for discerning professionals. Link: {link}")
        titles.append(f"Exclusive offer: {random_synonym2} at ETB {price_value}. Customizable options available! Link: {link}")

    elif 2200 <= price_value < 2800:
        titles.append(f"Stylish {random_synonym1} | {title} for ETB {price_value}. Limited time only! Link: {link}")
        titles.append(f"Seasonal Sale on {random_synonym2}! Now just ETB {price_value}. Link: {link}")

    else:
        titles.append(f"Affordable {random_synonym1} starting at ETB {price_value}. Link: {link}")
        titles.append(f"Flash sale on {random_synonym2} for ETB {price_value}! Link: {link}")

    return titles

# Function to extract frequent keywords and save to a text file
def extract_frequent_keywords(titles):
    ensure_output_directory()  # Ensure the output directory exists
    all_keywords = []
    for title in titles:
        words = re.findall(r'\b\w+\b', title.lower())
        all_keywords.extend(words)

    keyword_counts = Counter(all_keywords).most_common(10)

    try:
        with open(os.path.join(output_path, "top_keywords.txt"), "w", encoding='utf-8') as file:
            for keyword, count in keyword_counts:
                file.write(f"{keyword}: {count}\n")
        write_to_file("status.log", "Top keywords saved to top_keywords.txt")
    except Exception as e:
        write_to_file("errors.log", f"Error saving keywords: {e}")

    return keyword_counts

# Function to extract popular products based on title frequency after trend analysis
def extract_popular_products_after_analysis(titles, item_details):
    title_counts = Counter(titles)
    popular_products = title_counts.most_common(10)

    popular_items = []
    for title, frequency in popular_products:
        matched_items = [item for item in item_details if item['title'] == title]
        if matched_items:
            for item in matched_items:
                popular_items.append((title, frequency, item['link'], item['price']))

    return popular_items

# Function to generate dynamic trend analysis and recommendations
def generate_dynamic_trend_analysis(prices, item_details):
    ensure_output_directory()  # Ensure the output directory exists
    dominant_category = ''
    try:
        plt.figure(figsize=(10, 6))
        n, bins, patches = plt.hist(prices, bins=20, color='skyblue', edgecolor='black')
        plt.title('Price Distribution of Shoes (1800 - 3500 ETB)')
        plt.xlabel('Price (ETB)')
        plt.ylabel('Number of Listings')
        plt.grid(True)
        plt.savefig(os.path.join(output_path, "eph.jpeg"))  # Save plot directly to designated JPEG file
        plt.close()

        bin_width = bins[1] - bins[0]
        mid_bin = bins[len(bins) // 2]
        low_threshold = bins[0]
        mid_threshold = mid_bin
        high_threshold = bins[-1]

        low_prices = [price for price in prices if price < mid_threshold]
        mid_prices = [price for price in prices if mid_threshold <= price < high_threshold]
        high_prices = [price for price in prices if price >= high_threshold]

        price_counts = Counter()
        price_counts['low'] = len(low_prices)
        price_counts['mid'] = len(mid_prices)
        price_counts['high'] = len(high_prices)

        dominant_category = price_counts.most_common(1)[0][0]

        recommendations = generate_recommendations(dominant_category)

        with open(os.path.join(output_path, "informed_decisions.txt"), "w", encoding='utf-8') as file:
            file.write(f"Dynamic Trend Analysis: Dominant Price Category: {dominant_category.capitalize()} Products\n")
            file.write("=" * 50 + "\n")
            file.write(recommendations)
            file.write("=" * 50 + "\n")
            file.write("End of Dynamic Trend Analysis\n")

        write_to_file("status.log", "Informed decisions saved to informed_decisions.txt")

    except Exception as e:
        write_to_file("errors.log", f"Error generating trend analysis: {e}")

    return dominant_category

# Function to generate recommendations based on price category
def generate_recommendations(dominant_category):
    recommendations = ""
    if dominant_category == 'high':
        recommendations += (
            "For Middle-Class Business People:\n"
            "Target Market: Individuals looking for stylish and professional leather shoes, with a preference for value, reliability, and good quality, but within a moderate budget.\n\n"
            "High-Priced Leather Shoes (Premium Segment)\n"
            "Price Range: ETB 2,800 to ETB 3,500\n\n"
            "1. Premium Price with Practical Value: Position these shoes as both luxurious and professional.\n"
            "Example: “Premium leather shoes starting from ETB 3,200—crafted for the discerning professional.”\n\n"
            "2. Customizable Options for Personalization: Offer customization options that cater to individual needs.\n"
            "Example: “Personalize your leather shoes for just ETB 3,300.”\n\n"
            "3. Volume Discounts or Corporate Deals: Offer bulk pricing for businesses buying larger quantities.\n"
            "Example: “Corporate bulk purchase discount—leather shoes at ETB 2,900 each when you buy 5 or more pairs.”\n\n"
        )
    elif dominant_category == 'mid':
        recommendations += (
            "For Middle-Class Business People:\n"
            "Mid-Priced Leather Shoes (Affordable Luxury Segment)\n"
            "Price Range: ETB 2,200 to ETB 2,800\n\n"
            "1. Value for Money with Professional Appeal: Price these shoes to offer solid value for money.\n"
            "Example: “Stylish leather shoes for ETB 2,500.”\n\n"
            "2. Seasonal Promotions & Discounts: Run seasonal promotions offering discounts during significant times.\n"
            "Example: “Seasonal Sale—Leather shoes for ETB 2,400.”\n\n"
            "3. Exclusive Membership Pricing: Create a program for repeat buyers that provides ongoing discounts.\n"
            "Example: “Join our Exclusive Club—Leather shoes at ETB 2,350.”\n\n"
        )
    else:
        recommendations += (
            "For Young Fashion-Conscious Enthusiasts:\n"
            "Low-Priced Leather Shoes (Value Segment)\n"
            "Price Range: ETB 1,800 to ETB 2,200\n\n"
            "1. Budget-Friendly, Durable Options: Price these shoes to balance affordability with quality.\n"
            "Example: “Affordable leather shoes starting at ETB 1,950.”\n\n"
            "2. Frequent Discount Campaigns: Offer regular sales or promotional discounts.\n"
            "Example: “Flash Sale—Leather shoes for ETB 1,800.”\n\n"
            "3. Value Bundles: Bundle shoes with accessories to increase perceived value.\n"
            "Example: “Bundle Offer: Get leather shoes and a matching belt for ETB 2,100.”\n\n"
        )
    return recommendations

# Main workflow execution
def main():
    ensure_output_directory()  # Ensure the output directory exists
    keywords = ["leather shoes", "boots", "shoes for men", "shoes for women"]

    # Step 1: Scrape Marketplace Data
    items_data, prices_data, titles_data = scrape_facebook_marketplace(keywords=keywords)

    # Save the scraped data to CSV
    save_to_csv(items_data)

    # Extract keywords from titles and save to a text file
    keywords_data = extract_frequent_keywords(titles_data)

    # Generate dynamic trend analysis
    dominant_category = generate_dynamic_trend_analysis(prices_data, items_data)

    # Extract popular products based on title frequency after trend analysis
    popular_products = extract_popular_products_after_analysis(titles_data, items_data)

    # Save popular products to a CSV file
    save_popular_products_to_csv(popular_products)

if __name__ == "__main__":
    main()

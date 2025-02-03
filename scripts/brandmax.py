from playwright.sync_api import sync_playwright
from playwright._impl._errors import TimeoutError
import pandas as pd
import time
import os
import matplotlib.pyplot as plt
import re
from collections import Counter

def scrape():
    # Set up output paths and create directories
    output_folder = "eco/brandmax"
    output_file = "brandmax.csv"
    os.makedirs(output_folder, exist_ok=True)  # Ensure output folder exists
    output_path = os.path.join(output_folder, output_file)

    trend_analysis_file = os.path.join(output_folder, "trend_analysis.txt")
    popular_products_file = os.path.join(output_folder, "popular_products.csv")
    informed_decisions_file = os.path.join(output_folder, "informed_decisions.txt")  # New file for informed decisions

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
        context = browser.new_context(user_agent=user_agent)
        page = context.new_page()
        page.goto('https://jiji.com.et/shop/brandmax/shoes')

        data = []
        previous_height = 0

        # Load existing data if available
        existing_data = pd.read_csv(output_path) if os.path.exists(output_path) else pd.DataFrame()
        existing_links = set(existing_data['link']) if not existing_data.empty else set()

        # Wait for the main content to load
        try:
            page.wait_for_selector('div.masonry-item', timeout=10000)
        except TimeoutError as e:
            print(f"Error: Could not load page elements due to timeout. {e}")
            browser.close()
            return

        # Infinite scroll to load more items
        while True:
            page.mouse.wheel(0, 2000)
            time.sleep(3)  # Delay to allow more items to load

            current_height = page.evaluate("document.body.scrollHeight")
            if current_height == previous_height:  # Stop if no more new items
                break
            previous_height = current_height

            items = page.query_selector_all('div.masonry-item')
            print(f"Items found so far: {len(items)}")

            # Extract data from each item
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

            # Get popular products and trend analysis
            popular_products = get_popular_products(merged_data)
            popular_products.to_csv(popular_products_file, index=False)
            print(f"Popular products saved to '{popular_products_file}'.")

            # Perform Analysis and Generate Dynamic Reports
            trend_analysis = analyze_trends(merged_data)
            with open(trend_analysis_file, "w", encoding='utf-8') as f:
                f.write(trend_analysis)
            print(f"Trend analysis saved to '{trend_analysis_file}'.")

            informed_decisions = analyze_price_distribution(merged_data)
            with open(informed_decisions_file, "w", encoding='utf-8') as f:
                f.write(informed_decisions)
            print(f"Informed decisions saved to '{informed_decisions_file}'.")

        else:
            print("No new data found. Existing file remains unchanged.")

        browser.close()

def plot_price_distribution(data):
    # Ensure 'price' is numeric
    data['price'] = pd.to_numeric(data['price'], errors='coerce')
    data = data.dropna(subset=['price'])  # Drop rows where 'price' could not be converted

    # Plotting the price distribution
    plt.figure(figsize=(14, 8))
    plt.bar(data.index, data['price'], color='skyblue', edgecolor='black')
    plt.title('Price Distribution and Range of Items', fontsize=16)
    plt.xlabel('Items (Scraped Titles)', fontsize=12)
    plt.ylabel('Price (ETB)', fontsize=12)

    # Set horizontal titles on X-axis with proper spacing and rotation
    plt.xticks(data.index, data['title'], rotation=45, ha='right', fontsize=10)

    # Save the plot as a JPEG file
    plot_path = os.path.join('eco/brandmax', "brandmax.jpeg")
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()

    print(f"Price distribution plot saved to '{plot_path}'.")

def get_popular_products(data):
    # Count the frequency of product titles
    title_counts = Counter(data['title'])
    
    # Get the top 10 most frequent products
    popular_products = pd.DataFrame(title_counts.most_common(10), columns=['Title', 'Frequency'])
    return popular_products

def analyze_trends(data):
    trend_analysis = "Trend Analysis for Price Ranges\n\n"
    # Trends analysis based on pricing
    if data.empty:
        return trend_analysis + "No data available for analysis.\n"

    min_price = data['price'].min()
    max_price = data['price'].max()

    # Create dynamic price bins based on data
    price_bins = [min_price + i * (max_price - min_price) // 4 for i in range(5)]
    
    price_ranges = {
        'Low': data[data['price'] <= price_bins[1]],
        'Mid': data[(data['price'] > price_bins[1]) & (data['price'] <= price_bins[2])],
        'High': data[data['price'] > price_bins[2]]
    }

    # Dynamic counting of high, mid, and low price products
    high_price_products = len(price_ranges['High'])
    mid_price_products = len(price_ranges['Mid'])
    low_price_products = len(price_ranges['Low'])

    trend_analysis += f"Number of High Price Products: {high_price_products}\n"
    trend_analysis += f"Number of Mid Price Products: {mid_price_products}\n"
    trend_analysis += f"Number of Low Price Products: {low_price_products}\n\n"

    # Adding the titles, prices, and links of products in each price range to the report
    if high_price_products > 0:
        trend_analysis += f"High Price Products (Titles, Prices, Links):\n"
        for index, row in price_ranges['High'].iterrows():
            trend_analysis += f"- Title: {row['title']}, Price: {row['price']}, Link: {row['link']}\n"
        trend_analysis += "\n"

    if mid_price_products > 0:
        trend_analysis += f"Mid Price Products (Titles, Prices, Links):\n"
        for index, row in price_ranges['Mid'].iterrows():
            trend_analysis += f"- Title: {row['title']}, Price: {row['price']}, Link: {row['link']}\n"
        trend_analysis += "\n"

    if low_price_products > 0:
        trend_analysis += f"Low Price Products (Titles, Prices, Links):\n"
        for index, row in price_ranges['Low'].iterrows():
            trend_analysis += f"- Title: {row['title']}, Price: {row['price']}, Link: {row['link']}\n"
        trend_analysis += "\n"

    # Conditional statements for trend analysis
    if high_price_products > 0:
        trend_analysis += f"1. High Price Bar (Premium Products)\n"
        trend_analysis += "English:\n"
        trend_analysis += "- Trend: Luxury and exclusivity are in demand. Consumers are paying for quality and status.\n"
        trend_analysis += "- Action: Focus on exclusive launches and personalized experiences. Provide top-tier customer service and innovative offerings.\n"
        trend_analysis += "Amharic:\n"
        trend_analysis += "የቅንጦት እና የኤክስክሉስቭ ምርቶች ተፈላጊ ናቸው። ተጠቃሚዋች ለጥራት እና ደረጃ ምርቶች እየከፈሉ ነው።\n"
        trend_analysis += "Actions:\n"
        trend_analysis += "ትኩረት በ ልዩ ጅምሮች እና ግላዊ ተሞክሮዎች ላይ ያተኩሩ። ከፍተኛ-ደረጃ የደንበኞች አገልግሎት እና የፈጠራ አቅርቦቶች ያቅርቡ\n\n"

    if mid_price_products > 0:
        trend_analysis += f"2. Mid Price Bar (Affordable Quality Products)\n"
        trend_analysis += "English:\n"
        trend_analysis += "- Trend: Consumers are seeking good value for their money, especially during economic uncertainty. Discounts and promotions drive purchases.\n"
        trend_analysis += "- Action: Highlight value-for-money and use seasonal sales and bundle offers to stay competitive.\n"
        trend_analysis += "Amharic:\n"
        trend_analysis += "ተጠቃሚዎች ለገንዘባቸው ጥሩ ዋጋ ይፈልጋሉ ፣ በተለይም በኢኮኖሚያዊ አለመረጋጋት ወቅት። ቅናሾች እና ማስተዋወቂያዎች ግዥዎችን ያቅርቡ.\n"
        trend_analysis += "Action:\n"
        trend_analysis += "በዋጋ-ለገንዘብ ላይ ያተኩሩ እና ወቅታዊ ሽያጮችን ይጠቀሙ እና ተወዳዳሪ ሆነው ለመቆየት የጥቅል አቅርቦቶችን ይጠቀሙ።\n\n"

    if low_price_products > 0:
        trend_analysis += f"3. Low Price Bar (Budget Products)\n"
        trend_analysis += "English:\n"
        trend_analysis += "- Trend: Budget-conscious consumers are looking for affordable and quick deals. Flash sales and time-limited offers dominate buying behavior.\n"
        trend_analysis += "- Action: Focus on frequent flash sales and loyalty programs to create urgency and retain customers.\n"
        trend_analysis += "Amharic:\n"
        trend_analysis += "የበጀት ግንዛቤ ያላቸው ተጠቃሚዋች ተመጣጣኝ እና ፈጣን ስምምነቶችን ይፈልጋሉ። የፍላሽ ሽያጭ እና በጊዜ የተገደቡ ቅናሾች ላይ ያተኩሩ .\n"
        trend_analysis += "Action:\n"
        trend_analysis += "አስቸኳይ ሁኔታ ለመፍጠር እና ደንበኞችን ለማቆየት በ ተደጋጋሚ የፍላሽ ሽያጭ እና የታማኝነት ፕሮግራሞች ላይ ያተኩሩ\n"

    return trend_analysis

def analyze_price_distribution(data):
    # Analyze price distribution and generate dynamic recommendations
    if data.empty:
        return "No price data available for analysis.\n"

    min_price = data['price'].min()
    max_price = data['price'].max()
    
    # Create dynamic price bins based on data
    price_bins = [min_price + i * (max_price - min_price) // 4 for i in range(5)]
    
    low_count = len(data[data['price'] <= price_bins[1]])
    mid_count = len(data[(data['price'] > price_bins[1]) & (data['price'] <= price_bins[2])])
    high_count = len(data[data['price'] > price_bins[2]])

    total_count = len(data)
    
    recommendations = "Recommendations & Suggestions Based on Data Visualization\n\n"
    
    if high_count > (total_count * 0.3):
        recommendations += "1. High Price Bar (Premium Products)\n"
        recommendations += "English:\n"
        recommendations += "- Attract Customers:\n"
        recommendations += "  - Offer exclusive deals like limited editions or early access to special collections. This makes the product feel unique and worth the higher price.\n"
        recommendations += "- Stay Competitive:\n"
        recommendations += "  - Provide excellent customer service (fast responses, easy returns) to justify the premium price.\n"
        recommendations += "  - Regularly release new and innovative products to keep customers interested and excited.\n"
        recommendations += "Amharic:\n"
        recommendations += "ደንበኞችን ይሳቡ:\n"
        recommendations += "- እንደ ውስን እትሞች ወይም የልዩ ስብስቦች ቀደምት መዳረሻ ያሉ ልዩ ቅናሾችን ያቅርቡ። ይህ ምርቱ ልዩ እና ከፍተኛ ዋጋ ያለው እንዲሰማው ያደርገዋል.\n"
        recommendations += "- ተወዳዳሪ ሁን:\n"
        recommendations += "  - የፕሪሚየም ዋጋን ትክክለኛነት ለማረጋገጥ እጅግ በጣም ጥሩ የደንበኞች አገልግሎት  (ፈጣን ምላሾች ፣ ቀላል ተመላሾች) ያቅርቡ።\n\n"

    if mid_count > (total_count * 0.4):
        recommendations += "2. Mid Price Bar (Affordable Quality Products)\n"
        recommendations += "English:\n"
        recommendations += "- Attract Customers:\n"
        recommendations += "  - Emphasize value for money—show customers they get great quality at a fair price. Offer discounts or free shipping to make the deal even better.\n"
        recommendations += "- Stay Competitive:\n"
        recommendations += "  - Keep your prices competitive by checking competitors regularly and adjusting as needed.\n"
        recommendations += "  - Offer bundles (e.g., buy one get one free) to increase perceived value.\n"
        recommendations += "Amharic:\n"
        recommendations += "ደንበኞችን ይሳቡ:\n"
        recommendations += "- አጽንኦት ይስጡ ለገንዘብ ዋጋ ደንበኛው በተመጣጣኝ ዋጋ ጥሩ ጥራት እንደሚያገኙ አሳይ። ስምምነቱን የበለጠ የተሻለ ለማድረግ ቅናሾች ወይም ነፃ መላኪያ ያቅርቡ።\n"
        recommendations += "- ተወዳዳሪ ሁን:\n"
        recommendations += "  - ተፎካካሪዎችን በመደበኛነት በመፈተሽ እና እንደ አስፈላጊነቱ በማስተካከል ዋጋዎችዎን ተወዳዳሪ ያድርጉ.\n"
        recommendations += "  - የታሰበውን እሴት ለመጨመር ጥቅሎች  (ለምሳሌ ፣ አንድ ይግዙ ነፃ) ያቅርቡ።\n\n"

    if low_count > (total_count * 0.3):
        recommendations += "3. Low Price Bar (Budget Products)\n"
        recommendations += "English:\n"
        recommendations += "- Attract Customers:\n"
        recommendations += "  - Run flash sales (limited-time discounts) to create urgency and encourage quick purchases.\n"
        recommendations += "  - Use time-limited offers to make customers feel they’re getting a great deal that won’t last.\n"
        recommendations += "- Stay Competitive:\n"
        recommendations += "  - Reduce costs by negotiating with suppliers for lower prices or using more efficient methods.\n"
        recommendations += "  - Reward repeat customers with loyalty programs (e.g., discounts on next purchase).\n"
        recommendations += "Amharic:\n"
        recommendations += "ደንበኞችን ይሳቡ:\n"
        recommendations += "- አስቸኳይ ሁኔታን ለመፍጠር እና ፈጣን ግዢዎችን ለማበረታታት የፍላሽ ሽያጮችን ያሂዱ  (የተገደበ ጊዜ ቅናሾች)።\n"
        recommendations += "- ደንበኞች የማይዘልቅ ትልቅ ነገር እያገኙ እንደሆነ እንዲሰማቸው ለማድረግ ጊዜ-የተገደበ ቅናሾችን ይጠቀሙ.\n"
        recommendations += "- ተወዳዳሪ ሁን:\n"
        recommendations += "  - ወጪን ይቀንሱ ከአቅራቢዎች ጋር በዝቅተኛ ዋጋ በመደራደር ወይም ይበልጥ ቀልጣፋ ዘዴዎችን በመጠቀም.\n"
        recommendations += "  - ተደጋጋሚ ደንበኞችን በ የታማኝነት ፕሮግራሞች ይሸልሙ (ለምሳሌ ፣ በሚቀጥለው ግዢ ላይ ቅናሾች)።\n"

    return recommendations

scrape()

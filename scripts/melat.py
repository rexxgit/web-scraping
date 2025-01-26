import asyncio
import random
import os
from collections import Counter
import pandas as pd
import matplotlib.pyplot as plt
from playwright.async_api import async_playwright
from playwright._impl._errors import TimeoutError

# List of user agents to mimic different browsers
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 9; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Mobile Safari/537.36",
]

async def run():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        user_agent = random.choice(USER_AGENTS)
        context = await browser.new_context(user_agent=user_agent)
        page = await context.new_page()
        
        output_folder = "eco/melat"
        output_file = "ef.csv"
        os.makedirs(output_folder, exist_ok=True)  # Ensure output folder exists
        output_path = os.path.join(output_folder, output_file)

        # File paths for analysis outputs
        trend_analysis_file = os.path.join(output_folder, "trend_ef.txt")
        popular_products_file = os.path.join(output_folder, "popular_ef.csv")
        informed_decisions_file = os.path.join(output_folder, "informed_ef.txt")

        await page.goto("https://web.facebook.com/marketplace/profile/100076346097013/", wait_until="domcontentloaded")
        
        await page.wait_for_selector("div.x9f619")

        all_results, seen_titles = [], set()  # To track unique titles

        for _ in range(5):  # Scroll a number of times
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            await page.wait_for_timeout(2000)

        listings = await page.query_selector_all("div.x9f619")

        for listing in listings:
            try:
                title_element = await listing.query_selector("span.x1lliihq.x6ikm8r.x10wlt62.x1n2onr6")
                price_element = await listing.query_selector("span.x78zum5")
                link_element = await listing.query_selector("a")

                title = await title_element.inner_text() if title_element else None
                price = await price_element.inner_text() if price_element else "No Price"
                link = await link_element.get_attribute("href") if link_element else None

                # Skip listings without title or link
                if not title or not link or price == "No Price":
                    continue

                if link.startswith('/'):
                    link = f"https://web.facebook.com{link}"

                # Check for duplicates based on title
                if title not in seen_titles:
                    seen_titles.add(title)
                    all_results.append({
                        'title': title,
                        'price': price,
                        'link': link
                    })

                    # Adding a delay to mimic human behavior
                    await asyncio.sleep(random.uniform(1, 3))

            except Exception as e:
                print("Error extracting data from listing:", e)

        await browser.close()

        new_data = pd.DataFrame(all_results)
        
        if not new_data.empty:
            existing_data = pd.read_csv(output_path) if os.path.exists(output_path) else pd.DataFrame()

            # Check if 'link' column exists in existing_data before accessing
            if 'link' in existing_data.columns:
                merged_data = pd.concat([existing_data, new_data]).drop_duplicates(subset=['link'], keep='last')
                updates = merged_data[~merged_data['link'].isin(existing_data['link'])]
            else:
                print("Column 'link' not found in existing data. Merging without filtering by updates.")
                merged_data = pd.concat([existing_data, new_data]).drop_duplicates(keep='last')
                updates = new_data  # Treating all new data as updates since we can't find existing links

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

def plot_price_distribution(data):
    # Ensure 'price' is treated as strings first
    data['price'] = data['price'].astype(str)
    
    # Remove the currency symbol and convert to numeric
    data['price'] = pd.to_numeric(data['price'].str.replace('ETB', '').str.replace(',', '').str.strip(), errors='coerce')
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
    plot_path = os.path.join('eco/melat', "ef.jpeg")
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
    if data.empty:
        return trend_analysis + "No data available for analysis.\n"

    # Convert prices to string to avoid errors when using .str accessor
    data['price'] = data['price'].astype(str)

    # Remove the currency symbol and convert to numeric
    data['price'] = pd.to_numeric(data['price'].str.replace('ETB', '').str.replace(',', '').str.strip(), errors='coerce')
    min_price = data['price'].min()
    max_price = data['price'].max()

    if pd.isna(min_price) or pd.isna(max_price):
        return trend_analysis + "No valid price data available for analysis.\n"

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
        trend_analysis += "1. High Price Bar (Premium Products)\n"
        trend_analysis += "English:\n"
        trend_analysis += "- Trend: Luxury and exclusivity are in demand. Consumers are paying for quality and status.\n"
        trend_analysis += "- Action: Focus on exclusive launches and personalized experiences. Provide top-tier customer service and innovative offerings.\n"
        trend_analysis += "Amharic:\n"
        trend_analysis += "ደንበኞች ይሳቡ:\n"
        trend_analysis += "- እንደ ውስን እትሞች ወይም የልዩ ስብስቦች ቀደምት መዳረሻ ያሉ ልዩ ቅናሾች ያቅርቡ። ይህ ምርቱ ልዩ እና ከፍተኛ ዋጋ ያለው እንዲሰማው ያደርገዋል.\n"
        trend_analysis += "Actions:\n"
        trend_analysis += "ትኩረት በ ልዩ ጅምሮች እና ግላዊ ተሞክሮዎች ላይ ያተኩሩ። ከፍተኛ-ደረጃ የደንበኞች አገልግሎት እና የፈጠራ አቅርቦቶች ያቅርቡ\n\n"

    if mid_price_products > 0:
        trend_analysis += "2. Mid Price Bar (Affordable Quality Products)\n"
        trend_analysis += "English:\n"
        trend_analysis += "- Trend: Consumers are seeking good value for their money, especially during economic uncertainty. Discounts and promotions drive purchases.\n"
        trend_analysis += "- Action: Highlight value-for-money and use seasonal sales and bundle offers to stay competitive.\n"
        trend_analysis += "Amharic:\n"
        trend_analysis += "ደንበኞችን ይሳቡ:\n"
        trend_analysis += "- አጽንኦት ይስጡ ለገንዘብ ዋጋ ደንበኛው በተመጣጣኝ ዋጋ ጥሩ ጥራት እንደሚያገኙ አሳይ። ስምምነቱን የበለጠ የተሻለ ለማድረግ ቅናሾች ወይም ነፃ መላኪያ ያቅርቡ።\n"
        trend_analysis += "- ተወዳዳሪ ሁን:\n"
        trend_analysis += "  - በዋጋ-ለገንዘብ ላይ ያተኩሩ እና ወቅታዊ ሽያጮችን ይጠቀሙ እና ተወዳዳሪ ሆነው ለመቆየት የጥቅል አቅርቦቶችን ይጠቀሙ።\n\n"

    if low_price_products > 0:
        trend_analysis += "3. Low Price Bar (Budget Products)\n"
        trend_analysis += "English:\n"
        trend_analysis += "- Trend: Budget-conscious consumers are looking for affordable and quick deals. Flash sales and time-limited offers dominate buying behavior.\n"
        trend_analysis += "- Action: Focus on frequent flash sales and loyalty programs to create urgency and retain customers.\n"
        trend_analysis += "Amharic:\n"
        trend_analysis += "ደንበኞችን ይሳቡ:\n"
        trend_analysis += "- አስቸኳይ ሁኔታን ለመፍጠር እና ፈጣን ግዢዎችን ለማበረታታት የፍላሽ ሽያጮችን ያሂዱ  (የተገደበ ጊዜ ቅናሾች)።\n"
        trend_analysis += "- አስደመጥ ሁን:\n"
        trend_analysis += "  - በጣም በጀት ተደርጎ ወይም በአለመው አገልግሎት ይሸልሙ (ለምሳሌ ፣ በሚቀጥለው ግዢ ላይ ቅናሾች)\n"

    return trend_analysis

def analyze_price_distribution(data):
    if data.empty:
        return "No price data available for analysis.\n"

    data['price'] = data['price'].astype(str)
    data['price'] = pd.to_numeric(data['price'].str.replace('ETB', '').str.replace(',', '').str.strip(), errors='coerce')
    min_price = data['price'].min()
    max_price = data['price'].max()

    # Create dynamic price bins based on valid data range
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
        recommendations += "- እንደ ውስን እትሞች ወይም የልዩ ስብስቦች ቀደምት መዳረሻ ያሉ ልዩ ቅናሾች ያቅርቡ። ይህ ምርቱ ልዩ እና ከፍተኛ ዋጋ ያለው እንዲሰማው ያደርገዋል.\n"
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
        recommendations += "  - በዋጋ-ለገንዘብ ላይ ያተኩሩ እና ወቅታዊ ሽያጮችን ይጠቀሙ እና ተወዳዳሪ ሆነው ለመቆየት የጥቅል አቅርቦቶችን ይጠቀሙ።\n\n"

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

# Run the scraping function
asyncio.run(run())

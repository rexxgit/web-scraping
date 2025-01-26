import asyncio
import random
import os
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from playwright.async_api import async_playwright
from playwright._impl._errors import TimeoutError

# List of user agents to use for rotating
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0.2 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 11; Pixel 3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    # Add more user agents as needed
]

def create_output_paths():
    output_folder = "eco/melat"
    os.makedirs(output_folder, exist_ok=True)
    output_paths = {
        "csv": os.path.join(output_folder, "melat.csv"),
        "trend_analysis": os.path.join(output_folder, "trend_melat.txt"),
        "popular_products": os.path.join(output_folder, "popular_melat.csv"),
        "informed_decisions": os.path.join(output_folder, "informed_melat.txt")
    }
    return output_paths

async def scrape():
    output_paths = create_output_paths()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)

        all_results = []
        seen_titles = set()

        print("Starting the scraping process...")  # Indicate the start of the scraping process

        while True:
            user_agent = random.choice(USER_AGENTS)
            context = await browser.new_context(user_agent=user_agent)
            page = await context.new_page()
            
            try:
                await page.goto("https://web.facebook.com/marketplace/profile/100004503911329/", wait_until="domcontentloaded")
                await page.wait_for_selector("div.x9f619")

                listings = await page.query_selector_all("div.x9f619")

                for listing in listings:
                    try:
                        title_element = await listing.query_selector("span.x1lliihq.x6ikm8r.x10wlt62.x1n2onr6")
                        price_element = await listing.query_selector("span.x78zum5")
                        link_element = await listing.query_selector("a")

                        title = await title_element.inner_text() if title_element else None
                        price = await price_element.inner_text() if price_element else "No Price"
                        link = await link_element.get_attribute("href") if link_element else None

                        if title and link and price != "No Price" and title not in seen_titles:
                            seen_titles.add(title)
                            if link.startswith('/'):
                                link = f"https://web.facebook.com{link}"
                            all_results.append({'title': title, 'price': price, 'link': link, 'status': 'New'})

                        await asyncio.sleep(random.uniform(1, 3))

                    except Exception as e:
                        print("Error extracting data from listing:", e)

                await context.close()

            except TimeoutError:
                print("The operation timed out. Please check your internet connection or the website's availability.")
                await context.close()
                break

            print(f"{len(all_results)} listings have been gathered so far.")  # Number of listings collected

            # Add any condition to break the while loop if needed

        await browser.close()

        # Write results to CSV
        df = pd.DataFrame(all_results)
        if os.path.exists(output_paths['csv']):
            existing_data = pd.read_csv(output_paths['csv'])
            df = pd.concat([existing_data, df]).drop_duplicates(subset='title', keep='last')
            df['status'] = 'Existing'
        df.to_csv(output_paths['csv'], index=False, encoding='utf-8')

        print("Scraping done!")  # Indicate that scraping has finished
        return df

def plot_price_distribution(data):
    data['price'] = pd.to_numeric(data['price'].str.replace('ETB', '').str.replace(',', '').strip(), errors='coerce')
    data = data.dropna(subset=['price'])

    plt.figure(figsize=(14, 8))
    plt.bar(data.index, data['price'], color='skyblue', edgecolor='black')
    plt.title('Price Distribution and Range of Items', fontsize=16)
    plt.xlabel('Items (Scraped Titles)', fontsize=12)
    plt.ylabel('Price (ETB)', fontsize=12)

    plt.xticks(data.index, data['title'], rotation=45, ha='right', fontsize=10)
    plot_path = os.path.join('eco/melat', "melat.jpeg")
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()
    print(f"Price distribution plot saved to '{plot_path}'.")

def get_popular_products(data):
    title_counts = Counter(data['title'])
    popular_products = pd.DataFrame(title_counts.most_common(10), columns=['Title', 'Frequency'])
    return popular_products

def analyze_trends(data):
    trend_analysis = "Trend Analysis for Price Ranges\n\n"
    if data.empty:
        return trend_analysis + "No data available for analysis.\n"

    min_price = data['price'].min()
    max_price = data['price'].max()

    price_bins = [min_price + i * (max_price - min_price) // 4 for i in range(5)]
    
    price_ranges = {
        'Low': data[data['price'] <= price_bins[1]],
        'Mid': data[(data['price'] > price_bins[1]) & (data['price'] <= price_bins[2])],
        'High': data[data['price'] > price_bins[2]]
    }

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

    if high_price_products > 0:
        trend_analysis += "1. High Price Bar (Premium Products)\n"
        trend_analysis += "English:\n"
        trend_analysis += "- Trend: Luxury and exclusivity are in demand. Consumers are paying for quality and status.\n"
        trend_analysis += "- Action: Focus on exclusive launches and personalized experiences. Provide top-tier customer service and innovative offerings.\n"
        trend_analysis += "Amharic:\n"
        trend_analysis += "የቅንጦት እና የኤክስክሉስቭ ምርቶች ተፈላጊ ናቸው። ተጠቃሚዋች ለጥራት እና ደረጃ ምርቶች እየከፈሉ ነው።\n"
        trend_analysis += "Actions:\n"
        trend_analysis += "ትኩረት በ ልዩ ጅምሮች እና ግላዊ ተሞክሮዎች ላይ ያተኩሩ። ከፍተኛ-ደረጃ የደንበኞች አገልግሎት እና የፈጠራ አቅርቦቶች ያቅርቡ\n\n"

    if mid_price_products > 0:
        trend_analysis += "2. Mid Price Bar (Affordable Quality Products)\n"
        trend_analysis += "English:\n"
        trend_analysis += "- Trend: Consumers are seeking good value for their money, especially during economic uncertainty. Discounts and promotions drive purchases.\n"
        trend_analysis += "- Action: Highlight value-for-money and use seasonal sales and bundle offers to stay competitive.\n"
        trend_analysis += "Amharic:\n"
        trend_analysis += "ተጠቃሚዎች ለገንዘባቸው ጥሩ ዋጋ ይፈልጋሉ ፣ በተለይም በኢኮኖሚዊ አለመረጋጋት ወቅት። ቅናሾች እና ማስተዋወቂያዎች ግዥዎችን ይቅርቡ.\n"
        trend_analysis += "Action:\n"
        trend_analysis += "በዋጋ-ለገንዘብ ላይ ያተኩሩ እና ወቅታዊ ሽያጮችን ይጠቀሙ እና ተወዳዳሪ ሆነው ለመቆየት የጥቅል አቅርቦቶችን ይጠቀሙ።\n\n"

    if low_price_products > 0:
        trend_analysis += "3. Low Price Bar (Budget Products)\n"
        trend_analysis += "English:\n"
        trend_analysis += "- Trend: Budget-conscious consumers are looking for affordable and quick deals. Flash sales and time-limited offers dominate buying behavior.\n"
        trend_analysis += "- Action: Focus on frequent flash sales and loyalty programs to create urgency and retain customers.\n"
        trend_analysis += "Amharic:\n"
        trend_analysis += "የበጀት ግንዛቤ ያላቸው ተጠቃሚዋች ተመጣጣኝ እና ፈጣን ስምምነቶችን ይፈልጋሉ። የፍላሽ ሽያጭ እና በጊዜ የተገደቡ ቅናሾች ላይ ያተኩሩ .\n"
        trend_analysis += "Action:\n"
        trend_analysis += "አስቸኳይ ሁኔታ ለመፍጠር እና ደንበኞችን ለማቆየት በ ተደጋጋሚ የፍላሽ ሽያጭ እና የታማኝነት ፕሮግራሞች ላይ ያተኩሩ\n"

    return trend_analysis

def analyze_price_distribution(data):
    if data.empty:
        return "No price data available for analysis.\n"

    min_price = data['price'].min()
    max_price = data['price'].max()
    
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

async def main():
    data = await scrape()
    plot_price_distribution(data)
    
    # Get popular products and analysis
    popular_products = get_popular_products(data)
    print("Popular Products:\n", popular_products)

    trend_analysis = analyze_trends(data)
    print(trend_analysis)

    price_distribution_analysis = analyze_price_distribution(data)
    print(price_distribution_analysis)

# Run the main function
asyncio.run(main())

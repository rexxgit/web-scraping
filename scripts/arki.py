from playwright.sync_api import sync_playwright
import pandas as pd
import matplotlib.pyplot as plt
import os
from playwright._impl._errors import TimeoutError

def scrape():
    # Set up output paths and create directories
    output_folder = "web-scraping/eco/arki_store"
    output_file = "arki_store.csv"
    os.makedirs(output_folder, exist_ok=True)  # Ensure output folder exists
    output_path = os.path.join(output_folder, output_file)

    trend_analysis_file = os.path.join(output_folder, "trend_analysis.txt")
    informed_decision_file = os.path.join(output_folder, "informed_decision.txt")  # Updated file name
    popular_products_file = os.path.join(output_folder, "popular_products.csv")

    # Initialize a list to store all the scraped data
    scraped_data = []

    # Function to scrape data from a single page using Playwright
    def scrape_page(page, url, seen_titles):
        print(f"Scraping: {url}")  # Print the current URL being scraped
        page.goto(url)

        try:
            # Wait for the page to load and the listings to appear
            page.wait_for_selector('div.col-md-12.listingcolumn.normal.fourcolumn', timeout=20000)  # Increase timeout to 20 seconds
        except TimeoutError:
            print(f"Timeout occurred while waiting for listings on {url}.")
            return None  # Skip this page

        # Get the listing elements
        listings = page.query_selector_all('div.col-md-12.listingcolumn.normal.fourcolumn')

        if not listings:
            print(f"No listings found on {url}")  # No listings found
            return None

        # Loop through and extract data for each listing
        for listing in listings:
            title = listing.query_selector('span.listingtitle').inner_text().strip() if listing.query_selector('span.listingtitle') else 'N/A'
            price_text = listing.query_selector('span.price').inner_text().strip() if listing.query_selector('span.price') else 'N/A'
            try:
                price = float(price_text.replace('ETB', '').replace(',', '').strip()) if price_text != 'N/A' else None
            except ValueError:
                price = None  # Handle invalid price formats
            description = listing.query_selector('div.row.smalldesc').inner_text().strip() if listing.query_selector('div.row.smalldesc') else 'N/A'
            condition = listing.query_selector('div.attrib.cond.new').inner_text().strip() if listing.query_selector('div.attrib.cond.new') else 'N/A'
            location = listing.query_selector('span.location').inner_text().strip() if listing.query_selector('span.location') else 'N/A'

            # Extract the link to the listing page
            link = listing.query_selector('a').get_attribute('href') if listing.query_selector('a') else 'N/A'

            # Check if the title already exists in the list (to determine if it's new or existing)
            status = 'New' if title not in seen_titles else 'Existing'

            # Add the title to the seen titles list if it's new
            if status == 'New':
                seen_titles.add(title)

            # Store the extracted data in a dictionary
            data = {
                'Title': title,
                'Price': price,
                'Description': description,
                'Condition': condition,
                'Location': location,
                'Link': link,  # Include the link in the data
                'Status': status  # Add the status of the item (New or Existing)
            }
            scraped_data.append(data)

        # Handle pagination - look for the "Next" button
        next_button = page.query_selector('a:has-text("Next »")')
        if next_button:
            next_page_url = next_button.get_attribute('href')
            print(f"Moving to the next page: {next_page_url}")
            return next_page_url
        else:
            print("No more pages to scrape.")
            return None

    # Function to scrape multiple pages starting from the first one
    def scrape_all_pages(start_url):
        seen_titles = set()  # Set to store already seen titles (to mark as New or Existing)
        with sync_playwright() as p:
            # Launch a browser instance (Chromium, Firefox, or Webkit)
            browser = p.chromium.launch(headless=True)  # Set to False to see the browser window

            # Create a new browser context
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            
            # Create a new page within that context
            page = context.new_page()

            url = start_url
            while url:
                url = scrape_page(page, url, seen_titles)  # Scrape the current page and get the next page URL

            # Close the browser after scraping all pages
            browser.close()

    # Dynamic trend analysis function
    def analyze_trends(data):
        trend_analysis = "Trend Analysis for Price Ranges\n\n"
        # Trends analysis based on pricing
        if data.empty:
            return trend_analysis + "No data available for analysis.\n"

        min_price = data['Price'].min()
        max_price = data['Price'].max()

        # Create dynamic price bins based on data
        price_bins = [min_price + i * (max_price - min_price) // 4 for i in range(5)]
        
        price_ranges = {
            'Low': data[data['Price'] <= price_bins[1]],
            'Mid': data[(data['Price'] > price_bins[1]) & (data['Price'] <= price_bins[2])],
            'High': data[data['Price'] > price_bins[2]]
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
                trend_analysis += f"- Title: {row['Title']}, Price: {row['Price']}, Link: {row['Link']}\n"
            trend_analysis += "\n"

        if mid_price_products > 0:
            trend_analysis += f"Mid Price Products (Titles, Prices, Links):\n"
            for index, row in price_ranges['Mid'].iterrows():
                trend_analysis += f"- Title: {row['Title']}, Price: {row['Price']}, Link: {row['Link']}\n"
            trend_analysis += "\n"

        if low_price_products > 0:
            trend_analysis += f"Low Price Products (Titles, Prices, Links):\n"
            for index, row in price_ranges['Low'].iterrows():
                trend_analysis += f"- Title: {row['Title']}, Price: {row['Price']}, Link: {row['Link']}\n"
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
            trend_analysis += "ተጠቃሚዎች ለገንዘባቸው ጥሩ ዋጋ ይፈልጋሉ ፣ በተለይም በኢኮኖሚያዊ አለመረጋጋት ወቅት። ቅናሾች እና ማስተዋወቂያዎች ግዥዎችን ይኖር።\n"
            trend_analysis += "Action:\n"
            trend_analysis += "በዋጋ-ለገንዘብ ላይ ያተኩሩ እና ወቅታዊ ሽያጮችን ይጠቀሙ እና ተወዳዳሪ ሆነው ለመቆየት የጥቅል አቅርቦቶችን ይጠቀሙ።\n\n"

        if low_price_products > 0:
            trend_analysis += f"3. Low Price Bar (Budget Products)\n"
            trend_analysis += "English:\n"
            trend_analysis += "- Trend: Budget-conscious consumers are looking for affordable and quick deals. Flash sales and time-limited offers dominate buying behavior.\n"
            trend_analysis += "- Action: Focus on frequent flash sales and loyalty programs to create urgency and retain customers.\n"
            trend_analysis += "Amharic:\n"
            trend_analysis += "የበጀት ግንዛቤ ያላቸው ተጠቃሚዋች ተመጣጣኝ እና ፈጣን ስምምነቶችን ይፈልጋሉ። የፍላሽ ሽያጭ እና በጊዜ የተገደቡ ቅናሾች ላይ ያተኩሩ.\n"
            trend_analysis += "Action:\n"
            trend_analysis += "አስቸኳይ ሁኔታ ለመፍጠር እና ደንበኞችን ለማቆየት በ ተደጋጋሚ የፍላሽ ሽያጭ እና የታማኝነት ፕሮግራሞች ላይ ያተኩሩ\n"

        return trend_analysis

    # Dynamic price distribution analysis
    def analyze_price_distribution(data):
        # Analyze price distribution and generate dynamic recommendations
        if data.empty:
            return "No price data available for analysis.\n"

        min_price = data['Price'].min()
        max_price = data['Price'].max()
        
        # Create dynamic price bins based on data
        price_bins = [min_price + i * (max_price - min_price) // 4 for i in range(5)]
        
        low_count = len(data[data['Price'] <= price_bins[1]])
        mid_count = len(data[(data['Price'] > price_bins[1]) & (data['Price'] <= price_bins[2])])
        high_count = len(data[data['Price'] > price_bins[2]])

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
            recommendations += "- አስቸኳይ ሁኔታን ለመፍጠር እና ፈጣን ግዢዎችን ለማበረታታት የፍላሽ ሽያጮችን ይወገዱ (የተገደበ ጊዜ ቅናሾች).\n"
            recommendations += "- ደንበኞች የማይዘልቅ ትልቅ ነገር እያገኙ እንደሆነ እንዲሰማቸው ለማድረግ ጊዜ-የተገደበ ቅናሾችን ይጠቀሙ.\n"
            recommendations += "- ተወዳዳሪ ሁን:\n"
            recommendations += "  - ወጪን ይቀንሱ ከአቅራቢዎች ጋር በዝቅተኛ ዋጋ በመደራደር ወይም ይበልጥ ቀልጣፋ ዘዴዎችን በመጠቀም.\n"
            recommendations += "  - ተደጋጋሚ ደንበኞችን በ የታማኝነት ፕሮግራሞች ይሸልሙ (ለምሳሌ ፣ በሚቀጥለው ግዢ ላይ ቅናሾች)።\n"

        return recommendations

    # Starting URL (the first page)
    start_url = "https://engocha.com/business/35538-akia-store?page=1"

    # Start scraping all pages
    scrape_all_pages(start_url)

    # Convert the scraped data to a pandas DataFrame
    df = pd.DataFrame(scraped_data)

    # Save the DataFrame to the specified CSV file
    df.to_csv(output_path, index=False)

    # Print a message indicating that the scraping is finished and data is saved
    print(f"Scraping complete. Data saved to '{output_path}'.")

    # Analyze trends and price distribution
    trend_analysis_result = analyze_trends(df)
    price_distribution_result = analyze_price_distribution(df)

    # Save analysis results to files
    with open(trend_analysis_file, 'w', encoding='utf-8') as file:
        file.write(trend_analysis_result)

    with open(informed_decision_file, 'w', encoding='utf-8') as file:  # Updated file name
        file.write(price_distribution_result)

    print(f"Trend analysis saved at '{trend_analysis_file}'.")
    print(f"Informed decision analysis saved at '{informed_decision_file}'.")  # Updated message

    # Filter the DataFrame for valid prices
    valid_prices = df[df['Price'].notnull()]

    # Plot the histogram
    plt.figure(figsize=(14, 8))

    # Create the histogram with horizontal titles on the X-axis
    plt.bar(valid_prices.index, valid_prices['Price'], color='skyblue', edgecolor='black')

    # Add overall labels and titles
    plt.title('Price Distribution and Range of Items', fontsize=16)
    plt.xlabel('Items (Scraped Titles)', fontsize=12)
    plt.ylabel('Price (ETB)', fontsize=12)

    # Set horizontal titles on X-axis with proper spacing and rotation
    plt.xticks(valid_prices.index, valid_prices['Title'], rotation=45, ha='right', fontsize=10)

    # Save the plot as a JPEG file (always updated)
    plot_path = os.path.join(output_folder, "arki_store.jpeg")
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()

    print(f"Price distribution plot with titles saved to '{plot_path}'.")

    # Saving Popular Products based on frequency
    popular_products = valid_prices['Title'].value_counts().reset_index()
    popular_products.columns = ['Title', 'Frequency']
    popular_products.to_csv(popular_products_file, index=False)

    print(f"Popular products saved to '{popular_products_file}'.")

# Run the scrape function to execute the web scraping
scrape()

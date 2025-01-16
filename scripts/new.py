from playwright.sync_api import sync_playwright
import pandas as pd
import matplotlib.pyplot as plt
import os
from playwright._impl._errors import TimeoutError

# Initialize a list to store all the scraped data
scraped_data = []

# Output settings
output_folder = "web-scraping/ecommerce/project"
output_file = "engoyes2.csv"
os.makedirs(output_folder, exist_ok=True)  # Ensure the output folder exists
output_path = os.path.join(output_folder, output_file)

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
plot_path = os.path.join(output_folder, "arki2.jpeg")
plt.tight_layout()
plt.savefig(plot_path)
plt.close()

print(f"Price distribution plot with titles saved to '{plot_path}'.")

# Filter valid price ranges for decision-making
low_price_items = valid_prices[valid_prices['Price'] < 500]
mid_price_items = valid_prices[(valid_prices['Price'] >= 500) & (valid_prices['Price'] < 1500)]
high_price_items = valid_prices[valid_prices['Price'] >= 1500]

# Saving Popular Products based on frequency
popular_products = valid_prices['Title'].value_counts().reset_index()
popular_products.columns = ['Title', 'Frequency']
popular_products_file = os.path.join(output_folder, "popular_products.csv")
popular_products.to_csv(popular_products_file, index=False)

# Saving Trend Analysis based on price ranges
trend_analysis = []

if len(high_price_items) > len(mid_price_items) and len(high_price_items) > len(low_price_items):
    trend_analysis.append("High priced items are more popular, indicating a rise in premium product demand.")
    trend_analysis.append("ከፍተኛ ዋጋ ያላቸው እቃዎች በጣም ተደጋጋሚ ናቸው፣ ይህም በፕሪሚየም ምርቶች ላይ የፍላጎት መጨመርን ያሳያል.")
elif len(mid_price_items) > len(high_price_items) and len(mid_price_items) > len(low_price_items):
    trend_analysis.append("Mid-priced items are more common, indicating a strong demand in this price range.")
    trend_analysis.append("በዚህ የዋጋ ክልል ውስጥ ተወዳጅነት እያደገ መሆኑን የሚያመለክተው የመሃል ክልል ዕቃዎች የበላይነት አላቸው።")
else:
    trend_analysis.append("Low-priced items are gaining more popularity in the market.")
    trend_analysis.append("ዝቅተኛ ዋጋ ያላቸው እቃዎች የበላይ ናቸው፣ ይህም በተመጣጣኝ ዋጋ ለታዋቂነት ቁልፍ ምክንያት መሆኑን ይጠቁማል.")

# Save the Trend Analysis to a TXT file
trend_analysis_file = os.path.join(output_folder, "trend_analysis.txt")
with open(trend_analysis_file, 'w', encoding='utf-8') as f:
    f.write("\n".join(trend_analysis))

print(f"Trend analysis saved to '{trend_analysis_file}'.")

# Saving decision-making based on data visualization
decisions = []

# Price distribution insights
if len(high_price_items) > 0:
    decisions.append("High-priced items are trending with strong demand in premium categories.")
    decisions.append("ከፍተኛ ዋጋ ያላቸው እቃዎች በጣም ተደጋጋሚ ናቸው፣ ይህም በፕሪሚየም ምርቶች ላይ የፍላጎት መጨመርን ያሳያል.")
else:
    decisions.append("Consider targeting lower price ranges for a broader market appeal.")
    decisions.append("ለአፍላፊ ገበሬ ማስተዋወቅ በዝቅተኛ ዋጋ ተመራጭ የትኛውንም እቃ ማምረት ተመክሮ ይሆናል።")

decisions_file = os.path.join(output_folder, "decision_making.txt")
with open(decisions_file, 'w', encoding='utf-8') as f:
    f.write("\n".join(decisions))

print(f"Decision-making saved to '{decisions_file}'.")

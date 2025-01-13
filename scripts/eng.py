from playwright.sync_api import sync_playwright
import pandas as pd
import matplotlib.pyplot as plt
import os

# Initialize a list to store all the scraped data
scraped_data = []

# Output settings
output_folder = "web-scraping/ecommerce"
output_file = "engoyes.csv"
os.makedirs(output_folder, exist_ok=True)  # Ensure the output folder exists
output_path = os.path.join(output_folder, output_file)

# Function to scrape data from a single page using Playwright
def scrape_page(page, url):
    print(f"Scraping: {url}")  # Print the current URL being scraped
    page.goto(url)

    # Wait for the page to load and the listings to appear
    page.wait_for_selector('div.col-md-12.listingcolumn.normal.fourcolumn', timeout=10000)

    # Get the listing elements
    listings = page.query_selector_all('div.col-md-12.listingcolumn.normal.fourcolumn')

    if not listings:
        print(f"No listings found on {url}")  # No listings found
        return None

    # Loop through and extract data for each listing
    for listing in listings:
        # Extract title
        title = listing.query_selector('span.listingtitle').inner_text().strip() if listing.query_selector('span.listingtitle') else 'N/A'
        
        # Extract price
        price_text = listing.query_selector('span.price').inner_text().strip() if listing.query_selector('span.price') else 'N/A'
        try:
            price = float(price_text.replace('ETB', '').replace(',', '').strip()) if price_text != 'N/A' else None
        except ValueError:
            price = None  # Handle invalid price formats
        
        # Extract description
        description = listing.query_selector('div.row.smalldesc').inner_text().strip() if listing.query_selector('div.row.smalldesc') else 'N/A'
        
        # Extract condition
        condition = listing.query_selector('div.attrib.cond.new').inner_text().strip() if listing.query_selector('div.attrib.cond.new') else 'N/A'
        
        # Extract location
        location = listing.query_selector('span.location').inner_text().strip() if listing.query_selector('span.location') else 'N/A'

        # Store the extracted data in a dictionary
        data = {
            'Title': title,
            'Price': price,
            'Description': description,
            'Condition': condition,
            'Location': location
        }
        scraped_data.append(data)  # Add data to the list

    # Handle pagination - look for the "Next" button
    next_button = page.query_selector('a:has-text("Next »")')
    if next_button:
        next_page_url = next_button.get_attribute('href')
        print(f"Moving to the next page: {next_page_url}")  # Print next page URL
        return next_page_url
    else:
        print("No more pages to scrape.")  # No more pages to scrape
        return None  # No more pages to scrape

# Function to scrape multiple pages starting from the first one
def scrape_all_pages(start_url):
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
            url = scrape_page(page, url)  # Scrape the current page and get the next page URL
            
        # Close the browser after scraping all pages
        browser.close()

# Starting URL (the first page)
start_url = "https://engocha.com/business/30783-barkot?page=1"

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
bars = plt.bar(valid_prices.index, valid_prices['Price'], color='skyblue', edgecolor='black')

# Add titles on top of each bar
for bar, title in zip(bars, valid_prices['Title']):
    plt.text(
        bar.get_x() + bar.get_width() / 2,  # x-coordinate (center of the bar)
        bar.get_height() + 0.5,  # y-coordinate (just above the bar)
        title[:10] + "..." if len(title) > 10 else title,  # Concise title
        ha='center', fontsize=8, rotation=45
    )

# Add overall labels and titles
plt.title('Price Distribution and Range of Items')
plt.xlabel('Items (Scraped Titles)')
plt.ylabel('Price (ETB)')
plt.xticks(valid_prices.index, valid_prices['Title'], rotation=90, fontsize=8)

# Save the plot as a JPEG file
plot_path = os.path.join(output_folder, "price_distribution_with_titles.jpeg")
plt.tight_layout()
plt.savefig(plot_path)
plt.close()

print(f"Price distribution plot with titles saved to '{plot_path}'.")

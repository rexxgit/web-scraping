from playwright.sync_api import sync_playwright
import pandas as pd
import time
import os

def scrape():
    output_folder = "web-scraping/ecommerce"
    output_file = "furniture.csv"
    os.makedirs(output_folder, exist_ok=True)  # Ensure output folder exists
    output_path = os.path.join(output_folder, output_file)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
        context = browser.new_context(user_agent=user_agent)
        page = context.new_page()
        page.goto('https://jiji.com.et/addis-ababa/furniture?filter_attr_248_type=Sofas')

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
        else:
            print("No new data found. Existing file remains unchanged.")

        browser.close()

scrape()

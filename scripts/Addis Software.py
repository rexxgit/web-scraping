import requests
from bs4 import BeautifulSoup
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
import os

# Directory to save the PDF file
output_dir = 'website development companies in A.A/'
os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists

# Scrape website data
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
url = 'https://addissoftware.com/'
response = requests.get(url, headers=headers)

if response.status_code == 200:
    print("Page penetrated successfully")
else:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")
    exit()

soup = BeautifulSoup(response.text, 'html.parser')
data = []

items = soup.find_all('article', class_='post-5 page type-page status-publish has-post-thumbnail hentry')

for item in items:
    aboutus = item.find('div', class_='about_us_content').get_text(strip=True) if item.find('div', class_='about_us_content') else 'N/A'
    ourservices = item.find('div', class_='our_service_content').get_text(strip=True) if item.find('div', class_='our_service_content') else 'N/A'
    ourproduct = item.find('div', class_='our_product_content').get_text(strip=True) if item.find('div', class_='our_product_content') else 'N/A'
    corevalues = item.find('table', class_='core--values d-flex flex-wrap justify-content-between').get_text(strip=True) if item.find('table', class_='core--values d-flex flex-wrap justify-content-between') else 'N/A'
    ourprojects = item.find('div', class_='projects').get_text(strip=True) if item.find('div', class_='projects') else 'N/A'
    testimonials = item.find('section', class_='blog--container--fluid').get_text(strip=True) if item.find('section', class_='blog--container--fluid') else 'N/A'
    contactus = item.find('div', class_='footer_left second_footer_left').get_text(strip=True) if item.find('div', class_='footer_left second_footer_left') else 'N/A'

    data.append({
        'About Us': aboutus,
        'Our Services': ourservices,
        'Our Product': ourproduct,
        'Core Values': corevalues,
        'Our Projects': ourprojects,
        'Testimonials': testimonials,
        'Contact Us': contactus,
    })

# Save data to structured PDF
pdf_file = os.path.join(output_dir, "addis_software_structured.pdf")
doc = SimpleDocTemplate(pdf_file, pagesize=letter)
styles = getSampleStyleSheet()

# Create PDF content
content = []
for record in data:
    for key, value in record.items():
        # Add section heading
        content.append(Paragraph(f"<b>{key}:</b>", styles['Heading3']))
        # Add section content
        content.append(Paragraph(value, styles['BodyText']))
        # Add space between sections
        content.append(Spacer(1, 12))
    # Add space between records
    content.append(Spacer(1, 24))

# Build the PDF
doc.build(content)
print(f"Data saved to {pdf_file} successfully.")

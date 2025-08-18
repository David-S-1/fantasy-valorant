from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import json
import re
from bs4 import BeautifulSoup, Tag

# Set up Selenium with headless Chrome
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--window-size=1920,1080')

service = Service('chromedriver-win64/chromedriver.exe')
driver = webdriver.Chrome(service=service, options=chrome_options)

event_url = "https://www.vlr.gg/event/2282/valorant-masters-toronto-2025"  # Change this for any event
driver.get(event_url)
time.sleep(2)  # Wait for page to load

# Click 'Show More' until all matches are loaded
while True:
    try:
        show_more = driver.find_element(By.XPATH, "//a[contains(text(), 'Show More')]")
        driver.execute_script("arguments[0].scrollIntoView();", show_more)
        time.sleep(0.5)
        show_more.click()
        time.sleep(1.5)
    except Exception:
        break

# Parse the fully loaded page with BeautifulSoup
page_source = driver.page_source
soup = BeautifulSoup(page_source, 'html.parser')

# Find all section headers containing 'Playoffs'
playoff_urls = set()
section_headers = soup.find_all(['div', 'h2', 'h3', 'span'], string=lambda s: s and 'playoff' in s.lower())
for header in section_headers:
    # Walk through following siblings until the next section header
    for sib in header.find_all_next():
        if sib.name in ['div', 'h2', 'h3', 'span'] and sib.string and any(x in sib.string.lower() for x in ['group stage', 'swiss', 'round robin', 'main event', 'regular season', 'league', 'stage', 'bracket', 'playoff']) and sib is not header:
            break  # Stop at next section header
        # Collect match links in this sibling
        if isinstance(sib, Tag):
            for a in sib.find_all('a', class_='wf-module-item'):
                href = a.get('href')
                if href and re.match(r"/\d+/.+", href):
                    url = 'https://www.vlr.gg' + href
                    if '?tab=overview' not in url:
                        url += '?tab=overview'
                    playoff_urls.add(url)

print(f"Found {len(playoff_urls)} playoff match URLs (global section scan):")
for url in sorted(playoff_urls):
    print(url)

# Save to JSON file
with open('json/masters_toronto_2025_playoff_urls.json', 'w') as f:
    json.dump(sorted(playoff_urls), f, indent=2)

print('Done! Saved all playoff match URLs to json/masters_toronto_2025_playoff_urls.json')

driver.quit()

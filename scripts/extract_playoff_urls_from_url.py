import requests
import json
from bs4 import BeautifulSoup

# Change this to the event URL you want to parse
# Example: 'https://www.vlr.gg/event/2282/valorant-masters-toronto-2025'
event_urls = [
    'https://www.vlr.gg/event/2501/vct-2025-americas-stage-2'
]
# 'https://www.vlr.gg/event/2282/valorant-masters-toronto-2025',
# 'https://www.vlr.gg/event/2347/vct-2025-americas-stage-1',
# 'https://www.vlr.gg/event/2097/valorant-champions-2024/group-stage'

headers = {'User-Agent': 'Mozilla/5.0'}

for event_url in event_urls:
    print(f'\n==== {event_url} ===')
    res = requests.get(event_url, headers=headers)
    if res.status_code != 200:
        print(f'Failed to fetch {event_url} (status {res.status_code})')
        continue
    soup = BeautifulSoup(res.text, 'html.parser')

    playoff_urls = set()
    # Find all bracket columns (each round)
    for col in soup.find_all('div', class_='bracket-col'):
        # Get the round label
        label_div = col.find('div', class_='bracket-col-label')
        round_label = label_div.get_text(strip=True) if label_div else 'Unknown Round'
        # Find all match links in this column
        urls = []
        for a in col.find_all('a', class_='bracket-item'):
            href = a.get('href')
            if href and href.startswith('/'):
                url = 'https://www.vlr.gg' + href
                if '?tab=overview' not in url:
                    url += '?tab=overview'
                urls.append(url)
                playoff_urls.add(url)
        if urls:
            print(f'[{round_label}]')
            for url in urls:
                print(' ', url)

    # Save all found playoff match URLs to a JSON file
    event_id = event_url.rstrip('/').split('/')[-1]
    out_json = f'{event_id}_playoff_urls.json'
    with open(out_json, 'w') as f:
        json.dump(sorted(playoff_urls), f, indent=2)
    print(f'Saved {len(playoff_urls)} playoff match URLs to {out_json}')

from typing import Dict, List
import re

from bs4 import BeautifulSoup

from .http import http
from .models import MatchMeta


async def get_stage_matchlist_urls(event_url: str) -> Dict[str, str]:
    """Find all stage match-list URLs from the event's Matches tab.
    Returns dict mapping stage names to their match list URLs.
    """
    resp = await http.get(event_url)
    if resp.status_code != 200:
        print(f'Failed to fetch {event_url} (status {resp.status_code})')
        return {}

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Find the Matches tab link
    matches_tab = None
    for a in soup.find_all('a', class_='wf-nav-item'):
        if a.get_text(strip=True).lower().startswith('matches'):
            matches_tab = a.get('href')
            break

    if not matches_tab:
        print('Could not find Matches tab for event')
        return {}

    matches_url = 'https://www.vlr.gg' + matches_tab
    resp2 = await http.get(matches_url)
    if resp2.status_code != 200:
        print(f'Failed to fetch {matches_url} (status {resp2.status_code})')
        return {}

    soup2 = BeautifulSoup(resp2.text, 'html.parser')

    # Find all stage links in the stage dropdown
    stage_urls = {}
    for a in soup2.find_all('a'):
        txt = a.get_text(strip=True).lower()
        href = a.get('href')
        if href and href.startswith('/event/matches/') and 'series_id=' in href:
            if 'playoff' in txt:
                stage_urls['playoffs'] = 'https://www.vlr.gg' + href
            elif 'swiss' in txt:
                stage_urls['swiss'] = 'https://www.vlr.gg' + href
            elif 'group' in txt:
                stage_urls['group'] = 'https://www.vlr.gg' + href
            else:
                # fallback: use the text as key
                stage_urls[txt.replace(' ', '_')] = 'https://www.vlr.gg' + href

    # If no stage links found, fallback to matches_url
    if not stage_urls:
        stage_urls['main'] = matches_url

    return stage_urls


async def extract_list_match_urls(stage_url: str) -> List[str]:
    """Extract all match URLs from a stage match list page."""
    resp = await http.get(stage_url)
    if resp.status_code != 200:
        print(f'Failed to fetch {stage_url} (status {resp.status_code})')
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    match_urls = set()

    for a in soup.find_all('a', class_='wf-module-item'):
        href = a.get('href')
        classes = a.get('class', [])
        if href and href.startswith('/') and 'match-item' in classes:
            url = 'https://www.vlr.gg' + href
            if '?tab=overview' not in url:
                url += '?tab=overview'
            match_urls.add(url)

    return sorted(match_urls)


async def discover_matches(event_url: str) -> List[MatchMeta]:
    """Discover match overview URLs for an event page via comprehensive HTML parsing.
    Returns list of MatchMeta with basic fields (id, url). Stage detection minimal (best effort).
    """
    # Get all stage URLs for this event
    stage_urls = await get_stage_matchlist_urls(event_url)
    if not stage_urls:
        return []

    matches: List[MatchMeta] = []

    # Extract matches from each stage
    for stage_name, stage_url in stage_urls.items():
        print(f"-- Stage: {stage_name} ({stage_url})")
        stage_matches = await extract_list_match_urls(stage_url)
        print(f"Found {len(stage_matches)} matches for stage {stage_name}")

        for match_url in stage_matches:
            # Extract match ID from URL
            m = re.match(r"https://www.vlr.gg/(\d+)/", match_url)
            match_id = m.group(1) if m else match_url

            # Determine stage type
            stage = stage_name
            if stage_name in ('playoffs', 'swiss', 'group'):
                stage = stage_name
            else:
                stage = 'playoffs' if 'final' in stage_name or 'playoff' in stage_name or 'bracket' in stage_name else 'group'

            matches.append(MatchMeta(match_id=match_id, url=match_url, stage=stage))

    # De-dup by match ID (in case same match appears in multiple stages)
    uniq: Dict[str, MatchMeta] = {}
    for m in matches:
        uniq[m.match_id] = m

    return list(uniq.values())

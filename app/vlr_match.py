import hashlib
import re
from typing import Dict, List, Tuple

from bs4 import BeautifulSoup

from .http import http
from .models import MapStats, PlayerMapStats


async def fetch_match(match_url: str) -> Tuple[str, str]:
    """Fetch overview HTML and performance (all) HTML for a match."""
    overview_resp = await http.get(match_url)
    base_url = match_url.split('?')[0]
    perf_all_url = f"{base_url}?game=all&tab=performance"
    perf_resp = await http.get(perf_all_url)
    return overview_resp.text, perf_resp.text


def content_hash(*html_parts: str) -> str:
    h = hashlib.sha256()
    for part in html_parts:
        h.update(part.encode('utf-8', errors='ignore'))
    return h.hexdigest()


def parse_overview_for_maps(match_url: str, overview_html: str) -> List[Tuple[int, str]]:
    soup = BeautifulSoup(overview_html, 'html.parser')
    map_blocks = soup.find_all('div', class_='vm-stats-game')
    maps = []
    for block in map_blocks:
        game_id = block.get('data-game-id')
        if not game_id or game_id == 'all':
            continue
        map_num = len(maps) + 1
        name_div = block.find('div', class_='map')
        map_name = name_div.text.strip().split('\n')[0].strip() if name_div else None
        maps.append((map_num, map_name or ''))
    return maps


def parse_performance_all(perf_html_all: str) -> Dict[str, Dict[str, int]]:
    """Parse performance(all) multikills per player.
    Returns dict name -> { '2K': int, '3K': int, '4K': int, '5K': int, 'r2_0': float? }
    """
    soup = BeautifulSoup(perf_html_all, 'html.parser')
    # Find all advanced stats tables; infer structure like original scripts
    result: Dict[str, Dict[str, int]] = {}
    for table in soup.find_all('table', class_='mod-adv-stats'):
        for row in table.find_all('tr'):
            name_tag = row.find('div', class_='team')
            if not name_tag:
                continue
            name = name_tag.text.strip().split('\n')[0].strip()
            cells = row.find_all('td')
            def safe_int(cell_idx: int) -> int:
                try:
                    if cell_idx >= len(cells):
                        return 0
                    numbers = re.findall(r'\d+', cells[cell_idx].text.strip())
                    return int(numbers[0]) if numbers else 0
                except Exception:
                    return 0
            result.setdefault(name, {})
            result[name]['2K'] = safe_int(2)
            result[name]['3K'] = safe_int(3)
            result[name]['4K'] = safe_int(4)
            result[name]['5K'] = safe_int(5)
    # Overall R2.0: parse 'all' block
    for table in soup.find_all('table'):
        for row in table.find_all('tr'):
            name_tag = row.find('div', class_='text-of')
            stat_cells = row.find_all('td', class_='mod-stat')
            if not name_tag or not stat_cells:
                continue
            r2_span = stat_cells[0].find('span', class_='side mod-side mod-both')
            if r2_span:
                try:
                    val = float(r2_span.text.strip())
                except Exception:
                    val = None
                name = name_tag.text.strip()
                result.setdefault(name, {})
                if val is not None:
                    result[name]['r2_0'] = val
    return result


def parse_maps_with_players(match_url: str, overview_html: str, perf_all: Dict[str, Dict[str, int]]) -> List[MapStats]:
    soup = BeautifulSoup(overview_html, 'html.parser')
    map_blocks = [b for b in soup.find_all('div', class_='vm-stats-game') if b.get('data-game-id') != 'all']
    results: List[MapStats] = []
    for idx, block in enumerate(map_blocks, start=1):
        map_name_div = block.find('div', class_='map')
        map_name = map_name_div.text.strip().split('\n')[0].strip() if map_name_div else None
        kda_tables = block.find_all('table')
        players: List[PlayerMapStats] = []
        for t_idx, kda_table in enumerate(kda_tables):
            kda_tbodies = kda_table.find_all('tbody')
            for tbody in kda_tbodies:
                for row in tbody.find_all('tr'):
                    name_tag = row.find('div', class_='text-of')
                    kills_tag = row.find('td', class_='mod-vlr-kills')
                    assists_tag = row.find('td', class_='mod-vlr-assists')
                    deaths_tag = row.find('td', class_='mod-vlr-deaths')
                    if not name_tag or not kills_tag or not assists_tag or not deaths_tag:
                        continue
                    name = name_tag.text.strip()
                    def num(span_class: str) -> int:
                        try:
                            return int(row.find('td', class_=span_class).find('span', class_='mod-both').text.strip())
                        except Exception:
                            return 0
                    kills = num('mod-vlr-kills')
                    assists = num('mod-vlr-assists')
                    deaths = num('mod-vlr-deaths')
                    pm = PlayerMapStats(
                        name=name,
                        kills=kills,
                        deaths=deaths,
                        assists=assists,
                        two_k=perf_all.get(name, {}).get('2K', 0),
                        three_k=perf_all.get(name, {}).get('3K', 0),
                        four_k=perf_all.get(name, {}).get('4K', 0),
                        five_k=perf_all.get(name, {}).get('5K', 0),
                        r2_0=perf_all.get(name, {}).get('r2_0'),
                    )
                    players.append(pm)
        # match_id not parsed here; callers should set
        results.append(MapStats(match_id='', map_num=idx, map_name=map_name, players=players))
    return results

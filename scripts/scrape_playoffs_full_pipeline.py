import requests
import json
import re
import time
from bs4 import BeautifulSoup
from score_calc import calc_score

headers = {'User-Agent': 'Mozilla/5.0'}

def get_event_id(event_url):
    m = re.search(r'/event/(\d+)', event_url)
    if m:
        return m.group(1)
    return 'event'

def get_event_name(event_url):
    res = requests.get(event_url, headers=headers)
    if res.status_code != 200:
        return 'event'
    soup = BeautifulSoup(res.text, 'html.parser')
    h1 = soup.find('h1')
    if h1:
        name = h1.text.strip()
        # Clean for filename: lowercase, replace spaces with underscores, remove non-alphanum/underscore
        name = name.lower().replace(' ', '_')
        name = re.sub(r'[^a-z0-9_]+', '', name)
        return name
    return 'event'

# Find all stage match-list URLs from the event's Matches tab
def get_stage_matchlist_urls(event_url):
    res = requests.get(event_url, headers=headers)
    if res.status_code != 200:
        print(f'Failed to fetch {event_url} (status {res.status_code})')
        return {}
    soup = BeautifulSoup(res.text, 'html.parser')
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
    res2 = requests.get(matches_url, headers=headers)
    if res2.status_code != 200:
        print(f'Failed to fetch {matches_url} (status {res2.status_code})')
        return {}
    soup2 = BeautifulSoup(res2.text, 'html.parser')
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

def extract_list_match_urls(stage_url):
    res = requests.get(stage_url, headers=headers)
    if res.status_code != 200:
        print(f'Failed to fetch {stage_url} (status {res.status_code})')
        return []
    soup = BeautifulSoup(res.text, 'html.parser')
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

def scrape_match(overview_url):
    overview_res = requests.get(overview_url, headers=headers)
    overview_soup = BeautifulSoup(overview_res.text, 'html.parser')
    map_blocks = overview_soup.find_all('div', class_='vm-stats-game')
    actual_map_blocks = [block for block in map_blocks if block.get('data-game-id') != 'all']
    all_maps_data = {}
    series_team_tags = set()
    series_map_wins = {}
    series_team_names = {}
    for map_idx, map_block in enumerate(actual_map_blocks):
        map_key = f"Map {map_idx + 1}"
        game_id = map_block['data-game-id']
        base_url = overview_url.split('?')[0]
        performance_url = f"{base_url}?game={game_id}&tab=performance"
        perf_res = requests.get(performance_url, headers=headers)
        perf_soup = BeautifulSoup(perf_res.text, 'html.parser')
        team_divs = map_block.find_all('div', class_='team')
        if len(team_divs) >= 2:
            left_team_div = team_divs[0]
            right_team_div = team_divs[1]
            left_team_tag_div = left_team_div.find('div', class_='team-tag')
            right_team_tag_div = right_team_div.find('div', class_='team-tag')
            left_team_tag = left_team_tag_div.text.strip().lower() if left_team_tag_div else left_team_div.find('div', class_='team-name').text.strip().lower()
            right_team_tag = right_team_tag_div.text.strip().lower() if right_team_tag_div else right_team_div.find('div', class_='team-name').text.strip().lower()
            left_team_name = left_team_div.find('div', class_='team-name').text.strip()
            right_team_name = right_team_div.find('div', class_='team-name').text.strip()
        else:
            left_team_tag = right_team_tag = ''
            left_team_name = right_team_name = ''
        series_team_tags.add(left_team_tag)
        series_team_tags.add(right_team_tag)
        series_team_names[left_team_tag] = left_team_name
        series_team_names[right_team_tag] = right_team_name
        winner_block = map_block.find('div', class_='mod-win')
        if winner_block:
            team_parent = winner_block.find_parent('div', class_='team')
            winner_name = team_parent.find('div', class_='team-name').text.strip() if team_parent else 'Unknown'
            winner_tag_div = team_parent.find('div', class_='team-tag') if team_parent else None
            if winner_tag_div:
                winner_tag = winner_tag_div.text.strip().lower()
            else:
                winner_tag = winner_name.strip().lower() if winner_name != 'Unknown' else 'Unknown'
        else:
            winner_name = 'Unknown'
            winner_tag = 'Unknown'
        score_blocks = map_block.find_all('div', class_='score')
        if len(score_blocks) >= 2:
            left_score = int(score_blocks[0].text.strip())
            right_score = int(score_blocks[1].text.strip())
            score_str = f"{left_score}-{right_score}"
        else:
            left_score = right_score = None
            score_str = "Unknown"
        if winner_tag == left_team_tag:
            series_map_wins[left_team_tag] = series_map_wins.get(left_team_tag, 0) + 1
        elif winner_tag == right_team_tag:
            series_map_wins[right_team_tag] = series_map_wins.get(right_team_tag, 0) + 1
        kda_tables = map_block.find_all('table')
        player_stats = {}
        map_name = map_block.find('div', class_='map').text.strip() if map_block.find('div', class_='map') else 'Unknown'
        map_name = map_name.strip().split('\n')[0].strip()
        for t_idx, kda_table in enumerate(kda_tables):
            team_tag = left_team_tag if t_idx == 0 else right_team_tag
            kda_tbodies = kda_table.find_all('tbody')
            for i, tbody in enumerate(kda_tbodies):
                kda_rows = tbody.find_all('tr')
                for row in kda_rows:
                    name_tag = row.find('div', class_='text-of')
                    kills_tag = row.find('td', class_='mod-vlr-kills')
                    assists_tag = row.find('td', class_='mod-vlr-assists')
                    deaths_tag = row.find('td', class_='mod-vlr-deaths')
                    r2_td = row.find_all('td', class_='mod-stat')
                    r2_rating = None
                    if r2_td:
                        r2_both = r2_td[0].find('span', class_='side mod-side mod-both')
                        if r2_both:
                            try:
                                r2_rating = float(r2_both.text.strip())
                            except:
                                r2_rating = None
                    if name_tag and kills_tag and assists_tag and deaths_tag:
                        name = name_tag.text.strip()
                        kills = int(kills_tag.find('span', class_='mod-both').text.strip())
                        assists = int(assists_tag.find('span', class_='mod-both').text.strip())
                        deaths = int(deaths_tag.find('span', class_='mod-both').text.strip())
                        player_stats[name] = {
                            'name': name,
                            'kills': kills,
                            'deaths': deaths,
                            'assists': assists,
                            'org': team_tag,
                            'r2_0': r2_rating
                        }
        def safe_int(cell):
            try:
                val = cell.text.strip()
                numbers = re.findall(r'\d+', val)
                return int(numbers[0]) if numbers else 0
            except:
                return 0
        all_mkill_tables = perf_soup.find_all('table', class_='mod-adv-stats')
        target_index = map_idx + 1
        if len(all_mkill_tables) > target_index:
            mkill_table = all_mkill_tables[target_index]
            mkill_rows = mkill_table.find_all('tr')
            for row in mkill_rows:
                org_tag = row.find('div', class_='team-tag')
                name_tag = row.find('div', class_='team')
                if not org_tag or not name_tag:
                    continue
                name = name_tag.text.strip().split('\n')[0].strip()
                cells = row.find_all('td')
                two_k = safe_int(cells[2]) if len(cells) > 2 else 0
                three_k = safe_int(cells[3]) if len(cells) > 3 else 0
                four_k = safe_int(cells[4]) if len(cells) > 4 else 0
                five_k = safe_int(cells[5]) if len(cells) > 5 else 0
                matched_name = None
                for existing_name in player_stats.keys():
                    if name.lower() == existing_name.lower():
                        matched_name = existing_name
                        break
                if matched_name:
                    player_stats[matched_name].update({
                        '2K': two_k,
                        '3K': three_k,
                        '4K': four_k,
                        '5K': five_k
                    })
                else:
                    org = org_tag.text.strip().lower()
                    player_stats[name] = {
                        'name': name,
                        '2K': two_k,
                        '3K': three_k,
                        '4K': four_k,
                        '5K': five_k,
                        'org': org
                    }
        for player in player_stats.values():
            player_org = (player.get('org') or '').strip().lower()
            player['won_map'] = (player_org == winner_tag)
        all_maps_data[map_key] = {
            'map': map_name,
            'players': list(player_stats.values()),
            'winner': winner_name,
            'score': score_str,
            'left_team_tag': left_team_tag,
            'right_team_tag': right_team_tag,
            'left_score': left_score,
            'right_score': right_score
        }
    team_tags = list(series_team_tags)
    if len(team_tags) >= 2:
        team1, team2 = team_tags[0], team_tags[1]
        team1_wins = series_map_wins.get(team1, 0)
        team2_wins = series_map_wins.get(team2, 0)
    else:
        team1 = team2 = ''
        team1_wins = team2_wins = 0
    for map_key, map_data in all_maps_data.items():
        left_team_tag = map_data.get('left_team_tag', '')
        right_team_tag = map_data.get('right_team_tag', '')
        left_score = map_data.get('left_score', None)
        right_score = map_data.get('right_score', None)
        new_players = []
        for player in map_data['players']:
            player_org = (player.get('org') or '').strip().lower()
            if player_org == left_team_tag and left_score is not None and right_score is not None:
                player['map_differential'] = left_score - right_score
            elif player_org == right_team_tag and left_score is not None and right_score is not None:
                player['map_differential'] = right_score - left_score
            else:
                player['map_differential'] = None
            if player_org == team1:
                player['series_score'] = f"{team1_wins}-{team2_wins}"
            elif player_org == team2:
                player['series_score'] = f"{team2_wins}-{team1_wins}"
            else:
                player['series_score'] = None
            new_players.append(player)
        map_data['players'] = new_players
        del map_data['left_team_tag']
        del map_data['right_team_tag']
        del map_data['left_score']
        del map_data['right_score']
    overall_block = next((block for block in map_blocks if block.get('data-game-id') == 'all'), None)
    overall_ratings = []
    if overall_block:
        kda_tables = overall_block.find_all('table')
        for kda_table in kda_tables:
            kda_tbodies = kda_table.find_all('tbody')
            for tbody in kda_tbodies:
                kda_rows = tbody.find_all('tr')
                for row in kda_rows:
                    name_tag = row.find('div', class_='text-of')
                    r2_td = row.find_all('td', class_='mod-stat')
                    r2_rating = None
                    if r2_td:
                        r2_both = r2_td[0].find('span', class_='side mod-side mod-both')
                        if r2_both:
                            try:
                                r2_rating = float(r2_both.text.strip())
                            except:
                                r2_rating = None
                    if name_tag and r2_rating is not None:
                        name = name_tag.text.strip()
                        overall_ratings.append({'name': name, 'r2_0': r2_rating})
    overall_ratings_sorted = sorted(overall_ratings, key=lambda x: x['r2_0'], reverse=True)
    name_to_rank = {}
    for idx, player in enumerate(overall_ratings_sorted, 1):
        name_to_rank[player['name'].lower()] = idx
    for map_data in all_maps_data.values():
        for player in map_data['players']:
            player_name = player['name'].lower()
            player['overall_rank'] = name_to_rank.get(player_name)
    return all_maps_data

if __name__ == '__main__':
    event_urls = [
        'https://www.vlr.gg/event/2498/vct-2025-emea-stage-2',
        'https://www.vlr.gg/event/2500/vct-2025-pacific-stage-2',
        'https://www.vlr.gg/event/2499/vct-2025-china-stage-2',
        'https://www.vlr.gg/event/2501/vct-2025-americas-stage-2'
        # Add more event URLs here
    ]
    for event_url in event_urls:
        event_id = get_event_id(event_url)
        event_name = get_event_name(event_url)
        print(f'\n==== Processing event: {event_url} (id: {event_id}, name: {event_name}) ===')
        stage_urls = get_stage_matchlist_urls(event_url)
        print(f"Stage URLs found: {stage_urls}")
        seen_urls = set()
        all_stats_combined = []
        all_points_combined = {}
        # Determine which group stage key to use
        group_stage_key = None
        if 'group' in stage_urls:
            group_stage_key = 'group'
        elif 'swiss' in stage_urls:
            group_stage_key = 'swiss'
        stage_keys_to_process = ['playoffs']
        if group_stage_key:
            stage_keys_to_process.append(group_stage_key)
        for stage_key in stage_keys_to_process:
            stage_url = stage_urls.get(stage_key)
            if not stage_url or stage_url in seen_urls:
                continue
            seen_urls.add(stage_url)
            print(f'\n-- Stage: {stage_key} ({stage_url})')
            match_urls = extract_list_match_urls(stage_url)
            print(f'Found {len(match_urls)} matches for stage {stage_key}')
            all_stats = []
            for i, match_url in enumerate(match_urls, 1):
                print(f"Scraping match {i}/{len(match_urls)}: {match_url}")
                try:
                    match_maps = scrape_match(match_url)
                    for map_data in match_maps.values():
                        for player in map_data['players']:
                            player_copy = dict(player)
                            player_copy['match_url'] = match_url
                            player_copy['map_name'] = map_data.get('map', '')
                            all_stats.append(player_copy)
                    time.sleep(1)
                except Exception as e:
                    print(f"Error scraping {match_url}: {e}")
            stats_file = f'json/{event_name}_{stage_key}_stats.json'
            with open(stats_file, 'w') as f:
                json.dump(all_stats, f, indent=2)
            player_points = {}
            for player in all_stats:
                name = player['name']
                try:
                    player_points[name] = player_points.get(name, 0) + calc_score(player)
                except Exception as e:
                    print(f"Error calculating score for {name}: {e}")
            points_file = f'json/{event_name}_{stage_key}_points.json'
            with open(points_file, 'w') as f:
                json.dump(player_points, f, indent=2)
            print(f'Saved stats to {stats_file} and points to {points_file}')
            # Combine for all stages
            all_stats_combined.extend(all_stats)
            for name, pts in player_points.items():
                all_points_combined[name] = all_points_combined.get(name, 0) + pts
        # Save combined stats and points
        all_stats_file = f'json/{event_name}_all_stages_stats.json'
        with open(all_stats_file, 'w') as f:
            json.dump(all_stats_combined, f, indent=2)
        all_points_file = f'json/{event_name}_all_points.json'
        with open(all_points_file, 'w') as f:
            json.dump(all_points_combined, f, indent=2)
        print(f'Combined stats saved to {all_stats_file} and points to {all_points_file}')

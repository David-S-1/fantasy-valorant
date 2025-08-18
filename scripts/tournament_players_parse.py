import json
import requests
from bs4 import BeautifulSoup
from agents_to_roles import agents_to_roles
from collections import Counter, defaultdict
import re

def get_role_from_agents(agent_counts):
    # agent_counts: dict of agent -> count
    role_counts = Counter()
    for agent, count in agent_counts.items():
        role = agents_to_roles.get(agent, None)
        if role:
            role_counts[role] += count
    if not role_counts:
        return None
    max_count = max(role_counts.values())
    roles = [r for r, c in role_counts.items() if c == max_count]
    return "".join(sorted(roles)), dict(role_counts)

def get_event_name(soup):
    # Try to get from <h1> first
    h1 = soup.find('h1')
    if h1 and h1.text.strip():
        name = h1.text.strip()
    else:
        # Fallback to <title>
        title = soup.find('title')
        name = title.text.strip() if title else "event"
    # Clean for filename: lowercase, replace spaces with underscores, remove non-alphanum/underscore
    name = name.lower().replace(' ', '_')
    name = re.sub(r'[^a-z0-9_]+', '', name)
    return name

def parse_vlr_stats(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    event_name = get_event_name(soup)
    table = soup.find("table", class_="wf-table mod-stats mod-scroll")
    if not table:
        raise Exception("Could not find stats table on the page.")
    players = {}
    for row in table.find("tbody").find_all("tr"):
        cols = row.find_all("td")
        # Player name and team
        player_div = cols[0].find("div", class_="text-of")
        player_name = player_div.text.strip() if player_div else None
        team_div = cols[0].find("div", class_="stats-player-country")
        team = team_div.text.strip() if team_div else None
        # Agents and agent counts
        agent_imgs = cols[1].find_all("img")
        agent_counts = Counter()
        for img in agent_imgs:
            agent = img["src"].split("/")[-1].replace(".png", "").capitalize()
            agent_counts[agent] += 1
        agents = list(agent_counts.elements())
        # R2.0, ACS, KAST
        try:
            r2_0 = float(cols[3].text.strip())
        except:
            r2_0 = None
        try:
            acs = float(cols[4].text.strip())
        except:
            acs = None
        kast = cols[6].text.strip().replace("%", "")
        try:
            kast = float(kast)
        except:
            kast = None
        # Role
        role, role_counts = get_role_from_agents(agent_counts)
        players[player_name] = {
            "team": team,
            "r2_0": r2_0,
            "acs": acs,
            "kast": kast,
            "agents": dict(agent_counts),
            "role": role,
            "role_counts": role_counts
        }
    return players, event_name

if __name__ == "__main__":
    url = input("Enter VLR.gg tournament stats URL (e.g. https://www.vlr.gg/event/2499/vct-2025-china-stage-2/stats/): ").strip()
    players, event_name = parse_vlr_stats(url)
    out_path = f"json/{event_name}_players.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(players, f, indent=2, ensure_ascii=False)
    print(f"Parsed and saved player data to {out_path}")

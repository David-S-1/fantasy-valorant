import json
import re
from score_calc import calc_score

# Load the tournament data
with open('json/masters_toronto_2025_tournament.json') as f:
    tournament = json.load(f)

matches = tournament['matches']

# Define playoff match keywords (case-insensitive)
playoff_keywords = [
    'ub', 'lb', 'gf', 'sf', 'final', 'playoff', 'semifinal', 'quarterfinal', 'decider', 'bracket', 'elimination', 'grand'
]

def is_playoff_match(match_id, match_url):
    if 'swiss' in match_id.lower() or 'swiss' in match_url.lower():
        return False
    for kw in playoff_keywords:
        if kw in match_id.lower() or kw in match_url.lower():
            return True
    return False

# Helper to fix winner and won_map fields in map data
def fix_map_winner_and_won_map(map_data):
    left_team = map_data.get('left_team', '').strip().lower()
    right_team = map_data.get('right_team', '').strip().lower()
    left_score = map_data.get('left_score')
    right_score = map_data.get('right_score')
    winner = map_data.get('winner', '').strip().lower()
    # Fix winner if unknown and scores are present
    if (winner == 'unknown' or not winner) and left_score is not None and right_score is not None:
        if left_score > right_score:
            winner = left_team
        elif right_score > left_score:
            winner = right_team
        else:
            winner = 'draw'  # unlikely, but just in case
        map_data['winner'] = winner
    # Fix won_map for each player
    for player in map_data.get('players', []):
        player_org = (player.get('org') or '').strip().lower()
        player['won_map'] = (player_org == winner)

# Aggregate all playoff player stats
all_playoff_stats = []
for match in matches.values():
    match_id = match.get('match_id', '')
    match_url = match.get('match_url', '')
    if not is_playoff_match(match_id, match_url):
        continue
    for map_data in match.get('maps', {}).values():
        fix_map_winner_and_won_map(map_data)
        for player in map_data.get('players', []):
            # Add match and map info for context
            player_copy = dict(player)
            player_copy['match_id'] = match_id
            player_copy['match_url'] = match_url
            player_copy['map_name'] = map_data.get('map_name', '')
            # Ensure all fields required by calc_score are present and valid
            for key, default in [
                ('kills', 0),
                ('deaths', 0),
                ('assists', 0),
                ('2K', 0),
                ('3K', 0),
                ('4K', 0),
                ('5K', 0),
                ('won_map', False),
                ('map_differential', 0),
                ('series_score', ''),
                ('r2_0', 0.0),
                ('overall_rank', 0)
            ]:
                if key not in player_copy or player_copy[key] in [None, 'unknown', '']:
                    player_copy[key] = default
            all_playoff_stats.append(player_copy)

# Save all playoff stats to a file
with open('json/masters_toronto_2025_playoffs_stats.json', 'w') as f:
    json.dump(all_playoff_stats, f, indent=2)

# Calculate points for each player across all playoff maps
player_points = {}
for player in all_playoff_stats:
    name = player['name']
    try:
        player_points[name] = player_points.get(name, 0) + calc_score(player)
    except Exception as e:
        print(f"Error calculating score for {name}: {e}")

# Save player points to a file
with open('json/masters_toronto_2025_playoffs_points.json', 'w') as f:
    json.dump(player_points, f, indent=2)

print('Done! Saved stats to json/masters_toronto_2025_playoffs_stats.json and points to json/masters_toronto_2025_playoffs_points.json')

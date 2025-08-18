import json
from score_calc import calc_score

# Load the aggregated player stats (one entry per player per map)
with open('json/valorant_masters_toronto_2025_playoffs_stats.json') as f:
    stats = json.load(f)

player_points = {}
player_games = {}
player_org = {}

# Aggregate total points and games played for each player
for entry in stats:
    name = entry['name']
    org = entry.get('org', '')
    points = calc_score(entry)
    player_points[name] = player_points.get(name, 0) + points
    player_games[name] = player_games.get(name, 0) + 1
    player_org[name] = org

results = []
for name in player_points:
    total_points = player_points[name]
    games_played = player_games[name]
    org = player_org[name]
    ppg = total_points / games_played if games_played > 0 else 0
    expected_cost = 0.62 * ppg + 4.74
    expected_cost = round(expected_cost * 2) / 2
    actual_cost = min(expected_cost, 15)
    results.append({
        "name": name,
        "org": org,
        "total_points": total_points,
        "games_played": games_played,
        "ppg": ppg,
        "expected_cost": expected_cost,
        "actual_cost": actual_cost
    })

# Output results (print and save to file)
with open('player_costs.json', 'w') as f:
    json.dump(results, f, indent=2)

# for r in results:
#     print(f"{r['name']} ({r['org']}): Total Points={r['total_points']}, Games Played={r['games_played']}, PPG={r['ppg']:.2f}, Expected Cost={r['expected_cost']}, Actual Cost={r['actual_cost']}")

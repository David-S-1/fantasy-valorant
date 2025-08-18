import json
from score_calc import calc_score
import os

def process_file(filename):
    player_points = {}
    player_games = {}

    with open(filename, encoding="utf-8") as f:
        data = json.load(f)
    for entry in data:
        name = entry["name"]
        player_points[name] = player_points.get(name, 0) + calc_score(entry)
        player_games[name] = player_games.get(name, 0) + 1

    player_ppg = {name: (player_points[name] / player_games[name]) for name in player_points}
    player_cost = {name: round((0.62 * ppg + 4.74) * 2) / 2 for name, ppg in player_ppg.items()}

    output = []
    for name in player_points:
        output.append({
            "name": name,
            "ppg": player_ppg[name],
            "cost": player_cost[name],
            "games_played": player_games[name],
            "total_points": player_points[name]
        })

    # Save with event name in filename
    base = os.path.basename(filename)
    event_name = base.replace("_all_stages_stats.json", "").replace(".json", "")
    out_path = f"json/{event_name}_ppg_cost.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Saved player PPG and cost data to {out_path}")

if __name__ == "__main__":
    # MANUALLY LIST THE FILES TO USE HERE:
    file_list = [
        "json/vct_2025_americas_stage_2_all_stages_stats.json",
        "json/vct_2025_emea_stage_2_all_stages_stats.json",
        "json/vct_2025_pacific_stage_2_all_stages_stats.json",
        "json/vct_2025_china_stage_2_all_stages_stats.json",
        # Add more files as needed
    ]
    for file in file_list:
        process_file(file)

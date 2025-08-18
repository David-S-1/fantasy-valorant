import json
from player_info import players

# Build a lowercase-name-to-info mapping for robust matching
players_lower = {k.lower(): v for k, v in players.items()}

with open("player_costs.json") as f:
    costs = json.load(f)

merged = []
for p in costs:
    name = p["name"]
    # Try to match by lowercase name
    info = players_lower.get(name.lower())
    role = info["Role"] if info and "Role" in info else None
    merged.append({
        "name": name,
        "ppg": p.get("ppg", 0),
        "cost": p.get("actual_cost", p.get("Cost", 0)),
        "role": role,
        "org": p.get("org", "")
    })

with open("player_display.json", "w") as f:
    json.dump(merged, f, indent=2)

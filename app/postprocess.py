import json
import os

from player_info import players as base_players
from .storage import write_json


def build_player_display(json_dir: str = './json') -> str:
    """Merge player costs with player_info to produce player_display.json in repo root (compat with original).
    Prefers 'player_costs.json' if present, fallback to first '*_ppg_cost.json'.
    Returns written file path.
    """
    costs_path = 'player_costs.json'
    costs = None
    if os.path.exists(costs_path):
        with open(costs_path, 'r', encoding='utf-8') as f:
            costs = json.load(f)
    else:
        # try any ppg_cost file
        for name in os.listdir(json_dir):
            if name.endswith('_ppg_cost.json'):
                with open(os.path.join(json_dir, name), 'r', encoding='utf-8') as f:
                    costs = json.load(f)
                break
    if costs is None:
        costs = []
    players_lower = {k.lower(): v for k, v in base_players.items()}
    merged = []
    for p in costs:
        name = p.get('name')
        if not name:
            continue
        info = players_lower.get(name.lower())
        role = info.get('Role') if info and isinstance(info, dict) else None
        merged.append({
            'name': name,
            'ppg': p.get('ppg', 0),
            'cost': p.get('actual_cost', p.get('cost', 0)),
            'role': role,
            'org': p.get('org', ''),
        })

    # Use new storage system - write to repo root for compatibility
    out_filename = 'player_display.json'
    written = write_json(out_filename, merged)
    return written[0] if written else out_filename

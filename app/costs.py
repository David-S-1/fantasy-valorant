from typing import Dict, Iterable, List, Tuple
import json
import os

import numpy as np
from sklearn.linear_model import LinearRegression


def fit_cost_model(points_cost_rows: List[Tuple[float, float]]) -> Tuple[float, float]:
    """Fit linear regression Cost = a*PPG + b.
    Input list rows as (ppg, cost).
    Returns (a, b).
    """
    if not points_cost_rows:
        # Default from existing code heuristic
        return 0.62, 4.74
    X = np.array([[ppg] for ppg, _ in points_cost_rows])
    y = np.array([cost for _, cost in points_cost_rows])
    reg = LinearRegression().fit(X, y)
    return float(reg.coef_[0]), float(reg.intercept_)


def compute_ppg_and_costs(event_json_paths: Iterable[str], json_dir: str = './json') -> List[str]:
    """
    For each input path pointing to '*_all_stages_stats.json', compute per-player PPG and cost.
    Writes '{event}_ppg_cost.json' in the same json_dir.
    Returns list of written file paths.
    """
    written: List[str] = []
    for path in event_json_paths:
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        player_points: Dict[str, float] = {}
        player_games: Dict[str, int] = {}
        for entry in data:
            name = entry.get('name')
            if not name:
                continue
            # PPG base on score per map
            kp = 0  # not used directly; scores computed externally
            player_points[name] = player_points.get(name, 0) + entry.get('score', 0) if 'score' in entry else player_points.get(name, 0)
            player_games[name] = player_games.get(name, 0) + 1
        # If entries had no 'score', compute via calc_score if fields present
        if not any('score' in e for e in data):
            try:
                from score_calc import calc_score
                for entry in data:
                    name = entry.get('name')
                    if not name:
                        continue
                    player_points[name] = player_points.get(name, 0) + calc_score(entry)
            except Exception:
                pass
        player_ppg = {name: (player_points[name] / max(1, player_games.get(name, 1))) for name in player_points}
        def expected_cost(ppg: float) -> float:
            a, b = 0.62, 4.74
            return a * ppg + b
        output = []
        for name in player_points:
            ppg = player_ppg[name]
            cost = round(expected_cost(ppg) * 2) / 2
            cost = min(cost, 15)
            output.append({
                'name': name,
                'ppg': ppg,
                'cost': cost,
                'games_played': player_games.get(name, 0),
                'total_points': player_points[name],
            })
        base = os.path.basename(path)
        event_name = base.replace('_all_stages_stats.json', '').replace('.json', '')
        out_path = os.path.join(json_dir, f"{event_name}_ppg_cost.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        written.append(out_path)
    return written

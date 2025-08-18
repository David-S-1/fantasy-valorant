from typing import Iterable, List
import json
import os

from score_calc import calc_score as _calc_score
from .storage import write_json


def calc_score(player: dict) -> int:
    return _calc_score(player)


def compute_points(changed_event_prefixes: Iterable[str], json_dir: str = './json') -> List[str]:
    """
    Recompute *_points.json for impacted events only.
    changed_event_prefixes: iterable of event file prefixes, e.g. 'vct_2025_americas_stage_2'
    Returns list of updated points file paths.
    """
    updated: List[str] = []
    prefixes = list(dict.fromkeys(changed_event_prefixes))
    for prefix in prefixes:
        stats_path = os.path.join(json_dir, f"{prefix}_stats.json")
        points_filename = f"{prefix}_points.json"
        if not os.path.exists(stats_path):
            continue
        with open(stats_path, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        player_points = {}
        for player in stats:
            name = player.get('name')
            if not name:
                continue
            try:
                player_points[name] = player_points.get(name, 0) + _calc_score(player)
            except Exception:
                # Keep going on bad records
                continue

        # Use new storage system
        written = write_json(points_filename, player_points)
        updated.extend(written)

    return updated

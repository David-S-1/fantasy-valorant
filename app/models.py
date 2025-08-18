from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel

# Import data constants from existing files (keep originals)
from agents_to_roles import agents_to_roles  # noqa: F401
from player_info import players  # noqa: F401


class EventMeta(BaseModel):
    event_id: str
    url: str
    name: Optional[str] = None


class MatchMeta(BaseModel):
    match_id: str
    url: str
    stage: Optional[str] = None
    round: Optional[str] = None
    teams: Optional[Tuple[str, str]] = None
    status: Optional[str] = None


class PlayerMapStats(BaseModel):
    name: str
    kills: Optional[int] = 0
    deaths: Optional[int] = 0
    assists: Optional[int] = 0
    org: Optional[str] = None
    two_k: Optional[int] = 0
    three_k: Optional[int] = 0
    four_k: Optional[int] = 0
    five_k: Optional[int] = 0
    r2_0: Optional[float] = None
    won_map: Optional[bool] = None
    map_differential: Optional[int] = None
    series_score: Optional[str] = None
    overall_rank: Optional[int] = None


class MapStats(BaseModel):
    match_id: str
    map_num: int
    map_name: Optional[str] = None
    players: List[PlayerMapStats]

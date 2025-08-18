import json

def calc_score(player):
    """
    Calculate score for a player for a
    specific map
    """
    score = 0

    #Kill-based scoring
    kills = player.get('kills', 0) or 0
    if kills == 0:
        score -= 3
    elif 1 <= kills <= 4:
        score -= 1
    elif kills >= 10:
        mult_five_kills = (kills // 5) - 1
        score += mult_five_kills

    #Multikill-based scoring
    score += (player.get('4K', 0) or 0) + (3 * (player.get('5K', 0) or 0))

    #Map-based scoring
    if player.get('won_map', False):
        score += 1

    map_diff = player.get('map_differential', 0) or 0
    if map_diff == 13:
        score += 5
    elif map_diff == -13:
        score -= 5
    elif map_diff >= 10:
        score += 2
    elif 5 <= map_diff <= 9:
        score += 1
    elif map_diff <= -10:
        score -= 1

    #Series-based scoring
    series_score = player.get('series_score', '')
    if series_score == '2-0':
        score += 2
    elif series_score == '3-0':
        score += 4
    elif series_score == '3-1':
        score += 1

    #VLR-based scoring
    r2_0 = player.get('r2_0', 0) or 0
    if r2_0 >= 1.5:
        score += 1
    elif r2_0 >= 1.75:
        score += 2
    elif r2_0 >= 2:
        score += 3

    overall_rank = player.get('overall_rank', 0) or 0
    if overall_rank == 1:
        score += 3
    elif overall_rank == 2:
        score += 2
    elif overall_rank == 3:
        score += 1

    return score




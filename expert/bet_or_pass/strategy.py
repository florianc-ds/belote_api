from helpers.common_helpers import create_card
from helpers.constants import COLORS, NEXT_PLAYER


# COMBINATION RELATED HELPERS
def detect_combination_in_hand(pattern, hand_cards, trump_color, only_trump=True):
    def _and_pattern_detection(pat, cards, col):
        return int(all([create_card(val, col) in cards for val in pat.split('+')]))

    def _or_pattern_detection(pat, cards, col):
        return len([1 for val in pat.split('/') if create_card(val, col) in cards])

    def _mix_pattern_detection(pat, cards, col):
        present_cards = []
        for sub_pat in pat.split('+'):
            present_cards.append(any([create_card(val, col) in cards for val in sub_pat.split('/')]))
        return int(all(present_cards))

    nb_detections = 0
    for color in [c for c in COLORS if (c == trump_color) == only_trump]:
        if ('+' in pattern) and ('/' in pattern):
            nb_detections += _mix_pattern_detection(pattern, hand_cards, color)
        elif '+' in pattern:
            nb_detections += _and_pattern_detection(pattern, hand_cards, color)
        elif '/' in pattern:
            nb_detections += _or_pattern_detection(pattern, hand_cards, color)
        else:
            nb_detections += int(create_card(pattern, color) in hand_cards)
    return nb_detections


def derive_score(nb_detections, unit_value, max_value):
    if isinstance(unit_value, dict):
        return unit_value.get(nb_detections, 0)
    elif max_value is not None:
        return min(nb_detections * unit_value, max_value)
    else:
        return nb_detections * unit_value


# STRATEGY HELPERS
def extract_speakers(players_bids):
    return [player for (player, bid) in players_bids.items() if bid['value'] is not None]


def have_player_and_partner_spoken_over_same_color(player, players_bids):
    partner = NEXT_PLAYER[NEXT_PLAYER[player]]
    return (
            (players_bids[player]['color'] is not None)
            and (players_bids[player]['color'] == players_bids[partner]['color'])
    )


def extract_leader(players_bids):
    leader = None
    leading_value = -1
    speakers = extract_speakers(players_bids)
    for speaker in speakers:
        if players_bids[speaker]['value'] > leading_value:
            leader = speaker
            leading_value = players_bids[speaker]['value']
    return leader


# COMPUTATION METHODS
def compute_best_color_bet(player_cards, main_combinations):
    best_color = None
    best_score = -1
    for color in COLORS:
        for combination in main_combinations:
            if detect_combination_in_hand(combination['trigger'], player_cards, color, True) == 1:
                tmp_score = 80
                for bonus_combination in combination['bonus']:
                    nb_detections = detect_combination_in_hand(
                        bonus_combination['pattern'],
                        player_cards,
                        color,
                        bonus_combination['trump']
                    )
                    tmp_score += derive_score(nb_detections, bonus_combination['value'], bonus_combination.get('max'))
                if tmp_score > best_score:
                    best_score = tmp_score
                    best_color = color
                    break
    return best_color, best_score


def compute_support_score(player_cards, color, support_combinations):
    support_score = 0
    for combination in support_combinations:
        nb_detections = detect_combination_in_hand(combination['pattern'], player_cards, color, combination['trump'])
        support_score += derive_score(nb_detections, combination['value'], combination.get('max'))
    return support_score

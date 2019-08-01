from helpers.common_helpers import create_card
from helpers.constants import COLORS


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

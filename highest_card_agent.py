from helpers.common_helpers import extract_value, extract_color
from helpers.constants import TRUMP_POINTS, PLAIN_POINTS
from helpers.play_helpers import derive_playable_cards


def highest_card_sorting_key(card, trump_color):
    value = extract_value(card)
    color = extract_color(card)
    if color == trump_color:
        return TRUMP_POINTS[value]
    else:
        return PLAIN_POINTS[value]


def play_highest_card_strategy(player_cards, cards_playability, trump_color):
    playable_cards = derive_playable_cards(player_cards, cards_playability)
    card = sorted(
        playable_cards,
        key=lambda x: highest_card_sorting_key(x, trump_color),
        reverse=True
    )[0]
    return card

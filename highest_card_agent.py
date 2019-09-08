import math

from helpers.bet_or_pass_helpers import derive_currently_highest_bid_value
from helpers.common_helpers import extract_value, extract_color
from helpers.constants import TRUMP_POINTS, PLAIN_POINTS, COLORS
from helpers.play_helpers import derive_playable_cards

HIGHEST_CARD_MIN_POINTS = 50  # (J, 9, A)
MAX_POINTS_IN_HAND = 93  # (J, 9, A, 10 (Trump) + A * 3 + 10)
# raw_value = K * (points) ^ A
# K * (HIGHEST_CARD_MIN_POINTS) ^ A = 80
# K * (MAX_POINTS_IN_HAND) ^ A = 160
HIGHEST_CARD_VALUE_COEF_A = math.log(2) / (math.log(MAX_POINTS_IN_HAND) - math.log(HIGHEST_CARD_MIN_POINTS))
HIGHEST_CARD_VALUE_COEF_K = 80 / (pow(HIGHEST_CARD_MIN_POINTS, HIGHEST_CARD_VALUE_COEF_A))


########
# PLAY #
########

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


###############
# BET OR PASS #
###############

def get_best_trump_color(player_cards):
    best_trump_score = -1
    best_trump_color = None
    for color in COLORS:
        trump_score = 0
        for card in player_cards:
            if extract_color(card) == color:
                trump_score += TRUMP_POINTS[extract_value(card)]
        if trump_score > best_trump_score:
            best_trump_color = color
            best_trump_score = trump_score

    return best_trump_color


def get_points_in_hand(player_cards, trump_color):
    points = 0
    for card in player_cards:
        if extract_color(card) == trump_color:
            points += TRUMP_POINTS[extract_value(card)]
        else:
            points += PLAIN_POINTS[extract_value(card)]

    return points


def get_contract_value_from_points(points):
    raw_contract_value = HIGHEST_CARD_VALUE_COEF_K * pow(points, HIGHEST_CARD_VALUE_COEF_A)
    return int(round(raw_contract_value, -1))


def bet_or_pass_highest_card_strategy(player_cards, players_bids):
    color = get_best_trump_color(player_cards)
    points = get_points_in_hand(player_cards, color)

    if points >= HIGHEST_CARD_MIN_POINTS:
        action = 'bet'
        tmp_value = get_contract_value_from_points(points)
        value = max(80, tmp_value)
        currently_highest_bid_value = derive_currently_highest_bid_value(players_bids)
        if currently_highest_bid_value and (value <= currently_highest_bid_value):
            action = 'pass'
    else:
        action = 'pass'
        color = None
        value = None

    return action, color, value

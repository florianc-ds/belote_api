import random

import numpy as np

from helpers.bet_or_pass_helpers import derive_currently_highest_bid_value
from helpers.constants import COLORS
from helpers.play_helpers import derive_playable_cards

RANDOM_BET_PROBABILITY = 0.5
RANDOM_COLOR_WEIGHTS = [1, 1, 1, 1]
RANDOM_VALUE_NORMAL_MU = 0.
RANDOM_VALUE_NORMAL_SIGMA = 2.3


########
# PLAY #
########

def play_random_strategy(player_cards, cards_playability):
    playable_cards = derive_playable_cards(player_cards, cards_playability)
    card = random.choice(playable_cards)
    return card


###############
# BET OR PASS #
###############

def bet_or_pass_random_strategy(players_bids):
    if random.random() < RANDOM_BET_PROBABILITY:
        action = 'bet'
        color = random.choices(population=COLORS, weights=RANDOM_COLOR_WEIGHTS, k=1)[0]
        value = 80 + 10 * round(abs(np.random.normal(loc=RANDOM_VALUE_NORMAL_MU, scale=RANDOM_VALUE_NORMAL_SIGMA)))
        currently_highest_bid_value = derive_currently_highest_bid_value(players_bids)
        if currently_highest_bid_value and (value <= currently_highest_bid_value):
            action = 'pass'
    else:
        action = 'pass'
        color = None
        value = None

    return action, color, value

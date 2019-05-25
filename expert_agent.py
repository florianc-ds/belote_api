from helpers.common_helpers import extract_color, extract_value
from helpers.constants import NEXT_PLAYER, TRUMP_POINTS, PLAIN_POINTS, COLORS
from helpers.play_helpers import derive_playable_cards


########
# PLAY #
########


# HELPERS

def derive_player_rank_in_round(round_cards):
    return len([card for card in round_cards.values() if card is not None])


def is_trump_asked(player, round_cards, trump_color):
    next_player = NEXT_PLAYER[player]
    while next_player != player:
        if round_cards[next_player] is not None:
            return extract_color(round_cards[next_player]) == trump_color
        next_player = NEXT_PLAYER[next_player]
    # if no player has played yet during round
    return None


def has_trump_in_hand(cards, trump_color):
    return any([extract_color(card) == trump_color for card in cards])


def get_lowest_trump_card(cards, trump_color):
    def _rank_trump_card(card):
        return TRUMP_POINTS[extract_value(card)], extract_value(card)

    trump_cards = [card for card in cards if extract_color(card) == trump_color]
    return min(trump_cards, key=_rank_trump_card)


def get_lowest_plain_card(cards):
    def _rank_plain_card(card):
        return PLAIN_POINTS[extract_value(card)], extract_value(card), -COLORS.index(extract_color(card))

    return min(cards, key=_rank_plain_card)


# LEVEL 1

def play_expert_first_in_round():
    return None


def play_expert_second_in_round(trump_asked, playable_cards, trump_color):
    # LEVEL 2
    if trump_asked:
        # LEVEL 3
        if has_trump_in_hand(playable_cards, trump_color):
            return get_lowest_trump_card(playable_cards, trump_color)
        else:
            return get_lowest_plain_card(playable_cards)
    else:
        return None


def play_expert_third_in_round():
    return None


def play_expert_fourth_in_round():
    return None


# LEVEL 0

def play_expert_strategy(player, player_cards, cards_playability, round_cards, trump_color):
    playable_cards = derive_playable_cards(player_cards, cards_playability)
    # LEVEL 0
    if len(playable_cards) == 1:
        return player_cards[0]

    player_rank_in_round = derive_player_rank_in_round(round_cards)
    trump_asked = is_trump_asked(player, round_cards, trump_color)
    # LEVEL 1
    if player_rank_in_round == 0:
        card = play_expert_first_in_round()
    elif player_rank_in_round == 1:
        card = play_expert_second_in_round(trump_asked, playable_cards, trump_color)
    elif player_rank_in_round == 2:
        card = play_expert_third_in_round()
    elif player_rank_in_round == 3:
        card = play_expert_fourth_in_round()

    return card

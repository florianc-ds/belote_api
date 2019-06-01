import copy

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


def has_color_in_hand(cards, color):
    return any([extract_color(card) == color for card in cards])


def has_highest_plain_color_card_in_hand(hand_cards, cards_history, color):
    played_cards = [card for player_cards in cards_history.values() for card in player_cards]
    played_color_values = [extract_value(card) for card in played_cards if extract_color(card) == color]
    hand_color_values = [extract_value(card) for card in hand_cards if extract_color(card) == color]

    available_color_points = copy.copy(PLAIN_POINTS)
    for value in played_color_values:
        del available_color_points[value]

    if len(available_color_points) == 0:
        return False
    else:
        highest_plain_color_value = max(available_color_points, key=lambda k: (available_color_points[k], k))
        return highest_plain_color_value in hand_color_values


def has_player_cut_color(player, game_history, rounds_first_player, color, trump_color):
    for round, round_first_player in enumerate(rounds_first_player):
        asked_color = extract_color(game_history[round_first_player][round])
        played_color = extract_color(game_history[player][round])
        if (round_first_player != player) and (asked_color == color) and (played_color == trump_color):
            return True
    return False


def has_player_already_shown_he_had_no_more_trump(player, game_history, rounds_first_player, trump_color):
    def _partner_leads_in_color_round(round, round_first_player, asked_color):
        partner = NEXT_PLAYER[NEXT_PLAYER[player]]
        partner_card = game_history[partner][round]
        # partner did not play yet...
        if (round_first_player == NEXT_PLAYER[partner]) or (rounds_first_player == player):
            return False
        elif round_first_player == partner:
            opponent_cards = [game_history[NEXT_PLAYER[partner]][round]]
        elif round_first_player == NEXT_PLAYER[player]:
            opponent_cards = [game_history[NEXT_PLAYER[player]][round], game_history[NEXT_PLAYER[partner]][round]]

        if extract_color(partner_card) == asked_color:
            if any([extract_color(card) == trump_color for card in opponent_cards]):
                return False
            asked_color_opponent_cards = [card for card in opponent_cards if extract_color(card) == asked_color]
            if len(asked_color_opponent_cards) == 0:
                return True
            else:
                return (
                        PLAIN_POINTS[extract_value(partner_card)]
                        > max([PLAIN_POINTS[extract_value(card)] for card in asked_color_opponent_cards])
                )
        elif extract_color(partner_card) == trump_color:
            trump_opponent_cards = [card for card in opponent_cards if extract_color(card) == trump_color]
            if len(trump_opponent_cards) == 0:
                return True
            else:
                return (
                        TRUMP_POINTS[extract_value(partner_card)]
                        > max([TRUMP_POINTS[extract_value(card)] for card in trump_opponent_cards])
                )
        # partner cannot lead when he plays neither asked color nor trump
        else:
            return False

    for round, round_first_player in enumerate(rounds_first_player):
        asked_color = extract_color(game_history[round_first_player][round])
        played_color = extract_color(game_history[player][round])

        # trump asked but player did not supply
        if (round_first_player != player) and (played_color != trump_color) and (asked_color == trump_color):
            return True
        # color asked, player should have cut but did not
        elif (
                (round_first_player != player)
                and (played_color != trump_color)
                and (asked_color != trump_color)
                and (played_color != asked_color)
                and not _partner_leads_in_color_round(round, round_first_player, asked_color)
        ):
            return True
    return False


def get_lowest_trump_card(cards, trump_color):
    def _rank_trump_card(card):
        return TRUMP_POINTS[extract_value(card)], extract_value(card)

    trump_cards = [card for card in cards if extract_color(card) == trump_color]
    return min(trump_cards, key=_rank_trump_card)


def get_lowest_color_card(cards, color):
    def _rank_color_card(card):
        return PLAIN_POINTS[extract_value(card)], extract_value(card)

    color_cards = [card for card in cards if extract_color(card) == color]
    return min(color_cards, key=_rank_color_card)


def get_highest_color_card(cards, color):
    def _rank_color_card(card):
        return PLAIN_POINTS[extract_value(card)], extract_value(card)

    color_cards = [card for card in cards if extract_color(card) == color]
    return max(color_cards, key=_rank_color_card)


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
        if has_color_in_hand(playable_cards, trump_color):
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

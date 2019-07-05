import copy
import logging

from helpers.common_helpers import extract_color, extract_value, create_card
from helpers.constants import NEXT_PLAYER, TRUMP_POINTS, PLAIN_POINTS, COLORS
from helpers.play_helpers import derive_playable_cards

logger = logging.getLogger('flask.app.expert')

IMPORTANT_ROUND_LIMIT = 10

########
# PLAY #
########


# HELPERS

def _rank_trump_card(card):
    return TRUMP_POINTS[extract_value(card)], extract_value(card)


def _rank_plain_card(card):
    return PLAIN_POINTS[extract_value(card)], extract_value(card), -COLORS.index(extract_color(card))


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


def get_highest_color_card_remaining(cards_history, color):
    played_color_cards = [card for player_cards in cards_history.values()
                          for card in player_cards
                          if extract_color(card) == color]
    played_color_values = [extract_value(card) for card in played_color_cards]
    for value, _ in sorted(PLAIN_POINTS.items(), key=lambda kv: -kv[1]):
        if value not in played_color_values:
            return create_card(value, color)


def get_highest_trump_remaining(cards_history, trump_color):
    played_trump_cards = [card for player_cards in cards_history.values()
                          for card in player_cards
                          if extract_color(card) == trump_color]
    played_trump_values = [extract_value(card) for card in played_trump_cards]
    for value, _ in sorted(TRUMP_POINTS.items(), key=lambda kv: -kv[1]):
        if value not in played_trump_values:
            return create_card(value, trump_color)


def has_highest_plain_color_card_in_hand(hand_cards, cards_history, color):
    hand_color_cards = [card for card in hand_cards if extract_color(card) == color]
    if len(hand_color_cards) == 0:
        return False
    else:
        highest_color_card_remaining = get_highest_color_card_remaining(cards_history, color)
        return highest_color_card_remaining in hand_color_cards


def has_player_cut_color(player, game_history, rounds_first_player, color, trump_color):
    for round, round_first_player in enumerate(rounds_first_player):
        asked_color = extract_color(game_history[round_first_player][round])
        played_color = extract_color(game_history[player][round])
        if (round_first_player != player) and (asked_color == color) and (played_color == trump_color):
            return True
    return False


def has_player_already_shown_he_had_no_more_trump(player, game_history, rounds_first_player, trump_color):
    for round, round_first_player in enumerate(rounds_first_player):
        round_color = extract_color(game_history[round_first_player][round])
        played_color = extract_color(game_history[player][round])

        # build round_cards state before player has to play
        round_cards_before_player = {p: None for p in NEXT_PLAYER.keys()}
        tmp_player = round_first_player
        while tmp_player != player:
            round_cards_before_player[tmp_player] = game_history[tmp_player][round]
            tmp_player = NEXT_PLAYER[tmp_player]

        # trump asked but player did not supply
        if (round_first_player != player) and (played_color != trump_color) and (round_color == trump_color):
            return True
        # color asked, player should have cut but did not
        elif (
                (round_first_player != player)
                and (played_color != trump_color)
                and (round_color != trump_color)
                and (played_color != round_color)
                and not is_partner_leading(player, round_cards_before_player, round_color, trump_color)
        ):
            return True
    return False


def can_win_round(hand_cards, round_cards, round_color, trump_color):
    real_round_cards = [card for card in round_cards.values() if card is not None]
    # not the 4th player, can not win for sure...
    if len(real_round_cards) != 3:
        return False
    played_trumps = [card for card in real_round_cards if extract_color(card) == trump_color]
    played_round_color_cards = [card for card in real_round_cards if extract_color(card) == round_color]
    player_trumps = [card for card in hand_cards if extract_color(card) == trump_color]
    player_round_color_cards = [card for card in hand_cards if extract_color(card) == round_color]
    if round_color != trump_color:
        if len(played_trumps) == 0:
            if len(player_round_color_cards) != 0:
                return (
                        max([_rank_plain_card(card) for card in player_round_color_cards])
                        > max([_rank_plain_card(card) for card in played_round_color_cards])
                )
            elif len(player_trumps) > 0:
                return True
            else:
                return False
        elif (len(player_round_color_cards) == 0) and (len(player_trumps) != 0):
                return (
                        max([_rank_trump_card(card) for card in player_trumps])
                        > max([_rank_trump_card(card) for card in played_trumps])
                )
        else:
            return False
    else:
        if len(player_trumps) == 0:
            return False
        else:
            return (
                    max([_rank_trump_card(card) for card in player_trumps])
                    > max([_rank_trump_card(card) for card in played_trumps])
            )


def is_partner_leading(player, round_cards, round_color, trump_color):
    partner = NEXT_PLAYER[NEXT_PLAYER[player]]
    partner_card = round_cards[partner]
    # partner did not play yet...
    if partner_card is None:
        return False
    real_round_cards = [card for card in round_cards.values() if card is not None]
    played_trumps = [card for card in real_round_cards if extract_color(card) == trump_color]
    played_round_color_cards = [card for card in real_round_cards if extract_color(card) == round_color]
    if round_color != trump_color:
        if len(played_trumps) != 0:
            return max(played_trumps, key=_rank_trump_card) == partner_card
        else:
            return max(played_round_color_cards, key=_rank_plain_card) == partner_card
    else:
        return max(played_trumps, key=_rank_trump_card) == partner_card


def must_cut(playable_cards, trump_color):
    return all([extract_color(card) == trump_color for card in playable_cards])


def count_round_points(round_cards, trump_color, round):
    # Automatically 10 points for last round
    points = 0 if round != 7 else 10
    real_round_cards = [card for card in round_cards.values() if card is not None]
    for card in real_round_cards:
        if extract_color(card) == trump_color:
            points += TRUMP_POINTS[extract_value(card)]
        else:
            points += PLAIN_POINTS[extract_value(card)]
    return points


def get_lowest_trump_card(cards, trump_color):
    trump_cards = [card for card in cards if extract_color(card) == trump_color]
    return min(trump_cards, key=_rank_trump_card)


def get_lowest_color_card(cards, color):
    color_cards = [card for card in cards if extract_color(card) == color]
    return min(color_cards, key=_rank_plain_card)


def get_highest_color_card(cards, color):
    color_cards = [card for card in cards if extract_color(card) == color]
    return max(color_cards, key=_rank_plain_card)


def get_lowest_plain_card(cards, trump_color):
    plain_cards = [card for card in cards if extract_color(card) != trump_color]
    return min(plain_cards, key=_rank_plain_card)


def get_highest_plain_card(cards, trump_color, exclude_aces=False):
    plain_cards = [card for card in cards if extract_color(card) != trump_color]
    plain_cards_without_aces = [card for card in plain_cards if extract_value(card) != 'A']
    if exclude_aces and len(plain_cards_without_aces) != 0:
        return max(plain_cards_without_aces, key=_rank_plain_card)
    else:
        return max(plain_cards, key=_rank_plain_card)


# LEVEL 1

def play_expert_first_in_round():
    return None


def play_expert_second_in_round(player, trump_asked, playable_cards, trump_color, round_color, game_history,
                                rounds_first_player):
    third_player = NEXT_PLAYER[player]
    # LEVEL 2
    if trump_asked:
        # LEVEL 3
        if has_color_in_hand(playable_cards, trump_color):
            logger.info('LEAF 0111')
            return get_lowest_trump_card(playable_cards, trump_color)
        else:
            logger.info('LEAF 0110')
            return get_lowest_plain_card(playable_cards, trump_color)
    else:
        # LEVEL 3
        if has_color_in_hand(playable_cards, round_color):
            # LEVEL 4
            if (
                    has_highest_plain_color_card_in_hand(playable_cards, game_history, round_color)
                    and (
                            not has_player_cut_color(third_player, game_history, rounds_first_player,
                                                     round_color, trump_color)
                            or has_player_already_shown_he_had_no_more_trump(third_player, game_history,
                                                                             rounds_first_player, trump_color)
                    )
            ):
                logger.info('LEAF 01011')
                return get_highest_color_card(playable_cards, round_color)
            else:
                logger.info('LEAF 01010')
                return get_lowest_color_card(playable_cards, round_color)
        else:
            # LEVEL 4
            if has_color_in_hand(playable_cards, trump_color):
                logger.info('LEAF 01001')
                return get_lowest_trump_card(playable_cards, trump_color)
            else:
                logger.info('LEAF 01000')
                return get_lowest_plain_card(playable_cards, trump_color)


def play_expert_third_in_round(player, trump_asked, playable_cards, round_cards, trump_color, round_color, round,
                               game_history, rounds_first_player):
    partner = NEXT_PLAYER[NEXT_PLAYER[player]]
    partner_card = round_cards[partner]
    opponent = NEXT_PLAYER[partner]
    opponent_card = round_cards[opponent]
    fourth_player = NEXT_PLAYER[player]
    # LEVEL 2
    if trump_asked:
        # LEVEL 3
        if has_color_in_hand(playable_cards, trump_color):
            return get_lowest_trump_card(playable_cards, trump_color)
        else:
            # LEVEL 4
            if get_highest_trump_remaining(game_history, trump_color) == partner_card:
                return get_highest_plain_card(playable_cards, trump_color, exclude_aces=True)
            else:
                return get_lowest_plain_card(playable_cards, trump_color)
    else:
        # LEVEL 3
        if has_color_in_hand(playable_cards, round_color):
            # LEVEL 4
            if (
                    (extract_color(opponent_card) == trump_color)
                    or (opponent_card == get_highest_color_card_remaining(game_history, round_color))
            ):
                return get_lowest_color_card(playable_cards, round_color)
            else:
                # LEVEL 5
                if (
                        has_highest_plain_color_card_in_hand(playable_cards, game_history, round_color)
                        and
                        (
                             has_player_cut_color(fourth_player, game_history, rounds_first_player, round_color,
                                                  trump_color)
                             or has_player_already_shown_he_had_no_more_trump(fourth_player, game_history,
                                                                              rounds_first_player, trump_color)
                        )
                ):
                    get_lowest_color_card(playable_cards, round_color)
                else:
                    # LEVEL 6
                    if (
                            (
                                 is_partner_leading(player, round_cards, round_color, trump_color)
                                 and ((get_highest_color_card_remaining(game_history, round_color) == partner_card)
                                      or (extract_color(partner_card) == trump_color))
                            )
                            and (
                                    has_player_cut_color(fourth_player, game_history, rounds_first_player, round_color,
                                                         trump_color)
                                    or (has_player_already_shown_he_had_no_more_trump(fourth_player, game_history,
                                                                                      round_color, trump_color))
                            )
                    ):
                        return get_highest_color_card(playable_cards, round_color)
                    else:
                        return get_lowest_color_card(playable_cards, round_color)
        else:
            # LEVEL 4
            if (
                    (
                        is_partner_leading(player, round_cards, round_color, trump_color)
                        and ((get_highest_color_card_remaining(game_history, round_color) == partner_card)
                             or (extract_color(partner_card) == trump_color))
                    )
                    and (
                        has_player_cut_color(fourth_player, game_history, rounds_first_player, round_color, trump_color)
                        or (has_player_already_shown_he_had_no_more_trump(fourth_player, game_history, round_color,
                                                                      trump_color))
                    )
            ):
                # WARNING: WHAT IF ONLY TRUMPS IN HAND..?
                return "ERROR..."
                # return get_highest_plain_card(playable_cards, trump_color, exclude_aces=True)
            else:
                # LEVEL 5
                if (
                        (
                            is_partner_leading(player, round_cards, round_color, trump_color)
                            and ((get_highest_color_card_remaining(game_history, round_color) != partner_card)
                                 and extract_color(partner_card) != trump_color)
                        )
                        and (count_round_points(round_cards, trump_color, round) >= IMPORTANT_ROUND_LIMIT)
                        and (
                            has_player_cut_color(fourth_player, game_history, rounds_first_player, round_color, trump_color)
                            or (has_player_already_shown_he_had_no_more_trump(fourth_player, game_history, round_color,
                                                                              trump_color))
                        )
                        and has_color_in_hand(playable_cards, trump_color)
                ):
                    return get_lowest_trump_card(playable_cards, trump_color)
                else:
                    # LEVEL 6
                    if has_color_in_hand(playable_cards, trump_color) and must_cut(playable_cards, trump_color):
                        return get_lowest_trump_card(playable_cards, trump_color)
                    else:
                        return get_lowest_plain_card(playable_cards, trump_color)


def play_expert_fourth_in_round(player, trump_asked, playable_cards, round_cards, trump_color, round_color):
    # LEVEL 2
    if trump_asked:
        # LEVEL 3
        if has_color_in_hand(playable_cards, trump_color):
            logger.info('LEAF 0311')
            return get_lowest_trump_card(playable_cards, trump_color)
        else:
            # LEVEL 4
            if is_partner_leading(player, round_cards, round_color, trump_color):
                logger.info('LEAF 03101')
                return get_highest_plain_card(playable_cards, trump_color, exclude_aces=True)
            else:
                logger.info('LEAF 03100')
                return get_lowest_plain_card(playable_cards, trump_color)
    else:
        # LEVEL 3
        if has_color_in_hand(playable_cards, round_color):
            # LEVEL 4
            if can_win_round(playable_cards, round_cards, round_color, trump_color):
                logger.info('LEAF 03011')
                return get_highest_color_card(playable_cards, round_color)
            else:
                # LEVEL 5
                if is_partner_leading(player, round_cards, round_color, trump_color):
                    logger.info('LEAF 030101')
                    return get_highest_color_card(playable_cards, round_color)
                else:
                    logger.info('LEAF 030100')
                    return get_lowest_color_card(playable_cards, round_color)
        else:
            # LEVEL 4
            if is_partner_leading(player, round_cards, round_color, trump_color):
                logger.info('LEAF 03001')
                return get_highest_plain_card(playable_cards, trump_color, exclude_aces=True)
            else:
                # LEVEL 5
                if has_color_in_hand(playable_cards, trump_color):
                    logger.info('LEAF 030001')
                    return get_lowest_trump_card(playable_cards, trump_color)
                else:
                    logger.info('LEAF 030000')
                    return get_lowest_plain_card(playable_cards, trump_color)


# LEVEL 0

def play_expert_strategy(player, player_cards, cards_playability, round_cards, trump_color, round_color, game_history,
                         rounds_first_player):
    playable_cards = derive_playable_cards(player_cards, cards_playability)
    # LEVEL 0
    if len(playable_cards) == 1:
        logger.info('LEAF 1')
        return playable_cards[0]

    player_rank_in_round = derive_player_rank_in_round(round_cards)
    trump_asked = is_trump_asked(player, round_cards, trump_color)
    # LEVEL 1
    if player_rank_in_round == 0:
        card = play_expert_first_in_round()
    elif player_rank_in_round == 1:
        card = play_expert_second_in_round(player, trump_asked, playable_cards, trump_color, round_color, game_history,
                                           rounds_first_player)
    elif player_rank_in_round == 2:
        card = play_expert_third_in_round()
    elif player_rank_in_round == 3:
        card = play_expert_fourth_in_round(player, trump_asked, playable_cards, round_cards, trump_color, round_color)

    return card

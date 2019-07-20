import copy
import logging

from helpers.common_helpers import extract_color, extract_value, create_card
from helpers.constants import NEXT_PLAYER, TRUMP_POINTS, PLAIN_POINTS, COLORS
from helpers.exceptions import UnhandledPlayCaseException
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


# Highest color card remaining at the end of previous round (whatever cards have been played during current round)
def get_highest_color_card_remaining(cards_history, current_round, color):
    played_color_cards = [card for player_cards in cards_history.values()
                          for card in player_cards[:current_round]
                          if extract_color(card) == color]
    played_color_values = [extract_value(card) for card in played_color_cards]
    for value, _ in sorted(PLAIN_POINTS.items(), key=lambda kv: -kv[1]):
        if value not in played_color_values:
            return create_card(value, color)


# Highest trump remaining at the end of previous round (whatever cards have been played during current round)
def get_highest_trump_remaining(cards_history, current_round, trump_color):
    played_trump_cards = [card for player_cards in cards_history.values()
                          for card in player_cards[:current_round]
                          if extract_color(card) == trump_color]
    played_trump_values = [extract_value(card) for card in played_trump_cards]
    for value, _ in sorted(TRUMP_POINTS.items(), key=lambda kv: -kv[1]):
        if value not in played_trump_values:
            return create_card(value, trump_color)


def has_highest_plain_color_card_in_hand(hand_cards, current_round, cards_history, color):
    hand_color_cards = [card for card in hand_cards if extract_color(card) == color]
    if len(hand_color_cards) == 0:
        return False
    else:
        highest_color_card_remaining = get_highest_color_card_remaining(cards_history, current_round, color)
        return highest_color_card_remaining in hand_color_cards


# Only take into account past rounds
def has_player_cut_color(player, game_history, current_round, rounds_first_player, color, trump_color):
    for round, round_first_player in enumerate(rounds_first_player[:current_round]):
        asked_color = extract_color(game_history[round_first_player][round])
        played_color = extract_color(game_history[player][round])
        if (round_first_player != player) and (asked_color == color) and (played_color == trump_color):
            return True
    return False


# Only take into account past rounds
def has_player_already_shown_he_had_no_more_trump(player, game_history, current_round, rounds_first_player, trump_color):
    for round, round_first_player in enumerate(rounds_first_player[:current_round]):
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


# Take into account all played cards (previous and current rounds)
def are_there_remaining_trumps_in_other_hands(hand_cards, game_history, trump_color):
    hand_trumps = [c for c in hand_cards if extract_color(c) == trump_color]
    played_trumps = [c for p_cards in game_history.values() for c in p_cards if extract_color(c) == trump_color]
    return (len(hand_trumps) + len(played_trumps)) < len(TRUMP_POINTS)


def has_player_definitely_no_more_trump(player, visible_cards, game_history,
                                        current_round, rounds_first_player, trump_color):
    return (
            not are_there_remaining_trumps_in_other_hands(visible_cards, game_history, trump_color)
            or has_player_already_shown_he_had_no_more_trump(player, game_history, current_round, rounds_first_player,
                                                             trump_color)
    )


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


def has_only_trumps_and_aces(playable_cards, trump_color):
    return all([(extract_color(card) == trump_color) or (extract_value(card) == 'A') for card in playable_cards])


def is_player_in_contract_team(player, contract_team):
    return player in contract_team


def has_only_trumps(hand_cards, trump_color):
    return (len(hand_cards) > 0) and all([extract_color(card) == trump_color for card in hand_cards])


def can_opponents_cut(player, hand_cards, game_history, current_round, rounds_first_player, trump_color):
    if are_there_remaining_trumps_in_other_hands(hand_cards, game_history, trump_color):
        opponents = [NEXT_PLAYER[player], NEXT_PLAYER[NEXT_PLAYER[NEXT_PLAYER[player]]]]
        for opponent in opponents:
            if not has_player_already_shown_he_had_no_more_trump(opponent, game_history, current_round,
                                                                 rounds_first_player, trump_color):
                return True

    return False


def count_round_points(round_cards, trump_color, round):
    # Automatically add 10 points for last round
    points = 0 if round != 7 else 10
    real_round_cards = [card for card in round_cards.values() if card is not None]
    for card in real_round_cards:
        if extract_color(card) == trump_color:
            points += TRUMP_POINTS[extract_value(card)]
        else:
            points += PLAIN_POINTS[extract_value(card)]
    return points


def get_fresh_aces(hand_cards, game_history, current_round, rounds_first_player, trump_color):
    candidate_aces = [card for card in hand_cards if extract_value(card) == 'A' and extract_color(card) != trump_color]
    if len(candidate_aces) == 0:
        return []
    else:
        fresh_aces = [ace for ace in candidate_aces]
        for round, round_first_player in enumerate(rounds_first_player[:current_round]):
            asked_color = extract_color(game_history[round_first_player][round])
            asked_color_ace = create_card('A', asked_color)
            if asked_color_ace in fresh_aces:
                fresh_aces.remove(asked_color_ace)
        return fresh_aces


def get_colors_to_make_opponent_cut(player, hand_cards, game_history, current_round, rounds_first_player, trump_color):
    playable_plain_colors = set(
        [
            extract_color(card) for card in hand_cards
            if (extract_color(card) != trump_color) and (extract_value(card) not in ['10', 'A'])
        ]
    )
    candidate_colors = []
    opponents = [NEXT_PLAYER[player], NEXT_PLAYER[NEXT_PLAYER[NEXT_PLAYER[player]]]]
    for color in playable_plain_colors:
        for opponent in opponents:
            if (
                    has_player_cut_color(opponent, game_history, current_round, rounds_first_player, color, trump_color)
                    and not has_player_definitely_no_more_trump(player, hand_cards, game_history,
                                                                current_round, rounds_first_player, trump_color)
            ):
                candidate_colors.append(color)
                break

    return candidate_colors


def get_winning_cards(hand_cards, game_history, current_round, trump_color):
    hand_colors = set([extract_color(card) for card in hand_cards])
    winning_cards = []
    for color in hand_colors:
        if color == trump_color:
            highest_card = get_highest_trump_card(hand_cards, color)
            highest_card_remaining = get_highest_trump_remaining(game_history, current_round, color)
        else:
            highest_card = get_highest_color_card(hand_cards, color)
            highest_card_remaining = get_highest_color_card_remaining(game_history, current_round, color)
        if highest_card == highest_card_remaining:
            winning_cards.append(highest_card)
    return winning_cards


def get_lowest_trump_card(cards, trump_color):
    trump_cards = [card for card in cards if extract_color(card) == trump_color]
    return min(trump_cards, key=_rank_trump_card)


def get_highest_trump_card(cards, trump_color):
    trump_cards = [card for card in cards if extract_color(card) == trump_color]
    return max(trump_cards, key=_rank_trump_card)


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


def play_expert_second_in_round(player, player_cards, trump_asked, playable_cards, trump_color, round_color, round,
                                game_history, rounds_first_player):
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
                    has_highest_plain_color_card_in_hand(playable_cards, round, game_history, round_color)
                    and (
                            not has_player_cut_color(third_player, game_history, round, rounds_first_player,
                                                     round_color, trump_color)
                            or has_player_definitely_no_more_trump(third_player, player_cards, game_history, round,
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


def play_expert_third_in_round(player, player_cards, trump_asked, playable_cards, round_cards, trump_color, round_color,
                               round, game_history, rounds_first_player):
    partner = NEXT_PLAYER[NEXT_PLAYER[player]]
    partner_card = round_cards[partner]
    opponent = NEXT_PLAYER[partner]
    opponent_card = round_cards[opponent]
    fourth_player = NEXT_PLAYER[player]
    # LEVEL 2
    if trump_asked:
        # LEVEL 3
        if has_color_in_hand(playable_cards, trump_color):
            logger.info('LEAF 0211')
            return get_lowest_trump_card(playable_cards, trump_color)
        else:
            # LEVEL 4
            if get_highest_trump_remaining(game_history, round, trump_color) == partner_card:
                logger.info('LEAF 02101')
                return get_highest_plain_card(playable_cards, trump_color, exclude_aces=True)
            else:
                logger.info('LEAF 02100')
                return get_lowest_plain_card(playable_cards, trump_color)
    else:
        # LEVEL 3
        if has_color_in_hand(playable_cards, round_color):
            # LEVEL 4
            if (
                    (extract_color(opponent_card) == trump_color)
                    or (opponent_card == get_highest_color_card_remaining(game_history, round, round_color))
            ):
                logger.info('LEAF 02011')
                return get_lowest_color_card(playable_cards, round_color)
            else:
                # LEVEL 5
                if (
                        has_highest_plain_color_card_in_hand(playable_cards, round, game_history, round_color)
                        and
                        (
                             not has_player_cut_color(fourth_player, game_history, round, rounds_first_player,
                                                      round_color, trump_color)
                             or has_player_definitely_no_more_trump(fourth_player, player_cards, game_history, round,
                                                                    rounds_first_player, trump_color)
                        )
                ):
                    logger.info('LEAF 020101')
                    return get_highest_color_card(playable_cards, round_color)
                else:
                    # LEVEL 6
                    if (
                            (
                                 is_partner_leading(player, round_cards, round_color, trump_color) and
                                 (get_highest_color_card_remaining(game_history, round, round_color) == partner_card)
                            )
                            and (
                                    not has_player_cut_color(fourth_player, game_history, round, rounds_first_player,
                                                             round_color, trump_color)
                                    or has_player_definitely_no_more_trump(fourth_player, player_cards, game_history, round,
                                                                           rounds_first_player, trump_color)
                            )
                    ):
                        logger.info('LEAF 0201001')
                        return get_highest_color_card(playable_cards, round_color)
                    else:
                        logger.info('LEAF 0201000')
                        return get_lowest_color_card(playable_cards, round_color)
        else:
            # LEVEL 4
            if (
                    (
                        is_partner_leading(player, round_cards, round_color, trump_color)
                        and (get_highest_color_card_remaining(game_history, round, round_color) == partner_card)

                    )
                    and (
                        not has_player_cut_color(fourth_player, game_history, round, rounds_first_player,
                                                 round_color, trump_color)
                        or has_player_definitely_no_more_trump(fourth_player, player_cards, game_history, round,
                                                               rounds_first_player, trump_color)
                    )
            ):
                # LEVEL 5
                if has_only_trumps_and_aces(playable_cards, trump_color):
                    logger.info('LEAF 020011')
                    return get_lowest_trump_card(playable_cards, trump_color)
                else:
                    logger.info('LEAF 020010')
                    return get_highest_plain_card(playable_cards, trump_color, exclude_aces=True)
            else:
                # LEVEL 5
                if (
                        (
                            is_partner_leading(player, round_cards, round_color, trump_color)
                            and ((get_highest_color_card_remaining(game_history, round, round_color) != partner_card)
                                 and extract_color(partner_card) != trump_color)
                        )
                        and (count_round_points(round_cards, trump_color, round) >= IMPORTANT_ROUND_LIMIT)
                        and (
                            not has_player_cut_color(fourth_player, game_history, round, rounds_first_player,
                                                     round_color, trump_color)
                            or has_player_definitely_no_more_trump(fourth_player, player_cards, game_history, round,
                                                                   rounds_first_player, trump_color)
                        )
                        and has_color_in_hand(playable_cards, trump_color)
                ):
                    logger.info('LEAF 020001')
                    return get_lowest_trump_card(playable_cards, trump_color)
                else:
                    # LEVEL 6
                    if has_color_in_hand(playable_cards, trump_color) and must_cut(playable_cards, trump_color):
                        logger.info('LEAF 0200001')
                        return get_lowest_trump_card(playable_cards, trump_color)
                    else:
                        logger.info('LEAF 0200000')
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

def play_expert_strategy(player, player_cards, cards_playability, round_cards, trump_color, round_color, round,
                         game_history, rounds_first_player):
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
        card = play_expert_second_in_round(player, player_cards, trump_asked, playable_cards, trump_color, round_color,
                                           round, game_history, rounds_first_player)
    elif player_rank_in_round == 2:
        card = play_expert_third_in_round(player, player_cards, trump_asked, playable_cards, round_cards, trump_color,
                                          round_color, round, game_history, rounds_first_player)
    elif player_rank_in_round == 3:
        card = play_expert_fourth_in_round(player, trump_asked, playable_cards, round_cards, trump_color, round_color)
    else:
        raise UnhandledPlayCaseException(f'player_rank_in_round has unhandled value: {player_rank_in_round}. '
                                         f'Ill-shaped round_cards: {round_cards}')

    return card

import logging
from copy import deepcopy
from unittest.mock import patch

import pytest

from reinforcement.models import Game, Player, OK_CODE, NEXT_PLAYER, Bid, VALIDATION_ERROR_CODE, State, Card, Team


def partially_compare_dict(d1, d2, excluded_keys):
    d1_cp = deepcopy(d1)
    d2_cp = deepcopy(d2)
    for excl_k in excluded_keys:
        decomposed_k = excl_k.split(".")
        sub_d1_cp = d1_cp
        sub_d2_cp = d2_cp
        for sub_k in decomposed_k[:-1]:
            sub_d1_cp = sub_d1_cp[sub_k]
            sub_d2_cp = sub_d2_cp[sub_k]
        del sub_d1_cp[decomposed_k[-1]]
        del sub_d2_cp[decomposed_k[-1]]
    return d1_cp == d2_cp


def test_auction_passed():
    """
        new Game + passed (OK + all same expect for current_passed)
    """
    game = Game(first_player=Player.ONE)
    before_state = game.describe()
    action = {'player': Player.ONE, 'passed': True, 'color': None, 'value': None}
    assert game.update(**action) == OK_CODE
    after_state = game.describe()
    assert after_state['auction']['current_passed'] == 0
    assert partially_compare_dict(before_state, after_state, ['auction.current_passed'])


def test_auction_four_passed(caplog):
    """
        new Game + 4 passed (OK + end of auction log + new cards + first_player/round.trick_opener rotated)
    """
    caplog.set_level(logging.INFO)
    game = Game(first_player=Player.ONE)
    before_state = game.describe()
    current_player = Player.ONE
    for i in range(4):
        action = {'player': current_player, 'passed': True, 'color': None, 'value': None}
        assert game.update(**action) == OK_CODE
        current_player = NEXT_PLAYER[current_player]
    after_state = game.describe()
    log_messages = [msg for (logger_instance, lvl, msg) in caplog.record_tuples]
    assert 'Nobody bet. Dealing again' in log_messages
    assert before_state['round']['hands'] != after_state['round']['hands']
    assert after_state['first_player'] == Player.TWO.value
    assert after_state['round']['trick_opener'] == Player.TWO.value
    assert partially_compare_dict(before_state, after_state, ['round.hands', 'round.trick_opener', 'first_player'])


def test_auction_bid():
    """
        new Game + 1 bid (OK + all same except for bid)
    """
    game = Game(first_player=Player.ONE)
    before_state = game.describe()
    action = {'player': Player.ONE, 'passed': False, 'color': 's', 'value': 80}
    assert game.update(**action) == OK_CODE
    after_state = game.describe()
    assert after_state['auction']['bids'] == {
        Player.ONE.value: Bid(color='s', value=80).describe(),
        Player.TWO.value: None, Player.THREE.value: None, Player.FOUR.value: None
    }
    assert after_state['auction']['current_best'] == Player.ONE.value
    assert after_state['auction']['current_passed'] == 0
    assert partially_compare_dict(before_state, after_state,
                                  ['auction.bids', 'auction.current_best', 'auction.current_passed'])


def test_auction_passed_and_bid():
    """
        new Game + 1 passed + 1 bid (OK + all same except for bid and current_passed)
    """
    game = Game(first_player=Player.ONE)
    before_state = game.describe()
    actions = [{'player': Player.ONE, 'passed': True, 'color': None, 'value': None},
               {'player': Player.TWO, 'passed': False, 'color': 's', 'value': 80},
               {'player': Player.THREE, 'passed': True, 'color': None, 'value': None}]
    for action in actions:
        assert game.update(**action) == OK_CODE
    after_state = game.describe()
    assert after_state['auction']['bids'] == {
        Player.ONE.value: None, Player.TWO.value: Bid(color='s', value=80).describe(),
        Player.THREE.value: None, Player.FOUR.value: None
    }
    assert after_state['auction']['current_best'] == Player.TWO.value
    assert after_state['auction']['current_passed'] == 1
    assert partially_compare_dict(before_state, after_state,
                                  ['auction.bids', 'auction.current_best', 'auction.current_passed'])


def test_auction_invalid_bid(caplog):
    """
        new Game + 1 valid bid + 1 invalid bid (ERROR + log)
    """
    caplog.set_level(logging.WARNING)
    game = Game(first_player=Player.ONE)
    valid_bid = {'player': Player.ONE, 'passed': False, 'color': 's', 'value': 80}
    invalid_bid = {'player': Player.TWO, 'passed': False, 'color': 'd', 'value': 80}
    assert game.update(**valid_bid) == OK_CODE
    assert game.update(**invalid_bid) == VALIDATION_ERROR_CODE
    log_messages = [msg for (logger_instance, lvl, msg) in caplog.record_tuples]
    assert f"Validation went wrong in Class Auction for parameters {invalid_bid}" in log_messages


def test_auction_end(caplog):
    """
        new Game + 1 valid bid + 3 passed (OK + end of auction log + State.PLAYING + all same except for bid)
    """
    caplog.set_level(logging.INFO)
    game = Game(first_player=Player.ONE)
    before_state = game.describe()
    actions = [{'player': Player.ONE, 'passed': False, 'color': 's', 'value': 80},
               {'player': Player.TWO, 'passed': True, 'color': None, 'value': None},
               {'player': Player.THREE, 'passed': True, 'color': None, 'value': None},
               {'player': Player.FOUR, 'passed': True, 'color': None, 'value': None}]
    for action in actions:
        assert game.update(**action) == OK_CODE
    after_state = game.describe()
    log_messages = [msg for (logger_instance, lvl, msg) in caplog.record_tuples]
    assert 'End of the auction' in log_messages
    assert after_state['auction']['bids'] == {
        Player.ONE.value: Bid(color='s', value=80).describe(),
        Player.TWO.value: None, Player.THREE.value: None, Player.FOUR.value: None
    }
    assert after_state['auction']['current_best'] == Player.ONE.value
    assert after_state['auction']['current_passed'] == 2
    assert after_state['state'] == State.PLAYING.value
    assert after_state['round']['trump'] == 's'
    assert partially_compare_dict(before_state, after_state,
                                  ['auction.bids', 'auction.current_best', 'auction.current_passed',
                                   'state', 'round.trump'])


def test_round_invalid_card_index(caplog):
    """
        Game@Round + card not in hand (ERROR + log)
    """
    caplog.set_level(logging.WARNING)
    game = Game(first_player=Player.ONE)

    bid_actions = [{'player': Player.ONE, 'passed': False, 'color': 's', 'value': 80},
                   {'player': Player.TWO, 'passed': True, 'color': None, 'value': None},
                   {'player': Player.THREE, 'passed': True, 'color': None, 'value': None},
                   {'player': Player.FOUR, 'passed': True, 'color': None, 'value': None}]
    for action in bid_actions:
        assert game.update(**action) == OK_CODE

    action = {'player': Player.ONE, 'card_index': 8}
    assert game.update(**action) == VALIDATION_ERROR_CODE
    log_messages = [msg for (logger_instance, lvl, msg) in caplog.record_tuples]
    assert "Card index (8) is higher than the number of cards in hand (8)" in log_messages
    assert f"Validation went wrong in Class Round for parameters {action}" in log_messages


xxx = {
    Player.ONE: [Card('7', 's'), Card('8', 's'), Card('9', 's'), Card('10', 's'), Card('J', 's'), Card('Q', 's'), Card('K', 's'), Card('A', 's')],
    Player.TWO: [Card('7', 'd'), Card('8', 'd'), Card('9', 'd'), Card('10', 'd'), Card('J', 'd'), Card('Q', 'd'), Card('K', 'd'), Card('A', 'd')],
    Player.THREE: [Card('7', 'h'), Card('8', 'h'), Card('9', 'h'), Card('10', 'h'), Card('J', 'h'), Card('Q', 'h'), Card('K', 'h'), Card('A', 'h')],
    Player.FOUR: [Card('7', 'c'), Card('8', 'c'), Card('9', 'c'), Card('10', 'c'), Card('J', 'c'), Card('Q', 'c'), Card('K', 'c'), Card('A', 'c')],
}


@pytest.mark.parametrize('hands, trump, log', [
    # case 1: trump asked + trump in hand + no trump played
    (
        {
            Player.ONE: [Card('7', 's'), Card('8', 'd'), Card('9', 'd'), Card('10', 'd'), Card('J', 'd'), Card('Q', 'd'), Card('K', 'd'), Card('A', 'd')],
            Player.TWO: [Card('8', 's'), Card('7', 'h'), Card('8', 'h'), Card('9', 'h'), Card('10', 'h'), Card('J', 'h'), Card('Q', 'h'), Card('K', 'h')],
            Player.THREE: [Card('9', 's'), Card('7', 'c'), Card('8', 'c'), Card('9', 'c'), Card('10', 'c'), Card('J', 'c'), Card('Q', 'c'), Card('K', 'c')],
            Player.FOUR: [Card('7', 'd'), Card('10', 's'), Card('J', 's'), Card('Q', 's'), Card('K', 's'), Card('A', 's'), Card('A', 'h'), Card('A', 'c')],
        },
        's',
        f"Playing trumps, card ({Card('7', 'd').describe()}) must be trump (s)"
    ),
    # case 2: trump asked + trump in hand + trump played but not high enough
    (
        {
            Player.ONE: [Card('7', 's'), Card('8', 'd'), Card('9', 'd'), Card('10', 'd'), Card('J', 'd'), Card('Q', 'd'), Card('K', 'd'), Card('A', 'd')],
            Player.TWO: [Card('8', 's'), Card('7', 'h'), Card('8', 'h'), Card('9', 'h'), Card('10', 'h'), Card('J', 'h'), Card('Q', 'h'), Card('K', 'h')],
            Player.THREE: [Card('9', 's'), Card('7', 'c'), Card('8', 'c'), Card('9', 'c'), Card('10', 'c'), Card('J', 'c'), Card('Q', 'c'), Card('K', 'c')],
            Player.FOUR: [Card('10', 's'), Card('7', 's'), Card('J', 's'), Card('Q', 's'), Card('K', 's'), Card('A', 's'), Card('A', 'h'), Card('A', 'c')],
        },
        's',
        f"Playing trumps, card ({Card('10', 's').describe()}) "
        f"must be higher than current leading trump ({Card('9', 's').describe()})"
    ),
    # case 3: color asked + color in hand + no color played
    (
        {
            Player.ONE: [Card('7', 's'), Card('8', 'd'), Card('9', 'd'), Card('10', 'd'), Card('J', 'd'), Card('Q', 'd'), Card('K', 'd'), Card('A', 'd')],
            Player.TWO: [Card('8', 's'), Card('7', 'h'), Card('8', 'h'), Card('9', 'h'), Card('10', 'h'), Card('J', 'h'), Card('Q', 'h'), Card('K', 'h')],
            Player.THREE: [Card('9', 's'), Card('7', 'c'), Card('8', 'c'), Card('9', 'c'), Card('10', 'c'), Card('J', 'c'), Card('Q', 'c'), Card('K', 'c')],
            Player.FOUR: [Card('7', 'd'), Card('10', 's'), Card('J', 's'), Card('Q', 's'), Card('K', 's'), Card('A', 's'), Card('A', 'h'), Card('A', 'c')],
        },
        'd',
        f"Player has to play trick color (s), but played instead {Card('7', 'd').describe()}"
    ),
    # case 4: color asked + no color in hand + trump in hand + partner no leader + no trump played
    (
        {
            Player.ONE: [Card('7', 's'), Card('7', 'c'), Card('9', 's'), Card('10', 's'), Card('J', 's'), Card('Q', 's'), Card('K', 's'), Card('A', 's')],
            Player.TWO: [Card('A', 'd'), Card('8', 'd'), Card('9', 'd'), Card('10', 'd'), Card('J', 'd'), Card('Q', 'd'), Card('K', 'd'), Card('7', 'd')],
            Player.THREE: [Card('8', 's'), Card('8', 'h'), Card('9', 'h'), Card('10', 'h'), Card('J', 'h'), Card('Q', 'h'), Card('K', 'h'), Card('A', 'h')],
            Player.FOUR: [Card('7', 'h'), Card('8', 'c'), Card('9', 'c'), Card('10', 'c'), Card('J', 'c'), Card('Q', 'c'), Card('K', 'c'), Card('A', 'c')],
        },
        'c',
        f"Can not furnish on color s, player must cut but instead played {Card('7', 'h').describe()}"
    ),
    # case 5: color asked + no color in hand + trump in hand + partner no leader + trump leads + trump played but not high enough
    (
        {
            Player.ONE: [Card('7', 's'), Card('8', 's'), Card('9', 's'), Card('10', 's'), Card('J', 's'), Card('Q', 's'), Card('K', 's'), Card('A', 's')],
            Player.TWO: [Card('7', 'c'), Card('8', 'd'), Card('9', 'd'), Card('10', 'd'), Card('J', 'd'), Card('Q', 'd'), Card('K', 'd'), Card('A', 'd')],
            Player.THREE: [Card('10', 'c'), Card('8', 'h'), Card('9', 'h'), Card('10', 'h'), Card('J', 'h'), Card('Q', 'h'), Card('K', 'h'), Card('A', 'h')],
            Player.FOUR: [Card('8', 'c'), Card('7', 'd'), Card('9', 'c'), Card('7', 'h'), Card('J', 'c'), Card('Q', 'c'), Card('K', 'c'), Card('A', 'c')],
        },
        'c',
        f"Can not furnish on color s, player must cut with a high enough trump, "
        f"but instead played {Card('8', 'c').describe()}"
    ),
])
@patch('reinforcement.models.Game.deal')
def test_round_wrong_card(deal_mock, hands, trump, log, caplog):
    """
        Game@Round + wrong card (cf Round.card_is_playable for all possibilities) (ERROR + log)
    """
    deal_mock.return_value = hands
    caplog.set_level(logging.WARNING)
    game = Game(first_player=Player.ONE)

    bid_actions = [{'player': Player.ONE, 'passed': False, 'color': trump, 'value': 80},
                   {'player': Player.TWO, 'passed': True, 'color': None, 'value': None},
                   {'player': Player.THREE, 'passed': True, 'color': None, 'value': None},
                   {'player': Player.FOUR, 'passed': True, 'color': None, 'value': None}]
    for action in bid_actions:
        assert game.update(**action) == OK_CODE

    round_actions = [{'player': Player.ONE, 'card_index': 0},
                     {'player': Player.TWO, 'card_index': 0},
                     {'player': Player.THREE, 'card_index': 0}]
    for action in round_actions:
        assert game.update(**action) == OK_CODE

    wrong_card_action = {'player': Player.FOUR, 'card_index': 0}
    assert game.update(**wrong_card_action) == VALIDATION_ERROR_CODE
    log_messages = [msg for (logger_instance, lvl, msg) in caplog.record_tuples]
    assert {log, f"Validation went wrong in Class Round for parameters {wrong_card_action}"}.issubset(set(log_messages))


def test_round_valid_card():
    """
        Game@Round + correct card (OK + state checking)
    """
    game = Game(first_player=Player.ONE)

    bid_actions = [{'player': Player.ONE, 'passed': False, 'color': 's', 'value': 80},
                   {'player': Player.TWO, 'passed': True, 'color': None, 'value': None},
                   {'player': Player.THREE, 'passed': True, 'color': None, 'value': None},
                   {'player': Player.FOUR, 'passed': True, 'color': None, 'value': None}]
    for action in bid_actions:
        assert game.update(**action) == OK_CODE

    before_state = game.describe()
    action = {'player': Player.ONE, 'card_index': 0}
    assert game.update(**action) == OK_CODE
    after_state = game.describe()
    assert after_state['round']['hands'] == {
        Player.ONE.value: {'cards': before_state['round']['hands'][Player.ONE.value]['cards'][1:]},
        Player.TWO.value: before_state['round']['hands'][Player.TWO.value],
        Player.THREE.value: before_state['round']['hands'][Player.THREE.value],
        Player.FOUR.value: before_state['round']['hands'][Player.FOUR.value]
    }
    assert after_state['round']['trick_cards']['cards'] == {
        Player.ONE.value: before_state['round']['hands'][Player.ONE.value]['cards'][0],
        Player.TWO.value: None, Player.THREE.value: None, Player.FOUR.value:  None
    }
    assert after_state['round']['trick_cards']['leader'] == Player.ONE.value
    assert partially_compare_dict(before_state, after_state, ['round.belote', 'round.hands',
                                                              'round.trick_cards.cards', 'round.trick_cards.leader'])


@patch('reinforcement.models.Game.deal')
def test_round_full(deal_mock, caplog):
    """
        Game@Round + 1 FULL ROUND (including belote) (OK check at each update + check for score)
    """
    deal_mock.side_effect = [
        {
            Player.ONE: [Card('7', 'h'), Card('9', 'h'), Card('A', 'h'), Card('7', 's'), Card('A', 's'), Card('Q', 'd'), Card('K', 'c'), Card('A', 'c')],
            Player.TWO: [Card('J', 'h'), Card('K', 'h'), Card('9', 's'), Card('Q', 's'), Card('9', 'd'), Card('J', 'd'), Card('10', 'd'), Card('8', 'c')],
            Player.THREE: [Card('8', 'h'), Card('Q', 'h'), Card('10', 'h'), Card('K', 's'), Card('K', 'd'), Card('Q', 'c'), Card('10', 'c'), Card('J', 'c')],
            Player.FOUR: [Card('8', 's'), Card('J', 's'), Card('10', 's'), Card('7', 'd'), Card('8', 'd'), Card('A', 'd'), Card('7', 'c'), Card('9', 'c')]
        },
        {Player.ONE: 'RANDOM', Player.TWO: 'RANDOM', Player.THREE: 'RANDOM', Player.FOUR: 'RANDOM'}]
    caplog.set_level(logging.INFO)
    game = Game(first_player=Player.ONE)

    auction_actions = [
        {'player': Player.ONE, 'passed': True, 'color': None, 'value': None},
        {'player': Player.TWO, 'passed': True, 'color': None, 'value': None},
        {'player': Player.THREE, 'passed': False, 'color': 'c', 'value': 80},
        {'player': Player.FOUR, 'passed': True, 'color': None, 'value': None},
        {'player': Player.ONE, 'passed': False, 'color': 'c', 'value': 90},
        {'player': Player.TWO, 'passed': True, 'color': None, 'value': None},
        {'player': Player.THREE, 'passed': True, 'color': None, 'value': None},
        {'player': Player.FOUR, 'passed': True, 'color': None, 'value': None},
    ]
    # 'gameHistory':
    # {'west': [ 'Kc',  'Qd',  'Ac',  'Ah', '7h', '9h', 'As', '7s' ],
    #  'east': [ '10c', 'Kd',  '10h', 'Qh', 'Qc', '8h', 'Ks', 'Jc' ],
    #  'north': ['9c',  'Ad',  '7d',  '7c', '8d', '8s', 'Js', '10s'],
    #  'south': ['8c',  '10d', '9d',  'Jh', 'Jd', 'Kh', '9s', 'Qs' ]},
    round_actions = [
        # trick 1
        {'player': Player.ONE, 'card_index': 6}, {'player': Player.TWO, 'card_index': 7},
        {'player': Player.THREE, 'card_index': 6}, {'player': Player.FOUR, 'card_index': 7},
        # trick 2
        {'player': Player.FOUR, 'card_index': 5}, {'player': Player.ONE, 'card_index': 5},
        {'player': Player.TWO, 'card_index': 6}, {'player': Player.THREE, 'card_index': 4},  # <-- 5->6 P2
        # trick 3
        {'player': Player.FOUR, 'card_index': 3}, {'player': Player.ONE, 'card_index': 5},
        {'player': Player.TWO, 'card_index': 4}, {'player': Player.THREE, 'card_index': 2},
        # trick 4
        {'player': Player.ONE, 'card_index': 2}, {'player': Player.TWO, 'card_index': 0},
        {'player': Player.THREE, 'card_index': 1}, {'player': Player.FOUR, 'card_index': 4},
        # trick 5
        {'player': Player.FOUR, 'card_index': 3}, {'player': Player.ONE, 'card_index': 0},
        {'player': Player.TWO, 'card_index': 3}, {'player': Player.THREE, 'card_index': 2},
        # trick 6
        {'player': Player.THREE, 'card_index': 0}, {'player': Player.FOUR, 'card_index': 0},
        {'player': Player.ONE, 'card_index': 0}, {'player': Player.TWO, 'card_index': 0},
        # trick 7
        {'player': Player.TWO, 'card_index': 0}, {'player': Player.THREE, 'card_index': 0},
        {'player': Player.FOUR, 'card_index': 0}, {'player': Player.ONE, 'card_index': 1},
        # trick 8
        {'player': Player.ONE, 'card_index': 0}, {'player': Player.TWO, 'card_index': 0},
        {'player': Player.THREE, 'card_index': 0}, {'player': Player.FOUR, 'card_index': 0},
    ]

    for action in auction_actions + round_actions:
        assert game.update(**action) == OK_CODE

    after_state = game.describe()
    expected_state = {
        'auction': {'bids': {Player.THREE.value: None, Player.FOUR.value: None,
                             Player.TWO.value: None, Player.ONE.value: None},
                    'current_best': None,
                    'current_passed': -1},
        'first_player': Player.TWO.value,
        'round': {'belote': [],
                  'hands': {Player.ONE.value: {'cards': 'RANDOM'}, Player.TWO.value: {'cards': 'RANDOM'},
                            Player.THREE.value: {'cards': 'RANDOM'}, Player.FOUR.value: {'cards': 'RANDOM'}},
                  'score': {Team.ONE.value: 0, Team.TWO.value: 0},
                  'trick': 0,
                  'trick_cards': {'cards': {Player.THREE.value: None, Player.FOUR.value: None,
                                            Player.TWO.value: None, Player.ONE.value: None},
                                  'leader': None},
                  'trick_opener': Player.TWO.value,
                  'trump': None},
        'score': {Team.ONE.value: 0, Team.TWO.value: 250},
        'state': State.AUCTION.value
    }
    assert partially_compare_dict(after_state, expected_state, [])

    log_messages = [msg for (logger_instance, lvl, msg) in caplog.record_tuples]
    assert log_messages == [
        "End of the auction", "(Re-)Belote",
        "End of the trick", "End of the trick", "End of the trick", "End of the trick",
        "(Re-)Belote",
        "End of the trick", "End of the trick", "End of the trick", "End of the trick",
        "End of the round",
        f"Contract (90) has not been reached (86) by {Team.ONE.value}"
    ]

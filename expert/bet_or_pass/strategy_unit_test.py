from unittest.mock import patch

import pytest

from expert.bet_or_pass.combinations import MAIN_COMBINATIONS, SUPPORT_COMBINATIONS
from expert.bet_or_pass.strategy import (
    detect_combination_in_hand, compute_best_color_bet, compute_support_score,
    derive_score,
    extract_speakers,
    have_player_and_partner_spoken_over_same_color,
    extract_leader,
    get_best_opponent_bid,
    bet_or_pass_only_opponents_spoke,
    bet_or_pass_expert_strategy,
)
from helpers.exceptions import UnhandledBetOrPassCaseException


@pytest.mark.parametrize(
    'combination, cards, trump_color, only_trump, expected',
    [
        ('A', ['7s', 'As', '7d'], 'd', False, 1),
        ('A', ['7s', 'As', '7d'], 's', False, 0),
        ('A', ['7s', 'As', '7d'], 's', True, 1),
        ('K/A', ['7s', 'Ks', 'As', 'Kd', '7h'], 'h', False, 3),
        ('K+A', ['7s', 'Ks', 'As', 'Kd', '7h', 'Ac'], 'h', False, 1),
        ('K+A', ['7s', 'Ks', 'As', 'Kd', '7h', 'Ac'], 's', False, 0),
        ('7+8+9/Q+K+A', ['7s', '8s', '9s'], 's', True, 0),
        ('7+8+9/Q+K+A', ['7s', '8s', '9s', 'Ks', 'As'], 's', True, 1),
    ]
)
def test_detect_combination_in_hand(combination, cards, trump_color, only_trump, expected):
    assert detect_combination_in_hand(combination, cards, trump_color, only_trump) == expected


def test_derive_score_dict():
    assert derive_score(1, {1: 10, 2: 20}, None) == 10


def test_derive_score_dict_unknown_key():
    assert derive_score(3, {1: 10, 2: 20}, None) == 0


def test_derive_score_std_value():
    assert derive_score(1, 10, None) == 10


def test_derive_score_max():
    assert derive_score(3, 10, 20) == 20


@pytest.mark.parametrize(
    'players_bids, expected',
    [
        (
            {
                'west': {'value': None, 'color': None}, 'east': {'value': None, 'color': None},
                'north': {'value': None, 'color': None}, 'south': {'value': None, 'color': None},
            },
            set()  # none spoke
        ),
        (
            {
                'west': {'value': None, 'color': None}, 'east': {'value': 80, 'color': 's'},
                'north': {'value': None, 'color': None}, 'south': {'value': None, 'color': None},
            },
            {'east'}  # one spoke
        ),
        (
            {
                'west': {'value': 80, 'color': 's'}, 'east': {'value': 100, 'color': 'd'},
                'north': {'value': 110, 'color': 'h'}, 'south': {'value': 90, 'color': 'c'},
            },
            {'west', 'south', 'east', 'north'}  # all spoke
        ),
    ]
)
def test_extract_speakers(players_bids, expected):
    assert extract_speakers(players_bids) == expected


@pytest.mark.parametrize(
    'players_bids, expected',
    [
        (
            {
                'west': {'value': None, 'color': None}, 'east': {'value': None, 'color': None},
                'north': {'value': None, 'color': None}, 'south': {'value': None, 'color': None},
            },
            False  # none spoke
        ),
        (
            {
                'west': {'value': None, 'color': None}, 'east': {'value': None, 'color': None},
                'north': {'value': 80, 'color': 's'}, 'south': {'value': None, 'color': None},
            },
            False  # one spoke
        ),
        (
            {
                'west': {'value': 80, 'color': 's'}, 'east': {'value': 100, 'color': 'd'},
                'north': {'value': 110, 'color': 'h'}, 'south': {'value': 90, 'color': 'c'},
            },
            False  # both spoke with different colors
        ),
        (
            {
                'west': {'value': 80, 'color': 's'}, 'east': {'value': 100, 'color': 'd'},
                'north': {'value': 110, 'color': 'h'}, 'south': {'value': 90, 'color': 'h'},
            },
            True  # both spoke with same color
        ),
    ]
)
def test_have_player_and_partner_spoken_over_same_color(players_bids, expected):
    assert have_player_and_partner_spoken_over_same_color('south', players_bids) == expected


@pytest.mark.parametrize(
    'players_bids, expected',
    [
        (
            {
                'west': {'value': None, 'color': None}, 'east': {'value': None, 'color': None},
                'north': {'value': None, 'color': None}, 'south': {'value': None, 'color': None},
            },
            None  # none spoke
        ),
        (
            {
                'west': {'value': None, 'color': None}, 'east': {'value': None, 'color': None},
                'north': {'value': 80, 'color': 's'}, 'south': {'value': None, 'color': None},
            },
            'north'  # one spoke
        ),
        (
            {
                'west': {'value': 80, 'color': 's'}, 'east': {'value': 100, 'color': 'd'},
                'north': {'value': 110, 'color': 'h'}, 'south': {'value': 90, 'color': 'c'},
            },
            'north'  # all spoke
        ),
    ]
)
def test_extract_leader(players_bids, expected):
    assert extract_leader(players_bids) == expected


@pytest.mark.parametrize(
    'players_bids, expected',
    [
        (
            {
                'west': {'value': None, 'color': None}, 'east': {'value': None, 'color': None},
                'north': {'value': None, 'color': None}, 'south': {'value': None, 'color': None},
            },
            (None, None)  # none spoke
        ),
        (
            {
                'west': {'value': 90, 'color': 'h'}, 'east': {'value': None, 'color': None},
                'north': {'value': 80, 'color': 's'}, 'south': {'value': None, 'color': None},
            },
            ('h', 90)  # 2 spoke
        ),
        (
            {
                'west': {'value': 80, 'color': 's'}, 'east': {'value': 100, 'color': 'd'},
                'north': {'value': 110, 'color': 'h'}, 'south': {'value': 90, 'color': 'c'},
            },
            ('d', 100)  # all spoke
        ),
    ]
)
def test_get_best_opponent_bid(players_bids, expected):
    assert get_best_opponent_bid(players_bids, ['east', 'west']) == expected


@pytest.mark.parametrize(
    'player_cards, expected',
    [
        ([], (None, -1)),  # empty
        (['7s', 'Js', '8d', 'Ad', 'Kc', '10c', '7h', '8h'], (None, -1)),  # pass
        (['9s', 'Js', '7d', '8d', '10d', 'Jc', '9h', 'Kh'], ('s', 80)),  # bet without bonus (1)
        (['7s', '9s', 'Ks', '7d', '10d', '7h', 'Jh', 'Ah'], ('h', 80)),  # bet without bonus (2)
        (['Js', 'Qs', 'Ks', '10s', '8d', '10d', 'Kc', '10c'], ('s', 100)),  # bet with std + bonus
        (['7s', '8s', 'Js', 'Qs', 'Ks', '10c', '7h', '8h'], ('s', 100)),  # bet with std / bonus
        (['7s', '8s', 'Js', 'Ks', '8d', 'Ad', 'Ac', 'Ah'], ('s', 100)),  # bet with dict bonus
        (['7s', '8s', '9s', 'As', '10d', 'Ad', '10c', 'Ac'], ('s', 100)),  # bet with max bonus
        (['9s', 'Js', 'Qs', 'Ks', '7d', '10d', 'Ad', '7h'], ('s', 130)),  # bet with mixed bonus
        (['Js', 'Qs', 'Ks', '9d', 'Jd', '9c', 'Jc', '10c'], ('c', 90)),  # bet in best color
    ]
)
def test_compute_best_color_bet(player_cards, expected):
    assert compute_best_color_bet(player_cards, MAIN_COMBINATIONS) == expected


def test_compute_best_color_bet_without_trigger_info():
    with pytest.raises(KeyError):
        compute_best_color_bet([], [{'not_trigger': 'X'}])


def test_compute_best_color_bet_without_value_info():
    with pytest.raises(KeyError):
        compute_best_color_bet(['Xs'], [{'trigger': 'X', 'bonus': [{'pattern': 'Y', 'not_value': None}]}])


@pytest.mark.parametrize(
    'player_cards, expected',
    [
        ([], 0),  # empty
        (['7s', '10s', '8d', '10d', 'Kc', '10c', '7h', '8h'], 0),  # nothing
        (['7s', 'Js', '8d', '10d', 'Kc', '10c', '7h', '8h'], 20),  # J
        (['7s', '9s', '8d', '10d', 'Kc', '10c', '7h', '8h'], 10),  # 9
        (['Qs', 'Ks', '8d', '10d', 'Kc', '10c', '7h', '8h'], 20),  # Q+K
        (['As', '7d', '8d', 'Ad', 'Jc', 'Ac', '9h', 'Ah'], 20),  # enough A
        (['7d', '8d', 'Ad', 'Jc', 'Qc', '9h', '10h'], 0),  # not enough A
        (['9s', 'Js', 'Qs', 'Ks', 'Jc', 'Ac', '9h', 'Ah'], 60),  # all
    ]
)
def test_compute_support_score(player_cards, expected):
    assert compute_support_score(player_cards, 's', SUPPORT_COMBINATIONS) == expected


def test_bet_or_pass_expert_strategy_unhandled_case_exception_1():
    with pytest.raises(UnhandledBetOrPassCaseException), \
         patch('expert.bet_or_pass.strategy.extract_leader') as extract_leader_mock:
        extract_leader_mock.return_value  = None
        bet_or_pass_expert_strategy(
            player='south',
            player_cards=[],
            players_bids={
                'west': {'value': 100, 'color': 'h'}, 'east': {'value': 80, 'color': 'h'},
                'north': {'value': 90, 'color': 'c'}, 'south': {'value': None, 'color': None}
            },
        )


def test_bet_or_pass_expert_strategy_unhandled_case_exception_2():
    with pytest.raises(UnhandledBetOrPassCaseException), \
         patch('expert.bet_or_pass.strategy.extract_leader') as extract_leader_mock:
        extract_leader_mock.return_value = None
        bet_or_pass_expert_strategy(
            player='south',
            player_cards=[],
            players_bids={
                'west': {'value': None, 'color': None}, 'east': {'value': 90, 'color': 'h'},
                'north': {'value': 100, 'color': 'c'}, 'south': {'value': 80, 'color': 's'}
            },
        )


def test_bet_or_pass_expert_strategy_unhandled_case_exception_3():
    with pytest.raises(UnhandledBetOrPassCaseException), \
         patch('expert.bet_or_pass.strategy.extract_speakers') as extract_speakers_mock:
        extract_speakers_mock.return_value = {'mock_speaker_1', 'mock_speaker_2'}
        bet_or_pass_expert_strategy(
            player='south',
            player_cards=[],
            players_bids={},
        )

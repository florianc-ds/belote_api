import pytest

from expert.bet_or_pass.combinations import MAIN_COMBINATIONS
from expert.bet_or_pass.strategy import detect_combination_in_hand, compute_best_color_bet


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

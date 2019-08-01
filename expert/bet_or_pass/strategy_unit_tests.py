import pytest

from expert.bet_or_pass.strategy import detect_combination_in_hand


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

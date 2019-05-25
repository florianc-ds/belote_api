import pytest

from expert_agent import (
    derive_player_rank_in_round, is_trump_asked, has_trump_in_hand, get_lowest_trump_card,
    get_lowest_plain_card,
)


@pytest.mark.parametrize(
    'input, expected',
    [
        ({'west': None, 'east': None, 'north': None, 'south': None}, 0),
        ({'west': '10d', 'east': None, 'north': None, 'south': None}, 1),
        ({'west': '10d', 'east': '7s', 'north': None, 'south': None}, 2),
        ({'west': '10d', 'east': '7s', 'north': 'Kh', 'south': None}, 3),
    ]
)
def test_derive_player_rank_in_round(input, expected):
    assert derive_player_rank_in_round(input) == expected


@pytest.mark.parametrize(
    'round_cards, trump_color, expected',
    [
        ({'east': None, 'north': None, 'west': None, 'south': None}, 'd', None),
        ({'east': '10d', 'north': '7s', 'west': 'Kh', 'south': None}, 'd', True),
        ({'east': None, 'north': '7s', 'west': 'Kd', 'south': None}, 'd', False),
        ({'east': None, 'north': None, 'west': 'Kd', 'south': None}, 'd', True),
    ]
)
def test_is_trump_asked(round_cards, trump_color, expected):
    assert is_trump_asked('south', round_cards, trump_color) == expected


@pytest.mark.parametrize(
    'cards, trump_color, expected',
    [
        (['10h', 'Kd', '7s'], 'h', True),
        (['10s', 'Kd', '7s'], 'h', False),
        ([], 'h', False),
    ]
)
def test_has_trump_in_hand(cards, trump_color, expected):
    assert has_trump_in_hand(cards, trump_color) == expected


@pytest.mark.parametrize(
    'cards, trump_color, expected',
    [
        (['10h', 'Kh', '9h', '7s'], 'h', 'Kh'),
        (['10h', 'Kh', '9h', '7s', '7h', '8h'], 'h', '7h'),
    ]
)
def test_get_lowest_trump_card(cards, trump_color, expected):
    assert get_lowest_trump_card(cards, trump_color) == expected


def test_get_lowest_trump_card_fails():
    with pytest.raises(ValueError):
        get_lowest_trump_card(['10h', 'Kh', '9h', '7s'], 'd')


@pytest.mark.parametrize(
    'cards, expected',
    [
        (['10h', 'Kh', '9h', '7s'], '7s'),
        (['10h', 'Kh', '9h', '7s', '7h', '8d'], '7h'),
    ]
)
def test_get_lowest_plain_card(cards, expected):
    assert get_lowest_plain_card(cards) == expected


def test_get_lowest_plain_card_fails():
    with pytest.raises(ValueError):
        get_lowest_plain_card([])

import pytest

from expert_agent import (
    derive_player_rank_in_round, is_trump_asked, has_color_in_hand, get_lowest_trump_card,
    get_lowest_plain_card,
    has_highest_plain_color_card_in_hand,
    has_player_cut_color,
    has_player_already_shown_he_had_no_more_trump,
    get_lowest_color_card,
    get_highest_color_card,
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
def test_has_color_in_hand(cards, trump_color, expected):
    assert has_color_in_hand(cards, trump_color) == expected


@pytest.mark.parametrize(
    'hand_cards, cards_history, color, expected',
    [
        (['Ah'], {'east': ['10d'], 'north': ['7d'], 'west': ['Kd'], 'south': ['Ad']}, 'h', True),
        (['Qh', 'Kd', 'As'], {'east': ['10h'], 'north': [], 'west': ['Kh'], 'south': ['Ah']}, 'h', True),
        (['8h'], {'east': ['10h', 'Qh'], 'north': ['Jh'], 'west': ['Kh'], 'south': ['Ah']}, 'h', False),
        (
                ['As'],
                {'east': ['7h', '8h'], 'north': ['9h', '10h'], 'west': ['Jh', 'Qh'], 'south': ['Kh', 'Ah']},
                'h',
                False
        ),
    ]
)
def test_has_highest_plain_color_card_in_hand(hand_cards, cards_history, color, expected):
    assert has_highest_plain_color_card_in_hand(hand_cards, cards_history, color) == expected


@pytest.mark.parametrize(
    'game_history, rounds_first_player, expected',
    [
        ({'west': [], 'east': [], 'north': [], 'south': []}, [], False),
        ({'west': ['10s', 'Ah'], 'east': [], 'north': ['9s', '10c'], 'south': ['7s']}, ['south', 'west'], True),
        ({'west': ['10s', 'Ah'], 'east': [], 'north': ['9s', '10h'], 'south': ['7s']}, ['south', 'west'], False),
        ({'west': [], 'east': [], 'north': ['9h'], 'south': []}, ['north'], False),
        ({'west': ['10s'], 'east': [], 'north': ['10h'], 'south': []}, ['west'], False),
    ]
)
def test_has_player_cut_color(game_history, rounds_first_player, expected):
    assert has_player_cut_color('north', game_history, rounds_first_player, color='h', trump_color='c') == expected


@pytest.mark.parametrize(
    'game_history, rounds_first_player, expected',
    [
        ({'west': [], 'east': [], 'north': [], 'south': []}, [], False),
        ({'west': ['10c'], 'east': [], 'north': ['Kd'], 'south': []}, ['west'], True),
        ({'west': ['Jd'], 'east': ['10d'], 'north': ['7d'], 'south': ['Kd']}, ['west'], False),
        ({'west': ['Jd'], 'east': ['10d'], 'north': ['7c'], 'south': ['Kd']}, ['west'], False),
        ({'west': ['Jd'], 'east': ['10d'], 'north': ['7h'], 'south': ['Kd']}, ['west'], True),
        ({'west': ['Jd'], 'east': ['10d'], 'north': ['7h'], 'south': ['Ad']}, ['west'], False),
        ({'west': ['Jd'], 'east': ['10d'], 'north': ['7h'], 'south': ['Ad']}, ['east'], True),
        ({'west': ['Jd'], 'east': ['10d'], 'north': ['7h'], 'south': ['7c']}, ['west'], False),
    ]
)
def test_has_player_already_shown_he_had_no_more_trump(game_history, rounds_first_player, expected):
    assert has_player_already_shown_he_had_no_more_trump('north', game_history, rounds_first_player, 'c') == expected


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
    'cards, color, expected',
    [
        (['10h', 'Kh', '9h', '7s'], 'h', '9h'),
        (['10h', 'Kh', '9h', '7s', '7h', '8h'], 'h', '7h'),
    ]
)
def test_get_lowest_color_card(cards, color, expected):
    assert get_lowest_color_card(cards, color) == expected


def test_get_lowest_color_card_fails():
    with pytest.raises(ValueError):
        get_lowest_color_card(['10h', 'Kh', '9h', '7s'], 'd')


@pytest.mark.parametrize(
    'cards, color, expected',
    [
        (['10h', 'Kh', '9h', '7s'], 'h', '10h'),
        (['10h', 'Kh', '9h', '7s', '7h', 'Ah'], 'h', 'Ah'),
    ]
)
def test_get_highest_color_card(cards, color, expected):
    assert get_highest_color_card(cards, color) == expected


def test_get_highest_color_card_fails():
    with pytest.raises(ValueError):
        get_highest_color_card(['10h', 'Kh', '9h', '7s'], 'd')


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

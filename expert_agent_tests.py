import pytest

from expert_agent import derive_player_rank_in_round, is_trump_asked


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

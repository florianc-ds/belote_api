import json
from unittest.mock import patch

import pytest

from expert.bet_or_pass import strategy

GAME_CONFIGS_PATH = 'expert/bet_or_pass/game_configurations.json'


def generate_test_cases():
    with open(GAME_CONFIGS_PATH, 'rb') as json_file:
        game_configs = json.load(json_file)

    return game_configs


test_cases = generate_test_cases()


@pytest.mark.parametrize(
    'description, data, bet_or_pass_block, expected_action, expected_color, expected_value',
    [
        [
            test_case['_description'],
            {k: v for k, v in test_case.items() if not k.startswith('_')},
            test_case['_bet_or_pass_block'],
            test_case['_expected_action'],
            test_case['_expected_color'],
            test_case['_expected_value'],
        ]
        for test_case in test_cases
    ]
)
def test_play_expert_strategy(description, data, bet_or_pass_block, expected_action, expected_color, expected_value):
    print(description)  # only prints if test fails

    # check right bet_or_pass_... block has been called
    if bet_or_pass_block != 'pass':
        bet_or_pass_block_copy = getattr(strategy, bet_or_pass_block)
        with patch(f'expert.bet_or_pass.strategy.{bet_or_pass_block}') as bet_or_pass_block_mock:
            bet_or_pass_block_mock.side_effect = bet_or_pass_block_copy
            output = strategy.bet_or_pass_expert_strategy(**data)
            bet_or_pass_block_mock.assert_called_once()
    else:
        output = strategy.bet_or_pass_expert_strategy(**data)

    # check output
    assert output == (expected_action, expected_color, expected_value)

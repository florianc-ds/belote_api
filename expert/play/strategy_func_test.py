import json
import re

import pytest
import logging

from expert.play.strategy import play_expert_strategy

logger = logging.getLogger('flask.app')
GAME_CONFIGS_PATH = 'expert/play/game_configurations.json'
LEAF_LOG_PATTERN = r'^LEAF (.+)$'


def generate_test_cases():
    leaves = {}

    def get_leaves(current_path, json_object):
        for k, v in json_object.items():
            if '_id' in v.keys():
                leaves[f'{current_path}{k}'] = v
            else:
                get_leaves(f'{current_path}{k}-', v)

    with open(GAME_CONFIGS_PATH, 'rb') as json_file:
        game_configs = json.load(json_file)

    get_leaves('', game_configs)

    return leaves


test_cases = generate_test_cases()
real_test_cases = {tree_path: test_case for tree_path, test_case in test_cases.items() if tree_path != 'TEMPLATE'}


@pytest.mark.parametrize(
    '_id, data, expected, extras',
    [
        [
            test_case['_id'],
            {k: v for k, v in test_case.items() if not k.startswith('_')},
            test_case['_expected'],
            {k: v for k, v in test_case.items() if k.startswith('_')},
        ]
        for tree_path, test_case in sorted(real_test_cases.items(), key=lambda t: t[0])
    ],
    ids=sorted(real_test_cases.keys()),
)
def test_play_expert_strategy(_id, data, expected, extras, caplog):
    caplog.set_level(logging.INFO)

    # check output
    assert play_expert_strategy(**data) == expected

    # check log(s) correspond(s) to the usecase
    logs = caplog.record_tuples
    leaf_logs_message = [msg for (logger_instance, lvl, msg) in logs if re.match(LEAF_LOG_PATTERN, msg)]
    output_leaf_ids = [re.match(LEAF_LOG_PATTERN, log).group(1) for log in leaf_logs_message]
    expected_leaf_ids = [_id, extras['_final_leaf_id']] if '_final_leaf_id' in extras else [_id]
    assert output_leaf_ids == expected_leaf_ids

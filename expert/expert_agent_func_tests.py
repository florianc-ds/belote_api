import json
import re

import pytest
import logging

from expert.expert_agent import play_expert_strategy

logger = logging.getLogger('flask.app')
GAME_CONFIGS_PATH = 'expert/game_configurations.json'
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
    '_id, data, expected',
    [
        [test_case['_id'], {k: v for k, v in test_case.items() if not k.startswith('_')}, test_case['_expected']]
        for tree_path, test_case in sorted(real_test_cases.items(), key=lambda t: t[0])
    ],
    ids=sorted(real_test_cases.keys()),
)
def test_play_expert_strategy(_id, data, expected, caplog):
    caplog.set_level(logging.INFO)
    # check output
    assert play_expert_strategy(**data) == expected

    # check 1 log was outputted for a single leaf
    logs = caplog.record_tuples
    leaf_logs_message = [msg for (logger_instance, lvl, msg) in logs if re.match(LEAF_LOG_PATTERN, msg)]
    assert len(leaf_logs_message) == 1

    # check log corresponds to the usecase
    output_leaf_id = re.match(LEAF_LOG_PATTERN, leaf_logs_message[0]).group(1)
    assert output_leaf_id == _id

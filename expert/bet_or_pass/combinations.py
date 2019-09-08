MAIN_COMBINATIONS = [
    {
        'trigger': 'J+9',
        'bonus': [
            {
                'pattern': 'A/10/K/Q',
                'trump': True,
                'value': 10,
                'max': 30,
            },
            {
                'pattern': 'K+Q',
                'trump': True,
                'value': 10,
            },
            {
                'pattern': '8+7',
                'trump': True,
                'value': 10,
            },
            {
                'pattern': 'A',
                'trump': False,
                'value': {1: 10, 2: 10, 3: 20}
            },
            {
                'pattern': '10+A',
                'trump': False,
                'value': 10,
                'max': 10,
            },
        ],
    },
    {
        'trigger': 'J+A+8/7',
        'bonus': [
            {
                'pattern': '10/K/Q',
                'trump': True,
                'value': 10,
                'max': 20,
            },
            {
                'pattern': 'K+Q',
                'trump': True,
                'value': 10,
            },
            {
                'pattern': '7+8',
                'trump': True,
                'value': 10,
            },
            {
                'pattern': 'A',
                'trump': False,
                'value': {1: 10, 2: 10, 3: 20}
            },
            {
                'pattern': '10+A',
                'trump': False,
                'value': 10,
                'max': 10,
            },
        ]
    },
    {
        'trigger': 'J+10+K/Q',
        'bonus': [
            {
                'pattern': 'Q+K',
                'trump': True,
                'value': 20,
            },
            {
                'pattern': '7/8',
                'trump': True,
                'value': 10,
            },
            {
                'pattern': 'A',
                'trump': False,
                'value': {1: 10, 2: 10, 3: 20}
            },
        ]
    },
    {
        'trigger': 'J+10+8+7',
        'bonus': [
            {
                'pattern': 'A',
                'trump': False,
                'value': {1: 10, 2: 10, 3: 20}
            },
        ]
    },
    {
        'trigger': 'J+K+Q',
        'bonus': [
            {
                'pattern': '7/8',
                'trump': True,
                'value': 10,
            },
            {
                'pattern': 'A',
                'trump': False,
                'value': {1: 10, 2: 10, 3: 20}
            },
        ]
    },
    {
        'trigger': 'J+K/Q+8+7',
        'bonus': [
            {
                'pattern': 'Q+K',
                'trump': True,
                'value': 20,
            },
            {
                'pattern': 'A',
                'trump': False,
                'value': {1: 10, 2: 10, 3: 20}
            },
        ]
    },
    {
        'trigger': '9+A+10',
        'bonus': [
            {
                'pattern': 'K/Q',
                'trump': True,
                'value': {1: 10, 2: 30},
            },
            {
                'pattern': '7+8',
                'trump': True,
                'value': 10,
            },
            {
                'pattern': 'A',
                'trump': False,
                'value': {1: 10, 2: 10, 3: 20}
            },
        ]
    },
    {
        'trigger': '9+A+K/Q',
        'bonus': [
            {
                'pattern': 'Q+K',
                'trump': True,
                'value': 20,
            },
            {
                'pattern': '7+8',
                'trump': True,
                'value': 10,
            },
            {
                'pattern': 'A',
                'trump': False,
                'value': {1: 10, 2: 10, 3: 20}
            },
        ]
    },
    {
        'trigger': '9+A+8+7',
        'bonus': [
            {
                'pattern': 'A',
                'trump': False,
                'value': {1: 10, 2: 10, 3: 20}
            },
            {
                'pattern': '10+A',
                'trump': False,
                'value': 10,
                'max': 10,
            },
        ]
    },
    {
        'trigger': '9+10+8+7',
        'bonus': [
            {
                'pattern': 'A',
                'trump': False,
                'value': {1: 10, 2: 10, 3: 20}
            },
        ]
    },
    {
        'trigger': 'A+10+K/Q+8+7',
        'bonus': [
            {
                'pattern': 'Q+K',
                'trump': True,
                'value': 20,
            },
            {
                'pattern': 'A',
                'trump': False,
                'value': {1: 10, 2: 10, 3: 20}
            },
            {
                'pattern': '10+A',
                'trump': False,
                'value': 10,
                'max': 10,
            },
        ]
    },
    {
        'trigger': '10+K+Q+8+7',
        'bonus': [
            {
                'pattern': 'A',
                'trump': False,
                'value': 10,
                'max': 10,
            }
        ]
    },
]

SUPPORT_COMBINATIONS = [
    {
        'pattern': 'J',
        'trump': True,
        'value': 20,
    },
    {
        'pattern': '9',
        'trump': True,
        'value': 10,
    },
    {
        'pattern': 'Q+K',
        'trump': True,
        'value': 20,
    },
    {
        'pattern': 'A',
        'trump': False,
        'value': {2: 10, 3: 20},
    },
]

AGGRESSIVE_SUPPORT_COMBINATIONS = [
    {
        'pattern': 'J',
        'trump': True,
        'value': 20,
    },
    {
        'pattern': '9/10/A',
        'trump': True,
        'value': 10,
    },
    {
        'pattern': 'Q+K',
        'trump': True,
        'value': 20,
    },
    {
        'pattern': 'A',
        'trump': False,
        'value': 10,
    },
]

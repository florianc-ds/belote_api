import json
import random
import logging
from datetime import timedelta
from functools import update_wrapper

from flask import Flask
from flask import make_response, request, current_app
import numpy as np

from helpers.constants import TRUMP_POINTS, PLAIN_POINTS, COLORS
from helpers.common_helpers import extract_color, extract_value

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# RANDOM AGENT CONSTANTS
RANDOM_BET_PROBABILITY = 0.5
RANDOM_COLOR_WEIGHTS = [1, 1, 1, 1]
RANDOM_VALUE_NORMAL_MU = 0.
RANDOM_VALUE_NORMAL_GAMMA = 2.3


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, str):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, str):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


################
# PLAY HELPERS #
################

def play_template(data, used_fields, strategy):
    app.logger.info(f'data: {data}')
    # data contains:
    # - player
    # - trumpColor
    # - playerCards
    # - cardsPlayability
    # - roundCards
    # - roundColor
    # - gameHistory
    # - contract
    # - contractTeam
    # - globalScore
    player = data['player']
    used_info = [data[field] for field in used_fields]
    card = strategy(*used_info)

    app.logger.info(f'Returning {card} for player {player}')
    return {'card': card}


def derive_playable_cards(player_cards, cards_playability):
    return [card for (i, card) in enumerate(player_cards) if cards_playability[i]]


#######################
# RANDOM PLAY HELPERS #
#######################

def play_random_strategy(player_cards, cards_playability):
    playable_cards = derive_playable_cards(player_cards, cards_playability)
    card = random.choice(playable_cards)
    return card


#############################
# HIGHEST CARD PLAY HELPERS #
#############################

def highest_card_sorting_key(card, trump_color):
    value = extract_value(card)
    color = extract_color(card)
    if color == trump_color:
        return TRUMP_POINTS[value]
    else:
        return PLAIN_POINTS[value]


def play_highest_card_strategy(player_cards, cards_playability, trump_color):
    playable_cards = derive_playable_cards(player_cards, cards_playability)
    card = sorted(
        playable_cards,
        key=lambda x: highest_card_sorting_key(x, trump_color),
        reverse=True
    )[0]
    return card


#######################
# BET OR PASS HELPERS #
#######################

def bet_or_pass_template(data, used_fields, strategy):
    app.logger.info(f'data: {data}')
    # data contains:
    # - player
    # - playerCards
    # - playersBids
    # - auctionPassedTurnInRow
    # - globalScore
    # - gameFirstPlayer
    player = data['player']
    used_info = [data[field] for field in used_fields]
    action, color, value = strategy(*used_info)

    response = {'action': action}
    if action == 'pass':
        app.logger.info(f'{player} decides to {action}')
    elif action == 'bet':
        app.logger.info(f'{player} decides to {action} {value} on {color}')
        response['value'] = value
        response['color'] = color

    return response


def derive_currently_highest_bid_value(players_bids):
    placed_bid_values = [bid['value'] for bid in players_bids.values() if bid['value']]
    currently_highest_bid_value = max(placed_bid_values) if placed_bid_values else None
    return currently_highest_bid_value


##############################
# RANDOM BET OR PASS HELPERS #
##############################

def bet_or_pass_random_strategy(players_bids):
    if random.random() < RANDOM_BET_PROBABILITY:
        action = 'bet'
        color = random.choices(population=COLORS, weights=RANDOM_COLOR_WEIGHTS, k=1)[0]
        value = 80 + 10 * round(abs(np.random.normal(loc=RANDOM_VALUE_NORMAL_MU, scale=RANDOM_VALUE_NORMAL_GAMMA)))
        currently_highest_bid_value = derive_currently_highest_bid_value(players_bids)
        if currently_highest_bid_value and (value <= currently_highest_bid_value):
            action = 'pass'
    else:
        action = 'pass'
        color = None
        value = None

    return action, color, value


##########
# ROUTES #
##########

@app.route('/')
def hello():
    return "Hello World!!!"


@app.route('/random/play', methods=['OPTIONS', 'POST'])
@crossdomain(origin='*')
def play_random():
    if request.method == 'POST':
        app.logger.info('POST /random/play')
        data = json.loads(request.data)
        response = play_template(
            data=data,
            used_fields=['playerCards', 'cardsPlayability'],
            strategy=play_random_strategy
        )

        return json.dumps(response)


@app.route('/highest_card/play', methods=['OPTIONS', 'POST'])
@crossdomain(origin='*')
def play_highest_card():
    if request.method == 'POST':
        app.logger.info('POST /highest_card/play')
        data = json.loads(request.data)
        response = play_template(
            data=data,
            used_fields=['playerCards', 'cardsPlayability', 'trumpColor'],
            strategy=play_highest_card_strategy
        )

        return json.dumps(response)


@app.route('/expert/play', methods=['OPTIONS', 'POST'])
@crossdomain(origin='*')
def play_expert():
    if request.method == 'POST':
        app.logger.info('POST /expert/play')
        data = json.loads(request.data)
        response = play_template(
            data=data,
            used_fields=['playerCards', 'cardsPlayability'],
            strategy=play_random_strategy
        )

        return json.dumps(response)


@app.route('/reinforcement/play', methods=['OPTIONS', 'POST'])
@crossdomain(origin='*')
def play_reinforcement():
    if request.method == 'POST':
        app.logger.info('POST /reinforcement/play')
        data = json.loads(request.data)
        response = play_template(
            data=data,
            used_fields=['playerCards', 'cardsPlayability'],
            strategy=play_random_strategy
        )

        return json.dumps(response)


@app.route('/random/bet_or_pass', methods=['OPTIONS', 'POST'])
@crossdomain(origin='*')
def bet_or_pass_random():
    if request.method == 'POST':
        app.logger.info('POST /random/bet_or_pass')
        data = json.loads(request.data)
        response = bet_or_pass_template(
            data=data,
            used_fields=['playersBids'],
            strategy=bet_or_pass_random_strategy
        )

        return json.dumps(response)


if __name__ == '__main__':
    app.run()

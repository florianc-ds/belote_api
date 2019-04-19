import json
import logging
from datetime import timedelta
from functools import update_wrapper

from flask import Flask
from flask import make_response, request, current_app

from helpers.bet_or_pass_helpers import bet_or_pass_template
from helpers.play_helpers import play_template
from highest_card_agent import play_highest_card_strategy
from random_agent import play_random_strategy, bet_or_pass_random_strategy

app = Flask(__name__)
app.logger.setLevel(logging.INFO)


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
            strategy=play_random_strategy,
            logger=app.logger,
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
            strategy=play_highest_card_strategy,
            logger=app.logger,
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
            strategy=play_random_strategy,
            logger=app.logger,
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
            strategy=play_random_strategy,
            logger=app.logger,
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
            strategy=bet_or_pass_random_strategy,
            logger=app.logger,
        )

        return json.dumps(response)


if __name__ == '__main__':
    app.run()

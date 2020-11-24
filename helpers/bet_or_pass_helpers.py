import logging

from helpers.common_helpers import decrypt_cards

logger = logging.getLogger('flask.app')


def bet_or_pass_template(data, used_fields, strategy):
    logger.info(f'data: {data}')
    # data contains:
    # - player
    # - playerCards
    # - playersBids
    # - auctionPassedTurnInRow
    # - globalScore
    # - gameFirstPlayer
    # - encrypted
    player = data['player']
    used_info = [data[field] for field in used_fields]
    if data['encrypted'] and ('playerCards' in used_fields):
        used_info[used_fields.index('playerCards')] = decrypt_cards(cards=data['playerCards'], player=player)
    action, color, value = strategy(*used_info)

    response = {'action': action}
    if action == 'pass':
        logger.info(f'{player} decides to {action}')
    elif action == 'bet':
        logger.info(f'{player} decides to {action} {value} on {color}')
        response['value'] = value
        response['color'] = color

    return response


def derive_currently_highest_bid_value(players_bids):
    placed_bid_values = [bid['value'] for bid in players_bids.values() if bid['value']]
    currently_highest_bid_value = max(placed_bid_values) if placed_bid_values else None
    return currently_highest_bid_value

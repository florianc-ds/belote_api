import logging

logger = logging.getLogger('flask.app')


def play_template(data, used_fields, strategy):
    logger.info(f'data: {data}')
    # data contains:
    # - player
    # - trumpColor
    # - playerCards
    # - cardsPlayability
    # - roundCards
    # - roundColor
    # - gameHistory
    # - roundsFirstPlayer
    # - contract
    # - contractTeam
    # - globalScore
    player = data['player']
    used_info = [data[field] for field in used_fields]
    card = strategy(*used_info)

    logger.info(f'Returning {card} for player {player}')
    return {'card': card}


def derive_playable_cards(player_cards, cards_playability):
    return [card for (i, card) in enumerate(player_cards) if cards_playability[i]]

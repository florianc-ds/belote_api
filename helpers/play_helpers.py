import logging

from helpers.common_helpers import decrypt_cards

logger = logging.getLogger('flask.app')


def play_template(data, used_fields, strategy):
    logger.info(f'data: {data}')
    # data contains:
    # - player
    # - trumpColor
    # - playerCards
    # - cardsPlayability
    # - round
    # - roundCards
    # - roundColor
    # - gameHistory
    # - roundsFirstPlayer
    # - contract
    # - contractTeam
    # - globalScore
    # - encrypted
    player = data['player']
    used_info = [data[field] for field in used_fields]
    if data['encrypted'] and ('playerCards' in used_fields):
        used_info[used_fields.index('playerCards')] = decrypt_cards(cards=data['playerCards'], player=player)
    card = strategy(*used_info)

    logger.info(f'Returning {card} for player {player}')
    return {'card': card}


def derive_playable_cards(player_cards, cards_playability):
    return [card for (i, card) in enumerate(player_cards) if cards_playability[i]]

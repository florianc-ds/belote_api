from datetime import datetime
from time import time

import pandas as pd

from helpers.common_helpers import extract_color, extract_value
from random_agent import bet_or_pass_random_strategy, play_random_strategy
from reinforcement.models import Game, Player, NEXT_PLAYER, PLAYER_TO_TEAM, derive_leader, Card, COLOR_TO_SYMBOL

CONFIG_COLUMNS = ['experiment_id', 'nb_games', 'west_agent', 'south_agent', 'east_agent', 'north_agent']
AUCTIONS_COLUMNS = [
    'experiment_id', 'game_id', 'round_id', 'player', 'action_code', 'action', 'color', 'value', 'cards'
]
TRICKS_COLUMNS = [
    'experiment_id', 'game_id', 'round_id', 'trick_id', 'player', 'trick_position', 'action_code',
    'card',
    'is_last_in_trick', 'trick_winner', 'trick_points',
    'is_last_in_round', 'contract_reached', 'contract', 'east/west_points', 'north/south_points',
    'is_last_in_game', 'game_winners', 'east/west_score', 'north/south_score',
]
GAME_LIMIT = 3000
TOTAL_POINTS = 162


def main():
    config_df = pd.DataFrame(columns=CONFIG_COLUMNS)
    auctions_df = pd.DataFrame(columns=AUCTIONS_COLUMNS)
    tricks_df = pd.DataFrame(columns=TRICKS_COLUMNS)
    first_player = Player.ONE
    agents = {
        'west_agent': 'RANDOM',
        'south_agent': 'RANDOM',
        'east_agent': 'RANDOM',
        'north_agent': 'RANDOM',
    }
    experiment_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    nb_games = 2
    config_df = config_df.append({"experiment_id": experiment_id, "nb_games": nb_games, **agents}, ignore_index=True)

    for game_id in range(nb_games):  # loop over games
        game = Game(first_player=first_player)
        game_description = game.describe()
        player = first_player
        round_id = 0
        while max(game_description['score'].values()) < GAME_LIMIT:  # loop over rounds
            while game_description['state'] == 'auction':  # auction step
                agent_action, color, value = bet_or_pass_random_strategy(
                    players_bids={
                        player: bid
                        if bid is not None else {'value': None, 'color': None}
                        for player, bid in game_description['auction']['bids'].items()
                    }
                )
                action = {'player': player, 'passed': agent_action == 'pass', 'color': color, 'value': value}
                action_code = game.update(**action)
                game_description = game.describe()
                auctions_df = auctions_df.append(
                    {
                        'experiment_id': experiment_id,
                        'game_id': game_id,
                        'round_id': round_id,
                        'player': player.value,
                        'action_code': action_code,
                        'action': agent_action,
                        'color': color,
                        'value': value,
                        'cards': game_description['round']['hands'][player.value]['cards']
                    },
                    ignore_index=True
                )
                player = NEXT_PLAYER[player]
            while game_description['state'] == 'playing':  # tricks step
                trick_id = game_description['round']['trick']
                player = Player._value2member_map_[game_description['round']['trick_opener']]
                start_round_score = game_description['round']['score'].copy()
                start_score = game_description['score'].copy()
                contractor = game_description['auction']['current_best']
                contract = game_description['auction']['bids'][contractor]['value']
                trick_cards = {}
                trump_color = None
                trick_color = None
                belote_cards_players = []
                trick_row = {}
                for trick_position in range(4):  # loop over players
                    player_cards = [
                        card.describe().replace(COLOR_TO_SYMBOL[card.color], card.color)
                        for card in game.round.hands[player].cards
                    ]
                    agent_card = play_random_strategy(
                        player_cards=player_cards,
                        cards_playability=game.round.get_cards_playability(player)
                    )
                    trick_cards = game.round.trick_cards.cards.copy()
                    trick_cards.update({player: Card(value=extract_value(agent_card), color=extract_color(agent_card))})
                    trump_color = game_description['round']['trump']
                    trick_color = extract_color(agent_card)
                    belote_cards_players = game_description['round']['belote']
                    if len(belote_cards_players) != 2:
                        belote_cards_players.append(player.value)
                    action = {'player': player, 'card_index': player_cards.index(agent_card)}
                    action_code = game.update(**action)
                    game_description = game.describe()
                    trick_row = {
                        'experiment_id': experiment_id,
                        'game_id': game_id,
                        'round_id': round_id,
                        'trick_id': trick_id,
                        'player': player.value,
                        'trick_position': trick_position,
                        'action_code': action_code,
                        'card': agent_card,
                        'is_last_in_trick': False,
                        'is_last_in_round': False,
                        'is_last_in_game': False,
                    }
                    if trick_position != 3:
                        tricks_df = tricks_df.append(trick_row, ignore_index=True)
                    player = NEXT_PLAYER[player]
                trick_winner = derive_leader(cards=trick_cards, trump_color=trump_color, trick_color=trick_color)
                if trick_id < 7:
                    trick_winner_team = PLAYER_TO_TEAM[trick_winner]
                    trick_row.update(
                        {
                            'is_last_in_trick': True,
                            'trick_winner': trick_winner.value,
                            'trick_points': game_description['round']['score'][trick_winner_team.value] - start_round_score[trick_winner_team.value],
                        }
                    )
                else:
                    trick_points = TOTAL_POINTS - sum(start_round_score.values())
                    contract_team = PLAYER_TO_TEAM[Player._value2member_map_[contractor]]
                    contract_team_points = (
                            start_round_score[contract_team.value]
                            + (trick_points if trick_winner.value in contract_team.value else 0)
                            + (20 if (len(set(belote_cards_players)) == 1 and belote_cards_players[0] in contract_team.value)
                               else 0)
                    )
                    contract_reached = contract_team_points >= contract
                    trick_row.update(
                        {
                            'is_last_in_trick': True,
                            'trick_winner': trick_winner.value,
                            'trick_points': trick_points,
                            'is_last_in_round': True,
                            'contract_reached': contract_reached,
                            'contract': contract,
                            'east/west_points': game_description['score']['east/west'] - start_score['east/west'],
                            'north/south_points': game_description['score']['north/south'] - start_score['north/south'],
                        }
                    )
                    if max(game_description['score'].values()) >= GAME_LIMIT:
                        trick_row.update(
                            {
                                'is_last_in_game': True,
                                'game_winners': 'east/west' if game_description['score']['east/west'] > game_description['score']['north/south'] else 'north_south',
                                'east/west_score': game_description['score']['east/west'],
                                'north/south_score': game_description['score']['north/south'],
                            }
                        )
                tricks_df = tricks_df.append(trick_row, ignore_index=True)
            round_id += 1
    config_df.to_csv('./data/config_data.csv', sep=';')
    auctions_df.to_csv('./data/auctions_data.csv', sep=';')
    tricks_df.to_csv('./data/tricks_data.csv', sep=';')


if __name__ == "__main__":
    # TODO 1: DEBUG
    # TODO 2: Implement for other agents: highest_card & expert
    # TODO 3: refacto main() into multiple methods
    start_time = time()
    main()
    print(f'elapsed time: {time()-start_time} sec')

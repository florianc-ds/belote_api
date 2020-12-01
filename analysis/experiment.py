import os
from datetime import datetime
from time import time
from typing import Dict, Tuple, List, Optional

import pandas as pd

from helpers.common_helpers import extract_color, extract_value
from highest_card_agent import bet_or_pass_highest_card_strategy, play_highest_card_strategy
from random_agent import bet_or_pass_random_strategy, play_random_strategy
from reinforcement.models import Game, Player, NEXT_PLAYER, PLAYER_TO_TEAM, derive_leader, Card

CONFIG_COLUMNS = ['experiment_id', 'nb_games', 'west_agent', 'south_agent', 'east_agent', 'north_agent']
AUCTIONS_COLUMNS = [
    'experiment_id', 'game_id', 'round_id', 'player', 'action_code', 'action', 'color', 'value', 'cards'
]
TRICKS_COLUMNS = [
    'experiment_id', 'game_id', 'round_id', 'trick_id', 'player', 'trick_position', 'action_code',
    'card',
    'is_last_in_trick', 'trick_winner', 'trick_points',
    'is_last_in_round', 'east/west_points', 'north/south_points', 'belote_team', 'contract', 'contract_reached',
    'east/west_round_score', 'north/south_round_score',
    'is_last_in_game', 'game_winners', 'east/west_score', 'north/south_score',
]
GAME_LIMIT = 3000
TOTAL_POINTS = 162


def get_agent_bet_or_pass(
    agent: str, players_bids: Dict[str, Dict], player_cards: List[str]
) -> Tuple[str, Optional[str], Optional[int]]:
    if agent == 'RANDOM':
        return bet_or_pass_random_strategy(players_bids=players_bids)
    elif agent == 'HIGHEST_CARD':
        return bet_or_pass_highest_card_strategy(player_cards=player_cards, players_bids=players_bids)


def get_agent_play(
    agent: str, player_cards: List[str], cards_playability: List[bool], trump_color: str
) -> str:
    if agent == 'RANDOM':
        return play_random_strategy(player_cards=player_cards, cards_playability=cards_playability)
    elif agent == 'HIGHEST_CARD':
        return play_highest_card_strategy(
            player_cards=player_cards, cards_playability=cards_playability, trump_color=trump_color
        )


def handle_auction_step(
        game: Game, game_description: Dict, player: Player, agent: str,
        experiment_id: str, game_id: int, round_id: int, auctions_df: pd.DataFrame
) -> Tuple[Dict, Player, pd.DataFrame]:
    players_bids = {
        player_: bid
        if bid is not None else {'value': None, 'color': None}
        for player_, bid in game_description['auction']['bids'].items()
    }
    player_cards = [card.describe_plain() for card in game.round.hands[player].cards]
    agent_action, color, value = get_agent_bet_or_pass(
        agent=agent, players_bids=players_bids, player_cards=player_cards
    )
    action = {'player': player, 'passed': (agent_action == 'pass'), 'color': color, 'value': value}
    action_code = game.update(**action)
    new_game_description = game.describe()
    new_auctions_df = auctions_df.append(
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
    new_player = NEXT_PLAYER[player]

    return new_game_description, new_player, new_auctions_df


def handle_end_of_trick(
        game_description: Dict, player: Player, trick_cards: Dict[Player, Card],
        start_round_score: Dict[str, int], start_score: Dict[str, int], belote_cards_players: List[str],
        contractor: Player, contract: int,
        trump_color: str, trick_color: str, trick_id: int
) -> Dict:
    trick_winner = derive_leader(cards=trick_cards, trump_color=trump_color, trick_color=trick_color)
    trick_winner_team = PLAYER_TO_TEAM[trick_winner]
    if trick_id < 7:
        trick_row_update = {
            'is_last_in_trick': True,
            'trick_winner': trick_winner.value,
            'trick_points': game_description['round']['score'][trick_winner_team.value] - start_round_score[
                trick_winner_team.value],
        }
    else:
        if len(belote_cards_players) != 2:  # state of belote cards are only up-to-date with the penultimate step
            belote_cards_players.append(player.value)
        belote_team = None
        if len(set(belote_cards_players)) == 1:
            belote_team = PLAYER_TO_TEAM[Player._value2member_map_[belote_cards_players[0]]]
        trick_points = TOTAL_POINTS - sum(start_round_score.values())
        round_points = {
            'east/west': start_round_score['east/west'],
            'north/south': start_round_score['north/south'],
        }
        round_points[trick_winner_team.value] += trick_points
        if belote_team is not None:
            round_points[belote_team.value] += 20
        contract_team = PLAYER_TO_TEAM[contractor]
        contract_reached = round_points[contract_team.value] >= contract
        trick_row_update = {
            'is_last_in_trick': True,
            'trick_winner': trick_winner.value,
            'trick_points': trick_points,
            'is_last_in_round': True,
            'east/west_points': round_points['east/west'],
            'north/south_points': round_points['north/south'],
            'belote_team': belote_team.value if belote_team is not None else None,
            'contract': contract,
            'contract_reached': contract_reached,
            'east/west_round_score': game_description['score']['east/west'] - start_score['east/west'],
            'north/south_round_score': game_description['score']['north/south'] - start_score['north/south'],
        }
        if max(game_description['score'].values()) >= GAME_LIMIT:
            trick_row_update.update(
                {
                    'is_last_in_game': True,
                    'game_winners': 'east/west' if (game_description['score']['east/west']
                                                    > game_description['score']['north/south']) else 'north/south',
                    'east/west_score': game_description['score']['east/west'],
                    'north/south_score': game_description['score']['north/south'],
                }
            )
    return trick_row_update


def handle_trick(
        game: Game, game_description: Dict, agent: str,
        experiment_id: str, game_id: int, round_id: int, tricks_df: pd.DataFrame
):
    trick_id = game_description['round']['trick']
    player = Player._value2member_map_[game_description['round']['trick_opener']]
    start_round_score = game_description['round']['score'].copy()
    start_score = game_description['score'].copy()
    contractor = game.auction.current_best
    contract = game.auction.bids[contractor].value
    new_game_description = game_description.copy()
    new_tricks_df = tricks_df
    trick_cards = {}
    trump_color = None
    trick_color = None
    belote_cards_players = []
    trick_row = {}
    for trick_position in range(4):  # loop over players
        player_cards = [card.describe_plain() for card in game.round.hands[player].cards]
        cards_playability = game.round.get_cards_playability(player)
        current_trump_color = game_description['round']['trump']
        agent_card = get_agent_play(
            agent=agent, player_cards=player_cards, cards_playability=cards_playability, trump_color=current_trump_color
        )
        trick_cards = game.round.trick_cards.cards.copy()
        trick_cards.update({player: Card(value=extract_value(agent_card), color=extract_color(agent_card))})
        trump_color = new_game_description['round']['trump']
        trick_opener = game.round.trick_opener
        trick_color = trick_cards[trick_opener].color
        belote_cards_players = new_game_description['round']['belote']
        action = {'player': player, 'card_index': player_cards.index(agent_card)}
        action_code = game.update(**action)
        new_game_description = game.describe()
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
            new_tricks_df = new_tricks_df.append(trick_row, ignore_index=True)
        player = NEXT_PLAYER[player]
    trick_row_update = handle_end_of_trick(
        game_description=new_game_description, player=player, trick_cards=trick_cards,
        start_round_score=start_round_score, start_score=start_score, belote_cards_players=belote_cards_players,
        contractor=contractor, contract=contract,
        trump_color=trump_color, trick_color=trick_color, trick_id=trick_id
    )
    trick_row.update(trick_row_update)
    new_tricks_df = new_tricks_df.append(trick_row, ignore_index=True)

    return new_game_description, new_tricks_df


def prepare_data_folder(agent_A, agent_B, config_df, auctions_df, tricks_df):
    def create_csv_if_not_exist(file_path, df):
        if not os.path.exists(file_path):
            df.to_csv(file_path, sep=';', header=True)
    output_dir = f'./data/{agent_A}-vs-{agent_B}'
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    config_path = os.path.join(output_dir, 'config_data.csv')
    auctions_path = os.path.join(output_dir, 'auctions_data.csv')
    tricks_path = os.path.join(output_dir, 'tricks_data.csv')
    create_csv_if_not_exist(config_path, config_df)
    create_csv_if_not_exist(auctions_path, auctions_df)
    create_csv_if_not_exist(tricks_path, tricks_df)

    return config_path, auctions_path, tricks_path


def run_experiment(east_west_agents, north_south_agents, nb_games):
    experiment_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    agents = {
        'west_agent': east_west_agents,
        'south_agent': north_south_agents,
        'east_agent': east_west_agents,
        'north_agent': north_south_agents,
    }

    config_df = pd.DataFrame(columns=CONFIG_COLUMNS)
    auctions_df = pd.DataFrame(columns=AUCTIONS_COLUMNS)
    tricks_df = pd.DataFrame(columns=TRICKS_COLUMNS)
    config_path, auctions_path, tricks_path = prepare_data_folder(
        agent_A=east_west_agents, agent_B=north_south_agents,
        config_df=config_df, auctions_df=auctions_df, tricks_df=tricks_df
    )
    config_df = config_df.append({"experiment_id": experiment_id, "nb_games": nb_games, **agents}, ignore_index=True)

    first_player = Player.ONE
    for game_id in range(nb_games):  # loop over games
        game = Game(first_player=first_player)
        game_description = game.describe()
        player = first_player
        round_id = 0
        while max(game_description['score'].values()) < GAME_LIMIT:  # loop over rounds
            while game_description['state'] == 'auction':  # auction steps
                game_description, player, auctions_df = handle_auction_step(
                    game=game, game_description=game_description, player=player, agent=agents[f'{player.value}_agent'],
                    experiment_id=experiment_id, game_id=game_id, round_id=round_id, auctions_df=auctions_df
                )
            while game_description['state'] == 'playing':  # tricks steps
                game_description, tricks_df = handle_trick(
                    game=game, game_description=game_description, agent=agents[f'{player.value}_agent'],
                    experiment_id=experiment_id, game_id=game_id, round_id=round_id, tricks_df=tricks_df
                )
            round_id += 1

    config_df.to_csv(config_path, sep=';', mode='a', header=False)
    auctions_df.to_csv(auctions_path, sep=';', mode='a', header=False)
    tricks_df.to_csv(tricks_path, sep=';', mode='a', header=False)


if __name__ == "__main__":
    # TODO: Implement for other agents: highest_card & expert
    start_time = time()
    run_experiment(east_west_agents='RANDOM', north_south_agents='HIGHEST_CARD', nb_games=2)
    print(f'elapsed time: {time()-start_time} sec')

# RELATIVE MATRIX
#
# |       |AGENT A|AGENT B|AGENT C|
# |AGENT A|f(A, A)|f(A, B)|f(A, C)|
# |AGENT B|f(B, A)|f(B, B)|f(B, C)|
# |AGENT C|f(C, A)|f(C, B)|f(C, C)|

# f(x, y) = % of games won by x against y
#           % of rounds won by x against y
#           % of tricks won by x against y
#           % of contracted round by x
#           % of contracted and won round by x
#           average game score for x
#           average contract for x
#           average positive margin (diff between contract and score when won) for x
#           average negative margin (diff between contract and score when lost) for x
import os

import pandas as pd

PLAYER_TO_TEAM = {'east': 'east/west', 'west': 'east/west', 'north': 'north/south', 'south': 'north/south'}


def compute_pc_games_won(tricks_df: pd.DataFrame, team: str) -> float:
    nb_games = len(pd.unique(tricks_df['experiment_id'] + '-' + tricks_df['game_id'].astype(str)))
    nb_won_games = tricks_df[tricks_df['game_winners'] == team].shape[0]
    return nb_won_games / nb_games


def compute_pc_rounds_won(tricks_df: pd.DataFrame, auctions_df: pd.DataFrame, team: str) -> float:
    nb_rounds = len(
        pd.unique(
            tricks_df['experiment_id']
            + '-' + tricks_df['game_id'].astype(str)
            + '-' + tricks_df['round_id'].astype(str)
        )
    )
    round_end_df = tricks_df[tricks_df['is_last_in_round']]
    contractor_df = auctions_df[auctions_df['action'] == 'bet'].drop_duplicates(
        ['experiment_id', 'game_id', 'round_id'], keep='last'
    )[['experiment_id', 'game_id', 'round_id', 'player']]
    contractor_df = contractor_df.rename(
        columns={'experiment_id': 'experiment_id_', 'game_id': 'game_id_', 'round_id': 'round_id_', 'player': 'player_'}
    )
    round_end_with_contract_df = round_end_df.merge(
        right=contractor_df,
        how='inner',
        left_on=['experiment_id', 'game_id', 'round_id'],
        right_on=['experiment_id_', 'game_id_', 'round_id_']
    )

    def round_won(row, team):
        if row['contract_reached']:
            return PLAYER_TO_TEAM[row['player_']] == team
        else:
            return PLAYER_TO_TEAM[row['player_']] != team
    nb_won_rounds = round_end_with_contract_df[
        round_end_with_contract_df.apply(lambda row: round_won(row, team), axis=1)
    ].shape[0]

    return nb_won_rounds / nb_rounds


def compute_pc_tricks_won(tricks_df: pd.DataFrame, team: str) -> float:
    nb_tricks = len(
        pd.unique(
            tricks_df['experiment_id']
            + '-' + tricks_df['game_id'].astype(str)
            + '-' + tricks_df['round_id'].astype(str)
            + '-' + tricks_df['trick_id'].astype(str)
        )
    )
    trick_end_df = tricks_df[tricks_df['is_last_in_trick']]
    nb_won_tricks = trick_end_df[
        trick_end_df.apply(lambda row: PLAYER_TO_TEAM[row['trick_winner']] == team, axis=1)
    ].shape[0]

    return nb_won_tricks / nb_tricks


def compute_pc_contracted_rounds(auctions_df: pd.DataFrame, team: str) -> float:
    nb_rounds = len(
        pd.unique(
            auctions_df['experiment_id']
            + '-' + auctions_df['game_id'].astype(str)
            + '-' + auctions_df['round_id'].astype(str)
        )
    )
    contractor_df = auctions_df[auctions_df['action'] == 'bet'].drop_duplicates(
        ['experiment_id', 'game_id', 'round_id'], keep='last'
    )
    nb_contracted_rounds = contractor_df[
        contractor_df.apply(lambda row: PLAYER_TO_TEAM[row['player']] == team, axis=1)
    ].shape[0]

    return nb_contracted_rounds / nb_rounds


def compute_pc_contracted_rounds_won(tricks_df: pd.DataFrame, auctions_df: pd.DataFrame, team: str) -> float:
    contractor_df = auctions_df[auctions_df['action'] == 'bet'].drop_duplicates(
        ['experiment_id', 'game_id', 'round_id'], keep='last'
    )[['experiment_id', 'game_id', 'round_id', 'player']]
    contracted_df = contractor_df[
        contractor_df.apply(lambda row: PLAYER_TO_TEAM[row['player']] == team, axis=1)
    ]
    nb_contracted_rounds = contracted_df.shape[0]

    round_end_df = tricks_df[tricks_df['is_last_in_round']]
    contracted_df = contracted_df.rename(
        columns={'experiment_id': 'experiment_id_', 'game_id': 'game_id_', 'round_id': 'round_id_', 'player': 'player_'}
    )
    round_end_with_contracted_df = round_end_df.merge(
        right=contracted_df,
        how='inner',
        left_on=['experiment_id', 'game_id', 'round_id'],
        right_on=['experiment_id_', 'game_id_', 'round_id_']
    )
    nb_contracted_rounds_won = round_end_with_contracted_df[round_end_with_contracted_df['contract_reached']].shape[0]

    return nb_contracted_rounds_won / nb_contracted_rounds


def compute_avg_game_score(tricks_df: pd.DataFrame, team: str) -> float:
    return tricks_df[tricks_df['is_last_in_game']][f'{team}_score'].mean()


def compute_avg_contract(auctions_df: pd.DataFrame, team: str) -> float:
    contractor_df = auctions_df[auctions_df['action'] == 'bet'].drop_duplicates(
        ['experiment_id', 'game_id', 'round_id'], keep='last'
    )
    contracted_df = contractor_df[
        contractor_df.apply(lambda row: PLAYER_TO_TEAM[row['player']] == team, axis=1)
    ]
    return contracted_df['value'].mean()


# TODO: need to compute sum(trick_points) + access to belote => points
# def compute_avg_positive_margin(auctions_df: pd.DataFrame, tricks_df: pd.DataFrame, team: str) -> float:
#     contractor_df = auctions_df[auctions_df['action'] == 'bet'].drop_duplicates(
#         ['experiment_id', 'game_id', 'round_id'], keep='last'
#     )
#     contracted_df = contractor_df[
#         contractor_df.apply(lambda row: PLAYER_TO_TEAM[row['player']] == team, axis=1)
#     ][['experiment_id', 'game_id', 'round_id', 'player']]
#     contracted_df = contracted_df.rename(
#         columns={'experiment_id': 'experiment_id_', 'game_id': 'game_id_', 'round_id': 'round_id_', 'player': 'player_'}
#     )
#     succeeded_round_end_df = tricks_df[tricks_df['is_last_in_round'] & tricks_df['contract_reached']]
#     succeeded_round_end_with_contracted_df = succeeded_round_end_df.merge(
#         right=contracted_df,
#         how='inner',
#         left_on=['experiment_id', 'game_id', 'round_id'],
#         right_on=['experiment_id_', 'game_id_', 'round_id_']
#     )
#
#     return succeeded_round_end_with_contracted_df.apply(
#         lambda row: row[f'{team}_points'] - 2 * row['contract'], axis=1
#     ).mean()

# TODO: need to compute sum(trick_points) + access to belote => points
# TODO: investigate why sometimes have failed_round_end_with_contracted_df['contract_reached'] False + points earned (more than just belote...)
# def compute_avg_negative_margin(df: pd.DataFrame, team: str) -> float:
#     contractor_df = auctions_df[auctions_df['action'] == 'bet'].drop_duplicates(
#         ['experiment_id', 'game_id', 'round_id'], keep='last'
#     )
#     contracted_df = contractor_df[
#         contractor_df.apply(lambda row: PLAYER_TO_TEAM[row['player']] == team, axis=1)
#     ][['experiment_id', 'game_id', 'round_id', 'player']]
#     contracted_df = contracted_df.rename(
#         columns={'experiment_id': 'experiment_id_', 'game_id': 'game_id_', 'round_id': 'round_id_', 'player': 'player_'}
#     )
#     round_end_df = tricks_df[tricks_df['is_last_in_round']]
#     failed_round_end_df = round_end_df[~round_end_df['contract_reached'].astype(bool)]
#     failed_round_end_with_contracted_df = failed_round_end_df.merge(
#         right=contracted_df,
#         how='inner',
#         left_on=['experiment_id', 'game_id', 'round_id'],
#         right_on=['experiment_id_', 'game_id_', 'round_id_']
#     )
#
#     return failed_round_end_with_contracted_df.apply(
#         lambda row: -9999, axis=1
#     ).mean()


if __name__ == '__main__':
    agent_A = "RANDOM"
    agent_B = "RANDOM"
    team = 'east/west'

    path_to_dir = f'./data/{agent_A}-vs-{agent_B}'
    tricks_df = pd.read_csv(os.path.join(path_to_dir, 'tricks_data.csv'), sep=';', header='infer')
    auctions_df = pd.read_csv(os.path.join(path_to_dir, 'auctions_data.csv'), sep=';', header='infer')

    pc_games_won = compute_pc_games_won(tricks_df=tricks_df, team=team)
    print(f'pc_games_won: {pc_games_won}')
    pc_rounds_won = compute_pc_rounds_won(tricks_df=tricks_df, auctions_df=auctions_df, team=team)
    print(f'pc_rounds_won: {pc_rounds_won}')
    pc_tricks_won = compute_pc_tricks_won(tricks_df=tricks_df, team=team)
    print(f'pc_tricks_won: {pc_tricks_won}')
    pc_contracted_rounds = compute_pc_contracted_rounds(auctions_df=auctions_df, team=team)
    print(f'pc_contracted_rounds: {pc_contracted_rounds}')
    pc_contracted_rounds_won = compute_pc_contracted_rounds_won(tricks_df=tricks_df, auctions_df=auctions_df, team=team)
    print(f'pc_contracted_rounds_won: {pc_contracted_rounds_won}')
    avg_game_score = compute_avg_game_score(tricks_df=tricks_df, team=team)
    print(f'avg_game_score: {avg_game_score}')
    avg_contract = compute_avg_contract(auctions_df=auctions_df, team=team)
    print(f'avg_contract: {avg_contract}')
    # avg_positive_margin = compute_avg_positive_margin(tricks_df=tricks_df, auctions_df=auctions_df, team=team)
    # print(f'avg_positive_margin: {avg_positive_margin}')
    # avg_negative_margin = compute_avg_negative_margin(tricks_df=tricks_df, auctions_df=auctions_df, team=team)
    # print(f'avg_negative_margin: {avg_negative_margin}')


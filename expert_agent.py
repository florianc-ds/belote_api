from helpers.play_helpers import derive_playable_cards


########
# PLAY #
########

def derive_player_rank_in_round(round_cards):
    return len([card for card in round_cards.values() if card is not None])


def play_expert_first_in_round():
    return None


def play_expert_second_in_round():
    return None


def play_expert_third_in_round():
    return None


def play_expert_fourth_in_round():
    return None


def play_expert_strategy(player_cards, cards_playability, round_cards):
    playable_cards = derive_playable_cards(player_cards, cards_playability)
    # LEVEL 0
    if len(playable_cards) == 1:
        return player_cards[0]

    player_rank_in_round = derive_player_rank_in_round(round_cards)
    # LEVEL 1
    if player_rank_in_round == 0:
        card = play_expert_first_in_round()
    elif player_rank_in_round == 1:
        card = play_expert_second_in_round()
    elif player_rank_in_round == 2:
        card = play_expert_third_in_round()
    elif player_rank_in_round == 3:
        card = play_expert_fourth_in_round()

    return card

from expert.bet_or_pass.combinations import MAIN_COMBINATIONS, SUPPORT_COMBINATIONS, AGGRESSIVE_SUPPORT_COMBINATIONS
from helpers.common_helpers import create_card
from helpers.constants import COLORS, NEXT_PLAYER


# COMBINATION RELATED HELPERS
def detect_combination_in_hand(pattern, hand_cards, trump_color, only_trump=True):
    def _and_pattern_detection(pat, cards, col):
        return int(all([create_card(val, col) in cards for val in pat.split('+')]))

    def _or_pattern_detection(pat, cards, col):
        return len([1 for val in pat.split('/') if create_card(val, col) in cards])

    def _mix_pattern_detection(pat, cards, col):
        present_cards = []
        for sub_pat in pat.split('+'):
            present_cards.append(any([create_card(val, col) in cards for val in sub_pat.split('/')]))
        return int(all(present_cards))

    nb_detections = 0
    for color in [c for c in COLORS if (c == trump_color) == only_trump]:
        if ('+' in pattern) and ('/' in pattern):
            nb_detections += _mix_pattern_detection(pattern, hand_cards, color)
        elif '+' in pattern:
            nb_detections += _and_pattern_detection(pattern, hand_cards, color)
        elif '/' in pattern:
            nb_detections += _or_pattern_detection(pattern, hand_cards, color)
        else:
            nb_detections += int(create_card(pattern, color) in hand_cards)
    return nb_detections


def derive_score(nb_detections, unit_value, max_value):
    if isinstance(unit_value, dict):
        return unit_value.get(nb_detections, 0)
    elif max_value is not None:
        return min(nb_detections * unit_value, max_value)
    else:
        return nb_detections * unit_value


# STRATEGY HELPERS
def extract_speakers(players_bids):
    return set([player for (player, bid) in players_bids.items() if bid['value'] is not None])


def have_player_and_partner_spoken_over_same_color(player, players_bids):
    partner = NEXT_PLAYER[NEXT_PLAYER[player]]
    return (
            (players_bids[player]['color'] is not None)
            and (players_bids[player]['color'] == players_bids[partner]['color'])
    )


def extract_leader(players_bids):
    leader = None
    leading_value = -1
    speakers = extract_speakers(players_bids)
    for speaker in speakers:
        if players_bids[speaker]['value'] > leading_value:
            leader = speaker
            leading_value = players_bids[speaker]['value']
    return leader


def get_best_opponent_bid(players_bids, opponents):
    opponents_bids = [players_bids[opponent] for opponent in opponents if players_bids[opponent]['color'] is not None]
    if len(opponents_bids) == 0:
        return None, None
    else:
        best_bid = max(opponents_bids, key=lambda b: b['value'])
        return best_bid['color'], best_bid['value']


# COMPUTATION METHODS
def compute_best_color_bet(player_cards, main_combinations):
    best_color = None
    best_score = -1
    for color in COLORS:
        for combination in main_combinations:
            if detect_combination_in_hand(combination['trigger'], player_cards, color, True) == 1:
                tmp_score = 80
                for bonus_combination in combination['bonus']:
                    nb_detections = detect_combination_in_hand(
                        bonus_combination['pattern'],
                        player_cards,
                        color,
                        bonus_combination['trump']
                    )
                    tmp_score += derive_score(nb_detections, bonus_combination['value'], bonus_combination.get('max'))
                if tmp_score > best_score:
                    best_score = tmp_score
                    best_color = color
                    break
    return best_color, best_score


def compute_support_score(player_cards, color, support_combinations):
    support_score = 0
    for combination in support_combinations:
        nb_detections = detect_combination_in_hand(combination['pattern'], player_cards, color, combination['trump'])
        support_score += derive_score(nb_detections, combination['value'], combination.get('max'))
    return support_score


# STRATEGY
def bet_or_pass_none_spoke(player_cards):
    best_color, best_score = compute_best_color_bet(player_cards, MAIN_COMBINATIONS)
    if best_color is not None:
        return 'bet', best_color, best_score
    else:
        return 'pass', None, None


def bet_or_pass_only_opponents_spoke(player_cards, opponent_bid_value):
    best_color, best_score = compute_best_color_bet(player_cards, MAIN_COMBINATIONS)
    if (best_color is None) or (best_score < opponent_bid_value):
        return 'pass', None, None
    elif best_score == opponent_bid_value:
        return 'bet', best_color, best_score + 10
    elif best_score > opponent_bid_value:
        return 'bet', best_color, best_score
    else:
        print("RAISE EXCEPTION")
        return None, None, None


def bet_or_pass_only_partner_spoke(player_cards, partner_bid_color, partner_bid_value):
    best_color, best_score = compute_best_color_bet(player_cards, MAIN_COMBINATIONS)
    support_score = compute_support_score(player_cards, partner_bid_color, SUPPORT_COMBINATIONS)
    if (best_color is not None) and (best_score > (partner_bid_value + support_score)):
        return 'bet', best_color, best_score
    elif support_score > 0:
        return 'bet', partner_bid_color, partner_bid_value + support_score
    else:
        return 'pass', None, None


def bet_or_pass_only_player_partner_spoke_different_colors(player_cards, partner_bid_color, partner_bid_value):
    support_score = compute_support_score(player_cards, partner_bid_color, SUPPORT_COMBINATIONS)
    if support_score > 0:
        return 'bet', partner_bid_color, partner_bid_value + support_score
    else:
        return 'pass', None, None


def bet_or_pass_only_opponent_partner_spoke_opponent_leads(player_cards,
                                                           partner_bid_color, partner_bid_value,
                                                           opponent_bid_value):
    best_color, best_score = compute_best_color_bet(player_cards, MAIN_COMBINATIONS)
    aggressive_support_score = compute_support_score(player_cards, partner_bid_color, AGGRESSIVE_SUPPORT_COMBINATIONS)
    if (best_color is not None) and best_score > max(opponent_bid_value, partner_bid_value + aggressive_support_score):
        return 'bet', best_color, best_score
    elif (aggressive_support_score > 0) and ((partner_bid_value + aggressive_support_score) > opponent_bid_value):
        return 'bet', partner_bid_color, partner_bid_value + aggressive_support_score
    else:
        return 'pass', None, None


def bet_or_pass_only_opponent_partner_spoke_partner_leads(player_cards, partner_bid_color, partner_bid_value):
    return bet_or_pass_only_partner_spoke(player_cards, partner_bid_color, partner_bid_value)


def bet_or_pass_everyone_spoke_opponent_leads_different_color(player_cards,
                                                              partner_bid_color, partner_bid_value,
                                                              opponent_bid_value):
    aggressive_support_score = compute_support_score(player_cards, partner_bid_color, AGGRESSIVE_SUPPORT_COMBINATIONS)
    if (aggressive_support_score > 0) and ((partner_bid_value + aggressive_support_score) > opponent_bid_value):
        return 'bet', partner_bid_color, partner_bid_value + aggressive_support_score
    else:
        return 'pass', None, None


def bet_or_pass_everyone_spoke_partner_leads_different_color(player_cards, partner_bid_color, partner_bid_value):
    return bet_or_pass_only_player_partner_spoke_different_colors(player_cards, partner_bid_value, partner_bid_color)


def bet_or_pass_expert_strategy(player, players_bids):
    partner = NEXT_PLAYER[NEXT_PLAYER[player]]
    opponents = [NEXT_PLAYER[player], NEXT_PLAYER[partner]]

    speakers = extract_speakers(players_bids)

    if len(speakers) == 0:  # None spoke
        action, color, value = bet_or_pass_none_spoke()
    elif speakers.issubset(set(opponents)):  # only opponent(s) spoke
        action, color, value = bet_or_pass_only_opponents_spoke()
    elif speakers == {partner}:  # only partner spoke
        action, color, value = bet_or_pass_only_partner_spoke()
    elif speakers == {player, partner}:  # only player & partner spoke...
        if have_player_and_partner_spoken_over_same_color(player, players_bids):  # ...over same color
            action, color, value = 'pass', None, None
        else:  # ...over different colors
            action, color, value = bet_or_pass_only_player_partner_spoke_same_color()
    elif speakers.issubset(set(opponents + [partner])):  # only opponent & partner spoke...
        leader = extract_leader(players_bids)
        if leader in opponents:  # ...and opponent leads
            action, color, value = bet_or_pass_only_opponent_partner_spoke_opponent_leads()
        elif leader == partner:
            action, color, value = bet_or_pass_only_opponent_partner_spoke_partner_leads()
        else:
            print("RAISE EXCEPTION")
            action, color, value = 'pass', None, None
    elif speakers == set(opponents + [player, partner]):  # everyone spoke...
        leader = extract_leader(players_bids)
        if leader in opponents:  # ...and opponent leads...
            if have_player_and_partner_spoken_over_same_color(player, players_bids):
                # ...and same color for player & partner
                action, color, value = 'pass', None, None
            else:  # ...and differents color for player & partner
                action, color, value = bet_or_pass_everyone_spoke_opponent_leads_different_color()
        elif leader == partner:  # ...and partner leads...
            if have_player_and_partner_spoken_over_same_color(player, players_bids):
                # ...and same color for player & partner
                action, color, value = 'pass', None, None
            else:  # ...and different colors for player & partner
                action, color, value = bet_or_pass_everyone_spoke_partner_leads_different_color()
        else:
            print("RAISE EXCEPTION")
            action, color, value = 'pass', None, None
    else:
        print("RAISE EXCEPTION")
        action, color, value = 'pass', None, None

    return action, color, value

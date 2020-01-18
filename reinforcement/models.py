# @TODO: revise the _validate methods to check for type, format... And try to DRY (cf Round.update that calls for Hand._validate)
# @TODO: ensure player is the expected one in _validate methods

from typing import List, Dict, Optional
from enum import Enum
from itertools import product
from random import seed, shuffle

from helpers import constants

seed(13)

OK_CODE = 0
AUCTION_END_OK_CODE = 10
AUCTION_END_KO_CODE = 11
TRICK_END_CODE = 15
ROUND_END_CODE = 16
CHECK_ERROR_CODE = 20
VALIDATION_ERROR_CODE = 21
UNKNOWN_ERROR_CODE = 22


class Player(Enum):
    ONE = 'west'
    TWO = 'south'
    THREE = 'east'
    FOUR = 'north'


class Team(Enum):
    ONE = 'east/west'
    TWO = 'north/south'


PLAYER_TO_TEAM = {Player.ONE: Team.ONE, Player.TWO: Team.TWO, Player.THREE: Team.ONE, Player.FOUR: Team.TWO}
NEXT_PLAYER = {Player.ONE: Player.TWO, Player.TWO: Player.THREE, Player.THREE: Player.FOUR, Player.FOUR: Player.ONE}


class State(Enum):
    AUCTION = 'auction'
    PLAYING = 'playing'


class Describable(object):
    def __init__(self):
        pass

    @staticmethod
    def _describe(elt):
        if 'describe' in dir(elt):
            return elt.describe()
        elif '__dict__' in dir(elt):
            return elt.__dict__
        elif ('__iter__' in dir(elt)) and (type(elt) != dict):
            return [Describable._describe(e) for e in elt]
        else:
            return elt

    def describe(self):
        return {k: Describable._describe(v) for k, v in self.__dict__.items()}


class Updatable(Describable):
    UPDATE_PARAMS = None

    def __init__(self):
        super().__init__()
        pass

    def _check_params(self, **kwargs) -> bool:
        if self.UPDATE_PARAMS is None:
            raise NotImplementedError('UPDATE_PARAMS is not re-defined as a class attribute')
        return set(self.UPDATE_PARAMS).issubset(set(kwargs.keys()))

    def _validate(self, **kwargs) -> bool:
        raise NotImplementedError()

    def _update(self, **kwargs) -> int:
        raise NotImplementedError()

    def update(self, **kwargs) -> int:
        try:
            if not self._check_params(**kwargs):
                return CHECK_ERROR_CODE
            elif self._validate(**kwargs):
                return self._update(**kwargs)
            else:
                return VALIDATION_ERROR_CODE
        except:
            return UNKNOWN_ERROR_CODE

    def reset(self, **kwargs):
        raise NotImplementedError()


class Card(Describable):
    def __init__(self, color: str, value: str):
        super().__init__()
        self.color = color
        self.value = value

    def __eq__(self, other):
        return (self.color == other.color) and (self.value == other.value)


class Bid(Describable):
    def __init__(self, color: str, value: int):
        super().__init__()
        self.color = color
        self.value = value


class Hand(Updatable):
    UPDATE_PARAMS = ['card_index']

    def __init__(self, cards: List[Card]):
        super().__init__()
        self.cards = cards

    def __len__(self):
        return len(self.cards)

    def _validate(self, **kwargs) -> bool:
        return kwargs['card_index'] < len(self.cards)

    def _update(self, **kwargs) -> int:
        self.cards.pop(kwargs['card_index'])
        return OK_CODE

    def reset(self, **kwargs):
        self.cards = kwargs['cards']


class TrickCards(Updatable):
    UPDATE_PARAMS = ['player', 'card', 'trump_color']

    def __init__(self):
        super().__init__()
        self.cards: Dict[Player, Optional[Card]] = {player: None for player in Player}
        self.leader: Optional[Player] = None

    def set_leader(self, trump_color):
        trump_cards = [card for card in self.cards.values() if (card is not None) and (card.color == trump_color)]
        plain_cards = [card for card in self.cards.values() if (card is not None) and (card.color != trump_color)]
        if trump_cards:
            leading_card = sorted(trump_cards, key=_rank_trump_card)[-1]
        elif plain_cards:
            leading_card = sorted(trump_cards, key=_rank_plain_card)[-1]
        else:
            return
        self.leader = [player for (player, card) in self.cards.items() if card == leading_card][0]

    def _validate(self, **kwargs) -> bool:
        return self.cards[kwargs['player']] is None

    def _update(self, **kwargs) -> int:
        self.cards[kwargs['player']] = kwargs['card']
        self.set_leader(trump_color=kwargs['trump_color'])
        if any([cards is None for cards in self.cards.values()]):
            return OK_CODE
        else:
            return TRICK_END_CODE

    def reset(self, **kwargs):
        self.cards = {player: None for player in Player}
        self.leader = None


class Auction(Updatable):
    UPDATE_PARAMS = ['passed', 'player', 'color', 'value']

    def __init__(self):
        super().__init__()
        self.bids: Dict[Player, Optional[Bid]] = {player: None for player in Player}
        self.current_passed: int = 0
        self.current_best: int = None

    def auction_is_successful(self) -> bool:
        return any([bid is not None for bid in self.bids])

    def get_best_color(self):
        if self.current_best is not None:
            return [bid.color for bid in self.bids.values()
                    if (bid is not None) and (bid.value == self.current_best)][0]

    def _validate(self, **kwargs) -> bool:
        if kwargs['passed']:
            return True
        else:
            value = kwargs['value']
            value_format_is_valid = (type(value) == int) and (value % 10 == 0)
            value_amount_is_valid = (value > max(80, 0 if self.current_best is None else self.current_best))
            return value_format_is_valid and value_amount_is_valid

    def _update(self, **kwargs) -> int:
        if kwargs['passed']:
            if kwargs['passed'] == 3:
                return AUCTION_END_OK_CODE if self.auction_is_successful() else AUCTION_END_KO_CODE
            else:
                self.current_passed += 1
                return OK_CODE
        else:
            self.bids[kwargs['player']] = Bid(color=kwargs['color'], value=kwargs['value'])
            return OK_CODE

    def reset(self, **kwargs):
        self.bids = {player: None for player in Player}
        self.current_passed = 0
        self.current_best = None


class Round(Updatable):
    UPDATE_PARAMS = ['player', 'card_index']

    def __init__(self, hands: Dict[Player, List[Card]], trick_opener: Player):
        super().__init__()
        self.hands: Dict[Player, Hand] = {player: Hand(cards) for (player, cards) in hands}
        self.trick_cards: TrickCards = TrickCards()
        self.trick: int = 0
        self.trick_opener: Player = trick_opener
        self.score: Dict[Team, int] = {team: 0 for team in Team}
        self.belote: List[Player] = []
        self.trump: Optional[str] = None

    def card_is_playable(self, player: Player, card_index: int) -> bool:
        if player == self.trick_opener:
            return True
        else:
            player_card = self.hands[player].cards[card_index]
            trump_cards = [card for card in self.hands[player].cards if card.color == self.trump]
            trick_color = self.trick_cards.cards[self.trick_opener].color
            if trick_color == self.trump:
                if trump_cards:
                    leading_card = self.trick_cards.cards[self.trick_cards.leader]
                    player_highest_trump = max(trump_cards, key=_rank_trump_card)
                    return (
                            (_rank_trump_card(player_card) > _rank_trump_card(leading_card))
                            or (_rank_trump_card(leading_card) > _rank_trump_card(player_highest_trump))
                    )
                else:
                    return True
            else:
                color_cards = [card for card in self.hands[player].cards if card.color == trick_color]
                if color_cards:
                    return player_card in color_cards
                elif trump_cards:
                    leader = self.trick_cards.leader
                    if PLAYER_TO_TEAM[player] == PLAYER_TO_TEAM[leader]:
                        return True
                    else:
                        leading_card = self.trick_cards.cards[leader]
                        player_highest_trump = max(trump_cards, key=_rank_trump_card)
                        return (
                                (_rank_trump_card(player_card) > _rank_trump_card(leading_card))
                                or (_rank_trump_card(leading_card) > _rank_trump_card(player_highest_trump))
                        )
                else:
                    return True

    def is_belote_card(self, card: Card) -> bool:
        return (card.color == self.trump) and (card.value in ['Q', 'K'])

    # @TODO: implement Round.update_round_score (also check for belote if last_trick)
    def update_round_score(self, last_trick=False):
        raise NotImplementedError()

    def _validate(self, **kwargs) -> bool:
        player = kwargs['player']
        card_index = kwargs['card_index']
        if (type(card_index) != int) or (card_index >= len(self.hands[player])):
            return False
        return self.card_is_playable(player, card_index)

    def _update(self, **kwargs) -> int:
        card = self.hands[kwargs['player']][kwargs['card_index']]
        if self.is_belote_card(card):
            self.belote.append(kwargs['player'])
        trick_cards_update_code = self.trick_cards.update(card=card, trump_color=self.trump, **kwargs)
        hand_update_code = self.hands[kwargs['player']].update(**kwargs)
        if trick_cards_update_code == TRICK_END_CODE:
            self.update_round_score()
            self.trick_cards.reset()
            if self.trick == 7:
                self.update_round_score(last_trick=True)
                return ROUND_END_CODE
            else:
                self.trick += 1
                return hand_update_code
        else:
            return hand_update_code

    def set_trump(self, trump):
        self.trump: str = trump

    def reset(self, **kwargs):
        for player, hand in self.hands.items():
            hand.reset(cards=kwargs['cards'][player])
        self.trick_cards.reset(**kwargs)
        self.trick = 0
        self.trick_opener = kwargs['trick_opener']
        self.score = {team: 0 for team in Team}
        self.belote = []


class Game(Updatable):
    UPDATE_PARAMS = ['player']

    def __init__(self, first_player: Player):
        super().__init__()
        self.state: State = State.AUCTION
        self.first_player = first_player
        self.auction: Auction = Auction()
        self.round: Round = Round(hands=self.deal(), trick_opener=first_player)
        self.score: Dict[Team, int] = {team: 0 for team in Team}

    # @TODO: Implement Game.describe_state
    def describe_state(self):
        raise NotImplementedError()

    @classmethod
    def deal(cls) -> Dict[Player, List[Card]]:
        cards = [Card(color, value) for (color, value) in product(constants.COLORS, constants.PLAIN_POINTS.values())]
        shuffle(cards)
        return {player: cards[8 * i: 8 * (i + 1) + 1] for (i, player) in enumerate(Player)}

    def _validate(self, **kwargs) -> bool:
        return kwargs['player'] in Player.__members__

    def _update(self, **kwargs) -> int:
        if self.state == State.AUCTION:
            auction_update_code = self.auction.update(**kwargs)
            if auction_update_code in [AUCTION_END_OK_CODE, AUCTION_END_KO_CODE]:
                self.end_auction(status=auction_update_code, **kwargs)
                return OK_CODE
            else:
                return auction_update_code
        elif self.state == State.PLAYING:
            round_update_code = self.round.update(**kwargs)
            if round_update_code == ROUND_END_CODE:
                self.end_round(**kwargs)
                return OK_CODE
            else:
                return round_update_code
        else:
            return UNKNOWN_ERROR_CODE

    def reset(self, **kwargs):
        self.state = State.AUCTION
        self.first_player = kwargs['first_player']
        self.auction.reset(**kwargs)
        self.round.reset(cards=self.deal(), trick_opener=self.first_player, **kwargs)
        self.score = {team: 0 for team in Team}

    def end_auction(self, status, **kwargs):
        if status == AUCTION_END_OK_CODE:
            self.round.set_trump(self.auction.get_best_color())
            self.state = State.PLAYING
        elif status == AUCTION_END_KO_CODE:
            self.first_player = NEXT_PLAYER[self.first_player]
            self.auction.reset(**kwargs)
            self.round.reset(cards=self.deal(), trick_opener=self.first_player, **kwargs)

    # @TODO: implement Game.update_score (compare round.score to contract and compute game score)
    def update_score(self):
        raise NotImplementedError()

    def end_round(self, **kwargs):
        self.update_score()
        self.first_player = NEXT_PLAYER[self.first_player]
        self.auction.reset(**kwargs)
        self.round.reset(cards=self.deal(), trick_opener=self.first_player, **kwargs)
        self.state = State.AUCTION


# HELPERS
def _rank_trump_card(card: Card):
    return constants.TRUMP_POINTS[card.value], card.value


def _rank_plain_card(card: Card):
    return constants.PLAIN_POINTS[card.value], card.value, -constants.COLORS.index(card.color)

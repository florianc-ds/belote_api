# @TODO: revise the _validate methods to check for type, format... And try to DRY (cf Round.update that calls for Hand._validate)

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
    UPDATE_PARAMS = ['player', 'card']

    def __init__(self):
        super().__init__()
        self.cards: Dict[Player, Card] = dict(zip([p for p in Player], [None for i in range(len(Player.__members__))]))
        self.leader: Optional[Player] = None

    # @TODO: implement TrickCards.set_leader
    def set_leader(self):
        raise NotImplementedError()

    def _validate(self, **kwargs) -> bool:
        return self.cards[kwargs['player']] is None

    def _update(self, **kwargs) -> int:
        self.cards[kwargs['player']] = kwargs['card']
        self.set_leader()
        if any([cards is None for cards in self.cards.values()]):
            return OK_CODE
        else:
            return TRICK_END_CODE

    def reset(self, **kwargs):
        self.cards = dict(zip([p for p in Player], [None for i in range(len(Player.__members__))]))
        self.leader = None


class Auction(Updatable):
    UPDATE_PARAMS = ['passed', 'player', 'color', 'value']

    def __init__(self):
        super().__init__()
        self.bids: Dict[Player, Bid] = dict(zip([p for p in Player], [None for i in range(len(Player.__members__))]))
        self.current_passed: int = 0
        self.current_best: int = None

    def auction_is_successful(self) -> bool:
        return any([bid is not None for bid in self.bids])

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
        self.bids = dict(zip([p for p in Player], [None for i in range(len(Player.__members__))]))
        self.current_passed = 0
        self.current_best = None


class Round(Updatable):
    UPDATE_PARAMS = ['player', 'card_index']

    def __init__(self, hands: Dict[Player, List[Card]], trump: str):
        super().__init__()
        self.hands: Dict[Player, Hand] = {player: Hand(cards) for (player, cards) in hands}
        self.trick_cards: TrickCards = TrickCards()
        self.trick: int = 0
        self.score: Dict[Team, int] = {team: 0 for team in Team}
        self.belote: List[Player] = []
        self.trump: str = trump

    # @TODO: implement Round.card_is_playable
    def card_is_playable(self, card_index: int) -> bool:
        raise NotImplementedError()

    # @TODO: implement Round.is_belote_card
    def is_belote_card(self, card: Card) -> bool:
        raise NotImplementedError()

    # @TODO: implement Round.update_round_score
    def update_round_score(self):
        raise NotImplementedError()

    def _validate(self, **kwargs) -> bool:
        card_index = kwargs['card_index']
        if (type(card_index) != int) or (card_index >= len(self.hands[kwargs['player']])):
            return False
        return self.card_is_playable(card_index)

    def _update(self, **kwargs) -> int:
        card = self.hands[kwargs['player']][kwargs['card_index']]
        if self.is_belote_card(card):
            self.belote.append(kwargs['player'])
        trick_cards_update_code = self.trick_cards.update(card=card, **kwargs)
        hand_update_code = self.hands[kwargs['player']].update(**kwargs)
        if trick_cards_update_code == TRICK_END_CODE:
            self.update_round_score()
            self.trick_cards.reset()
            if self.trick == 7:
                return ROUND_END_CODE
            else:
                self.trick += 1
                return hand_update_code
        else:
            return hand_update_code

    def reset(self, **kwargs):
        for player, hand in self.hands.items():
            hand.reset(cards=kwargs['cards'][player])
        self.trick_cards.reset(**kwargs)
        self.trick: int = 0
        self.score = {team: 0 for team in Team}
        self.belote = []
        self.trump: str = kwargs['trump']


# @TODO: Adapt __init__ in order not to initialize from arguments
# @TODO: implement Game
class Game(Updatable):
    UPDATE_PARAMS = ['player']

    def __init__(self):
        super().__init__()
        self.state: State = State.AUCTION
        self.auction: Auction = Auction()
        self.round: Round = Round(self.deal())
        self.score: Dict[Team, int] = {team: 0 for team in Team}

    @classmethod
    def deal(cls) -> Dict[Player, List[Card]]:
        cards = [Card(color, value) for (color, value) in product(constants.COLORS, constants.PLAIN_POINTS.values())]
        shuffle(cards)
        return {player: cards[8 * i: 8 * (i + 1) + 1] for (i, player) in enumerate(Player)}

    # @TODO: implement Game._validate
    def _validate(self) -> bool:
        raise NotImplementedError()

    # @TODO: implement Game._update
    def _update(self) -> int:
        raise NotImplementedError()

    # @TODO: implement Game.reset
    def reset(self):
        raise NotImplementedError()

    # @TODO: implement Game.end_auction
    def end_auction(self):
        raise NotImplementedError()

    # @TODO: implement Game.end_round
    def end_round(self):
        raise NotImplementedError()

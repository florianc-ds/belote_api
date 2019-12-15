from typing import List, Dict, Optional
from enum import Enum

OK_CODE = 0
VALIDATION_ERROR_CODE = 10
UNKNOWN_ERROR_CODE = 20


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

    def describe(self):
        return self.__dict__


class Updatable(Describable):
    def __init__(self):
        super().__init__()
        pass

    def _validate(self, **kwargs):
        raise NotImplementedError()

    def _update(self, **kwargs):
        raise NotImplementedError()

    def update(self, **kwargs):
        try:
            if self._validate(**kwargs):
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
    def __init__(self, cards: List[Card]):
        super().__init__()
        self.cards = cards

    def _validate(self, **kwargs):
        return Card(kwargs['color'], kwargs['value']) in self.cards

    def _update(self, **kwargs):
        self.cards.remove(Card(kwargs['color'], kwargs['value']))
        return OK_CODE

    def reset(self, **kwargs):
        self.cards = kwargs['cards']


# @TODO: Adapt __init__ in order not to initialize from arguments
class TrickCards(Updatable):
    def __init__(self, cards: Dict[Player, Card], leader: Optional[Player]):
        super().__init__()
        self.cards = cards
        self.leader = leader

    # @TODO: implement TrickCards.set_leader
    def set_leader(self):
        raise NotImplementedError()

    def _validate(self, **kwargs):
        return self.cards[kwargs['player']] is None

    def _update(self, **kwargs):
        self.cards[kwargs['player']] = kwargs['card']
        self.set_leader()
        return OK_CODE

    def reset(self, **kwargs):
        self.cards = dict(zip([p for p in Player], [None for i in range(len(Player))]))


# @TODO: Adapt __init__ in order not to initialize from arguments
# @TODO: implement Round
class Round(Updatable):
    def __init__(self, hands: Dict[Player, Hand], trick_cards: TrickCards,
                 trick: int, belote: List[Player], trump: str):
        super().__init__()
        self.hands = hands
        self.trick_cards = trick_cards
        self.trick = trick
        self.belote = belote
        self.trump = trump


# @TODO: Adapt __init__ in order not to initialize from arguments
# @TODO: implement Auction
class Auction(Updatable):
    def __init__(self, bids: Dict[Player, Bid], current_passed: int):
        super().__init__()
        self.bids = bids
        self.current_passed = current_passed


# @TODO: Adapt __init__ in order not to initialize from arguments
# @TODO: implement Game
class Game(Updatable):
    def __init__(self, state: State, auction: Auction, round: Round, score: Dict[Team, int]):
        super().__init__()
        self.state = state
        self.auction = auction
        self.round = round
        self.score = score

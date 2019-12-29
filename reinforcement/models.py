from typing import List, Dict, Optional
from enum import Enum

OK_CODE = 0
CHECK_ERROR_CODE = 10
VALIDATION_ERROR_CODE = 20
UNKNOWN_ERROR_CODE = 30


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

    # @TODO: implement recursive dict representation
    def describe(self):
        return self.__dict__


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
        return OK_CODE

    def reset(self, **kwargs):
        self.cards = dict(zip([p for p in Player], [None for i in range(len(Player.__members__))]))
        self.leader = None


# @TODO: implement Auction
class Auction(Updatable):
    UPDATE_PARAMS = ['passed', 'player', 'color', 'value']

    def __init__(self):
        super().__init__()
        self.bids: Dict[Player, Bid] = dict(zip([p for p in Player], [None for i in range(len(Player.__members__))]))
        self.current_passed: int = 0

    # @TODO: implement Auction._validate
    def _validate(self) -> bool:
        raise NotImplementedError()

    # @TODO: implement Auction._update
    def _update(self) -> int:
        raise NotImplementedError()

    def reset(self):
        self.bids = dict(zip([p for p in Player], [None for i in range(len(Player.__members__))]))
        self.current_passed = 0


# @TODO: implement Round
class Round(Updatable):
    UPDATE_PARAMS = ['player', 'card_index']

    def __init__(self, hands: Dict[Player, List[Card]]):
        super().__init__()
        self.hands: Dict[Player, Hand] = {player: Hand(cards) for (player, cards) in hands}
        self.trick_cards: TrickCards = TrickCards()
        self.trick: int = 0
        self.belote: List[Player] = []
        self.trump: Optional[str] = None

    # @TODO: implement Round._validate
    def _validate(self) -> bool:
        raise NotImplementedError()

    # @TODO: implement Round._update
    def _update(self) -> int:
        raise NotImplementedError()

    # @TODO: implement Round.reset
    def reset(self):
        raise NotImplementedError()


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

    # @TODO: implement Game.deal
    @classmethod
    def deal(cls) -> Dict[Player, List[Card]]:
        raise NotImplementedError()

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

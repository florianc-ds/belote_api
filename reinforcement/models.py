# @TODO: revise the _validate methods to check for type, format... And try to DRY (cf Round.update that calls for Hand._validate)
# @TODO: ensure player is the expected one in _validate methods
import logging
from typing import List, Dict, Optional
from enum import Enum
from itertools import product
from random import seed, shuffle

from helpers import constants

seed(13)

COLOR_TO_SYMBOL = {'s': '♠', 'd': '♦', 'h': '♥', 'c': '♣'}

OK_CODE = 0
AUCTION_END_OK_CODE = 10
AUCTION_END_KO_CODE = 11
TRICK_END_CODE = 15
ROUND_END_CODE = 16
CHECK_ERROR_CODE = 20
VALIDATION_ERROR_CODE = 21
UNKNOWN_ERROR_CODE = 22

logger = logging.getLogger()


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
        elif isinstance(elt, Enum):
            return elt.value
        elif '__dict__' in dir(elt):
            return elt.__dict__
        elif type(elt) == dict:
            return {Describable._describe(k): Describable._describe(v) for k, v in elt.items()}
        elif ('__iter__' in dir(elt)) and (type(elt) not in [dict, str]):
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
        class_name = self.__class__.__name__
        try:
            if not self._check_params(**kwargs):
                logger.warning(f"Parameters passed ({kwargs}) for update action on {class_name} are not sufficient.\n"
                               f"Required parameters for Class {class_name} are {self.UPDATE_PARAMS}")
                return CHECK_ERROR_CODE
            elif not self._validate(**kwargs):
                logger.warning(f"Validation went wrong in Class {class_name} for parameters {kwargs}")
                return VALIDATION_ERROR_CODE
            else:
                return self._update(**kwargs)
        except Exception as e:
            logger.warning(f"Something went wrong during update process for Class {class_name}\n"
                           f"Parameters passed are: {kwargs}\n"
                           f"Current state of instance is: {self.describe()}\n"
                           f"ERROR: {e.__class__.__name__}: {e}")
            return UNKNOWN_ERROR_CODE

    def reset(self, **kwargs):
        raise NotImplementedError()


class Card(Describable):
    def __init__(self, value: str, color: str):
        super().__init__()
        self.value = value
        self.color = color

    def __eq__(self, other):
        return (self.color == other.color) and (self.value == other.value)

    def describe(self):
        return f'{self.value}{COLOR_TO_SYMBOL[self.color]}'

    def describe_plain(self):
        return f'{self.value}{self.color}'


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
        correct_index = kwargs['card_index'] < len(self.cards)
        if not correct_index:
            logger.warning(f"Card index ({kwargs['card_index']}) "
                           f"is higher than the number of cards in hand ({len(self.cards)})")
        return correct_index

    def _update(self, **kwargs) -> int:
        self.cards.pop(kwargs['card_index'])
        return OK_CODE

    def reset(self, **kwargs):
        self.cards = kwargs['cards']


class TrickCards(Updatable):
    UPDATE_PARAMS = ['player', 'card', 'trump_color', 'trick_color']

    def __init__(self):
        super().__init__()
        self.cards: Dict[Player, Optional[Card]] = {player: None for player in Player}
        self.leader: Optional[Player] = None

    def set_leader(self, trump_color: str, trick_color: str):
        self.leader = derive_leader(cards=self.cards, trump_color=trump_color, trick_color=trick_color)

    def _validate(self, **kwargs) -> bool:
        empty_card = self.cards[kwargs['player']] is None
        if not empty_card:
            logger.warning(f"Trying to override an existing card ({self.cards[kwargs['player']]}) in TrickCards")
        return empty_card

    def _update(self, **kwargs) -> int:
        self.cards[kwargs['player']] = kwargs['card']
        self.set_leader(trump_color=kwargs['trump_color'], trick_color=kwargs['trick_color'])
        if any([cards is None for cards in self.cards.values()]):
            return OK_CODE
        else:
            logger.info("End of the trick")
            return TRICK_END_CODE

    def reset(self, **kwargs):
        self.cards = {player: None for player in Player}
        self.leader = None


class Auction(Updatable):
    UPDATE_PARAMS = ['passed', 'player', 'color', 'value']

    def __init__(self):
        super().__init__()
        self.bids: Dict[Player, Optional[Bid]] = {player: None for player in Player}
        self.current_passed: int = -1
        self.current_best: Optional[Player] = None

    def auction_is_successful(self) -> bool:
        return any([bid is not None for bid in self.bids.values()])

    def get_best_color(self):
        if self.current_best is not None:
            return [bid.color for bid in self.bids.values()
                    if (bid is not None) and (bid.value == self.bids[self.current_best].value)][0]

    def _validate(self, **kwargs) -> bool:
        if kwargs['passed']:
            return True
        else:
            value = kwargs['value']
            value_format_is_valid = (type(value) == int) and (value % 10 == 0)
            if not value_format_is_valid:
                logger.warning(f"Value of the bid ({value}) is not valid: integer dividable by 10 is expected")
                return False
            current_best_bid = self.bids[self.current_best].value if self.current_best else None
            value_amount_is_valid = (value > (current_best_bid if current_best_bid is not None else 79))
            if not value_amount_is_valid:
                logger.warning(f"Value of the bid ({value}) is lesser than the current best bid ({current_best_bid})")
                return False
            return True

    def _update(self, **kwargs) -> int:
        if kwargs['passed']:
            if self.current_passed == 2:
                if self.auction_is_successful():
                    logger.info("End of the auction")
                    return AUCTION_END_OK_CODE
                else:
                    logger.info("Nobody bet. Dealing again")
                    return AUCTION_END_KO_CODE
            else:
                self.current_passed += 1
                return OK_CODE
        else:
            self.bids[kwargs['player']] = Bid(color=kwargs['color'], value=kwargs['value'])
            self.current_best = kwargs['player']
            self.current_passed = 0
            return OK_CODE

    def reset(self, **kwargs):
        self.bids = {player: None for player in Player}
        self.current_passed = -1
        self.current_best = None


class Round(Updatable):
    UPDATE_PARAMS = ['player', 'card_index']

    def __init__(self, hands: Dict[Player, List[Card]], trick_opener: Player):
        super().__init__()
        self.hands: Dict[Player, Hand] = {player: Hand(cards) for (player, cards) in hands.items()}
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
                    if player_card.color != self.trump:
                        logger.warning(f"Playing trumps, card ({player_card.describe()}) must be trump ({self.trump})")
                        return False
                    leading_card = self.trick_cards.cards[self.trick_cards.leader]
                    player_highest_trump = max(trump_cards, key=_rank_trump_card)
                    if not (
                            (_rank_trump_card(player_card) > _rank_trump_card(leading_card)) or
                            (_rank_trump_card(leading_card) > _rank_trump_card(player_highest_trump))
                    ):
                        logger.warning(f"Playing trumps, card ({player_card.describe()}) "
                                       f"must be higher than current leading trump ({leading_card.describe()})")
                        return False
                    else:
                        return True
                else:
                    return True
            else:
                color_cards = [card for card in self.hands[player].cards if card.color == trick_color]
                if color_cards:
                    valid_color = player_card in color_cards
                    if not valid_color:
                        logger.warning(f"Player has to play trick color ({trick_color}), "
                                       f"but played instead {player_card.describe()}")
                    return valid_color
                elif trump_cards:
                    leader = self.trick_cards.leader
                    if PLAYER_TO_TEAM[player] == PLAYER_TO_TEAM[leader]:
                        return True
                    else:
                        if player_card.color != self.trump:
                            logger.warning(f"Can not furnish on color {trick_color}, "
                                           f"player must cut but instead played {player_card.describe()}")
                            return False
                        leading_card = self.trick_cards.cards[leader]
                        player_highest_trump = max(trump_cards, key=_rank_trump_card)
                        if not (
                                (leading_card.color != self.trump) or
                                (_rank_trump_card(player_card) > _rank_trump_card(leading_card)) or
                                (_rank_trump_card(leading_card) > _rank_trump_card(player_highest_trump))
                        ):
                            logger.warning(f"Can not furnish on color {trick_color}, player must cut with "
                                           f"a high enough trump, but instead played {player_card.describe()}")
                            return False
                        else:
                            return True
                else:
                    return True

    def get_cards_playability(self, player: Player) -> List[bool]:
        player_hand = self.hands[player]
        logging_level = logger.level
        logger.setLevel(logging.ERROR)
        cards_playability = [self.card_is_playable(player, card_index) for card_index in range(len(player_hand))]
        logger.setLevel(logging_level)
        return cards_playability

    def is_belote_card(self, card: Card) -> bool:
        return (card.color == self.trump) and (card.value in ['Q', 'K'])

    def update_round_score(self, last_trick=False):
        leading_team = PLAYER_TO_TEAM[self.trick_cards.leader]
        self.score[leading_team] += sum(
            [constants.TRUMP_POINTS[card.value] if card.color == self.trump else constants.PLAIN_POINTS[card.value]
             for card in self.trick_cards.cards.values()]
        )
        if last_trick:
            self.score[leading_team] += 10
            if self.belote[0] == self.belote[1]:
                self.score[PLAYER_TO_TEAM[self.belote[0]]] += 20

    def _validate(self, **kwargs) -> bool:
        player = kwargs['player']
        card_index = kwargs['card_index']
        if type(card_index) != int:
            logger.warning(f"Card index ({card_index}) is invalid")
            return False
        elif card_index >= len(self.hands[player].cards):
            logger.warning(f"Card index ({card_index}) "
                           f"is higher than the number of cards in hand ({len(self.hands[player].cards)})")
            return False
        return self.card_is_playable(player, card_index)

    def _update(self, **kwargs) -> int:
        card = self.hands[kwargs['player']].cards[kwargs['card_index']]
        if self.is_belote_card(card):
            logger.info('(Re-)Belote')
            self.belote.append(kwargs['player'])
        if kwargs['player'] == self.trick_opener:
            trick_color = card.color
        else:
            trick_color = self.trick_cards.cards[self.trick_opener].color
        trick_cards_update_code = self.trick_cards.update(card=card, trump_color=self.trump, trick_color=trick_color,
                                                          **kwargs)
        if trick_cards_update_code not in [OK_CODE, TRICK_END_CODE]:
            return trick_cards_update_code
        hand_update_code = self.hands[kwargs['player']].update(**kwargs)
        if trick_cards_update_code == TRICK_END_CODE:
            if self.trick == 7:
                self.update_round_score(last_trick=True)
                self.trick_cards.reset()
                logger.info("End of the round")
                return ROUND_END_CODE
            else:
                self.update_round_score()
                self.trick_opener = self.trick_cards.leader
                self.trick_cards.reset()
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
        self.trump = None


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
        cards = [Card(color=color, value=value)
                 for (color, value) in product(constants.COLORS, constants.PLAIN_POINTS.keys())]
        shuffle(cards)
        return {player: cards[8 * i: 8 * (i + 1)] for (i, player) in enumerate(Player)}

    def _validate(self, **kwargs) -> bool:
        known_player = kwargs['player'] in Player
        if not known_player:
            logger.warning(f"Player ({kwargs['player']}) unknown. Please choose among {list(Player)}")
        return known_player

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

    def update_score(self):
        contract_team = PLAYER_TO_TEAM[self.auction.current_best]
        contract_team_round_score = self.round.score[contract_team]
        opponent_team = Team.ONE if contract_team == Team.TWO else Team.TWO
        opponent_team_round_score = self.round.score[opponent_team]
        contract = self.auction.bids[self.auction.current_best].value
        if contract_team_round_score >= contract:
            logger.info(f"Contract ({contract}) has been reached ({contract_team_round_score}) "
                        f"by {contract_team.value}")
            self.score[contract_team] += round(contract_team_round_score / 10) * 10 + contract
            self.score[opponent_team] += round(opponent_team_round_score / 10) * 10
        else:
            logger.info(f"Contract ({contract}) has not been reached ({contract_team_round_score}) "
                        f"by {contract_team.value}")
            self.score[opponent_team] += 160 + contract

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


def derive_leader(cards: Dict[Player, Optional[Card]], trump_color: str, trick_color: str) -> Optional[Player]:
    trump_cards = [card for card in cards.values() if (card is not None) and (card.color == trump_color)]
    color_cards = [card for card in cards.values() if (card is not None) and (card.color == trick_color)]
    if trump_cards:
        leading_card = sorted(trump_cards, key=_rank_trump_card)[-1]
    elif color_cards:
        leading_card = sorted(color_cards, key=_rank_plain_card)[-1]
    else:
        return
    return [player for (player, card) in cards.items() if card is not None and card == leading_card][0]

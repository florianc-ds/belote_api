from typing import Dict, Optional, List, Tuple

from reinforcement.models import Player, Card


class State(object):
    """
    contract_team: whether player is from contract team
    trick_cards: {Player.ONE: Card('7', 'h'), Player.TWO: None, ...}
    player_cards: [(Card('7', 'h'), True), ...]  bool corresponds to card playability
    """
    def __init__(self,
                 contract_team: bool,
                 trick_cards: Dict[Player, Optional[Card]],
                 player_cards: List[Tuple[Card, bool]]):
        self.contract_team: bool = contract_team
        self.trick_cards: Dict[Player, Optional[Card]] = trick_cards
        self.player_cards = player_cards

    def get_representation(self):
        sorted_trick_cards = [self.trick_cards[player]
                              for player in [Player.ONE, Player.TWO, Player.THREE, Player.FOUR]]
        trick_cards_representation = [(card.color, card.value) if card is not None else None
                                      for card in sorted_trick_cards]
        player_cards_representation = [(card.color, card.value, playable) for (card, playable) in self.player_cards]
        return (
            self.contract_team,
            trick_cards_representation,
            player_cards_representation
        )

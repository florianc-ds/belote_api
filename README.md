## DESCRIPTION
This repo defines a flask API than can interact with the belote game.

It works with the belote project found here: [belote](https://github.com/florianc-ds/belote).

4 different agents are currently presented:
- **random**
- **highest_card**
- **expert**
- **reinforcement** (*WIP*)

For each agent, 2 routes (*POST* method) are defined :
- /{agent}/bet_or_pass
- /{agent}/play

## INSTALL
`poetry install`

## LAUNCH API
`poetry run python app.py`

**N.B:** Flask API is available locally on port 5000.

## API details
You can define a new agent by implementing 2 routes, with following specification:
- /{agent}/bet_or_pass
```
Potential input:
 - player (str)
 - playerCards (list<str>)
 - playersBids (dict<player, dict<str, str|int>>)
 - auctionPassedTurnInRow (int)
 - globalScore (dict<str, int>)
 - gameFirstPlayer (str)
 - encrypted (bool)

Output:
{"action": "pass"}
or
{"action": "bet", "color": "h"|"s"|"d"|"c", "value": <value>}
```
- /{agent}/play
```
Potential input:
 - player (str)
 - trumpColor (str)
 - playerCards (list<str>)
 - cardsPlayability (list<bool>)
 - round (int)
 - roundCards (dict<player, str>)
 - roundColor (str)
 - gameHistory (dict<player, list<str>>)
 - roundsFirstPlayer (list<player>)
 - contract (int)
 - contractTeam (str)
 - globalScore (dict<str, int>)
 - encrypted (bool)

Output:
{"card": <card>}
```

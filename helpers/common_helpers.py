from helpers.encryption import decrypt


def extract_color(raw):
    return raw[-1]


def extract_value(raw):
    return raw[:-1]


def create_card(value, color):
    return value + color


def decrypt_cards(cards, player):
    return [decrypt(value=card, key=player) for card in cards]

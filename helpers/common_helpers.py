def extract_color(raw):
    return raw[-1]


def extract_value(raw):
    return raw[:-1]


def create_card(value, color):
    return value + color

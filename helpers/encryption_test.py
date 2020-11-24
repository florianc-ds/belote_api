from helpers.encryption import encrypt, decrypt, vigenere_encrypt, vigenere_decrypt


def test_vigenere_encrypt():
    assert vigenere_encrypt("ABCDE=", "AC") == "ADCFEB"


def test_vigenere_decrypt():
    assert vigenere_decrypt("ADCFEB", "AC") == "ABCDE="


def test_encrypt():
    assert encrypt("THISISAMESSAGE", "KEY") == "T6GZDTZIT2CILQJST2CI=QH7"


def test_decrypt():
    assert decrypt("T6GZDTZIT2CINSZTSOEJWSJET2LIUQZE", "KEY") == "THISISANOTHERMESSAGE"


def test_bijection():
    assert decrypt(encrypt("ABC", "KEY"), "KEY") == "ABC"


def test_encrypt_needs_key():
    assert encrypt("ABC", "KEY") != encrypt("ABC", "KEY2")


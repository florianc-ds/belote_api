from base64 import b32encode, b32decode
from typing import Optional

from helpers.exceptions import StringNotInAlphabetException

BASE32_WITH_PADDING = (
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P",
    "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "2", "3", "4", "5", "6", "7",
    "="
)


def is_compatible(string, alphabet=BASE32_WITH_PADDING):
    return all([x in alphabet for x in string])


def vigenere_encrypt(value: str, key: str, alphabet=BASE32_WITH_PADDING) -> Optional[str]:
    if (not is_compatible(value, alphabet)) or (not is_compatible(key, alphabet)):
        raise StringNotInAlphabetException
    encrypted_value = ""
    for (i, letter) in enumerate(value):
        key_letter = key[i % len(key)]
        key_letter_index = alphabet.index(key_letter)
        letter_index = alphabet.index(letter)
        encrypted_letter_index = (letter_index + key_letter_index) % len(alphabet)
        encrypted_value += alphabet[encrypted_letter_index]
    return encrypted_value


def vigenere_decrypt(value: str, key: str, alphabet=BASE32_WITH_PADDING) -> Optional[str]:
    if (not is_compatible(value, alphabet)) or (not is_compatible(key, alphabet)):
        raise StringNotInAlphabetException
    decrypted_value = ""
    for (i, letter) in enumerate(value):
        key_letter = key[i % len(key)]
        key_letter_index = alphabet.index(key_letter)
        letter_index = alphabet.index(letter)
        decrypted_letter_index = (letter_index - key_letter_index) % len(alphabet)
        decrypted_value += alphabet[decrypted_letter_index]
    return decrypted_value


def b32_encrypt(value: str) -> str:
    byte_value = value.encode()
    return b32encode(byte_value).decode()


def b32_decrypt(value: str) -> str:
    byte_value = value.encode()
    return b32decode(byte_value).decode()


def encrypt(value: str, key: str) -> str:
    b32_encrypted_value = b32_encrypt(value)
    b32_encrypted_key = b32_encrypt(key)
    return vigenere_encrypt(b32_encrypted_value, b32_encrypted_key)


def decrypt(value: str, key: str) -> str:
    b32_encrypted_key = b32_encrypt(key)
    vigenere_decrypted = vigenere_decrypt(value, b32_encrypted_key)
    return b32_decrypt(vigenere_decrypted)

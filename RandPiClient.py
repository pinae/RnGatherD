#!/usr/bin/python3
# -*- coding: utf-8 -*-

import hmac
import sys
from base64 import b64decode

import requests
from Crypto.Cipher import AES
from Crypto.Hash import SHA256, SHA384, HMAC
from pbkdf2 import PBKDF2

SHARED_SECRET = ("Mein tolles langes Passwort, das total sicher ist. " +
                 "Das sieht man an den Sonderzeichen wie / (Slash) oder $ (Dollar). " +
                 "Außerdem enthält diese Passphrase einfach eine Menge Zeichen, " +
                 "die ein Angreifer erst mal erraten muss.")
SHARED_SALT = "pepper"
base_key = PBKDF2(SHARED_SECRET.encode('utf-8'), SHARED_SALT.encode('utf-8'),
                  iterations=32000, digestmodule=SHA384, macmodule=HMAC).read(48)
ENCRYPTION_KEY = base_key[:32]
ENCRYPTION_IV = base_key[32:48]


def remove_pkcs7_padding(data):
        return data[:-data[-1]]


def get_random(length=64):
    try:
        response = requests.get('http://10.22.253.135/entropy/random?length=' + str(length))
        response_data = response.json()
    except OSError:
        return b''
    if hmac.new(ENCRYPTION_KEY,
                b64decode(response_data['encrypted_data']),
                SHA256).digest() != b64decode(response_data['hmac']):
        print("Wrong signature!")
        return b''
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC, ENCRYPTION_IV)
    data = remove_pkcs7_padding(cipher.decrypt(b64decode(response_data['encrypted_data'])))
    return data

if __name__ == "__main__":
    sys.stdout.buffer.write(get_random())

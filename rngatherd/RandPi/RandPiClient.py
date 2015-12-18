#!/usr/bin/python3
# -*- coding: utf-8 -*-

import hmac
import sys
from base64 import b64decode

import requests
from Crypto.Cipher import AES
from Crypto.Hash import SHA256, SHA384, HMAC

from rngatherd.RandPi.pbkdf2 import PBKDF2


class RandPiClient(object):
    def __init__(self):
        self.SHARED_SECRET = ("Mein tolles langes Passwort, das total sicher ist. " +
                         "Das sieht man an den Sonderzeichen wie / (Slash) oder $ (Dollar). " +
                         "Außerdem enthält diese Passphrase einfach eine Menge Zeichen, " +
                         "die ein Angreifer erst mal erraten muss.")
        self.SHARED_SALT = "pepper"
        base_key = PBKDF2(self.SHARED_SECRET.encode('utf-8'), self.SHARED_SALT.encode('utf-8'),
                          iterations=32000, digestmodule=SHA384, macmodule=HMAC).read(48)
        self.ENCRYPTION_KEY = base_key[:32]
        self.ENCRYPTION_IV = base_key[32:48]

    @staticmethod
    def remove_pkcs7_padding(data):
            return data[:-data[-1]]

    def get_random(self, length=64):
        try:
            response = requests.get('http://10.22.253.134/entropy/random?length=' + str(length))
            response_data = response.json()
        except OSError:
            return b''
        if hmac.new(self.ENCRYPTION_KEY,
                    b64decode(response_data['encrypted_data']),
                    SHA256).digest() != b64decode(response_data['hmac']):
            print("Wrong signature!")
            return b''
        cipher = AES.new(self.ENCRYPTION_KEY, AES.MODE_CBC, self.ENCRYPTION_IV)
        data = self.remove_pkcs7_padding(cipher.decrypt(b64decode(response_data['encrypted_data'])))
        return data

if __name__ == "__main__":
    client = RandPiClient()
    sys.stdout.buffer.write(client.get_random())

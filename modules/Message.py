from __future__ import annotations
from datetime import datetime
import json
from accessify import private
from .Database import cur, conn, DB_TABLE
from .CustomExceptions import VerifyError
import base64
from termcolor import colored

from Crypto.PublicKey.RSA import RsaKey
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto import Random


'''
Класс сообщения

Атрибуты:
    1. timestamp - время отправки
    2. sender    - отправитель
    3. recipient - получатель
    4. message   - зашифрованное сообщение
    5. sign      - электроцифровая подпись (ЭЦП)
    6. msg_key   - зашифрованный ключ для дешифровки сообщения
    7. json      - все атрибуты в формате json

Методы:
    1. __init__         - создание объекта класса
    2. __str__          - строковое представление класса
    3. encode_message   - шифрование сообщения
    4. sign_message     - генерация ЭЦП
    5. get_public_key   - получение открытого ключа пользователя
    6. load_from_json   - загрузка класса из .json
    7. decrypt_message  - расшифровка сообщения
    8. verify           - проверка сообщения на подлинность
'''
class Message:

    def __init__(self, sender: str, recipient: str, message: str, sender_prk: RsaKey) -> None:
        if (sender is None) and (recipient is None) and (message is None) and (sender_prk is None):
            pass
        else:
            self.timestamp = str(datetime.now())
            self.sender = self.calc_hash(sender)
            self.recipient = self.calc_hash(recipient)
            self.key, self.message = self.encode_message(message)
            self.sign = self.sign_message(message, sender_prk)

    
    def __str__(self) -> str:
        data = f"{' CLASS MESSAGE ':-^75}\n"
        for name in self.__dict__:
            data += f"{colored(name.capitalize(), 'green')}: {colored(self.__dict__[name], 'yellow')}\n"
        return data.strip()
    

    @private
    def encode_message(self, message: str) -> tuple[str, str]:
        sessionkey = Random.new().read(32)
        iv = Random.new().read(16)
        pub_key = self.get_public_key(self.recipient)

        obj = AES.new(sessionkey, AES.MODE_CFB, iv)
        ciphertext = iv + obj.encrypt(message.encode())
        ciphertext = base64.encodebytes(ciphertext).decode().strip()
        
        cipherrsa = PKCS1_OAEP.new(pub_key)
        sessionkey = cipherrsa.encrypt(sessionkey)
        sessionkey = base64.encodebytes(sessionkey).decode().strip()

        return sessionkey, ciphertext


    
    @private
    def sign_message(self, message: str, pk_key: RsaKey) -> str:
        text_hash = SHA256.new(message.encode())

        # print(f"HASH: {text_hash.hexdigest()}, MESSAGE: {message}")

        signature = PKCS1_v1_5.new(pk_key)
        signature = signature.sign(text_hash)
        pub_key = self.get_public_key(self.recipient)
        cipherrsa = PKCS1_OAEP.new(pub_key)
        sig = cipherrsa.encrypt(signature[:128])
        sig = sig + cipherrsa.encrypt(signature[128:])
        return base64.encodebytes(sig).decode().strip()


    @staticmethod
    def calc_hash(string: str) -> str:
        return SHA256.new(string.encode()).hexdigest()


    @private
    def get_public_key(self, user_hash: str) -> RsaKey:
        cur.execute(f"select public_key from {DB_TABLE} where username='{user_hash}'")
        key_str = cur.fetchone()[0]
        key = RSA.import_key(key_str)
        return key


    @property
    def json(self) -> dict:
        metadata = {}
        metadata["sign"] = self.sign
        metadata["timestamp"] = self.timestamp
        metadata["sender"] = self.sender
        metadata["recipient"] = self.recipient
        
        data = {}
        data["message"] = self.message
        data["key"] = self.key
        data["metadata"] = metadata

        return data


    @classmethod
    def load_from_json(cls, data: dict) -> Message:
        msg_object = cls(None, None, None, None)
        metadata = data["metadata"]

        msg_object.__dict__["timestamp"] = metadata["timestamp"]
        msg_object.__dict__["sender"] = metadata["sender"]
        msg_object.__dict__["recipient"] = metadata["recipient"]
        msg_object.__dict__["key"] = data["key"]
        msg_object.__dict__["message"] = data["message"]
        msg_object.__dict__["sign"] = metadata["sign"]

        
        return msg_object
    

    def decrypt_message(self, key: RsaKey) -> str:
        cipherrsa = PKCS1_OAEP.new(key)
        session_key = base64.decodebytes(self.key.encode())
        session_key = cipherrsa.decrypt(session_key)
        
        ciphertext = base64.decodebytes(self.message.encode())
        iv = ciphertext[:16]

        obj = AES.new(session_key, AES.MODE_CFB, iv)
        msg = obj.decrypt(ciphertext[16:]).decode()
        pub_key = self.get_public_key(self.sender)

        if self.verify(msg, key, pub_key):
            return msg
        
        raise VerifyError
        

    @private
    def verify(self, message: str, pr_key: RsaKey, pub_key: RsaKey) -> bool:
        cipherrsa = PKCS1_OAEP.new(pr_key)
        signature = base64.decodebytes(self.sign.encode())
        sig = cipherrsa.decrypt(signature[:256])
        sig = sig + cipherrsa.decrypt(signature[256:])

        msg_hash = SHA256.new(message.encode())
        signature = PKCS1_v1_5.new(pub_key)

        return signature.verify(msg_hash, sig)
import json
from Crypto.PublicKey.RSA import RsaKey
from Crypto.Cipher import AES
from Crypto import Random
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA
from Crypto.Signature import PKCS1_v1_5
import os
from dotenv import load_dotenv
import psycopg2
from datetime import datetime
import base64

load_dotenv()
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

class Transaction:
    def __init__(self, sender: str, recipient: str, message: str) -> None:
        self.sender = sender
        self.recipient = recipient
        self.message, self.session_key = self.encrypt_message(message)
        # self.__recipient_public_key = self.get_public_key(recipient)
        self.sign = self.sign_message(message)
        self.sender_public_key = self.get_public_key(sender)
    

    def __str__(self) -> str:
        data = f"{' CLASS TRANSACTION ':-^75}\n"
        for name in self.__dict__:
            data += f"{name.capitalize()}: {self.__dict__[name]}\n\n"
        
        return data
    

    @staticmethod
    def get_public_key(username: str) -> str:
        query = f"select public_key from my_users where username = '{username}'"
        cur.execute(query)
        resp = cur.fetchone()
        if resp is None:
            raise ValueError("Такого получателя нет, проверьте имя")
        else:
            return resp[0]

    
    
    def load_private_key(self) -> str:
        with open(f"metadata/{self.sender}_metadata.json", "r") as f:
            return json.load(f)["keys"]["private"]
    

    def encrypt_message(self, message: str) -> tuple:
        session_key = Random.new().read(32)
        iv = Random.new().read(16)

        obj = AES.new(session_key, AES.MODE_CFB, iv)
        message = iv + obj.encrypt(bytes(message.encode()))
        message = base64.encodebytes(message).decode().strip()

        cipherrsa = PKCS1_OAEP.new(RSA.import_key(self.get_public_key(self.recipient)))
        session_key = cipherrsa.encrypt(session_key)
        session_key = base64.encodebytes(session_key).decode().strip()
        
        # data = {}
        # data["message"] = message
        # data["session_key"] = session_key

        return (message, session_key)


    def sign_message(self, message: str) -> str:
        text_hash = SHA.new(bytes(message.encode()))
        signature = PKCS1_v1_5.new(RSA.import_key(self.load_private_key()))
        signature = signature.sign(text_hash)

        cipherrsa = PKCS1_OAEP.new(RSA.import_key(self.get_public_key(self.recipient)))
        sig = cipherrsa.encrypt(signature[:128])
        sig = sig + cipherrsa.encrypt(signature[128:])

        return base64.encodebytes(sig).decode().strip()


    @property
    def json(self) -> str:
        data = {}
        data["sender"] = self.sender
        data["recipient"] = self.recipient
        data["message_meta"] = {
            "message": self.message,
            "session_key": self.session_key
            }
        data["sender_public_key"] = self.sender_public_key
        data["sign"] = self.sign

        return data


    @staticmethod
    def decrypt_message(data: dict, recipient_private_key: str) -> dict:
        cipherrsa = PKCS1_OAEP.new(RSA.import_key(recipient_private_key))
        
        session_key = data["message_meta"]["session_key"]
        session_key = base64.decodebytes(session_key.encode())
        session_key = cipherrsa.decrypt(session_key)

        cipher_text = data["message_meta"]["message"]
        cipher_text = base64.decodebytes(cipher_text.encode())
        iv = cipher_text[:16]
        obj = AES.new(session_key, AES.MODE_CFB, iv)

        cipher_text = obj.decrypt(cipher_text)[16:]

        test = Transaction.verify(data["sign"], data["sender_public_key"], recipient_private_key, cipher_text.decode())
        if test:
            return {"status": "ok", "message": cipher_text.decode()}
        else:
            return {"status": "failed", "message": ""}


    @staticmethod
    def verify(sign: str, sender_public_key: str, recipient_private_key: str, text: str) -> bool:
        signature = base64.decodebytes(sign.encode())
        
        private_key = RSA.import_key(recipient_private_key)
        public_key = RSA.import_key(sender_public_key)

        cipherrsa = PKCS1_OAEP.new(private_key)
        sig = cipherrsa.decrypt(signature[:256])
        sig = sig + cipherrsa.decrypt(signature[256:])

        text_hash = SHA.new(bytes(text.encode()))
        signature = PKCS1_v1_5.new(public_key)

        test = signature.verify(text_hash, sig)
        return test


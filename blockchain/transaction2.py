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
import jwt
from cryptography.hazmat.primitives import serialization
from jwt.exceptions import InvalidSignatureError

load_dotenv()
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

class Transaction:

    def __init__(self, sender: str, recipient: str, message: str) -> None:
        self.timestamp = str(datetime.now())
        self.sender = sender
        self.recipient = recipient
        self.token = self.generate_token(self.__generate_payload(message))

    
    def __str__(self) -> str:
        data = f"{' CLASS TRANSACTION ':-^75}\n"
        for name in self.__dict__:
            data += f"{name.capitalize()}: {self.__dict__[name]}\n"
        return data.strip()


    def __generate_payload(self, message: str) -> dict:
        data = {}
        data["timestamp"] = str(datetime.now())
        payload = {}
        payload["sender"] = self.sender
        payload["recipient"] = self.recipient
        payload["message"] = message
        data["payload"] = payload

        return data


    @staticmethod
    def load_private_key(username: str) -> str:
        with open(f"metadata/{username}_metadata.json", "r") as f:
            return json.load(f)["keys"]["private"]

    
    def generate_token(self, payload: dict) -> str:
        key = self.load_private_key(self.sender)
        token = jwt.encode(
            payload=payload,
            key=key,
            algorithm="RS256"
        )

        return token

    
    @staticmethod
    def verify(token, public_key) -> dict:
        try:
            decoded = jwt.decode(
                jwt=token,
                key=public_key,
                algorithms="RS256"
            ) 
            return {"status": "ok", "data": decoded}
        except InvalidSignatureError:
            return {"status": "invalid signature", "data": ""}
        
        except:
            return {"status": "public key error", "data": ""}

    
    @staticmethod
    def get_public_key(username: str) -> str:
        query = f"select public_key from my_users where username = '{username}'"
        cur.execute(query)
        return cur.fetchone()[0]

    
    @property
    def json(self) -> str:
        return json.dumps(self.__dict__)
import psycopg2
from dotenv import load_dotenv
import json
import os
from datetime import datetime
from Crypto.PublicKey import RSA
from Crypto.PublicKey.RSA import RsaKey
import json

load_dotenv()

# создание ключей и их экспорт
def generate_key(*filenames: tuple[str], key_len: int = 2048) -> dict[str, dict[str, RsaKey]]:
    """
    Генерация ключей

    Args:
        filenames (tuple[str]): список имен для генераци ключей
        key_len (int, optional): длина ключа. По умолчанию 2048

    Raises:
        ValueError: Отстутствует имя файла
    
    Returns:
        dict: {name: dict: {private: ключ, public: ключ}}
    """

    private_key = RSA.generate(key_len)
    public_key = private_key.publickey()

    if len(filenames) == 0:
        raise ValueError("Надо обязательно указать хотя бы одно имя")
    else:
        keys = {}
        for name in filenames:
            keys[name] = {"private": private_key.export_key("PEM").decode("ascii"), "public": public_key.export_key("PEM").decode("ascii")}

    return keys

def create_keys(name: str) -> None:
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()

    cur.execute(f"select public_key from my_users where username ='{name}'")
    resp = cur.fetchone()
    
    if resp is None:
        keys = generate_key(name)[name]
        private = keys["private"]
        public = keys["public"]

        with open(f"metadata/{name}_metadata.json", "w") as f:
            data = {}
            data["timestamp"] = str(datetime.now())
            data["username"] = name
            data["keys"] = {"private": private, "public": public}

            cur.execute(f"insert into my_users values ('{name}', '{public}')")
            conn.commit()

            json.dump(data, f)
    else:
        print("Все ок, вы уже есть в базе")
    conn.close()
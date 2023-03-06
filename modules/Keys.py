from Crypto.PublicKey import RSA
from Crypto.PublicKey.RSA import RsaKey
from Crypto.Hash import SHA256
from .Database import cur, conn, DB_TABLE
from .ProgressBar import progress
import json


def generate_keys(username: str, key_len: int = 2048) -> None:
    print("Загрузка данных...")
    
    private_key = RSA.generate(key_len)
    public_key = private_key.public_key().export_key("PEM").decode()
    user_hash = SHA256.new(username.encode()).hexdigest()

    progress(20, ".")


    # проверка на наличие в базе, если нету, то происходит добавление
    cur.execute(f"select * from {DB_TABLE} where username='{user_hash}'")
    if cur.fetchone():
        print("Все готово")
        print()
        return
    

    print("Создание данных...")
    print()
    with open(f"metadata/{user_hash}.json", "w") as fo:
        data = {}
        data["username"] = user_hash
        data["pk_key"] = private_key.export_key("PEM").decode()
        json.dump(data, fo)
        cur.execute(f"insert into {DB_TABLE} values ('{user_hash}', '{public_key}')")
        conn.commit()
        return


def load_key(username: str) -> RsaKey:
    user_hash = SHA256.new(username.encode()).hexdigest()
    with open(f"metadata/{user_hash}.json", "r") as fi:
        key_str = json.load(fi)["pk_key"]
        return RSA.import_key(key_str)
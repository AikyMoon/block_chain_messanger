from flask import Flask, request
from modules.Database import cur, conn
from psycopg2.extras import Json
import json

app = Flask(__name__)


def add_user(username: str, json_data = None) -> None:
    cur.execute(f"select username from users_online where username='{username}'")
    if cur.fetchone():
        return
    
    if json_data:
        cur.execute(f"insert into users_online values ('{username}', true, ARRAY{[json.dumps(json_data)]}::json[])")
    else:
        cur.execute(f"insert into users_online values ('{username}', true)")
    conn.commit()


@app.route('/send', methods=["POST"])
def hello():
    data = request.json
    sender = data["metadata"]["sender"]
    recipient = data["metadata"]["recipient"]
    print(request.remote_addr)

    # add_user(sender)
    # add_user(recipient, data)

    # print(data)
    return {"status_code": 200, "ip": request.remote_addr}


# if __name__ == "__main__":
#     app.run()
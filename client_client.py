import socket
from modules import *
from pprint import pprint
import requests

HOST = "192.168.1.69"
PORT = 2000

name = "Alisa"
rec = "Bob"
msg = "hello"

pk_key = load_key(name)
msg = Message(name, rec, msg, pk_key)

response = requests.post("http://127.0.0.1:5000/send", json = msg.json)
print(response)
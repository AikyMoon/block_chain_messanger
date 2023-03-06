import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

DB_NAME = os.getenv("LOCAL_DB_NAME")
DB_LOGIN = os.getenv("LOCAL_DB_LOGIN")
DB_HOST = os.getenv("LOCAL_DB_HOST")
DB_PASSWORD = os.getenv("LOCAL_DB_PASSWORD")
DB_PORT = os.getenv("LOCAL_DB_PORT")
DB_TABLE = os.getenv("LOCAL_DB_TABLE")

conn = psycopg2.connect(database=DB_NAME, user=DB_LOGIN, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
cur = conn.cursor()
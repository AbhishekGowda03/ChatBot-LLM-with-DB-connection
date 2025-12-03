import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


def db_query(query):
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        dbname=os.getenv("DB_NAME")
    )
    cur = conn.cursor()
    cur.execute(query)
    try:
        result = cur.fetchall()
    except:
        result = None

    conn.commit()
    cur.close()
    conn.close()
    return result

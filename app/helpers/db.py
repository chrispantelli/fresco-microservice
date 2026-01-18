import os
import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import connection as PGConnection

load_dotenv()

def get_db_connection() -> PGConnection:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("Missing DATABASE_URL")

    return psycopg2.connect(database_url)
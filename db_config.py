import os
import mysql.connector
from urllib.parse import urlparse

def get_connection():
    url = os.getenv("DATABASE_URL")

    if not url:
        raise Exception("DATABASE_URL not found in environment!")

    parsed = urlparse(url)

    return mysql.connector.connect(
        host=parsed.hostname,
        user=parsed.username,
        password=parsed.password,
        port=parsed.port,
        database=parsed.path.lstrip("/")
    )

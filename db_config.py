import mysql.connector

def get_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",          # apna MySQL user
        password="root123",   # apna MySQL password
        database="canteen_queue"
    )
    return conn

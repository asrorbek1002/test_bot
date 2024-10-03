import sqlite3

def create_connect():
    conn = sqlite3.connect("BotDB.db")
    return conn
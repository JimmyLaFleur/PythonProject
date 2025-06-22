import sqlite3

def connect():
    return sqlite3.connect('finance_bot.db')

def drop_tables(connection):
    with connection:
        connection.executescript('''
        DROP TABLE IF EXISTS spendings;
        DROP TABLE IF EXISTS users;
        ''')

def create_tables(connection):
    with connection:
        connection.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE
        );

        CREATE TABLE IF NOT EXISTS spendings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            price INTEGER NOT NULL,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        ''')

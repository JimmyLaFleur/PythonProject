import psycopg2

import DBManager as db
from config import host, user, password, db_name


conn = (db.connect())
db.drop_tables(conn)
db.create_tables(conn)
db.execute_query(conn, "INSERT INTO categories VALUES (0, 'Без категории')")
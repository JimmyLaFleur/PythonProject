
import DBManager as db

conn = db.connect()
db.drop_tables(conn)
db.create_tables(conn)
conn.close()

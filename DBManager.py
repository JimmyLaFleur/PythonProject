import psycopg2
from config import host, user, password, db_name

def connect():
    try:
        connection = psycopg2.connect(
            database=db_name,
            user=user,
            password=password,
            host=host)
        connection.autocommit = True

        with connection.cursor() as cursor:
            cursor.execute('SELECT version();')
            print(f"Server version: {cursor.fetchone()}")
        return connection
    except Exception as e:
        print("[INFO] Error while working with PostgreSQL:", e)

def create_tables(connection):
    with connection.cursor() as cursor:
        cursor.execute('''
        CREATE TABLE telegram_profiles (
        id SERIAL PRIMARY KEY UNIQUE,
        telegram_id INT NOT NULL UNIQUE
        );
        
        CREATE TABLE categories (
        id SERIAL PRIMARY KEY UNIQUE,
        title varchar(30) NOT NULL UNIQUE
        );
        
        CREATE TABLE users (
        id SERIAL PRIMARY KEY UNIQUE,
        telegram_id INT REFERENCES telegram_profiles(id) NOT NULL UNIQUE
        );
        
        CREATE TABLE spendings (
        id SERIAL PRIMARY KEY UNIQUE,
        user_id INT REFERENCES users(id) NOT NULL,
        price INT NOT NULL,
        category_id INT REFERENCES categories(id) NOT NULL ,
        date TIMESTAMP NOT NULL,
        rate INT
        );''')


# finally:
#     if connection:
#         connection.close()
#         print("[INFO] PostgreSQL connection is closed")
def execute_query(connection, query):
    with connection.cursor() as cursor:
        cursor.execute(query)
def add_user(connection, user_id):
    execute_query(connection, f"INSERT INTO telegram_profiles (telegram_id) VALUES ({user_id}) ON CONFLICT DO NOTHING")

# def create_tables(connection):
#     with connection.cursor() as cursor:
#         cursor.execute('''CREATE TABLE users (
# 	    id SERIAL PRIMARY KEY,
# 	    spendings_id INT
#         );'''
#         )
if __name__ == '__main__':
    create_tables(connect())